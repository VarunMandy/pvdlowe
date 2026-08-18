"""Materials: dispersion sign conventions, alloys, TCOs, resistivity."""

import numpy as np

from pvdlowe.materials.alloys import (Alloy, ag_cu, discriminating_wavelengths,
                                      nordheim_resistivity)
from pvdlowe.materials.metals import metal
from pvdlowe.materials.tco import azo_from_al_content, tco


def test_extinction_coefficient_is_non_negative():
    """k >= 0 everywhere: a passive material cannot amplify light."""
    lam = np.logspace(np.log10(300), np.log10(50000), 200)
    for sym in ("Ag", "Cu", "Al", "Au", "Ti"):
        nk = metal(sym).dispersion()(lam)
        assert np.all(nk.imag >= -1e-12), sym


def test_metals_are_metallic_in_the_infrared():
    """eps_1 must be large and negative at 10 um for every metal."""
    for sym in ("Ag", "Cu", "Al", "Au"):
        eps = metal(sym).dispersion().epsilon(np.array([10000.0]))
        assert eps.real[0] < -100, (sym, eps)


def test_drude_damping_matches_dc_resistivity():
    """Resistivity-anchored damping must reproduce the metal's own rho."""
    from pvdlowe.constants import drude_damping_from_resistivity_ev
    for sym in ("Ag", "Cu"):
        m = metal(sym)
        gamma = drude_damping_from_resistivity_ev(
            m.plasma_energy_ev * np.sqrt(m.f0), m.resistivity_bulk_uohm_cm)
        assert 0.005 < gamma < 0.05, (sym, gamma)


def test_nordheim_is_symmetric_and_peaks_mid_composition():
    r50 = nordheim_resistivity({"Ag": 0.5, "Cu": 0.5})
    r10 = nordheim_resistivity({"Ag": 0.9, "Cu": 0.1})
    r90 = nordheim_resistivity({"Ag": 0.1, "Cu": 0.9})
    assert r50 > r10 and r50 > r90
    assert nordheim_resistivity({"Ag": 1.0}) < r10


def test_pure_alloy_reduces_to_the_element():
    pure = Alloy({"Ag": 1.0})
    lam = np.array([550.0, 10000.0])
    assert np.allclose(pure.dispersion()(lam), metal("Ag").dispersion()(lam))


def test_alloy_composition_normalises():
    a = Alloy({"Ag": 70.0, "Cu": 30.0})
    assert abs(a.composition["Ag"] - 0.7) < 1e-12
    assert a.label == "Ag70Cu30"


def test_microstructure_hypotheses_are_distinguishable():
    """The two Ag-Cu models must differ measurably -- the whole point."""
    res = discriminating_wavelengths(ag_cu(0.7), np.linspace(400, 2500, 200))
    assert res["distinguishable"]


def test_ema_and_solid_solution_give_different_resistivity():
    ss = ag_cu(0.7, "solid_solution").bulk_resistivity_uohm_cm
    ema = ag_cu(0.7, "ema").bulk_resistivity_uohm_cm
    assert ss > ema, (ss, ema)


def test_tco_resistivity_matches_carrier_parameters():
    """rho = 1/(N e mu) must hold exactly for every preset."""
    for key in ("AZO", "GZO", "ITO", "FTO"):
        p = tco(key)
        expected = 1.0 / (p.carrier_density_cm3 * 1.602176634e-19
                          * p.mobility_cm2_vs)
        assert abs(p.resistivity_ohm_cm - expected) / expected < 1e-9, key


def test_azo_doping_has_an_optimum():
    """Resistivity must fall then rise with Al content."""
    rho = [azo_from_al_content(x).resistivity_ohm_cm
           for x in (0.5, 2.0, 4.0, 8.0, 12.0)]
    assert rho[0] > rho[2] and rho[-1] > rho[2], rho


def test_tco_index_is_calibrated_to_target():
    for key in ("AZO", "GZO"):
        p = tco(key)
        n = float(np.atleast_1d(p.dispersion()(550.0)).real[0])
        assert abs(n - p.n_visible) < 0.02, (key, n, p.n_visible)


def test_dielectrics_are_insulating():
    """Si3N4 and TiO2 must contribute nothing to sheet resistance."""
    for key in ("Si3N4", "TiO2"):
        p = tco(key)
        assert p.sheet_resistance(40.0) > 1e6, key


def test_dielectric_indices_are_calibrated():
    for key, expected in (("Si3N4", 2.02), ("TiO2", 2.45), ("SnO2", 2.00)):
        n = float(np.atleast_1d(tco(key).dispersion()(550.0)).real[0])
        assert abs(n - expected) < 0.02, (key, n)


def test_phonons_absorb_in_the_thermal_band_only():
    """Lattice absorption must appear at 10 um and not disturb the visible."""
    import dataclasses
    p = tco("Si3N4")
    stripped = dataclasses.replace(p, far_ir_phonons=())
    n_vis_on = float(np.atleast_1d(p.dispersion()(550.0)).real[0])
    n_vis_off = float(np.atleast_1d(stripped.dispersion()(550.0)).real[0])
    assert abs(n_vis_on - n_vis_off) < 0.01          # visible unaffected
    k_on = float(np.atleast_1d(p.dispersion()(10000.0)).imag[0])
    k_off = float(np.atleast_1d(stripped.dispersion()(10000.0)).imag[0])
    assert k_on > k_off + 0.5                        # far IR absorbs


def test_phonon_penalty_is_small_behind_a_good_mirror():
    """A working metal layer screens the dielectric's lattice absorption.

    The physical point behind the Si3N4/Cu result: at 10 um the metal reflects
    almost everything, so little field reaches the nitride to be absorbed.
    """
    import dataclasses
    from pvdlowe.optics.integrate import hemispherical_emissivity, normal_emissivity
    from pvdlowe.optimize.thickness import build
    p = tco("Si3N4")
    on = hemispherical_emissivity(normal_emissivity(
        build("Cu", 12.0, 55.0, 45.0, p).stack()))
    off = hemispherical_emissivity(normal_emissivity(
        build("Cu", 12.0, 55.0, 45.0, dataclasses.replace(p, far_ir_phonons=())).stack()))
    assert 0.0 <= on - off < 0.005, (on, off)
