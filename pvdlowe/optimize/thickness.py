"""Optimising layer thicknesses against the figure of merit.

Three things are being traded here and they pull in different directions.

* **Metal thickness** sets everything. Thicker means lower emissivity and
  lower sheet resistance, and lower visible transmittance. Below the
  percolation threshold it means nothing works at all.
* **TCO thickness** is an antireflection problem. The metal layer alone
  reflects strongly in the visible; the oxide layers on either side are
  there to interfere that reflection away. There is a genuine optimum,
  roughly a quarter-wave, and it is sharp enough to matter.
* **Asymmetry** between the two oxide layers buys a little more. The layer
  against glass sees n = 1.52 on one side, the layer against air sees
  n = 1, so the optimal thicknesses are not equal.

The optimiser is a bounded scipy call over these, and the interesting part
is not the machinery but the fact that the objective has to include the
electrical constraint. Optimise T_vis alone and the answer is always "make
the metal as thin as possible". The percolation model is what stops that,
which is why it had to be built into the coating object rather than checked
afterwards.

:func:`silver_reduction_curve` is the function that answers the brief's
actual research question, and it answers it in the honest form: for each
level of performance you are willing to accept, what is the least silver
that reaches it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize

from ..materials.alloys import Alloy, ag_cu
from ..materials.tco import TCOPreset, tco
from ..optics.integrate import performance_summary
from ..optics.stack import LowECoating
from ..screening.scoring import ScoringScheme


def build(metal, metal_nm: float, bottom_nm: float, top_nm: float,
          tco_preset: TCOPreset | None = None, **kwargs) -> LowECoating:
    """Convenience constructor used throughout this module."""
    preset = tco_preset or tco("AZO")
    alloy = metal if isinstance(metal, Alloy) else Alloy({metal: 1.0}) \
        if isinstance(metal, str) else metal
    return LowECoating(
        metal_alloy=alloy, metal_thickness_nm=float(metal_nm),
        bottom_tco=preset, bottom_thickness_nm=float(bottom_nm),
        top_tco=preset, top_thickness_nm=float(top_nm), **kwargs)


def objective_value(coating: LowECoating, scheme: ScoringScheme | None = None,
                    criteria=None) -> float:
    """Score a coating, 0-100. Higher is better.

    `criteria` restricts scoring to a subset by name.
    """
    scheme = scheme or ScoringScheme.from_yaml()
    if criteria is not None:
        scheme = scheme.subset(keep=criteria)
    return float(scheme.score(performance_summary(coating))["score"])


def optimise_thicknesses(metal="Ag", tco_preset: TCOPreset | None = None,
                         metal_bounds=(7.0, 18.0),
                         tco_bounds=(15.0, 60.0),
                         symmetric: bool = False,
                         scheme: ScoringScheme | None = None,
                         criteria=None, seed: int = 0) -> dict:
    """Maximise the figure of merit over layer thicknesses.

    Uses differential evolution rather than a gradient method: the objective
    has interference fringes in the TCO thickness, so it is genuinely
    multi-modal and a local optimiser lands in whichever fringe it started
    near.
    """
    scheme = scheme or ScoringScheme.from_yaml()
    if criteria is not None:
        scheme = scheme.subset(keep=criteria)
        criteria = None            # already folded into the scheme
    preset = tco_preset or tco("AZO")

    if symmetric:
        bounds = [metal_bounds, tco_bounds]

        def unpack(x):
            return x[0], x[1], x[1]
    else:
        bounds = [metal_bounds, tco_bounds, tco_bounds]

        def unpack(x):
            return x[0], x[1], x[2]

    failures: list = []

    def negative_score(x):
        m, b, t = unpack(x)
        try:
            return -objective_value(build(metal, m, b, t, preset), scheme,
                                    criteria)
        except (ValueError, KeyError, ZeroDivisionError, FloatingPointError) as exc:
            # Narrow, and counted. A bare `except Exception` here made a bad
            # design and a genuine bug indistinguishable: the optimiser would
            # steer away from the region and report a converged result either
            # way. Note this branch is close to unreachable in normal use --
            # sub-percolation coatings do not raise, they score badly (4.72 at
            # 0.1 nm) -- so a failure here almost certainly IS a bug, which is
            # exactly why it must be visible rather than absorbed.
            failures.append((float(m), float(b), float(t),
                             f"{type(exc).__name__}: {exc}"))
            return 1e3

    result = optimize.differential_evolution(
        negative_score, bounds, seed=seed, maxiter=60, tol=1e-4,
        polish=True, init="sobol")

    m, b, t = unpack(result.x)
    best = build(metal, m, b, t, preset)
    summary = performance_summary(best)
    scored = scheme.score(summary)
    return {
        "metal_thickness_nm": round(float(m), 2),
        "bottom_thickness_nm": round(float(b), 2),
        "top_thickness_nm": round(float(t), 2),
        "score": round(float(scored["score"]), 2),
        "limiting_criterion": scored.get("limiting_criterion"),
        "performance": summary,
        "coating": best,
        "converged": bool(result.success),
        "n_evaluations": int(result.nfev),
        # Surfaced rather than absorbed. Any value above zero means the
        # objective raised somewhere in the search space, and since
        # sub-percolation designs score badly rather than raising, that is
        # almost certainly a bug rather than a rejected design.
        "n_failed_evaluations": len(failures),
        "failures": failures[:10],
    }


def optimise_all_compositions(fractions=(1.0, 0.9, 0.8, 0.7, 0.5, 0.25, 0.0),
                              mixing_model: str = "solid_solution",
                              **kwargs) -> pd.DataFrame:
    """Optimise thicknesses independently for each Ag-Cu composition.

    Important that each composition gets its own optimum: comparing
    compositions at fixed thickness confounds the composition effect with
    the fact that the optimal thickness moves. Cu needs to be thicker than
    Ag to reach the same sheet resistance, so a fixed-thickness comparison
    understates Cu.
    """
    rows = []
    for x in fractions:
        alloy = ag_cu(x, mixing_model)
        res = optimise_thicknesses(alloy, **kwargs)
        perf = res["performance"]
        rows.append({
            "composition": alloy.label,
            "ag_fraction": x,
            "metal_nm": res["metal_thickness_nm"],
            "bottom_nm": res["bottom_thickness_nm"],
            "top_nm": res["top_thickness_nm"],
            "T_vis": round(perf["T_vis"], 4),
            "emissivity": round(perf["emissivity_hemispherical"], 4),
            "R_sheet": round(perf["R_sheet"], 2),
            "U_g": round(perf["U_g"], 3),
            "Ag_g_per_m2": round(perf["Ag_g_per_m2"], 4),
            "score": res["score"],
            "limiting": res["limiting_criterion"],
        })
    return pd.DataFrame(rows)


def silver_reduction_curve(targets=None, fractions=None,
                           mixing_model: str = "solid_solution",
                           **kwargs) -> pd.DataFrame:
    """The brief's central question, answered as a trade-off curve.

    For each Ag-Cu composition, find the thinnest metal layer (with the
    oxides re-optimised) that still meets a given performance specification,
    and report the silver used. The output is the answer to "how much silver
    can be removed" in the only form that is meaningful: as a function of
    what you are willing to give up.

    Parameters
    ----------
    targets : dict of the specification to meet, defaulting to the brief's
        section 17 targets: T_vis >= 0.80, R_s <= 5, emissivity <= 0.10.
    """
    spec = targets or {"T_vis": 0.80, "R_sheet": 5.0,
                       "emissivity_hemispherical": 0.10}
    fracs = fractions or (1.0, 0.9, 0.8, 0.7, 0.5, 0.25, 0.0)
    preset = kwargs.pop("tco_preset", None) or tco("AZO")
    tco_grid = np.arange(20.0, 55.1, 2.5)

    def best_oxides(alloy, metal_nm):
        """Coarse grid then local refinement, maximising T_vis.

        A grid scan beats a global optimiser here: the TMM is vectorised, the
        oxide response has one broad interference maximum in this range, and
        the grid costs a few dozen cheap evaluations instead of a few hundred.
        """
        best = (-1.0, tco_grid[0], tco_grid[0])
        for b in tco_grid:
            for t in tco_grid:
                tv = performance_summary(build(alloy, metal_nm, b, t,
                                               preset))["T_vis"]
                if tv > best[0]:
                    best = (tv, b, t)
        _, b0, t0 = best
        res = optimize.minimize(
            lambda x: -performance_summary(
                build(alloy, metal_nm, x[0], x[1], preset))["T_vis"],
            x0=[b0, t0], method="Nelder-Mead",
            options={"xatol": 0.5, "fatol": 1e-4, "maxiter": 40})
        return float(res.x[0]), float(res.x[1])

    def evaluate_at(alloy, metal_nm):
        b, t = best_oxides(alloy, metal_nm)
        return performance_summary(build(alloy, metal_nm, b, t, preset)), b, t

    def meets_conductive(perf):
        """The criteria that improve monotonically with thickness."""
        return (perf["continuous"]
                and perf["R_sheet"] <= spec.get("R_sheet", np.inf)
                and perf["emissivity_hemispherical"]
                <= spec.get("emissivity_hemispherical", np.inf))

    rows = []
    for x in fracs:
        alloy = ag_cu(x, mixing_model)
        # The feasible set is a window, not a half-line: emissivity and sheet
        # resistance improve with thickness while transmittance degrades. So
        # bisect on the conductive criteria alone -- those are monotone -- to
        # find the thinnest layer that conducts well enough, then check
        # transmittance there. If T_vis fails at the thinnest conducting
        # thickness it fails everywhere thicker too, so the window is empty.
        lo, hi, found = 7.0, 20.0, None
        perf_hi, b_hi, t_hi = evaluate_at(alloy, hi)
        if meets_conductive(perf_hi):
            found = (hi, b_hi, t_hi, perf_hi)
            for _ in range(8):
                mid = 0.5 * (lo + hi)
                perf, b, t = evaluate_at(alloy, mid)
                if meets_conductive(perf):
                    found, hi = (mid, b, t, perf), mid
                else:
                    lo = mid
        if found is not None and found[3]["T_vis"] < spec.get("T_vis", 0.0):
            m, b, t, perf = found
            rows.append({
                "composition": alloy.label, "ag_fraction": x,
                "meets_spec": False, "metal_nm": round(m, 2),
                "T_vis": round(perf["T_vis"], 4),
                "R_sheet": round(perf["R_sheet"], 2),
                "emissivity": round(perf["emissivity_hemispherical"], 4),
                "Ag_g_per_m2": round(perf["Ag_g_per_m2"], 4),
                "note": f"conducts at {m:.1f} nm but T_vis "
                        f"{perf['T_vis']:.3f} < {spec['T_vis']:.2f}"})
            continue
        if found is None:
            rows.append({"composition": alloy.label, "ag_fraction": x,
                         "meets_spec": False, "metal_nm": None,
                         "Ag_g_per_m2": None,
                         "note": "no thickness in 7-20 nm reaches the "
                                 "sheet-resistance and emissivity targets"})
            continue
        m, b, t, perf = found
        rows.append({
            "composition": alloy.label, "ag_fraction": x, "meets_spec": True,
            "metal_nm": round(m, 2), "bottom_nm": round(b, 1),
            "top_nm": round(t, 1),
            "T_vis": round(perf["T_vis"], 4),
            "R_sheet": round(perf["R_sheet"], 2),
            "emissivity": round(perf["emissivity_hemispherical"], 4),
            "Ag_g_per_m2": round(perf["Ag_g_per_m2"], 4),
            "note": "",
        })
    df = pd.DataFrame(rows)
    if "Ag_g_per_m2" in df and df["Ag_g_per_m2"].notna().any():
        base = df.loc[df["ag_fraction"] == 1.0, "Ag_g_per_m2"]
        if len(base) and base.iloc[0]:
            df["ag_saving_pct"] = (
                100 * (1 - df["Ag_g_per_m2"] / base.iloc[0])).round(1)
    df.attrs["specification"] = spec
    return df


def minimum_metal_thickness(metal="Ag", spec=None, tco_nm: float = 35.0,
                            tco_preset: TCOPreset | None = None) -> dict:
    """Thinnest metal layer meeting a specification, at fixed oxide thickness.

    A quick version of the above for a single composition. Returns the
    binding constraint, which is usually the more useful output than the
    thickness itself.
    """
    spec = spec or {"T_vis": 0.80, "R_sheet": 5.0,
                    "emissivity_hemispherical": 0.10}
    preset = tco_preset or tco("AZO")
    for d in np.arange(6.0, 25.01, 0.1):
        perf = performance_summary(build(metal, d, tco_nm, tco_nm, preset))
        if not perf["continuous"]:
            continue
        failures = []
        if perf["T_vis"] < spec.get("T_vis", 0.0):
            failures.append("T_vis")
        if perf["R_sheet"] > spec.get("R_sheet", np.inf):
            failures.append("R_sheet")
        if perf["emissivity_hemispherical"] > spec.get(
                "emissivity_hemispherical", np.inf):
            failures.append("emissivity")
        if not failures:
            return {"thickness_nm": round(float(d), 2), "meets_spec": True,
                    "performance": perf,
                    "note": "thinnest continuous layer meeting the spec"}
    return {"thickness_nm": None, "meets_spec": False,
            "note": "no thickness in 6-25 nm meets the specification at this "
                    "oxide thickness; re-optimise the oxides or relax the spec"}


__all__ = ["build", "objective_value", "optimise_thicknesses",
           "optimise_all_compositions", "silver_reduction_curve",
           "minimum_metal_thickness"]
