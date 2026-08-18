"""Stage-2 compound screening against the Materials Project."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .client import MPClient, MPUnavailable, applicability

#: The chemical systems the brief nominates in its section 9, stage 2.
BRIEF_SYSTEMS = {
    "Zn-O": "ZnO host",
    "Al-Zn-O": "AZO, the primary TCO",
    "Ga-Zn-O": "GZO, the secondary TCO",
    "Sn-O": "SnO2 host",
    "F-Sn-O": "FTO",
    "In-O": "In2O3 host",
    "In-Sn-O": "ITO benchmark",
    "Ti-O": "TiO2 systems",
    "Cu-O": "Cu oxidation products -- the failure mode for the Cu route",
    "Ag-Cu": "the central alloy question",
    "Ag-Cu-O": "oxidation of the alloy",
    "Ag-O": "Ag oxidation, for comparison with Cu",
    "Al-Cu": "dilute Al stabiliser",
    "Cu-Ti": "dilute Ti stabiliser",
    "Ag-Ti": "dilute Ti stabiliser",
}


@dataclass
class CompoundCriteria:
    """Screening thresholds for stage 2."""

    max_energy_above_hull: float = 0.05    # eV/atom
    min_band_gap: float | None = None      # eV, for transparency
    max_band_gap: float | None = None
    require_experimental: bool = False      # exclude 'theoretical' entries

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        mask = df["energy_above_hull"].fillna(1e9) <= self.max_energy_above_hull
        if self.min_band_gap is not None:
            mask &= df["band_gap"].fillna(-1) >= self.min_band_gap
        if self.max_band_gap is not None:
            mask &= df["band_gap"].fillna(1e9) <= self.max_band_gap
        if self.require_experimental and "theoretical" in df.columns:
            mask &= ~df["theoretical"].fillna(True)
        return df[mask]


def screen_system(client: MPClient, chemsys: str,
                  criteria: CompoundCriteria | None = None) -> dict:
    """Query one chemical system and apply the stage-2 filter."""
    crit = criteria or CompoundCriteria()
    entries = client.chemical_system(chemsys)
    df = pd.json_normalize(entries) if entries else pd.DataFrame()
    kept = crit.apply(df)
    return {
        "chemsys": chemsys,
        "n_entries": len(df),
        "all": df,
        "kept": kept,
        "applicability": applicability(chemsys),
    }


def screen_all(client: MPClient, systems=None,
               criteria: CompoundCriteria | None = None) -> dict:
    """Screen every system, recording which queries failed rather than
    silently dropping them."""
    systems = systems or list(BRIEF_SYSTEMS)
    results, failures = {}, {}
    for sys_name in systems:
        try:
            results[sys_name] = screen_system(client, sys_name, criteria)
        except MPUnavailable as exc:
            failures[sys_name] = str(exc)
    return {"results": results, "failures": failures,
            "coverage": f"{len(results)}/{len(systems)} systems retrieved"}


def stability_summary(results: dict) -> pd.DataFrame:
    """One row per system: how many stable phases, and which."""
    rows = []
    for name, res in results.get("results", {}).items():
        kept = res["kept"]
        rows.append({
            "chemsys": name,
            "purpose": BRIEF_SYSTEMS.get(name, ""),
            "entries": res["n_entries"],
            "stable_or_near": len(kept),
            "formulas": ", ".join(sorted(kept.get("formula_pretty", [])))[:80],
        })
    return pd.DataFrame(rows)


def miscibility_verdict(agcu_result: dict) -> dict:
    """Read a segregation verdict off the Ag-Cu convex hull.

    If no intermediate ordered compound sits on or near the hull, the system
    has no thermodynamic driving force to form a compound and will tend to
    phase separate at equilibrium. That is the brief's section 5 point,
    stated as a database observation rather than an assertion.
    """
    df = agcu_result.get("all", pd.DataFrame())
    if df.empty:
        return {"verdict": "no data", "note": "query returned nothing"}
    binaries = df[df["formula_pretty"].str.contains("Ag") &
                  df["formula_pretty"].str.contains("Cu")] \
        if "formula_pretty" in df.columns else pd.DataFrame()
    stable_binaries = binaries[binaries["energy_above_hull"].fillna(1e9) <= 0.01] \
        if not binaries.empty else pd.DataFrame()
    return {
        "n_intermediate_phases": len(binaries),
        "n_stable_intermediate": len(stable_binaries),
        "verdict": ("segregating: no stable ordered Ag-Cu compound"
                    if len(stable_binaries) == 0 else
                    "ordered compound(s) present on the hull"),
        "minimum_hull_distance_eV_per_atom": (
            float(binaries["energy_above_hull"].min()) if not binaries.empty else None),
        "caveat": ("equilibrium statement only. A magnetron-sputtered film is "
                   "quenched from the vapour at effective rates that routinely "
                   "trap metastable solid solutions, so this does not predict "
                   "the as-deposited microstructure -- it predicts what the "
                   "film wants to do when annealed."),
    }


__all__ = ["BRIEF_SYSTEMS", "CompoundCriteria", "screen_system", "screen_all",
           "stability_summary", "miscibility_verdict"]
