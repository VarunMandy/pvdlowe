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
