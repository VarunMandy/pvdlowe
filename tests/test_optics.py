"""Optics: TMM correctness, energy conservation, and known analytic limits."""

import numpy as np

from pvdlowe.materials.dispersion import ConstantIndex
from pvdlowe.materials.glass import FLOAT_GLASS
from pvdlowe.optics import integrate as I
from pvdlowe.optics.stack import Layer, Stack, dmd


def test_bare_interface_matches_fresnel():
    """A substrate with no layers must give the exact Fresnel reflectance."""
    stack = Stack.bare_substrate(ConstantIndex(1.52))
    res = stack.evaluate(np.array([550.0]))
    expected = ((1.52 - 1.0) / (1.52 + 1.0)) ** 2
    assert abs(float(res.R[0]) - expected) < 1e-12


def test_energy_conservation():
    """R + T + A = 1 to machine precision, for a real absorbing stack."""
    res = dmd("Ag", 10.0).stack().evaluate(np.linspace(300.0, 2500.0, 60))
    assert np.max(np.abs(res.R + res.T + res.A - 1.0)) < 1e-10


def test_reported_energy_error_is_zero():
    res = dmd("Ag", 12.0).stack().evaluate(np.linspace(400.0, 20000.0, 40))
    assert res.energy_error < 1e-10


def test_lossless_film_is_lossless():
    """A non-absorbing layer must produce exactly zero absorption."""
    stack = Stack([Layer(ConstantIndex(2.0), 100.0)], ConstantIndex(1.52))
    res = stack.evaluate(np.linspace(400, 800, 25))
    assert np.max(np.abs(res.A)) < 1e-12


def test_quarter_wave_antireflection():
    """A quarter-wave of index sqrt(n_s) must null the reflection exactly."""
    n_s = 2.25
    n_film = np.sqrt(n_s)
    lam0 = 550.0
    stack = Stack([Layer(ConstantIndex(n_film), lam0 / (4 * n_film))],
                  ConstantIndex(n_s))
    assert float(stack.evaluate(np.array([lam0])).R[0]) < 1e-12


def test_thick_metal_is_opaque():
    """200 nm of silver must transmit essentially nothing."""
    res = dmd("Ag", 200.0).stack().evaluate(np.array([550.0, 1000.0, 10000.0]))
    assert np.max(res.T) < 1e-4


def test_polarisation_agrees_at_normal_incidence():
    """s and p polarisation must coincide at theta = 0."""
    st = dmd("Ag", 10.0).stack()
    lam = np.linspace(400, 1200, 20)
    s = st.evaluate(lam, angle_deg=0.0, polarization="s")
    p = st.evaluate(lam, angle_deg=0.0, polarization="p")
    assert np.max(np.abs(s.R - p.R)) < 1e-10


def test_oblique_incidence_raises_reflectance():
    """Reflectance must rise with angle for a dielectric interface."""
    st = Stack.bare_substrate(ConstantIndex(1.52))
    lam = np.array([550.0])
    r0 = float(st.evaluate(lam, angle_deg=0.0).R[0])
    r60 = float(st.evaluate(lam, angle_deg=60.0).R[0])
    assert r60 > r0


def test_bare_glass_emissivity_is_calibrated():
    """Bare float glass must return the accepted 0.837."""
    eps = I.normal_emissivity(Stack.bare_substrate(FLOAT_GLASS))
    assert abs(eps - 0.837) < 0.005


def test_hemispherical_correction_agrees_with_direct_integration():
    """The EN 673 polynomial and direct angular integration must agree."""
    st = dmd("Ag", 12.0).stack()
    poly = I.hemispherical_emissivity(I.normal_emissivity(st))
    direct = I.hemispherical_emissivity_direct(st)
    assert abs(poly - direct) < 0.01, (poly, direct)


def test_emissivity_matches_impedance_limit():
    """A continuous metal film must sit near the thin-sheet impedance limit."""
    from pvdlowe.validate import sheet_resistance_to_emissivity
    for d in (10.0, 12.0, 15.0):
        coating = dmd("Ag", d)
        eps = I.normal_emissivity(coating.stack())
        limit = sheet_resistance_to_emissivity(coating.sheet_resistance())
        assert 0.5 * limit < eps < 2.0 * limit, (d, eps, limit)


