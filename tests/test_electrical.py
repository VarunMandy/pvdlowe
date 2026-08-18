"""Thin-film transport: size effect, percolation, and its optical coupling."""

import numpy as np

from pvdlowe.electrical.thinfilm import (PERCOLATION, ThinFilmResistivity,
                                         fuchs_sondheimer_ratio,
                                         mayadas_shatzkes_ratio,
                                         parallel_sheet_resistance)
from pvdlowe.optics.stack import dmd


def test_size_effect_vanishes_for_thick_films():
    assert abs(fuchs_sondheimer_ratio(5000.0, 53.0, 0.5) - 1.0) < 0.02


def test_size_effect_grows_as_film_thins():
    ratios = [fuchs_sondheimer_ratio(d, 53.0, 0.5) for d in (50, 25, 15, 10)]
    assert all(a < b for a, b in zip(ratios, ratios[1:])), ratios


def test_specular_surfaces_give_no_size_effect():
    assert abs(fuchs_sondheimer_ratio(10.0, 53.0, specularity=1.0) - 1.0) < 1e-6


def test_grain_boundary_scattering_grows_as_grains_shrink():
    ratios = [mayadas_shatzkes_ratio(d, 53.0, 0.25) for d in (200, 50, 20, 10)]
    assert all(a < b for a, b in zip(ratios, ratios[1:])), ratios


def test_percolation_is_continuous_at_the_critical_thickness():
    """The multiplier must be exactly 1 at d_c -- no discontinuity."""
    for sym in ("Ag", "Cu"):
        p = PERCOLATION[sym]
        assert abs(p.resistivity_multiplier(p.critical_thickness_nm) - 1.0) < 0.3
        assert p.is_continuous(p.critical_thickness_nm)
        assert not p.is_continuous(p.critical_thickness_nm - 0.1)


def test_percolation_diverges_below_threshold():
    p = PERCOLATION["Ag"]
    assert not np.isfinite(p.resistivity_multiplier(
        p.percolation_thickness_nm - 0.5))


def test_ten_nm_silver_is_several_times_bulk():
    """A 10 nm Ag film cannot be at bulk resistivity."""
    from pvdlowe.materials.metals import metal
    model = ThinFilmResistivity.for_metal(metal("Ag"))
    assert 2.0 < model.ratio(10.0) < 8.0, model.ratio(10.0)


def test_parallel_sheet_resistance():
    assert abs(parallel_sheet_resistance(4.0, 4.0) - 2.0) < 1e-12
    assert abs(parallel_sheet_resistance(4.0, np.inf) - 4.0) < 1e-12


def test_sheet_resistance_falls_with_thickness():
    values = [dmd("Ag", d).sheet_resistance() for d in (10, 12, 14, 16)]
    assert all(a > b for a, b in zip(values, values[1:])), values


def test_thin_film_penalised_in_both_optics_and_transport():
    """The coupling that makes 'how thin can silver go' answerable."""
    thin, thick = dmd("Ag", 8.0), dmd("Ag", 13.0)
    from pvdlowe.optics.integrate import normal_emissivity
    assert thin.sheet_resistance() > thick.sheet_resistance()
    assert normal_emissivity(thin.stack()) > normal_emissivity(thick.stack())
    assert not thin.is_continuous and thick.is_continuous


def _synthetic(p, r, dc, excess, thicknesses=(8., 10., 12., 14., 16., 18., 20.)):
    from pvdlowe.electrical.calibrate import _model_with
    m = _model_with("Cu", p, r, dc, excess)
    d = np.array(thicknesses)
    return d, np.array([m.sheet_resistance(t) for t in d])


def test_calibration_recovers_the_percolation_threshold():
    """d_c is the identifiable parameter, and the one that matters most:
    it sets the minimum usable thickness and therefore every silver number."""
    from pvdlowe.electrical.calibrate import fit_series
    for true_dc in (11.0, 13.0, 15.0):
        d, rs = _synthetic(0.5, 0.25, true_dc, 0.0)
        fit = fit_series(d, rs, "Cu")
        assert abs(fit.critical_thickness_nm - true_dc) < 1.0, (true_dc, fit)


def test_calibration_separates_impurity_excess_from_size_effect():
    """The diagnosis that decides whether the Cu route is recoverable."""
    from pvdlowe.electrical.calibrate import diagnose
    d, rs = _synthetic(0.5, 0.25, 11.0, 12.0)
    verdicts = [f["verdict"] for f in diagnose(d, rs, "Cu")["findings"]]
    assert any("excess" in v for v in verdicts), verdicts

    d, rs = _synthetic(0.35, 0.30, 11.0, 0.0)
    verdicts = [f["verdict"] for f in diagnose(d, rs, "Cu")["findings"]]
    assert any("size effect" in v for v in verdicts), verdicts


def test_calibration_fits_the_data_even_where_parameters_are_degenerate():
    """p and R are not separately identifiable; predictions still are.

    Guards the honest claim: the fitted model predicts sheet resistance to a
    few per cent, but the individual scattering parameters are not
    measurements and must not be quoted as such.
    """
    from pvdlowe.electrical.calibrate import fit_series
    d, rs = _synthetic(0.35, 0.30, 11.0, 0.0)
    fit = fit_series(d, rs, "Cu")
    assert fit.relative_rms < 0.05
    assert fit.identifiable is False


def test_open_circuit_films_bound_percolation_without_breaking_the_fit():
    """A sub-percolation film reads open. It is evidence about d_c, not a
    point the size-effect model can fit, and it must not crash the fit."""
    from pvdlowe.electrical.calibrate import fit_series
    d, rs = _synthetic(0.5, 0.25, 13.0, 0.0)
    assert not np.all(np.isfinite(rs)), "expected an open-circuit film"
    fit = fit_series(d, rs, "Cu")
    assert np.isfinite(fit.critical_thickness_nm)
    assert fit.critical_thickness_nm >= d[~np.isfinite(rs)].max() / 0.75 - 1e-6
