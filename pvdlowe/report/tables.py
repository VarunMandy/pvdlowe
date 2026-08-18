"""Result tables, formatted for a report rather than for a console."""

from __future__ import annotations

import pandas as pd

from ..provenance import Provenance
from ..screening.candidates import evaluate_all, load_candidates, not_predicted
from ..screening.pareto import knee_point, pareto_front
from ..screening.scoring import ScoringScheme

#: Display names and rounding for the columns that appear in a report.
COLUMN_SPEC = {
    "id": ("ID", None),
    "label": ("Architecture", None),
    "metal_thickness_nm": ("t_metal (nm)", 1),
    "T_vis": ("T_vis", 3),
    "T_vis_glazed": ("T_vis glazed", 3),
    "T_sol": ("T_sol", 3),
    "g_value": ("g (SHGC)", 3),
    "LSG": ("LSG", 2),
    "selectivity": ("Selectivity", 2),
    "emissivity_normal": ("eps_n", 4),
    "emissivity_hemispherical": ("eps_h", 4),
    "R_sheet": ("R_s (ohm/sq)", 2),
    "U_g": ("U_g (W/m2K)", 2),
    "Ag_g_per_m2": ("Ag (g/m2)", 3),
    "cost_usd_per_m2": ("Metal cost (USD/m2)", 2),
    "supply_risk": ("Supply risk", 1),
    "score": ("Score", 1),
    "limiting_criterion": ("Limiting", None),
    "provenance": ("Provenance", None),
}


def candidate_table(scheme: ScoringScheme | None = None,
                    columns=None, include_hypotheses: bool = True
                    ) -> pd.DataFrame:
    """The main results table: every candidate, evaluated and scored."""
    scheme = scheme or ScoringScheme.from_yaml()
    df = evaluate_all()
    scored = scheme.score_frame(df)[["id", "score", "limiting"]]
    df = df.merge(scored.rename(columns={"limiting": "limiting_criterion"}),
                  on="id", how="left")
    if not include_hypotheses:
        df = df[df["provenance"] != Provenance.HYPOTHESIS.value]
    cols = columns or [c for c in COLUMN_SPEC if c in df.columns]
    out = df[cols].copy()
    for col in out.columns:
        _, digits = COLUMN_SPEC.get(col, (col, None))
        if digits is not None:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)
    out = out.rename(columns={c: COLUMN_SPEC.get(c, (c, None))[0]
                              for c in out.columns})
    return out.sort_values("Score", ascending=False).reset_index(drop=True)


def pareto_table(objectives=None, df: pd.DataFrame | None = None
                 ) -> pd.DataFrame:
    """Non-dominated candidates on the chosen objectives."""
    objectives = objectives or {"T_vis": "higher",
                                "emissivity_hemispherical": "lower",
                                "cost_usd_per_m2": "lower"}
    data = df if df is not None else evaluate_all()
    front = pareto_front(data, objectives).copy()
    # the knee is defined on a two-objective trade; use the silver-versus-
    # transmittance pair, which is the trade the brief actually poses
    knee = None
    if {"Ag_g_per_m2", "T_vis"} <= set(data.columns):
        knee = knee_point(data, "Ag_g_per_m2", "T_vis",
                          x_direction="lower", y_direction="higher")
    front["is_knee"] = (front.index == knee.name) if knee is not None else False
    keep = ["id", "label"] + list(objectives) + ["is_knee"]
    return front[[c for c in keep if c in front.columns]].reset_index(drop=True)


def provenance_table() -> pd.DataFrame:
    """Every candidate with its evidence grade.

    Belongs in any report built on this framework. It is the difference
    between "the model predicts Ag70Cu29Ti1 scores 78" and "the model
    predicts Ag70Cu29Ti1 scores 78 on parameters that have never been
    measured or calculated for that composition".
    """
    rows = []
    for cand in load_candidates():
        rows.append({
            "id": cand.id, "architecture": cand.label,
            "provenance": cand.provenance.value,
            "reportable": not cand.is_hypothesis,
            "purpose": cand.purpose[:70],
        })
    return pd.DataFrame(rows)


def limitations_table() -> pd.DataFrame:
    """What the framework does not predict, and what would be needed."""
    return pd.DataFrame(
        [{"property": k, "why_not": v} for k, v in not_predicted().items()])


def targets_table(scheme: ScoringScheme | None = None) -> pd.DataFrame:
    """The specification being scored against."""
    scheme = scheme or ScoringScheme.from_yaml()
    rows = []
    for name, crit in scheme.criteria.items():
        rows.append({
            "criterion": crit.label, "key": name,
            "direction": crit.direction,
            "unacceptable_at": crit.floor, "satisfied_at": crit.target,
            "unit": crit.unit,
            "weight": scheme.weights.get(name, 0.0),
            "source": (crit.source or "")[:60],
        })
    return pd.DataFrame(rows).sort_values("weight", ascending=False)


def comparison_to_benchmarks(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Each candidate against the Ag benchmark, as percentage changes.

    A reviewer's first question about any proposed substitute is "how much
    worse is it than silver, and how much cheaper". This answers both in one
    table.
    """
    data = df if df is not None else evaluate_all()
    if "id" not in data.columns or "M0" not in set(data["id"]):
        return pd.DataFrame()
    base = data[data["id"] == "M0"].iloc[0]
    rows = []
    for _, row in data.iterrows():
        if row["id"] == "M0":
            continue
        rows.append({
            "id": row["id"], "architecture": row["label"],
            "dT_vis_pct": round(100 * (row["T_vis"] - base["T_vis"])
                                / base["T_vis"], 1),
            "d_emissivity_pct": round(
                100 * (row["emissivity_hemispherical"]
                       - base["emissivity_hemispherical"])
                / base["emissivity_hemispherical"], 1),
            "dR_sheet_pct": round(100 * (row["R_sheet"] - base["R_sheet"])
                                  / base["R_sheet"], 1),
            "silver_saving_pct": round(
                100 * (1 - row["Ag_g_per_m2"] / max(base["Ag_g_per_m2"], 1e-9)), 1),
            "cost_saving_pct": round(
                100 * (1 - row["cost_usd_per_m2"]
                       / max(base["cost_usd_per_m2"], 1e-9)), 1),
        })
    return pd.DataFrame(rows)


__all__ = ["candidate_table", "pareto_table", "provenance_table",
           "limitations_table", "targets_table", "comparison_to_benchmarks",
           "COLUMN_SPEC"]
