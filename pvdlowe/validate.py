"""Validation: does the model reproduce the literature, and is the literature
internally consistent?

Two separate jobs, both worth doing before any of the numbers are used.

**Model validation** runs the framework against each transcribed benchmark
and reports the deviation. Large deviations tell you where the model is weak
-- and the model *is* weak in known places, chiefly visible-range metal
optics, where the Lorentz-Drude fit is only good to a few percent.

**Consistency checking** asks whether a reported set of numbers can all be
true at once, using relations that hold regardless of the model. The strongest
of these is the impedance limit: a conducting layer of sheet resistance R_s
between media of index n1 and n2 has a far-infrared reflectance fixed by

    r = (n1 - n2 - Z0/R_s) / (n1 + n2 + Z0/R_s)

with Z0 = 376.73 ohm the impedance of free space. This follows from the sheet
being much thinner than the wavelength, which at 10 um is true by three
orders of magnitude, and from the DC and far-IR conductivity being close,
which holds when the Drude relaxation energy exceeds the photon energy. It
does not depend on any fitted parameter. A reported emissivity meaningfully
below that limit for its reported sheet resistance means one of the two
numbers is not what it appears to be -- different sample, different spot,
hemispherical versus normal basis, or a transcription error.

This is not scepticism for its own sake. The brief builds its central
recommendation on one such pair, and it is cheaper to check it now than after
six months of sputtering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .materials.alloys import Alloy
from .materials.tco import tco
from .optics.integrate import (normal_emissivity, performance_summary,
                               visible_transmittance)
from .optics.stack import LowECoating
from .provenance import Provenance

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BENCHMARKS_YAML = DATA_DIR / "benchmarks.yaml"

#: Impedance of free space, ohm.
Z0 = 376.730313668

#: Representative far-infrared refractive index of soda-lime glass, used only
#: for the model-independent impedance limit.
N_GLASS_FIR = 2.0


def sheet_resistance_to_emissivity(sheet_resistance: float,
                                   n_substrate: float = N_GLASS_FIR,
                                   n_ambient: float = 1.0) -> float:
    """Lowest emissivity a conducting sheet of this R_s can have.

    Model-independent within the thin-sheet approximation. Any measured
    emissivity below this, for that sheet resistance, needs explaining.
    """
    rs = float(sheet_resistance)
    if rs <= 0:
        return 0.0
    r = (n_ambient - n_substrate - Z0 / rs) / (n_ambient + n_substrate + Z0 / rs)
    return float(np.clip(1.0 - r ** 2, 0.0, 1.0))


def emissivity_to_sheet_resistance(emissivity: float,
                                   n_substrate: float = N_GLASS_FIR,
                                   n_ambient: float = 1.0) -> float:
    """Inverse of the above: the R_s implied by a reported emissivity."""
    eps = float(np.clip(emissivity, 1e-9, 1.0))
    s = np.sqrt(1.0 - eps)          # |r|; r itself is negative for a mirror
    # r = (n1 - n2 - x)/(n1 + n2 + x) = -s  with x = Z0/R_s
    #  ->  x = (n1(1+s) - n2(1-s)) / (1-s)
    denom = 1.0 - s
    if denom < 1e-12:
        return 0.0                  # perfect mirror: zero sheet resistance
    x = (n_ambient * (1.0 + s) - n_substrate * denom) / denom
    return float(Z0 / x) if x > 0 else np.inf


def load_benchmarks(path: Path | None = None) -> list:
    with open(path or BENCHMARKS_YAML) as fh:
        return yaml.safe_load(fh)["benchmarks"]


def _build(arch: dict) -> LowECoating | None:
    if not arch or not arch.get("metal"):
        return None
    preset = tco(arch.get("tco", "AZO"))
    thickness = float(arch.get("tco_thickness_nm", 30.0))
    return LowECoating(
        metal_alloy=Alloy(dict(arch["metal"])),
        metal_thickness_nm=float(arch.get("metal_thickness_nm", 10.0)),
        bottom_tco=preset, bottom_thickness_nm=thickness,
        top_tco=preset, top_thickness_nm=thickness)


@dataclass
class BenchmarkComparison:
    id: str
    label: str
    metric: str
    reported: float
    modelled: float | None
    verified: bool

    @property
    def absolute_error(self):
        if self.modelled is None:
            return None
        return abs(self.modelled - self.reported)

    @property
    def relative_error(self):
        if self.modelled is None or self.reported == 0:
            return None
        return abs(self.modelled - self.reported) / abs(self.reported)


def validate_model(path: Path | None = None,
                   include_disputed: bool = False) -> pd.DataFrame:
    """Compare the framework against the transcribed benchmarks.

    **Disputed entries are excluded by default, and the reason is not
    housekeeping.** The two benchmarks whose figures could not be matched to
    any locatable source happen to be the model's three closest agreements --
    0.3%, 1.0% and 1.2% relative error. Including them puts the median error at
    14.7%; excluding them puts it at 30.6%. The lower number flatters the model
    using values that cannot be traced, so it is not the one to quote.

    Pass ``include_disputed=True`` to see them, which is worth doing when
    auditing rather than reporting. The returned frame carries
    ``.attrs["excluded"]`` naming what was left out, so a table cannot silently
    become the flattering version.
    """
    rows = []
    excluded = []
    for bm in load_benchmarks(path):
        if bm.get("verified") == "disputed" and not include_disputed:
            excluded.append(bm["id"])
            continue
        coating = _build(bm.get("architecture") or {})
        reported = bm.get("reported", {})
        modelled = {}
        if coating is not None:
            summary = performance_summary(coating)
            modelled = {
                "T_vis": summary["T_vis"],
                "R_sheet": summary["R_sheet"],
                "emissivity": summary["emissivity_normal"],
                "far_ir_reflectance": 1.0 - summary["emissivity_normal"],
            }
        for metric, value in reported.items():
            if not isinstance(value, (int, float)):
                continue
            m = modelled.get(metric)
            rows.append({
                "id": bm["id"], "label": bm["label"], "metric": metric,
                "reported": float(value),
                "modelled": None if m is None else round(float(m), 4),
                "abs_error": None if m is None else round(abs(m - value), 4),
                "rel_error_pct": None if m is None or value == 0
                else round(100 * abs(m - value) / abs(value), 1),
                # the flag is tri-state (True / "partial" / "disputed" /
                # False); bool() would report every non-empty string as
                # verified, which is exactly the conflation this system exists
                # to prevent
                "source_state": (bm.get("verified") if bm.get("verified")
                                 else "not located"),
            })
    df = pd.DataFrame(rows)
    df.attrs["excluded"] = excluded
    df.attrs["include_disputed"] = include_disputed
    comparable = df.dropna(subset=["modelled"]) if "modelled" in df else df
    if len(comparable):
        df.attrs["median_rel_error_pct"] = round(
            float(comparable["rel_error_pct"].median()), 1)
    if excluded:
        df.attrs["note"] = (
            f"{len(excluded)} disputed benchmark(s) excluded: "
            f"{', '.join(excluded)}. Their figures could not be matched to any "
            "locatable source, and they are the model's closest agreements, so "
            "including them would overstate its accuracy. Pass "
            "include_disputed=True to audit them.")
    return df


def check_consistency(path: Path | None = None) -> pd.DataFrame:
    """Model-independent consistency checks on the reported benchmark values."""
    findings = []
    for bm in load_benchmarks(path):
        rep = bm.get("reported", {})
        bid, label = bm["id"], bm["label"]

        # 1. emissivity against the impedance limit for the reported R_s
        rs = rep.get("R_sheet")
        eps = rep.get("emissivity")
        if eps is None and rep.get("far_ir_reflectance") is not None:
            eps = 1.0 - rep["far_ir_reflectance"]
        if rs and eps is not None:
            limit = sheet_resistance_to_emissivity(rs)
            implied_rs = emissivity_to_sheet_resistance(eps)
            if eps < limit * 0.85:
                findings.append({
                    "id": bid, "label": label, "severity": "high",
                    "check": "emissivity vs sheet-resistance impedance limit",
                    "detail": (
                        f"reported emissivity {eps:.3f} at {rs:g} ohm/sq is below "
                        f"the thin-sheet limit {limit:.3f} for that sheet "
                        f"resistance; {eps:.3f} would require about "
                        f"{implied_rs:.1f} ohm/sq"),
                    "action": "confirm both were measured on the same sample, "
                              "and whether the emissivity is normal or hemispherical",
                })
            elif eps > limit * 2.0:
                findings.append({
                    "id": bid, "label": label, "severity": "medium",
                    "check": "emissivity vs sheet-resistance impedance limit",
                    "detail": (
                        f"reported emissivity {eps:.3f} at {rs:g} ohm/sq is well "
                        f"above the limit {limit:.3f}; consistent with a "
                        f"discontinuous or heavily damped film, or with extra "
                        f"far-IR absorption in the oxide layers"),
                    "action": "expected if the metal is near percolation; "
                              "otherwise check for oxide absorption",
                })

        # 2. quoted thin-film resistivity against the bulk value
        for key, symbol in (("resistivity_ag_uohm_cm", "Ag"),
                            ("resistivity_cu_uohm_cm", "Cu")):
            if key not in rep:
                continue
            # Local import: keeps validate.py importable without pulling the materials
            # package, which matters because the CLI imports it for a bare `validate`.
            from .materials.metals import metal as _metal
            bulk = _metal(symbol).resistivity_bulk_uohm_cm
            thickness = rep.get("thickness_nm")
            ratio = rep[key] / bulk
            if thickness and ratio < 1.15:
                findings.append({
                    "id": bid, "label": label, "severity": "high",
                    "check": f"{symbol} thin-film resistivity vs bulk",
                    "detail": (
                        f"{rep[key]:g} uohm.cm quoted for a {thickness:g} nm film "
                        f"is {ratio:.2f}x bulk ({bulk:g} uohm.cm). A film this "
                        f"thin cannot reach bulk resistivity: the electron mean "
                        f"free path is {_metal(symbol).mean_free_path_nm:g} nm, "
                        f"so surface and grain-boundary scattering alone force a "
                        f"ratio above about 2"),
                    "action": "check whether the bulk value was tabulated "
                              "alongside measured values for the other films",
                })

        # 3. resistivity, sheet resistance and thickness self-consistency
        rho = rep.get("resistivity_ohm_cm")
        if rho and rs:
            implied_nm = rho / rs * 1e7
            arch_t = (bm.get("architecture") or {}).get("tco_thickness_nm")
            if arch_t and abs(implied_nm - arch_t) / arch_t > 0.25:
                findings.append({
                    "id": bid, "label": label, "severity": "low",
                    "check": "rho / R_s / thickness self-consistency",
                    "detail": (f"rho={rho:g} ohm.cm with R_s={rs:g} ohm/sq implies "
                               f"a {implied_nm:.0f} nm film, against the "
                               f"{arch_t:g} nm recorded"),
                    "action": "record the true film thickness for this entry",
                })
            elif not arch_t:
                findings.append({
                    "id": bid, "label": label, "severity": "info",
                    "check": "rho / R_s / thickness self-consistency",
                    "detail": f"implies a film thickness of about {implied_nm:.0f} nm",
                    "action": "note that this differs from the 30-40 nm layers "
                              "used inside the multilayer stacks",
                })

    return pd.DataFrame(findings)


def verification_status(path: Path | None = None) -> dict:
    """How much of the evidence base has actually been checked."""
    bms = load_benchmarks(path)
    verified = [b for b in bms if b.get("verified") is True]
    partial = [b for b in bms if b.get("verified") == "partial"]
    disputed = [b for b in bms if b.get("verified") == "disputed"]
    unread = len(bms) - len(verified) - len(partial) - len(disputed)
    return {
        "total": len(bms),
        "verified": len(verified),
        "partial": len(partial),
        "disputed": len(disputed),
        "unverified": unread,
        "fraction_verified": round(len(verified) / max(len(bms), 1), 3),
        "provenance": Provenance.LITERATURE_UNVERIFIED,
        "message": (
            f"{len(bms)} benchmarks: {len(verified)} fully verified, "
            f"{len(partial)} located with numbers confirmed against the "
            f"published abstract, {len(disputed)} DISPUTED -- located sources "
            f"do not match the quoted figures -- and {unread} not located.\n"
            "  'partial' means the transcription is right and the source is "
            "identified; it does not mean the full text has been read.\n"
            "  'disputed' means do not cite: the numbers in the brief could "
            "not be matched to any located source."),
    }


def report(path: Path | None = None) -> str:
    """Human-readable validation report."""
    lines = ["=" * 74, "MODEL VALIDATION AGAINST TRANSCRIBED BENCHMARKS", "=" * 74]
    mv = validate_model(path)
    have = mv.dropna(subset=["modelled"])
    lines.append(have.to_string(index=False) if len(have)
                 else "  (no comparable benchmarks)")
    if len(have):
        lines += ["", f"median relative error: "
                      f"{have['rel_error_pct'].median():.1f}%"]
    if mv.attrs.get("excluded"):
        lines += ["", "  " + mv.attrs["note"]]
        alt = validate_model(path, include_disputed=True).dropna(subset=["modelled"])
        if len(alt):
            lines.append(f"  For comparison, including them: "
                         f"{alt['rel_error_pct'].median():.1f}% -- do not quote "
                         "this figure.")

    lines += ["", "=" * 74, "INTERNAL CONSISTENCY OF THE REPORTED VALUES", "=" * 74]
    cc = check_consistency(path)
    if len(cc):
        for _, row in cc.iterrows():
            lines += [f"[{row['severity'].upper():<6}] {row['label']}",
                      f"         check : {row['check']}",
                      f"         detail: {row['detail']}",
                      f"         action: {row['action']}", ""]
    else:
        lines.append("  no inconsistencies detected")

    status = verification_status(path)
    lines += ["=" * 74, "VERIFICATION STATUS", "=" * 74, "  " + status["message"]]
    return "\n".join(lines)


__all__ = ["Z0", "sheet_resistance_to_emissivity", "emissivity_to_sheet_resistance",
           "load_benchmarks", "validate_model", "check_consistency",
           "verification_status", "report", "BenchmarkComparison"]
