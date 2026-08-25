"""Parameter sweeps and maps across composition and thickness."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..materials.alloys import Alloy, ag_cu
from ..materials.tco import tco
from ..optics.integrate import performance_summary
from .thickness import build


def thickness_sweep(metal="Ag", thicknesses=None, tco_nm: float = 35.0,
                    tco_preset=None, mixing_model: str = "solid_solution"
                    ) -> pd.DataFrame:
    """Performance versus metal thickness at fixed oxide thickness."""
    ds = np.asarray(thicknesses if thicknesses is not None
                    else np.arange(6.0, 20.1, 0.5), dtype=float)
    preset = tco_preset or tco("AZO")
    rows = []
    for d in ds:
        perf = performance_summary(build(metal, d, tco_nm, tco_nm, preset))
        rows.append({"metal_nm": float(d), **{
            k: perf[k] for k in ("T_vis", "T_vis_glazed", "T_sol", "R_sheet",
                                 "emissivity_normal", "emissivity_hemispherical",
                                 "U_g", "Ag_g_per_m2", "continuous",
                                 "selectivity")}})
    return pd.DataFrame(rows)


def composition_thickness_map(fractions=None, thicknesses=None,
                              tco_nm: float = 35.0, metric: str = "T_vis",
                              mixing_model: str = "solid_solution",
                              tco_preset=None) -> pd.DataFrame:
    """2D map of one metric over (Ag fraction) x (metal thickness).

    Returned as a pivot table, so `df.values` is directly plottable as a
    contour or heat map.
    """
    fracs = np.asarray(fractions if fractions is not None
                       else np.linspace(0.0, 1.0, 11), dtype=float)
    ds = np.asarray(thicknesses if thicknesses is not None
                    else np.arange(8.0, 18.1, 1.0), dtype=float)
    preset = tco_preset or tco("AZO")
    rows = []
    for x in fracs:
        alloy = ag_cu(float(x), mixing_model)
        for d in ds:
            perf = performance_summary(build(alloy, float(d), tco_nm, tco_nm,
                                             preset))
            rows.append({"ag_fraction": float(x), "metal_nm": float(d),
                         metric: perf[metric]})
    return pd.DataFrame(rows).pivot(index="ag_fraction", columns="metal_nm",
                                    values=metric)


def tco_thickness_sweep(metal="Ag", metal_nm: float = 10.0,
                        thicknesses=None, tco_preset=None) -> pd.DataFrame:
    """Performance versus symmetric oxide thickness.

    Shows the antireflection interference directly. The visible
    transmittance peak is sharp; the emissivity is nearly flat, because at
    10 um a 35 nm oxide is optically invisible. That contrast is the clearest
    demonstration in the framework that the two objectives are controlled by
    different layers.
    """
    ts = np.asarray(thicknesses if thicknesses is not None
                    else np.arange(10.0, 70.1, 2.0), dtype=float)
    preset = tco_preset or tco("AZO")
    rows = []
    for t in ts:
        perf = performance_summary(build(metal, metal_nm, t, t, preset))
        rows.append({"tco_nm": float(t), "T_vis": perf["T_vis"],
                     "R_vis": perf["R_vis"], "A_vis": perf["A_vis"],
                     "emissivity_normal": perf["emissivity_normal"],
                     "R_sheet": perf["R_sheet"]})
    return pd.DataFrame(rows)


def microstructure_comparison(fractions=None, metal_nm: float = 10.0,
                              tco_nm: float = 35.0) -> pd.DataFrame:
    """Solid-solution versus segregated predictions, side by side.

    The output that turns the brief's section 5 caveat into an experiment:
    where the two columns differ by more than measurement uncertainty, a
    spectrophotometer can decide which microstructure the film has.
    """
    fracs = np.asarray(fractions if fractions is not None
                       else (0.9, 0.8, 0.7, 0.5, 0.25), dtype=float)
    rows = []
    for x in fracs:
        out = {"composition": ag_cu(float(x)).label, "ag_fraction": float(x)}
        for model in ("solid_solution", "ema"):
            perf = performance_summary(
                build(ag_cu(float(x), model), metal_nm, tco_nm, tco_nm))
            out[f"T_vis_{model}"] = round(perf["T_vis"], 4)
            out[f"Rs_{model}"] = round(perf["R_sheet"], 2)
            out[f"eps_{model}"] = round(perf["emissivity_hemispherical"], 4)
        out["dT_vis"] = round(out["T_vis_ema"] - out["T_vis_solid_solution"], 4)
        out["dRs"] = round(out["Rs_ema"] - out["Rs_solid_solution"], 2)
        out["distinguishable"] = bool(abs(out["dT_vis"]) > 0.01
                                      or abs(out["dRs"]) > 0.3)
        rows.append(out)
    df = pd.DataFrame(rows)
    df.attrs["note"] = (
        "'distinguishable' uses 1 percentage point in T_vis and 0.3 ohm/sq "
        "as rough measurement resolutions; tighten to your own instrument")
    return df


def composition_series(fractions=None, mixing_model: str = "solid_solution",
                       dielectric: str = "AZO", scheme=None,
                       metal_range=(8.0, 15.0), tco_range=(15.0, 70.0),
                       tco_step: float = 11.0, elements=("Ag", "Cu"),
                       progress=None) -> pd.DataFrame:
    """Score a full binary composition series, geometry optimised per point.

    The point of re-optimising at every composition is that the optimum moves.
    A Cu-rich metal needs a thicker layer to reach a given sheet resistance and
    a different antireflection design to reach a given transmittance, so
    comparing compositions at one fixed geometry systematically favours
    whichever composition the geometry happened to suit.

    **Optimise against the scheme you intend to report.** Geometry chosen for a
    heating-dominated objective and then scored under a cooling-dominated one
    is not a curve -- it is one objective's optimum sampled by another's ruler,
    and it will look erratic because the g-value swings with oxide thickness.
    Pass the scheme you care about; the returned frame records which was used.
    """
    # Local imports: these break an import cycle, since screening imports
    # optics which this module also uses.
    from ..materials.tco import tco as _tco
    from ..screening.candidates import record_for as record
    from ..screening.scoring import ScoringScheme

    scheme = scheme or ScoringScheme.from_yaml()
    fracs = np.asarray(fractions if fractions is not None
                       else np.round(np.arange(0.0, 1.001, 0.05), 3), dtype=float)
    preset = _tco(dielectric)
    a_el, b_el = elements

    rows = []
    for x in fracs:
        if x >= 1.0:
            comp = {a_el: 1.0}
        elif x <= 0.0:
            comp = {b_el: 1.0}
        else:
            comp = {a_el: float(x), b_el: float(1.0 - x)}
        alloy = Alloy(comp, mixing_model=mixing_model)
        best = None
        for dm in np.arange(metal_range[0], metal_range[1] + 0.01, 1.0):
            for b in np.arange(tco_range[0], tco_range[1] + 0.01, tco_step):
                for t in np.arange(tco_range[0], tco_range[1] + 0.01, tco_step):
                    r = record(build(alloy, float(dm), float(b), float(t), preset))
                    if not r["continuous"]:
                        continue
                    sc = scheme.score(r)["score"]
                    if best is None or sc > best[0]:
                        best = (sc, dm, b, t, r)
        if best is None:
            continue
        sc, dm, b, t, r = best
        # Canonical criterion names throughout, including the criteria that
        # are currently unpopulated. An earlier version renamed
        # emissivity_hemispherical to emissivity_h and omitted the three
        # unpopulated criteria, so re-scoring the emitted frame would have
        # silently dropped emissivity -- 0.25 of the weight -- and scored on a
        # different subset from the candidate table. Keep the names the
        # scoring scheme uses.
        rows.append({
            "mixing_model": mixing_model, "dielectric": dielectric,
            f"{a_el}_fraction": float(x), "metal_nm": float(dm),
            "bottom_nm": float(b), "top_nm": float(t),
            "T_vis": round(r["T_vis"], 4), "T_sol": round(r["T_sol"], 4),
            "emissivity_hemispherical": round(r["emissivity_hemispherical"], 4),
            "emissivity_normal": round(r["emissivity_normal"], 4),
            "R_sheet": round(r["R_sheet"], 2),
            "g_value": round(r["g_value"], 3), "LSG": round(r["LSG"], 2),
            "U_g": round(r["U_g"], 3),
            "Ag_g_per_m2": round(r["Ag_g_per_m2"], 4),
            "cost_usd_per_m2": round(r["cost_usd_per_m2"], 3),
            "supply_risk": round(r["supply_risk"], 2),
            "structural_stability": r["structural_stability"],
            "thermal_stability_c": r["thermal_stability_c"],
            "deposition_efficiency": r["deposition_efficiency"],
            "score": round(sc, 1),
            "limiting": scheme.score(r)["limiting_criterion"],
            "meets_spec": bool(r["T_vis"] >= 0.80 and r["R_sheet"] <= 5.0
                               and r["emissivity_hemispherical"] <= 0.10)})
        if progress:
            progress(rows[-1])
    df = pd.DataFrame(rows)
    df.attrs["scheme_aggregation"] = scheme.aggregation
    df.attrs["note"] = ("geometry re-optimised at every composition against "
                        "the supplied scheme; do not re-score this frame under "
                        "a different objective")
    return df


def series_optimum(df: pd.DataFrame, fraction_col: str = "Ag_fraction") -> dict:
    """The peak of a composition series, and how sharp it is.

    Reports the plateau width as well as the argmax, because a broad plateau
    means the composition tolerance is loose and a sharp peak means it is not
    -- which matters more for a sputtering process than the peak position.
    """
    if df.empty:
        return {}
    best = df.loc[df["score"].idxmax()]
    within_one = df[df["score"] >= best["score"] - 1.0]
    return {
        "optimum_fraction": float(best[fraction_col]),
        "optimum_score": float(best["score"]),
        "plateau_low": float(within_one[fraction_col].min()),
        "plateau_high": float(within_one[fraction_col].max()),
        "plateau_width": float(within_one[fraction_col].max()
                               - within_one[fraction_col].min()),
        "Ag_at_optimum_g_per_m2": float(best["Ag_g_per_m2"]),
        "monotonic": bool(df.sort_values(fraction_col)["score"].is_monotonic_increasing
                          or df.sort_values(fraction_col)["score"].is_monotonic_decreasing),
    }


__all__ = ["thickness_sweep", "composition_thickness_map",
           "composition_series", "series_optimum",
           "tco_thickness_sweep", "microstructure_comparison"]
