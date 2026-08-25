"""Physical constants and unit conversions.

All values are SI unless a suffix says otherwise. Energies used by the
dispersion models are in eV, wavelengths in nanometres, thicknesses in
nanometres. Conversions live here so no module re-derives them.
"""

from __future__ import annotations

import numpy as np

# --- fundamental constants (CODATA 2018) ---------------------------------
C0 = 2.997_924_58e8          # m/s      speed of light in vacuum
H_PLANCK = 6.626_070_15e-34  # J*s
HBAR = 1.054_571_817e-34     # J*s
K_B = 1.380_649e-23          # J/K
E_CHARGE = 1.602_176_634e-19  # C
M_E = 9.109_383_7015e-31     # kg       electron rest mass
EPS0 = 8.854_187_8128e-12    # F/m
SIGMA_SB = 5.670_374_419e-8  # W/(m^2 K^4)

# --- convenience conversions --------------------------------------------
# hc in eV*nm: a photon of wavelength L nm has energy HC_EV_NM / L eV.
HC_EV_NM = H_PLANCK * C0 / E_CHARGE * 1e9   # 1239.8419843320025

#: hbar in eV*s -- used to turn a scattering time into a damping energy.
HBAR_EV_S = HBAR / E_CHARGE                 # 6.582e-16


def wavelength_to_ev(wavelength_nm) -> "float | np.ndarray":
    """Photon energy (eV) from vacuum wavelength (nm)."""
    return HC_EV_NM / np.asarray(wavelength_nm, dtype=float)


def ev_to_wavelength(energy_ev) -> "float | np.ndarray":
    """Vacuum wavelength (nm) from photon energy (eV)."""
    return HC_EV_NM / np.asarray(energy_ev, dtype=float)


def wavelength_to_um(wavelength_nm) -> "float | np.ndarray":
    return np.asarray(wavelength_nm, dtype=float) / 1000.0


def um_to_wavelength(wavelength_um) -> "float | np.ndarray":
    return np.asarray(wavelength_um, dtype=float) * 1000.0


# --- reference temperatures used by the glazing standards ---------------
#: EN 12898 / EN 673 evaluate normal emissivity against a 283 K black body.
T_EMISSIVITY_K = 283.0

#: EN 673 declares the standard interior/exterior boundary temperature.
T_STANDARD_K = 283.0


def drude_plasma_energy_ev(carrier_density_cm3, effective_mass_ratio,
                           relative_permittivity=1.0) -> "float | np.ndarray":
    """Unscreened Drude plasma energy hbar*wp in eV.

    wp^2 = N e^2 / (eps0 eps_r m*)

    Parameters
    ----------
    carrier_density_cm3 : float or array
        Free-carrier density N in cm^-3.
    effective_mass_ratio : float
        m* / m_e.
    relative_permittivity : float
        Background permittivity screening the plasma (use 1.0 to obtain the
        bare plasma energy, or eps_inf when the model already carries an
        eps_inf term multiplying the Drude contribution).
    """
    n_si = np.asarray(carrier_density_cm3, dtype=float) * 1e6  # cm^-3 -> m^-3
    m_eff = effective_mass_ratio * M_E
    wp2 = n_si * E_CHARGE ** 2 / (EPS0 * relative_permittivity * m_eff)
    wp = np.sqrt(wp2)                      # rad/s
    return HBAR_EV_S * wp                  # eV


def drude_damping_energy_ev(mobility_cm2_vs, effective_mass_ratio) -> "float | np.ndarray":
    """Drude damping hbar/tau in eV from a Hall mobility.

    tau = m* mu / e  ->  hbar/tau = hbar e / (m* mu)
    """
    mu_si = np.asarray(mobility_cm2_vs, dtype=float) * 1e-4  # cm^2/Vs -> m^2/Vs
    m_eff = effective_mass_ratio * M_E
    tau = m_eff * mu_si / E_CHARGE
    return HBAR_EV_S / tau


def damping_from_resistivity_ev(resistivity_ohm_cm, carrier_density_cm3,
                                effective_mass_ratio) -> "float | np.ndarray":
    """Drude damping hbar/tau in eV from a measured DC resistivity.

    rho = m* / (N e^2 tau)  ->  hbar/tau = hbar N e^2 rho / m*
    """
    rho_si = np.asarray(resistivity_ohm_cm, dtype=float) * 1e-2  # ohm.cm -> ohm.m
    n_si = np.asarray(carrier_density_cm3, dtype=float) * 1e6
    m_eff = effective_mass_ratio * M_E
    return HBAR_EV_S * n_si * E_CHARGE ** 2 * rho_si / m_eff


def drude_damping_from_resistivity_ev(plasma_energy_ev, resistivity_uohm_cm) -> "float | np.ndarray":
    """Drude damping hbar/tau in eV consistent with a DC resistivity.

    Within one Drude model, rho = 1/(eps0 wp^2 tau), so

        hbar/tau = eps0 * E_p^2 * e * rho / hbar

    with E_p the plasma energy in eV and rho in ohm.m.

    This matters more than it looks. Optical Lorentz-Drude fits are made
    against visible and UV data, where the free-electron damping trades off
    against the interband oscillators, and the fitted Gamma_0 routinely comes
    out well above the value implied by the metal's DC conductivity -- for
    silver, Rakic's 0.048 eV corresponds to about 4.4 uohm.cm against a true
    1.59 uohm.cm. Using the fitted value in the far infrared, and then
    multiplying it by a thin-film size-effect ratio, counts the same
    scattering twice and inflates emissivity by a factor of two to three.
    """
    rho_si = np.asarray(resistivity_uohm_cm, dtype=float) * 1e-8  # uohm.cm -> ohm.m
    return float(EPS0 * float(plasma_energy_ev) ** 2 * E_CHARGE * rho_si / HBAR)


def planck_spectral_radiance_wavelength(wavelength_nm, temperature_k) -> "float | np.ndarray":
    """Planck spectral radiance L(lambda, T) in W/(m^2 sr m).

    Returned per metre of wavelength; only its shape matters when it is used
    as a normalised weighting function.
    """
    lam = np.asarray(wavelength_nm, dtype=float) * 1e-9
    a = 2.0 * H_PLANCK * C0 ** 2 / lam ** 5
    x = H_PLANCK * C0 / (lam * K_B * float(temperature_k))
    # expm1 keeps the small-x limit well conditioned
    return a / np.expm1(x)


__all__ = [
    "C0", "H_PLANCK", "HBAR", "K_B", "E_CHARGE", "M_E", "EPS0", "SIGMA_SB",
    "HC_EV_NM", "HBAR_EV_S", "T_EMISSIVITY_K", "T_STANDARD_K",
    "wavelength_to_ev", "ev_to_wavelength", "wavelength_to_um", "um_to_wavelength",
    "drude_plasma_energy_ev", "drude_damping_energy_ev",
    "damping_from_resistivity_ev", "drude_damping_from_resistivity_ev",
    "planck_spectral_radiance_wavelength",
]
