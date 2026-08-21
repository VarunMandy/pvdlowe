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


def test_dielectric_ordering_matches_measurement():
    """The model must reproduce the measured dielectric ranking.

    Cueva & Carretero, Coatings 13, 1709 (2023), 10 nm Ag, identical
    deposition and dielectric thickness across five materials. Measured
    emissivity: AZO 0.058 < ZnO 0.064 < SiAlNx 0.067 < SnO2 0.083.

    The first version of this framework got this ORDER WRONG, preferring
    nitrides on index-matching grounds, because it had no representation of
    how the underlayer affects metal nucleation. `metal_growth_factor` is
    that representation, calibrated to this data.
    """
    from pvdlowe.optics.integrate import hemispherical_emissivity, normal_emissivity
    from pvdlowe.optimize.thickness import build
    eps = {}
    for key in ("AZO", "ZnO", "Si3N4", "SnO2"):
        st = build("Ag", 10.0, 35.0, 35.0, tco(key)).stack()
        eps[key] = hemispherical_emissivity(normal_emissivity(st))
    assert eps["AZO"] < eps["ZnO"] < eps["Si3N4"] < eps["SnO2"], eps
    # and within 15% of the measured values, not merely ordered correctly
    for key, measured in (("AZO", 0.058), ("ZnO", 0.064),
                          ("Si3N4", 0.067), ("SnO2", 0.083)):
        assert abs(eps[key] - measured) / measured < 0.15, (key, eps[key], measured)


def test_growth_factor_defaults_to_unity_and_penalises_never_helps():
    """A growth factor below 1 would claim a dielectric improves the metal
    beyond its own bulk behaviour, which nothing in the data supports."""
    from pvdlowe.materials.tco import TCOS
    for key, preset in TCOS.items():
        assert preset.metal_growth_factor >= 1.0, (key, preset.metal_growth_factor)
    assert tco("AZO").metal_growth_factor == 1.0, "AZO is the reference"


def test_xrd_discriminates_the_microstructure_hypotheses():
    """The two hypotheses must be separated by more than the peak width.

    Segregated Ag-Cu gives two fcc peak sets at the pure-element angles; a
    solid solution gives one set at a Vegard-interpolated angle. If that
    separation were comparable with the peak width, diffraction would not
    discriminate and the sheet-resistance measurement would stand alone.
    """
    from pvdlowe.characterise import microstructure_signatures
    df = microstructure_signatures(ag_fraction=0.70, grain_nm=15.0)
    first = df.iloc[0]
    assert abs(first.shift_from_Ag) > 2 * first.fwhm_deg, (
        "solid-solution peak is not resolved from pure silver at this grain "
        "size; diffraction would not discriminate")
    assert first.segregated_Cu_2theta > first.solid_solution_2theta > \
        first.segregated_Ag_2theta, "Vegard peak must lie between the elements"


def test_scherrer_round_trips():
    """Width -> size -> width must be self-consistent, or the inversion is
    wrong and every grain size read off a diffractogram would be too."""
    from pvdlowe.characterise import (grain_size_from_fwhm, scherrer_fwhm,
                                      two_theta, LATTICE_A)
    tt = two_theta(LATTICE_A["Ag"], (1, 1, 1))
    for d in (6.0, 15.0, 25.0, 40.0):
        w = scherrer_fwhm(d, tt)
        back = grain_size_from_fwhm(w, tt, instrumental_fwhm_deg=0.0)
        assert abs(back - d) / d < 0.01, (d, w, back)


def test_patent_grain_sizes_are_resolvable():
    """25 nm on ZnO against 15 nm on amorphous oxide must be distinguishable.

    US 7,632,572 measured that difference by TEM. If the corresponding peak
    widths were within instrumental broadening, the XRD route recommended in
    the report would not substitute for TEM.
    """
    from pvdlowe.characterise import scherrer_fwhm, two_theta, LATTICE_A
    tt = two_theta(LATTICE_A["Ag"], (1, 1, 1))
    wide, narrow = scherrer_fwhm(15.0, tt), scherrer_fwhm(25.0, tt)
    assert wide - narrow > 0.15, "difference is below typical instrumental width"
    assert wide / narrow > 1.5