def test_thicker_metal_lowers_emissivity_monotonically():
    values = [I.normal_emissivity(dmd("Ag", d).stack())
              for d in (10.0, 12.0, 14.0, 16.0)]
    assert all(a > b for a, b in zip(values, values[1:])), values


def test_u_value_improves_with_a_low_e_coating():
    """The whole point of the coating, checked end to end."""
    from pvdlowe.optics.integrate import center_pane_u_value
    bare = center_pane_u_value(0.837)["U_g"]
    eps = I.hemispherical_emissivity(I.normal_emissivity(dmd("Ag", 12.0).stack()))
    coated = center_pane_u_value(eps)["U_g"]
    assert coated < 0.5 * bare, (bare, coated)


def test_g_value_exceeds_solar_transmittance():
    """g = T_sol + N*A_sol, so it must be at least T_sol."""
    from pvdlowe.optics.integrate import (g_value, solar_absorptance,
                                          solar_transmittance)
    st = dmd("Ag", 10.0).stack()
    g, ts, a = g_value(st), solar_transmittance(st), solar_absorptance(st)
    assert g >= ts
    assert abs(g - (ts + 0.36 * a)) < 1e-9


def test_lsg_is_tvis_over_g():
    from pvdlowe.optics.integrate import g_value, light_to_solar_gain
    st = dmd("Ag", 10.0).stack()
    assert abs(light_to_solar_gain(st)
               - I.visible_transmittance(st) / g_value(st)) < 1e-9


def test_conductive_oxide_rejects_solar_near_infrared():
    """AZO's free carriers do solar-control work a passive nitride cannot.

    The physical reason the two climate profiles disagree: AZO's screened
    plasma wavelength sits at ~1.25 um, inside the solar band, so it absorbs
    and reflects the NIR. Si3N4 is transparent there and passes solar heat.
    """
    from pvdlowe.materials.tco import tco
    from pvdlowe.optimize.thickness import build
    lam = np.array([1600.0, 2000.0, 2400.0])
    t_azo = build("Cu", 11.0, 45.0, 45.0, tco("AZO")).stack().evaluate(lam).T
    t_nit = build("Cu", 11.0, 60.0, 50.0, tco("Si3N4")).stack().evaluate(lam).T
    assert np.all(t_azo < t_nit), (t_azo, t_nit)
    assert I.g_value(build("Cu", 11.0, 45.0, 45.0, tco("AZO")).stack()) < \
           I.g_value(build("Cu", 11.0, 60.0, 50.0, tco("Si3N4")).stack())


def test_multimetal_reduces_to_single_when_n_is_one():
    """A one-metal MultiMetalCoating must match the equivalent LowECoating."""
    from pvdlowe.materials.alloys import Alloy
    from pvdlowe.materials.tco import tco
    from pvdlowe.optics.stack import MultiMetalCoating
    p = tco("AZO")
    single = dmd("Ag", 10.0, p, 35.0)
    multi = MultiMetalCoating(metal_alloys=(Alloy({"Ag": 1.0}),),
                              metal_thicknesses_nm=(10.0,),
                              dielectrics=(p, p),
                              dielectric_thicknesses_nm=(35.0, 35.0))
    assert abs(I.visible_transmittance(single.stack())
               - I.visible_transmittance(multi.stack())) < 1e-9
    assert abs(single.sheet_resistance() - multi.sheet_resistance()) < 1e-9
    assert abs(single.silver_areal_mass() - multi.silver_areal_mass()) < 1e-12


def test_splitting_a_film_raises_sheet_resistance():
    """Two 7 nm layers are not one 14 nm layer.

    Each thin layer carries its own surface scattering, so the pair is more
    resistive than a single film of the same total thickness. The model must
    charge for that rather than treating thickness as fungible.
    """
    from pvdlowe.optics.stack import dmdmd
    from pvdlowe.materials.tco import tco
    single = dmd("Ag", 24.0, tco("AZO"), 35.0)
    double = dmdmd("Ag", 12.0, tco("AZO"), 35.0, 70.0)
    assert double.sheet_resistance() > single.sheet_resistance()
    assert abs(double.metal_thickness_nm - single.metal_thickness_nm) < 1e-9


def test_every_metal_layer_must_clear_percolation():
    from pvdlowe.optics.stack import dmdmd
    from pvdlowe.materials.tco import tco
    assert not dmdmd("Ag", 8.0, tco("AZO")).is_continuous
    assert dmdmd("Ag", 12.0, tco("AZO")).is_continuous
    assert dmdmd("Ag", 12.0, tco("AZO")).layer_continuity() == (True, True)


