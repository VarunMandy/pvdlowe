"""Loading candidate architectures and evaluating them end to end.

This is the join between the material models and the scoring: it takes a
candidate definition, builds the coating, runs the optics and the transport
model, prices the metal, and returns a record the scoring scheme can consume.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from ..materials.alloys import Alloy
from ..materials.tco import tco
from ..optics.integrate import performance_summary
from ..optics.stack import LowECoating
from ..provenance import Provenance
from .elements import coating_material_cost, load_elements

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CANDIDATES_YAML = DATA_DIR / "candidates.yaml"

_PROVENANCE_MAP = {
    "benchmark": Provenance.LITERATURE_UNVERIFIED,
    "candidate": Provenance.MODEL,
    "hypothesis": Provenance.HYPOTHESIS,
}


@dataclass
class Candidate:
    """A named coating architecture with its provenance grade."""

    id: str
    label: str
    coating: LowECoating
    provenance: Provenance
    purpose: str = ""

    @property
    def is_hypothesis(self) -> bool:
        return self.provenance is Provenance.HYPOTHESIS


def load_candidates(path: Path | None = None) -> list:
    """Read candidates.yaml into LowECoating objects."""
    with open(path or CANDIDATES_YAML) as fh:
        cfg = yaml.safe_load(fh)
    defaults = cfg.get("defaults", {})
    out = []
    for entry in cfg["candidates"]:
        spec = {**defaults, **entry}
        alloy = Alloy(dict(spec["metal"]),
                      mixing_model=spec.get("mixing_model", "solid_solution"))
        coating = LowECoating(
            metal_alloy=alloy,
            metal_thickness_nm=float(spec.get("metal_thickness_nm", 10.0)),
            bottom_tco=tco(spec.get("bottom_tco", "AZO")),
            bottom_thickness_nm=float(spec.get("bottom_thickness_nm", 35.0)),
            top_tco=tco(spec.get("top_tco", "AZO")),
            top_thickness_nm=float(spec.get("top_thickness_nm", 35.0)),
            barrier_metal=spec.get("barrier_metal"),
            barrier_thickness_nm=float(spec.get("barrier_thickness_nm", 0.0)),
            label=spec["label"])
        out.append(Candidate(
            id=spec["id"], label=spec["label"], coating=coating,
            provenance=_PROVENANCE_MAP.get(spec.get("provenance", "candidate"),
                                           Provenance.MODEL),
            purpose=(spec.get("purpose") or "").strip()))
    return out


def composition_supply_risk(alloy: Alloy, path: Path | None = None) -> float:
    """Atomic-fraction-weighted supply risk of the metal layer."""
    df = load_elements(path)
    return float(sum(frac * float(df.loc[sym, "supply_risk_score"])
                     for sym, frac in alloy.composition.items()
                     if sym in df.index))


def evaluate(candidate, glass_thickness_mm: float = 4.0, gap_mm: float = 16.0,
             gas: str = "argon", cost_kwargs: dict | None = None) -> dict:
    """Full evaluation of one candidate into a scoreable record.

    Accepts a :class:`Candidate` or a bare :class:`LowECoating`.
    """
    coating = candidate.coating if isinstance(candidate, Candidate) else candidate
    prov = candidate.provenance if isinstance(candidate, Candidate) \
        else Provenance.MODEL

    record = performance_summary(coating, glass_thickness_mm, gap_mm, gas)
    record["id"] = getattr(candidate, "id", coating.label)
    record["label"] = coating.label

    masses = coating.element_areal_mass()
    cost = coating_material_cost(masses, **(cost_kwargs or {}))
    record["cost_usd_per_m2"] = cost["total_usd_per_m2"]
    record["supply_risk"] = composition_supply_risk(coating.metal_alloy)
    record["metal_areal_mass_g_m2"] = sum(masses.values())
    record["film_resistivity_uohm_cm"] = coating.film_resistivity_uohm_cm
    record["size_effect_ratio"] = coating.size_effect_ratio
    record["mixing_model"] = coating.metal_alloy.mixing_model
    record["provenance"] = prov.value
    record["reportable"] = prov in {Provenance.MODEL, Provenance.LITERATURE,
                                    Provenance.LITERATURE_UNVERIFIED,
                                    Provenance.MEASURED}

    # Criteria the framework cannot predict. Left absent rather than guessed:
    # the scoring scheme renormalises over what is present, so a missing
    # thermal-stability measurement reduces confidence instead of the score.
    record.setdefault("thermal_stability_c", None)
    record.setdefault("structural_stability", None)
    record.setdefault("deposition_efficiency", None)
    return record


def evaluate_all(candidates=None, **kwargs) -> pd.DataFrame:
    """Evaluate every candidate into a table."""
    cands = candidates if candidates is not None else load_candidates()
    return pd.DataFrame([evaluate(c, **kwargs) for c in cands])


def not_predicted() -> dict:
    """Criteria in the brief that this framework deliberately does not predict.

    Stated explicitly because the most dangerous kind of model is one that
    quietly returns a number for something it cannot know. The brief's own
    section 17 table makes the same distinction between what DFT can give
    and what needs an experiment; this is the same list for this framework.
    """
    return {
        "deposition_rate": "requires sputter-yield and plasma modelling, or a "
                           "rate calibration on the actual tool; see pvdlowe.doe.sputter",
        "thermal_stability": "requires annealing and thermal-cycling experiments; "
                             "agglomeration of thin Ag is kinetic, not thermodynamic",
        "adhesion": "scratch or tape test only",
        "film_continuity": "predicted only through a calibrated percolation model; "
                           "confirm by SEM/AFM and an R_s(d) series",
        "surface_roughness": "AFM",
        "interdiffusion": "requires interface DFT plus XPS depth profiling",
        "structural_stability": "energy above hull from the Materials Project for "
                                "known crystalline phases; sputtered metastable "
                                "alloys are outside that database by construction",
        "durability": "damp-heat, salt-spray, abrasion; no model substitutes",
    }


__all__ = ["Candidate", "load_candidates", "evaluate", "evaluate_all",
           "composition_supply_risk", "not_predicted", "CANDIDATES_YAML"]
