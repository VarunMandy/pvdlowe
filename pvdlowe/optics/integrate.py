"""Turning spectra into the numbers a glazing specification is written in.

The chain the brief needs is: complex refractive indices -> transfer-matrix
spectra -> weighted integrals -> emissivity -> U-value. The last step is the
one that makes the whole exercise legible to a product engineer, because
nobody specifies a window by its far-infrared reflectance; they specify it by
U_g in W/(m^2 K).

Standards implemented:

* EN 410 / ISO 9050  visible and solar transmittance
* EN 12898           normal emissivity, 283 K black body over 5-50 um
* EN 673             hemispherical emissivity correction and centre-pane
                     thermal transmittance
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..constants import SIGMA_SB, T_STANDARD_K
from ..provenance import Provenance, Quantity
from ..spectra import (Weighting, emissivity_weighting, solar_weighting,
                       visible_weighting)
from . import tmm


def _as_stack(obj):
    """Accept a Stack or anything exposing .stack() (e.g. LowECoating)."""
    return obj.stack() if hasattr(obj, "stack") else obj


# --- visible and solar ---------------------------------------------------

def visible_transmittance(stack, weighting: Weighting | None = None,
                          angle_deg: float = 0.0) -> float:
    """T_vis of the coated surface (semi-infinite substrate).

    For the transmittance of a finished pane, including the second glass-air
    surface and the glass bulk absorption, use :func:`glazing`.
    """
    w = weighting or visible_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.T)


def visible_reflectance(stack, weighting: Weighting | None = None,
                        angle_deg: float = 0.0) -> float:
    w = weighting or visible_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.R)


def visible_absorptance(stack, weighting: Weighting | None = None,
                        angle_deg: float = 0.0) -> float:
    w = weighting or visible_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.A)


def solar_transmittance(stack, weighting: Weighting | None = None,
                        angle_deg: float = 0.0) -> float:
    w = weighting or solar_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.T)


def solar_reflectance(stack, weighting: Weighting | None = None,
                      angle_deg: float = 0.0) -> float:
    w = weighting or solar_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.R)


def solar_absorptance(stack, weighting: Weighting | None = None,
                      angle_deg: float = 0.0) -> float:
    w = weighting or solar_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return w.apply(res.A)


#: Inward-flowing fraction of absorbed solar energy, EN 410's secondary
#: internal heat transfer factor N = h_in / (h_in + h_out). With the standard
#: 8 and 23 W/m2K this is 0.26 for a single pane. For a double-glazed unit
#: with the coating on surface 2 -- the usual Low-E position -- absorbed heat
#: sits inside the cavity and a larger share flows inward; 0.36 is the
#: representative value and the default here.
INWARD_FRACTION_SINGLE = 8.0 / (8.0 + 23.0)
INWARD_FRACTION_IGU_SURFACE2 = 0.36


def g_value(stack, inward_fraction: float = INWARD_FRACTION_IGU_SURFACE2,
            **kwargs) -> float:
    """Solar heat gain coefficient (SHGC, or g-value), EN 410 / ISO 9050.

        g = T_sol + N * A_sol

    The total solar energy entering the building: what is transmitted
    directly, plus the share of what the glazing absorbs that then flows
    inward rather than back out. Absorption matters, which is why a coating
    cannot be judged on transmittance alone -- a strongly absorbing metal
    layer heats up and re-radiates part of that heat indoors.

    The inward fraction depends on the coating's position in the unit and on
    the surface heat transfer coefficients, so it is a convention rather than
    a property of the coating. EN 410 defines the calculation properly for a
    given build-up; this is the standard simplification.
    """
    ts = solar_transmittance(stack, **kwargs)
    a = solar_absorptance(stack, **kwargs)
    return float(ts + inward_fraction * a)


def light_to_solar_gain(stack, **kwargs) -> float:
    """LSG = T_vis / g. The figure of merit for a cooling-dominated climate.

    How much daylight you get per unit of solar heat admitted. Above about
    1.25 a glazing is conventionally called spectrally selective; the best
    commercial triple-silver solar-control products reach roughly 2.

    This is the metric that matters in Mumbai, Chennai or Dubai and the one
    that matters least in Stockholm, where admitted solar energy offsets
    heating demand and a high g-value is an asset. The framework does not
    choose for you: see `data/targets_cooling.yaml` against
    `data/targets.yaml`.
    """
    g = g_value(stack, **kwargs)
    return float(visible_transmittance(stack, **kwargs) / g) if g > 0 else np.inf


def selectivity(stack, **kwargs) -> float:
    """T_vis / T_sol. Above 1 means the coating is spectrally selective:
    it passes daylight while rejecting solar heat, which is the property that
    distinguishes a solar-control Low-E from a plain one."""
    ts = solar_transmittance(stack, **kwargs)
    return float(visible_transmittance(stack, **kwargs) / ts) if ts > 0 else np.inf


# --- emissivity ----------------------------------------------------------

def normal_emissivity(stack, weighting: Weighting | None = None,
                      angle_deg: float = 0.0) -> float:
    """EN 12898 normal emissivity: 1 - R, weighted by a 283 K black body.

    Kirchhoff's law with the substrate opaque in the far IR, so absorptance
    equals emittance and the transmitted term vanishes. The function checks
    that assumption rather than assuming it -- see
    :func:`emissivity_diagnostics`.
    """
    w = weighting or emissivity_weighting()
    res = _as_stack(stack).evaluate(w.wavelength_nm, angle_deg)
    return float(np.clip(w.apply(1.0 - res.R), 0.0, 1.0))


#: EN 673 Annex A correction from normal to hemispherical emissivity.
EN673_COEFFICIENTS = (1.1887, -0.4967, 0.2452)


def illuminant_sensitivity(stack, temperatures=(5000., 5500., 6504., 7500.),
                           solar_temperatures=(5000., 5778., 6000.)) -> dict:
    """How much do the illuminant approximations move T_vis and T_sol?

    D65 and AM1.5 are approximated here by Planck spectra and flagged MODEL.
    Rather than leave that as an unquantified caveat, this measures it: vary
    the assumed colour temperature and see what moves.

    The answer differs sharply between the two bands, and the difference is
    structural rather than incidental. The photopic response V(lambda) is
    narrow and peaked, so it dominates the visible weighting and the
    illuminant contributes little -- T_vis shifts by about 0.1% across
    5000-7500 K. The solar band has no such weighting function; the spectrum
    *is* the weighting, so T_sol shifts by roughly 5-10% over a plausible
    range.

    Practical consequence: **T_vis is reportable as computed. T_sol, and the
    g-value and LSG derived from it, carry a systematic uncertainty of order
    5-10% until a tabulated AM1.5G spectrum is supplied** via
    `Weighting.from_csv`. That does not affect rankings within a climate
    profile, since the bias is common to all candidates, but it does affect
    any absolute solar-gain figure quoted against a building code.
    """
    # Local import of a numeric constant, used only here. Kept out of module
    # scope so that `constants` stays a leaf with no importers to invalidate.
    from ..constants import planck_spectral_radiance_wavelength as _planck
    from ..spectra import solar_weighting, visible_weighting

    st = _as_stack(stack)
    vw, sw = visible_weighting(), solar_weighting()
    res_v, res_s = st.evaluate(vw.wavelength_nm), st.evaluate(sw.wavelength_nm)

    t_vis = {}
    ref = _planck(vw.wavelength_nm, 6504.0)
    for T in temperatures:
        w = _planck(vw.wavelength_nm, T) * vw.weight / ref
        t_vis[T] = float(np.trapezoid(res_v.T * w, vw.wavelength_nm)
                         / np.trapezoid(w, vw.wavelength_nm))
    t_sol = {}
    for T in solar_temperatures:
        w = _planck(sw.wavelength_nm, T)
        t_sol[T] = float(np.trapezoid(res_s.T * w, sw.wavelength_nm)
                         / np.trapezoid(w, sw.wavelength_nm))

    vv, ss = list(t_vis.values()), list(t_sol.values())
    return {
        "T_vis": {k: round(v, 4) for k, v in t_vis.items()},
        "T_sol": {k: round(v, 4) for k, v in t_sol.items()},
        "T_vis_spread_pct": round(100 * (max(vv) - min(vv)) / np.mean(vv), 2),
        "T_sol_spread_pct": round(100 * (max(ss) - min(ss)) / np.mean(ss), 2),
        "verdict": ("T_vis is robust to the illuminant approximation; T_sol, "
                    "g and LSG are not. Supply a tabulated AM1.5G spectrum "
                    "before quoting an absolute solar heat gain figure."),
    }


def band_emissivity(stack, band_um=(8.0, 14.0), temperature_k: float = 293.0,
                    angle_deg: float = 0.0) -> float:
    """Emissivity averaged over a restricted spectral band.

    EN 12898 weights 1 - R across the whole thermal spectrum by a 283 K Planck
    radiance. Much of the infrared-stealth and low-emissivity literature
    instead reports a band-emissometer value -- the IR-2 and similar
    instruments read the 8-14 um atmospheric window, because that is the band
    a thermal imager sees.

    These are different quantities. A metal's reflectance rises with
    wavelength, so restricting the average to 8-14 um and dropping the 5-8 um
    region, where reflectance is lower, returns a systematically smaller
    number. Comparing a band-emissometer value with a standards-grade
    emissivity, or with a sheet-resistance impedance limit, compares unlike
    things.

    Provided so a literature value can be recomputed on its own terms before
    being called inconsistent.
    """
    from ..constants import planck_spectral_radiance_wavelength
    lo, hi = float(band_um[0]) * 1000.0, float(band_um[1]) * 1000.0
    lam = np.linspace(lo, hi, 400)
    res = _as_stack(stack).evaluate(lam, angle_deg)
    weight = planck_spectral_radiance_wavelength(lam, temperature_k)
    return float(np.trapezoid((1.0 - res.R) * weight, lam)
                 / np.trapezoid(weight, lam))


def hemispherical_emissivity(normal_eps: float) -> float:
    """EN 673 correction, eps = 1.1887 e_n - 0.4967 e_n^2 + 0.2452 e_n^3."""
    e = float(normal_eps)
    a, b, c = EN673_COEFFICIENTS
    return float(np.clip(a * e + b * e ** 2 + c * e ** 3, 0.0, 1.0))


def hemispherical_emissivity_direct(stack, weighting: Weighting | None = None,
                                    n_angles: int = 18) -> float:
    """Hemispherical emissivity by direct angular integration.

    Independent of the EN 673 polynomial, so the two can be compared. They
    should agree closely for a metallic Low-E surface; a large disagreement
    is a signal that the coating's angular reflectance behaves unlike the
    metallic surfaces the EN 673 fit was built from, and that the polynomial
    should not be trusted for it.
    """
    w = weighting or emissivity_weighting()
    angles = np.linspace(0.0, 89.0, n_angles)
    s = _as_stack(stack)
    eps_theta = np.array([w.apply(1.0 - s.evaluate(w.wavelength_nm, a).R)
                          for a in angles])
    return float(np.clip(
        tmm.hemispherical_from_angles(eps_theta, angles), 0.0, 1.0))


def emissivity_diagnostics(stack, weighting: Weighting | None = None) -> dict:
    """Cross-check the two hemispherical routes and the opacity assumption."""
    w = weighting or emissivity_weighting()
    s = _as_stack(stack)
    res = s.evaluate(w.wavelength_nm, 0.0)
    eps_n = float(np.clip(w.apply(1.0 - res.R), 0.0, 1.0))
    eps_h_poly = hemispherical_emissivity(eps_n)
    eps_h_direct = hemispherical_emissivity_direct(s, w)
    far_ir_transmittance = w.apply(res.T)
    return {
        "normal_emissivity": eps_n,
        "hemispherical_en673": eps_h_poly,
        "hemispherical_direct": eps_h_direct,
        "polynomial_discrepancy": abs(eps_h_poly - eps_h_direct),
        "far_ir_transmittance": float(far_ir_transmittance),
        "substrate_opaque": bool(far_ir_transmittance < 1e-3),
        "consistent": bool(abs(eps_h_poly - eps_h_direct) < 0.02
                           and far_ir_transmittance < 1e-3),
    }


def emissivity_quantity(stack, hemispherical: bool = True) -> Quantity:
    eps_n = normal_emissivity(stack)
    value = hemispherical_emissivity(eps_n) if hemispherical else eps_n
    kind = "hemispherical (EN 673)" if hemispherical else "normal (EN 12898)"
    return Quantity(value, "", Provenance.MODEL, source=f"{kind} emissivity",
                    note="from modelled optical constants; confirm with an "
                         "emissometer or FTIR reflectance measurement")


# --- whole-pane (incoherent substrate) ----------------------------------

@dataclass
class GlazingResult:
    wavelength_nm: np.ndarray
    R: np.ndarray
    T: np.ndarray
    A: np.ndarray


def glazing(coating_stack, glass_thickness_mm: float = 4.0,
            wavelength_nm=None, angle_deg: float = 0.0) -> GlazingResult:
    """Full pane: coherent coating, incoherent glass bulk, back surface.

    The coating interferes coherently; 4 mm of glass does not, so its
    multiple internal reflections are summed in intensity. Skipping this step
    typically overstates T_vis by three to four percentage points, because
    the second glass-air surface reflects about 4% that a semi-infinite
    substrate calculation never gives back.
    """
    # Local import: avoids optics/integrate depending on materials at module scope.
    from ..materials.dispersion import ConstantIndex

    stack = _as_stack(coating_stack)
    lam = (np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
           if wavelength_nm is not None else visible_weighting().wavelength_nm)

    front = stack.evaluate(lam, angle_deg)
    back_stack_in = stack.reversed_illumination()
    front_from_glass = back_stack_in.evaluate(lam, angle_deg)

    n_glass = np.atleast_1d(stack.substrate(lam))
    air = ConstantIndex(1.0)
    bare_back = tmm.solve(lam, np.stack([n_glass, np.atleast_1d(air(lam))
                                         * np.ones_like(n_glass)]),
                          np.array([]), angle_deg, "both")

    k = np.abs(n_glass.imag)
    d_nm = float(glass_thickness_mm) * 1e6
    tau = np.exp(-4.0 * np.pi * k * d_nm / lam)

    R, T, A = tmm.incoherent_sandwich(
        front.R, front.T, front_from_glass.R, front_from_glass.T,
        tau, bare_back.R, bare_back.T)
    return GlazingResult(lam, np.clip(R, 0, 1), np.clip(T, 0, 1), np.clip(A, 0, 1))


def glazing_visible_transmittance(coating_stack, glass_thickness_mm: float = 4.0,
                                  weighting: Weighting | None = None) -> float:
    w = weighting or visible_weighting()
    g = glazing(coating_stack, glass_thickness_mm, w.wavelength_nm)
    return w.apply(g.T)


# --- thermal transmittance ----------------------------------------------

#: EN 673 Annex B fill-gas properties at 283 K.
#: (thermal conductivity W/mK, density kg/m3, dynamic viscosity Pa.s,
#:  specific heat J/kgK). LITERATURE_UNVERIFIED -- transcribed, not checked.
FILL_GASES = {
    "air":     (0.02535, 1.2320, 1.7610e-5, 1008.0),
    "argon":   (0.01684, 1.6990, 2.1640e-5, 519.0),
    "krypton": (0.00900, 3.5600, 2.3400e-5, 245.0),
    "xenon":   (0.00529, 5.5800, 2.2600e-5, 161.0),
}


def center_pane_u_value(emissivity_1: float, emissivity_2: float = 0.837,
                        gap_mm: float = 16.0, gas: str = "argon",
                        mean_temperature_k: float = T_STANDARD_K,
                        delta_t: float = 15.0,
                        h_external: float = 23.0, h_internal: float = 8.0,
                        tilt_deg: float = 90.0) -> dict:
    """EN 673 centre-pane thermal transmittance of a double-glazed unit.

    This is the number the coating is ultimately sold on. It also shows why
    the brief's emissivity target matters so much and why chasing emissivity
    below about 0.03 has diminishing returns: the radiative conductance is
    proportional to the emissivity, but once it drops below the gas
    conductance the total stops responding.

    Parameters
    ----------
    emissivity_1 : corrected (hemispherical) emissivity of the coated surface
    emissivity_2 : emissivity of the facing uncoated surface, 0.837 default
    gap_mm : cavity width
    gas : one of FILL_GASES
    """
    if gas not in FILL_GASES:
        raise KeyError(f"unknown fill gas {gas!r}; have {sorted(FILL_GASES)}")
    lam_g, rho, mu, cp = FILL_GASES[gas]
    e1 = float(np.clip(emissivity_1, 1e-4, 1.0))
    e2 = float(np.clip(emissivity_2, 1e-4, 1.0))
    s = float(gap_mm) * 1e-3
    tm = float(mean_temperature_k)

    # radiative conductance
    h_r = 4.0 * SIGMA_SB * tm ** 3 / (1.0 / e1 + 1.0 / e2 - 1.0)

    # gas conductance: Nusselt correlation, EN 673 form
    grashof = (9.81 * s ** 3 * delta_t * rho ** 2) / (tm * mu ** 2)
    prandtl = mu * cp / lam_g
    ra = grashof * prandtl
    a, n = (0.035, 0.38) if abs(tilt_deg - 90.0) < 1e-6 else (0.10, 0.31)
    nusselt = max(a * ra ** n, 1.0)
    h_g = nusselt * lam_g / s

    h_t = h_r + h_g
    u = 1.0 / (1.0 / h_external + 1.0 / h_t + 1.0 / h_internal)
    return {
        "U_g": float(u),
        "h_radiative": float(h_r),
        "h_gas": float(h_g),
        "h_total_cavity": float(h_t),
        "rayleigh": float(ra),
        "nusselt": float(nusselt),
        "gas": gas,
        "gap_mm": gap_mm,
        "provenance": Provenance.MODEL,
        "note": "EN 673 centre-pane only; excludes frame and edge effects",
    }


def performance_summary(coating, glass_thickness_mm: float = 4.0,
                        gap_mm: float = 16.0, gas: str = "argon") -> dict:
    """Every headline metric for one coating, in one pass."""
    stack = _as_stack(coating)
    eps_n = normal_emissivity(stack)
    eps_h = hemispherical_emissivity(eps_n)
    u = center_pane_u_value(eps_h, gap_mm=gap_mm, gas=gas)
    out = {
        "label": getattr(coating, "label", getattr(stack, "label", "stack")),
        "T_vis": visible_transmittance(stack),
        "R_vis": visible_reflectance(stack),
        "A_vis": visible_absorptance(stack),
        "T_vis_glazed": glazing_visible_transmittance(stack, glass_thickness_mm),
        "T_sol": solar_transmittance(stack),
        "A_sol": solar_absorptance(stack),
        "selectivity": selectivity(stack),
        "g_value": g_value(stack),
        "LSG": light_to_solar_gain(stack),
        "emissivity_normal": eps_n,
        "emissivity_hemispherical": eps_h,
        "U_g": u["U_g"],
    }
    if hasattr(coating, "sheet_resistance"):
        out["R_sheet"] = coating.sheet_resistance()
        out["Ag_g_per_m2"] = coating.silver_areal_mass()
        out["metal_thickness_nm"] = coating.metal_thickness_nm
        out["continuous"] = coating.is_continuous
    return out


__all__ = [
    "visible_transmittance", "visible_reflectance", "visible_absorptance",
    "solar_transmittance", "solar_reflectance", "solar_absorptance",
    "selectivity", "g_value", "light_to_solar_gain", "band_emissivity",
    "illuminant_sensitivity",
    "INWARD_FRACTION_SINGLE", "INWARD_FRACTION_IGU_SURFACE2",
    "normal_emissivity", "hemispherical_emissivity",
    "hemispherical_emissivity_direct", "emissivity_diagnostics",
    "emissivity_quantity", "EN673_COEFFICIENTS", "glazing", "GlazingResult",
    "glazing_visible_transmittance", "center_pane_u_value", "FILL_GASES",
    "performance_summary",
]