def test_double_metal_beats_the_single_metal_lsg_ceiling():
    """The architectural result: two metals reach a light-to-solar-gain ratio
    no single-metal stack can, because the dielectric between them adds an
    interference degree of freedom."""
    from pvdlowe.optics.stack import dmdmd
    from pvdlowe.materials.tco import tco
    best_single = max(I.light_to_solar_gain(dmd("Ag", d, tco("Si3N4"), t).stack())
                      for d in (10.0, 12.0, 14.0) for t in (20.0, 35.0, 50.0))
    double = I.light_to_solar_gain(
        dmdmd("Ag", 12.0, tco("Si3N4"), 15.0, 60.0).stack())
    assert double > best_single, (double, best_single)


def test_band_emissivity_exceeds_full_band_for_a_metal_stack():
    """Restricting to 8-14 um reads HIGHER, not lower.

    Pins the result that falsified the band-emissometer explanation for the
    literature emissivity discrepancy. A Drude metal's reflectance is nearly
    flat across 5-14 um and the 283 K Planck weight already peaks near 10 um,
    so the restricted band drops the 5-8 um tail where these stacks reflect
    slightly worse.
    """
    from pvdlowe.materials.tco import tco
    from pvdlowe.optimize.thickness import build
    for metal, d in (("Cu", 12.0), ("Ag", 10.0)):
        st = build(metal, d, 40.0, 40.0, tco("AZO")).stack()
        full = I.normal_emissivity(st)
        band = I.band_emissivity(st, (8.0, 14.0))
        assert 1.02 < band / full < 1.15, (metal, d, band / full)


def test_illuminant_approximation_matters_for_solar_not_visible():
    """Quantifies a caveat that was previously unquantified.

    V(lambda) is narrow and dominates the visible weighting, so T_vis barely
    moves with the assumed illuminant. The solar band has no such weighting
    function -- the spectrum IS the weighting -- so T_sol does move.
    """
    from pvdlowe.materials.tco import tco
    from pvdlowe.optimize.thickness import build
    r = I.illuminant_sensitivity(build("Ag", 10.0, 35.0, 35.0, tco("AZO")))
    assert r["T_vis_spread_pct"] < 1.0, r
    assert r["T_sol_spread_pct"] > 3.0, r


def test_manufacturability_flags_an_implausibly_thin_top_layer():
    """The optimiser found a 15 nm top oxide: optically fine, physically not."""
    from pvdlowe.materials.tco import tco
    from pvdlowe.optimize.thickness import build
    assert not build("Ag", 10., 35., 15., tco("AZO")).manufacturability()["manufacturable"]
    assert build("Ag", 10., 25., 35., tco("AZO")).manufacturability()["manufacturable"]


def test_third_metal_layer_gives_diminishing_returns():
    """Closes the triple-metal question with a negative result.

    Going from one metal layer to two buys a large LSG gain; the third buys
    almost nothing and triples the silver. The architecture argument stops at
    two for this specification.
    """
    from pvdlowe.materials.alloys import Alloy
    from pvdlowe.materials.tco import tco
    from pvdlowe.optics.stack import MultiMetalCoating
    a, p = Alloy({"Ag": 1.0}), tco("Si3N4")

    def lsg(n, dm, outer, mid):
        c = MultiMetalCoating(
            metal_alloys=(a,) * n, metal_thicknesses_nm=(dm,) * n,
            dielectrics=(p,) * (n + 1),
            dielectric_thicknesses_nm=(outer,) + (mid,) * (n - 1) + (outer,))
        return I.light_to_solar_gain(c.stack()), c.silver_areal_mass()

    l1, ag1 = lsg(1, 11.0, 15.0, 0.0)
    l2, ag2 = lsg(2, 12.0, 15.0, 60.0)
    l3, ag3 = lsg(3, 10.0, 15.0, 45.0)
    assert l2 - l1 > 0.2, (l1, l2)          # the second layer earns its place
    assert l3 - l2 < 0.15, (l2, l3)         # the third adds little
    # and each layer costs silver: 0.115 -> 0.252 -> 0.315 g/m2
    assert ag1 < ag2 < ag3, (ag1, ag2, ag3)
    assert ag3 > 2.5 * ag1, (ag1, ag3)
