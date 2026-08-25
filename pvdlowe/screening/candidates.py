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


def record_for(coating, glass_thickness_mm: float = 4.0, gap_mm: float = 16.0,
               gas: str = "argon", cost_kwargs: dict | None = None,
               identifier: str | None = None,
               provenance: Provenance = Provenance.MODEL) -> dict:
    """Build the canonical scoreable record for a coating.

    **This is the single place a scoreable record is constructed.** Everything
    that scores a coating -- :func:`evaluate`, the composition series, the
    sweeps, any analysis script -- must go through here.

    The reason is a defect this replaces. `evaluate()` and
    `optimize.sweep.composition_series()` each built their own record, and the
    hand-rolled one omitted ten keys, three of which are scored criteria. That
    was harmless only because those three were `None` for every candidate and
    :class:`ScoringScheme` renormalises over what is present. The moment any of
    them is populated -- which is the explicit intent, they are defined in
    `targets.yaml` -- the two paths would have scored on different criteria
    subsets, a composition series would have become non-comparable with the
    candidate table, and nothing would have flagged it.

    `identifier` and `provenance` are the only things a :class:`Candidate`
    supplies that a bare coating cannot, so they are parameters rather than a
    reason to have two functions.
    """
    record = performance_summary(coating, glass_thickness_mm, gap_mm, gas)
    record["id"] = identifier if identifier is not None else coating.label
    record["label"] = coating.label

    masses = coating.element_areal_mass()
    cost = coating_material_cost(masses, **(cost_kwargs or {}))
    record["cost_usd_per_m2"] = cost["total_usd_per_m2"]
    record["supply_risk"] = composition_supply_risk(coating.metal_alloy)
    record["metal_areal_mass_g_m2"] = sum(masses.values())
    record["film_resistivity_uohm_cm"] = coating.film_resistivity_uohm_cm
    record["size_effect_ratio"] = coating.size_effect_ratio
    record["mixing_model"] = coating.metal_alloy.mixing_model
    record["provenance"] = provenance.value
    record["reportable"] = provenance in {Provenance.MODEL, Provenance.LITERATURE,
                                          Provenance.LITERATURE_UNVERIFIED,
                                          Provenance.MEASURED}

    # Criteria the framework cannot predict. Left absent rather than guessed:
    # the scoring scheme renormalises over what is present, so a missing
    # thermal-stability measurement reduces confidence instead of the score.
    # They are weighted 0.0 in targets.yaml for the same reason -- see the
    # sixth defect in docs/FINDINGS.md section 2.
    record.setdefault("thermal_stability_c", None)
    record.setdefault("structural_stability", None)
    record.setdefault("deposition_efficiency", None)
    return record


#: Keys every scoreable record carries. Used by the guard test that keeps the
#: two construction paths from drifting apart again.
RECORD_KEYS = frozenset({
    "id", "label", "cost_usd_per_m2", "supply_risk", "metal_areal_mass_g_m2",
    "film_resistivity_uohm_cm", "size_effect_ratio", "mixing_model",
    "provenance", "reportable", "thermal_stability_c", "structural_stability",
    "deposition_efficiency",
})


def evaluate(candidate, glass_thickness_mm: float = 4.0, gap_mm: float = 16.0,
             gas: str = "argon", cost_kwargs: dict | None = None) -> dict:
    """Full evaluation of one candidate into a scoreable record.

    Accepts a :class:`Candidate` or a bare :class:`LowECoating`. A thin wrapper
    over :func:`record_for`, which does the work.
    """
    is_candidate = isinstance(candidate, Candidate)
    coating = candidate.coating if is_candidate else candidate
    return record_for(
        coating, glass_thickness_mm, gap_mm, gas, cost_kwargs,
        identifier=getattr(candidate, "id", coating.label),
        provenance=candidate.provenance if is_candidate else Provenance.MODEL)


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
