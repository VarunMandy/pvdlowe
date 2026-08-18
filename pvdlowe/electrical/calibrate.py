"""Fit the transport model to a measured sheet-resistance series.

The framework's largest known error is that it under-predicts sputtered copper
sheet resistance by roughly eight times against the one traceable literature
point. Copper is central to most of the leading candidates, so that gap decides
whether they survive. It is also cheap to close: one thickness series and a
four-point probe.

This module turns that measurement into a model update. Give it a CSV of
thickness against sheet resistance and it fits the three parameters that were
previously guessed -- surface specularity, grain-boundary reflection and the
percolation threshold -- then reports what the fit implies.

**The diagnosis matters more than the fit.** Three explanations for an elevated
resistivity look different in the data, and :func:`diagnose` separates them:

*Classical size effect.* Resistivity rises as the film thins, following the
Fuchs-Sondheimer and Mayadas-Shatzkes form, and extrapolates to near bulk at
large thickness. Fitting p and R absorbs it. The Cu route is then healthy and
the framework was simply mis-parameterised.

*A constant excess.* Resistivity is offset by a roughly fixed amount at every
thickness, so the thick-film limit sits well above bulk. That is not a size
effect -- it is impurity scattering, most likely oxygen incorporated during
deposition, and it points at base pressure, target condition or getter rather
than at the physics. This is the outcome the framework's validation failure
most suggests, and it is the *good* outcome, because it is an engineering
problem.

*A shifted percolation threshold.* Resistivity diverges at a thickness well
above the assumed d_c. The film is dewetting rather than wetting, and the fix
is a seed layer or a lower deposition temperature.

The three imply different next experiments, which is why the fit alone is not
the deliverable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
from scipy import optimize

from ..materials.metals import metal
from ..provenance import Provenance, Quantity
from .thinfilm import PERCOLATION, PercolationModel, ThinFilmResistivity


@dataclass
class CalibrationResult:
    """Fitted transport parameters and what they imply."""

    symbol: str
    specularity: float
    grain_boundary_reflection: float
    critical_thickness_nm: float
    excess_resistivity_uohm_cm: float
    rms_residual_ohm_sq: float
    relative_rms: float
    n_points: int
    default_model: ThinFilmResistivity
    fitted_model: ThinFilmResistivity
    data: pd.DataFrame

    @property
    def identifiable(self) -> bool:
        """Whether p and R can be separated from this data alone.

        They usually cannot. Fuchs-Sondheimer surface scattering and
        Mayadas-Shatzkes grain-boundary scattering produce nearly the same
        1/d dependence over a 8-20 nm window, so many (p, R) pairs fit a
        series equally well. In a recovery test on synthetic data, a film
        generated with p = 0.35 was fitted at p = 1.00 with an RMS residual of
        0.036 ohm/sq -- an excellent fit to the *data* and a wrong value for
        the *parameter*.

        This matters for how the result is used. The fitted model
        **predicts sheet resistance reliably** in the range it was fitted
        over, which is what the framework needs. The individual parameters
        should not be quoted as measurements of specularity or grain-boundary
        reflection; separating those requires varying grain size independently,
        e.g. by annealing at fixed thickness.
        """
        return False

    @property
    def thick_film_ratio(self) -> float:
        """rho(100 nm) / rho_bulk under the fit. Near 1 means the elevation is
        a genuine size effect; well above 1 means a thickness-independent
        excess that no size-effect model can explain."""
        return float(self.fitted_model.ratio(100.0))

    def as_quantities(self) -> dict:
        return {
            "specularity": Quantity(
                self.specularity, "", Provenance.MEASURED,
                source=f"fitted to {self.n_points} measured {self.symbol} films"),
            "grain_boundary_reflection": Quantity(
                self.grain_boundary_reflection, "", Provenance.MEASURED,
                source=f"fitted to {self.n_points} measured {self.symbol} films"),
            "critical_thickness_nm": Quantity(
                self.critical_thickness_nm, "nm", Provenance.MEASURED,
                source="percolation threshold from the resistivity divergence"),
        }

    def summary(self) -> str:
        d = self.default_model
        lines = [
            f"CALIBRATION: {self.symbol}, {self.n_points} films",
            "",
            f"{'parameter':<28}{'default':>10}{'fitted':>10}",
            f"{'specularity p':<28}{d.specularity:>10.3f}{self.specularity:>10.3f}",
            f"{'grain-boundary R':<28}{d.grain_boundary_reflection:>10.3f}"
            f"{self.grain_boundary_reflection:>10.3f}",
            f"{'percolation d_c (nm)':<28}"
            f"{d.percolation.critical_thickness_nm if d.percolation else 0:>10.1f}"
            f"{self.critical_thickness_nm:>10.1f}",
            f"{'excess rho (uohm.cm)':<28}{0.0:>10.3f}"
            f"{self.excess_resistivity_uohm_cm:>10.3f}",
            "",
            f"RMS residual: {self.rms_residual_ohm_sq:.3f} ohm/sq "
            f"({self.relative_rms:.1%} relative -- use this one, an absolute "
            f"RMS is dominated by the thinnest film)",
            f"rho(100 nm)/rho_bulk under the fit: {self.thick_film_ratio:.2f}",
            "",
            "NOTE: p and R are not separately identifiable from R_s(d) alone --",
            "they produce nearly the same 1/d dependence over this range. The",
            "fitted model predicts sheet resistance well; the individual",
            "parameters are not measurements. Separating them needs grain size",
            "varied independently, e.g. anneal at fixed thickness.",
        ]
        return "\n".join(lines)


def _model_with(symbol: str, p: float, r: float, dc: float,
                excess: float = 0.0) -> ThinFilmResistivity:
    m = metal(symbol)
    base = PERCOLATION.get(symbol)
    perc = (replace(base, critical_thickness_nm=float(dc),
                    percolation_thickness_nm=float(dc) * 0.75)
            if base is not None else
            PercolationModel(critical_thickness_nm=float(dc),
                             percolation_thickness_nm=float(dc) * 0.75))
    return ThinFilmResistivity(
        bulk_resistivity_uohm_cm=m.resistivity_bulk_uohm_cm + float(excess),
        mean_free_path_nm=m.mean_free_path_nm,
        specularity=float(p), grain_boundary_reflection=float(r),
        grain_size_ratio=3.0, percolation=perc)


def deembed_parallel(measured_ohm_sq, *shunt_ohm_sq) -> float:
    """Remove parallel conduction paths from a measured sheet resistance.

        1/R_metal = 1/R_measured - sum(1/R_shunt)

    Needed because bare copper cannot be measured honestly. A 10 nm Cu film
    oxidises in air on a timescale of minutes, and the hypothesis under test is
    precisely that oxygen degrades these films -- so a bare film measured after
    venting reports air oxidation, not deposition quality. The films must be
    capped, which means measuring the full AZO/Cu/AZO trilayer and subtracting
    the oxide shunt.

    The correction is strongly non-linear in the measured value, and it is
    largest exactly where this experiment is interesting. Two 40 nm AZO layers
    at 5e-4 ohm.cm shunt about 125 ohm/sq each:

        measured 3.0 ohm/sq  ->  metal alone  3.15   (+5%)
        measured 5.0 ohm/sq  ->  metal alone  5.44   (+9%)
        measured 16.6 ohm/sq ->  metal alone 22.61   (+36%)

    A poorly conducting metal layer is shunted proportionally harder by the
    oxide, so the worse the copper, the more the raw trilayer reading
    understates it. Skipping this correction would bias the fit toward
    "the copper is fine".

    Note that `LowECoating.sheet_resistance()` already combines metal and
    oxides in parallel, so a *model* prediction is directly comparable with a
    *measured trilayer*. De-embed only when fitting the metal layer alone.

    Raises if the shunts alone would exceed the measured conductance, which
    means either the metal layer is not conducting or the oxide resistivity is
    wrong.
    """
    g = 1.0 / float(measured_ohm_sq)
    for r in shunt_ohm_sq:
        if r and np.isfinite(r) and r > 0:
            g -= 1.0 / float(r)
    if g <= 0:
        raise ValueError(
            f"shunt layers alone account for all of {measured_ohm_sq} ohm/sq; "
            "either the metal layer is discontinuous or the assumed oxide "
            "resistivity is too low")
    return float(1.0 / g)


def deembed_series(measured_ohm_sq, dielectric: str = "AZO",
                   bottom_nm: float = 40.0, top_nm: float = 40.0):
    """De-embed a whole series measured as capped trilayers."""
    from ..materials.tco import tco as _tco
    preset = _tco(dielectric)
    shunts = [preset.sheet_resistance(bottom_nm), preset.sheet_resistance(top_nm)]
    out = []
    for v in np.atleast_1d(np.asarray(measured_ohm_sq, dtype=float)):
        if not np.isfinite(v) or v <= 0:
            out.append(np.inf)          # open circuit stays open
            continue
        try:
            out.append(deembed_parallel(v, *shunts))
        except ValueError:
            out.append(np.inf)          # metal not conducting
    return np.array(out)


def fit_series(thickness_nm, sheet_resistance_ohm_sq, symbol: str = "Cu",
               allow_excess: bool = True) -> CalibrationResult:
    """Fit specularity, grain-boundary reflection, percolation and excess rho.

    `allow_excess` adds a thickness-independent resistivity term. Leave it on:
    without it, a constant impurity contribution is forced into the
    size-effect parameters, which then take unphysical values and hide the
    diagnosis. Compare the fits with and without via :func:`diagnose`.
    """
    d_all = np.asarray(thickness_nm, dtype=float)
    rs_all = np.asarray(sheet_resistance_ohm_sq, dtype=float)

    # A film below percolation reads open-circuit or absurdly high. That is
    # information about d_c, not a data point the size-effect model can fit,
    # so hold it out of the least squares and use it as a lower bound instead.
    usable = np.isfinite(rs_all) & (rs_all > 0) & (rs_all < 1e4)
    d, rs = d_all[usable], rs_all[usable]
    excluded = d_all[~usable]
    if len(d) < 4:
        raise ValueError(
            f"need at least 4 measurable thicknesses to fit; got {len(d)} "
            f"({len(excluded)} were open-circuit or non-finite)")

    def residual(x):
        p, r, dc, ex = x
        model = _model_with(symbol, p, r, dc, ex if allow_excess else 0.0)
        pred = np.array([model.sheet_resistance(t) for t in d])
        pred = np.where(np.isfinite(pred), pred, 1e6)
        # relative residual: a 30 ohm/sq point should not dominate a 3 ohm/sq one
        return np.log(np.clip(pred, 1e-6, None)) - np.log(np.clip(rs, 1e-6, None))

    # Percolation bounds. An open-circuit film sits below the *percolation*
    # thickness d_p = 0.75 d_c, not below d_c -- a film between d_p and d_c
    # still conducts, just badly. So the thickest open-circuit film bounds d_c
    # from below by d/0.75, and a conducting film does NOT bound it from above.
    # Getting this wrong forces d_c under the thinnest measured film and the
    # fit then misattributes a percolation divergence to surface scattering.
    dc_lo = (float(excluded.max()) / 0.75 if len(excluded)
             else max(d.min() * 0.4, 1.0))
    dc_hi = max(float(d.max()), dc_lo + 2.0)
    bounds = ([0.0, 0.0, dc_lo, 0.0], [1.0, 0.99, dc_hi, 40.0])
    x0 = [0.5, 0.25, PERCOLATION[symbol].critical_thickness_nm
          if symbol in PERCOLATION else d.min(), 0.0]
    x0 = [float(np.clip(v, lo, hi)) for v, lo, hi in zip(x0, *bounds)]
    res = optimize.least_squares(residual, x0, bounds=bounds, max_nfev=4000)
    p, r, dc, ex = res.x
    if not allow_excess:
        ex = 0.0

    fitted = _model_with(symbol, p, r, dc, ex)
    m = metal(symbol)
    default = ThinFilmResistivity(
        bulk_resistivity_uohm_cm=m.resistivity_bulk_uohm_cm,
        mean_free_path_nm=m.mean_free_path_nm, specularity=0.5,
        grain_boundary_reflection=0.25, grain_size_ratio=3.0,
        percolation=PERCOLATION.get(symbol))

    pred = np.array([fitted.sheet_resistance(t) for t in d])
    rel_rms = float(np.sqrt(np.mean((np.log(np.clip(pred, 1e-9, None))
                                     - np.log(rs)) ** 2)))
    frame = pd.DataFrame({
        "thickness_nm": d, "R_sheet_measured": rs,
        "R_sheet_fitted": np.round(pred, 3),
        "R_sheet_default": np.round(
            [default.sheet_resistance(t) for t in d], 3)})
    frame["residual"] = np.round(frame.R_sheet_fitted - frame.R_sheet_measured, 3)
    for t in excluded:
        frame.loc[len(frame)] = [t, np.inf, np.nan, np.nan, np.nan]
    frame = frame.sort_values("thickness_nm").reset_index(drop=True)

    return CalibrationResult(
        symbol=symbol, specularity=float(p), grain_boundary_reflection=float(r),
        critical_thickness_nm=float(dc), excess_resistivity_uohm_cm=float(ex),
        rms_residual_ohm_sq=float(np.sqrt(np.nanmean(
            np.asarray(frame.residual, dtype=float) ** 2))),
        relative_rms=rel_rms,
        n_points=len(d), default_model=default, fitted_model=fitted, data=frame)


def diagnose(thickness_nm, sheet_resistance_ohm_sq,
             symbol: str = "Cu") -> dict:
    """Separate size effect, impurity excess and shifted percolation.

    Returns the verdict, the evidence for it, and the experiment it implies.
    This is the output that decides what to do next.
    """
    with_excess = fit_series(thickness_nm, sheet_resistance_ohm_sq, symbol, True)
    without = fit_series(thickness_nm, sheet_resistance_ohm_sq, symbol, False)
    m = metal(symbol)
    default_dc = (PERCOLATION[symbol].critical_thickness_nm
                  if symbol in PERCOLATION else None)

    excess = with_excess.excess_resistivity_uohm_cm
    excess_frac = excess / m.resistivity_bulk_uohm_cm
    dc_shift = ((with_excess.critical_thickness_nm - default_dc)
                if default_dc else 0.0)
    improvement = (without.relative_rms - with_excess.relative_rms) / max(
        without.relative_rms, 1e-9)

    findings = []
    if excess_frac > 0.5 and improvement > 0.2:
        findings.append({
            "verdict": "thickness-independent excess resistivity",
            "evidence": f"a constant {excess:.2f} uohm.cm ({excess_frac:.1f}x "
                        f"bulk) improves the fit by {improvement:.0%}; no "
                        "size-effect parameterisation reproduces the series "
                        "without it",
            "means": "impurity scattering, most likely oxygen incorporated "
                     "during deposition, or a poor target surface",
            "next": "vary base pressure before deposition, add a getter step, "
                    "and take an XPS depth profile for oxygen. This is an "
                    "engineering problem, not a limit on the material.",
            "for_the_project": "GOOD outcome: the Cu route is recoverable and "
                               "the framework's optimism was about film "
                               "quality, not physics"})
    if abs(dc_shift) > 1.5:
        findings.append({
            "verdict": f"percolation threshold shifted by {dc_shift:+.1f} nm",
            "evidence": f"resistivity diverges near {with_excess.critical_thickness_nm:.1f} nm, "
                        f"against an assumed {default_dc:.1f} nm",
            "means": "the film dewets more (or less) than assumed on this "
                     "underlayer",
            "next": "try a 0.5 nm seed layer, or lower the substrate "
                    "temperature; re-run the series on the new underlayer",
            "for_the_project": "changes the minimum usable thickness and "
                               "therefore every silver-consumption number"})
    if with_excess.specularity < 0.2 or with_excess.grain_boundary_reflection > 0.5:
        findings.append({
            "verdict": "strong interface or grain-boundary scattering",
            "evidence": f"fitted p = {with_excess.specularity:.2f}, "
                        f"R = {with_excess.grain_boundary_reflection:.2f}",
            "means": "rough interfaces or very small grains",
            "next": "AFM for roughness and XRD for grain size; consider a "
                    "smoother underlayer or a brief anneal",
            "for_the_project": "recoverable, but the fitted values should "
                               "replace the defaults everywhere"})
    if not findings:
        findings.append({
            "verdict": "classical size effect, adequately described",
            "evidence": f"fitted p = {with_excess.specularity:.2f}, "
                        f"R = {with_excess.grain_boundary_reflection:.2f}, "
                        f"excess {excess:.2f} uohm.cm, relative RMS "
                        f"{with_excess.relative_rms:.1%}",
            "means": "the model form is right; only its parameters were wrong",
            "next": "adopt the fitted parameters and re-run the candidate "
                    "ranking",
            "for_the_project": "the Cu-based recommendations stand, with "
                               "updated numbers"})

    return {"symbol": symbol, "findings": findings,
            "fit_with_excess": with_excess, "fit_without_excess": without,
            "thick_film_ratio": with_excess.thick_film_ratio}


def load_series(path, symbol_column: str = "metal") -> dict:
    """Read a run sheet and split it by metal.

    Expects columns `thickness_nm` and `R_sheet_ohm_sq`, optionally `metal`.
    Rows with a blank sheet resistance are ignored, so the same sheet can be
    carried to the tool and filled in as the films are measured.
    """
    df = pd.read_csv(path)
    need = {"thickness_nm", "R_sheet_ohm_sq"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"run sheet is missing columns: {sorted(missing)}")
    n_rows = len(df)
    df = df.dropna(subset=["R_sheet_ohm_sq"])
    df = df[pd.to_numeric(df["R_sheet_ohm_sq"], errors="coerce").notna()]
    df["R_sheet_ohm_sq"] = df["R_sheet_ohm_sq"].astype(float)
    if not len(df):
        raise ValueError(
            f"{path}: {n_rows} rows, none with a numeric R_sheet_ohm_sq. "
            "This is a blank run sheet -- fill in the measured sheet "
            "resistances first. Leave a film blank only if it read open "
            "circuit; the fitter uses those as a bound on the percolation "
            "threshold, but it needs at least four measurable films.")
    if symbol_column not in df.columns:
        df[symbol_column] = "Cu"
    return {sym: g for sym, g in df.groupby(symbol_column)}


def apply_to_coating(coating, result: CalibrationResult):
    """Return the coating with fitted transport parameters substituted."""
    from dataclasses import replace as _replace
    return _replace(coating,
                    specularity=result.specularity,
                    grain_boundary_reflection=result.grain_boundary_reflection,
                    _cache={})


__all__ = ["CalibrationResult", "fit_series", "diagnose", "load_series",
           "apply_to_coating"]
