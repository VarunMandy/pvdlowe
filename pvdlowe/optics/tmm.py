"""Transfer-matrix solver for absorbing multilayers.

Conventions (matching Byrnes, arXiv:1603.02720, so results can be checked
against the reference `tmm` package):

* fields go as exp(-i omega t), refractive index n + ik with k >= 0;
* the forward direction is into the stack, enforced by requiring
  Im(n cos theta) >= 0 for the semi-infinite media;
* s polarisation has E perpendicular to the plane of incidence.

Everything is vectorised over wavelength. A stack evaluation is one
matrix chain per wavelength sample, done with einsum, so a 400-point IR
sweep across a five-layer stack costs a few milliseconds -- which is what
makes it affordable to put this inside an optimiser loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _forward_cos_theta(n: np.ndarray, sin_theta0_n0: np.ndarray) -> np.ndarray:
    """cos(theta) in a medium of index n, on the forward-propagating branch."""
    n = np.asarray(n, dtype=complex)
    sin_theta = sin_theta0_n0 / n
    cos_theta = np.sqrt(1.0 - sin_theta ** 2 + 0j)
    # For an absorbing medium the physical root is the one that decays going
    # forward: Im(n cos theta) >= 0.
    bad = (n * cos_theta).imag < 0
    return np.where(bad, -cos_theta, cos_theta)


def fresnel(pol: str, n_i, cos_i, n_f, cos_f):
    """Amplitude reflection and transmission at one interface."""
    n_i, n_f = np.asarray(n_i, dtype=complex), np.asarray(n_f, dtype=complex)
    if pol == "s":
        denom = n_i * cos_i + n_f * cos_f
        r = (n_i * cos_i - n_f * cos_f) / denom
        t = 2.0 * n_i * cos_i / denom
    elif pol == "p":
        denom = n_f * cos_i + n_i * cos_f
        r = (n_f * cos_i - n_i * cos_f) / denom
        t = 2.0 * n_i * cos_i / denom
    else:
        raise ValueError("pol must be 's' or 'p'")
    return r, t


@dataclass
class TMMResult:
    """Reflectance, transmittance and absorptance versus wavelength."""

    wavelength_nm: np.ndarray
    R: np.ndarray
    T: np.ndarray
    A: np.ndarray
    r: np.ndarray | None = None
    t: np.ndarray | None = None
    layer_absorption: np.ndarray | None = None   # (n_layers, n_wavelengths)

    def __post_init__(self):
        for f in ("wavelength_nm", "R", "T", "A"):
            setattr(self, f, np.atleast_1d(np.asarray(getattr(self, f))))

    @property
    def energy_error(self) -> float:
        """max |R + T + A - 1|, the solver's own consistency check."""
        return float(np.max(np.abs(self.R + self.T + self.A - 1.0)))


def solve(wavelength_nm, indices, thicknesses_nm, angle_deg: float = 0.0,
          polarization: str = "both", want_layer_absorption: bool = False
          ) -> TMMResult:
    """Solve a coherent multilayer.

    Parameters
    ----------
    wavelength_nm : array of vacuum wavelengths
    indices : (n_media, n_wavelengths) complex array.
        Row 0 is the semi-infinite incident medium, row -1 the semi-infinite
        exit medium, rows in between the finite layers.
    thicknesses_nm : array of length n_media - 2, the finite layer thicknesses.
    angle_deg : angle of incidence in the incident medium.
    polarization : 's', 'p', or 'both' (unpolarised average).
    """
    lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
    n = np.asarray(indices, dtype=complex)
    if n.ndim == 1:
        n = n[:, None]
    if n.shape[1] != lam.size:
        raise ValueError(
            f"indices has {n.shape[1]} wavelength columns, expected {lam.size}")
    d = np.asarray(thicknesses_nm, dtype=float)
    n_media = n.shape[0]
    if d.size != n_media - 2:
        raise ValueError(
            f"{n_media} media require {n_media - 2} finite thicknesses, "
            f"got {d.size}")

    if polarization == "both":
        rs = solve(lam, n, d, angle_deg, "s", want_layer_absorption)
        rp = solve(lam, n, d, angle_deg, "p", want_layer_absorption)
        la = None
        if want_layer_absorption:
            la = 0.5 * (rs.layer_absorption + rp.layer_absorption)
        return TMMResult(lam, 0.5 * (rs.R + rp.R), 0.5 * (rs.T + rp.T),
                         0.5 * (rs.A + rp.A), layer_absorption=la)

    theta0 = np.deg2rad(float(angle_deg))
    sin_component = n[0] * np.sin(theta0)          # conserved across interfaces
    cos_theta = np.stack([_forward_cos_theta(n[j], sin_component)
                          for j in range(n_media)])

    # phase thickness of each finite layer
    delta = np.zeros((n_media - 2, lam.size), dtype=complex)
    for j in range(1, n_media - 1):
        delta[j - 1] = 2.0 * np.pi * d[j - 1] * n[j] * cos_theta[j] / lam
    # guard against overflow in strongly absorbing thick layers
    delta = np.where(delta.imag > 70.0, delta.real + 70.0j, delta)

    # chain: I(0,1) L(1) I(1,2) ... L(N) I(N, s)
    M = np.zeros((2, 2, lam.size), dtype=complex)
    M[0, 0] = 1.0
    M[1, 1] = 1.0

    def matmul(a, b):
        return np.einsum("ijw,jkw->ikw", a, b)

    for j in range(n_media - 1):
        r, t = fresnel(polarization, n[j], cos_theta[j], n[j + 1], cos_theta[j + 1])
        interface = np.zeros((2, 2, lam.size), dtype=complex)
        interface[0, 0] = 1.0 / t
        interface[0, 1] = r / t
        interface[1, 0] = r / t
        interface[1, 1] = 1.0 / t
        M = matmul(M, interface)
        if j < n_media - 2:
            prop = np.zeros((2, 2, lam.size), dtype=complex)
            prop[0, 0] = np.exp(-1j * delta[j])
            prop[1, 1] = np.exp(1j * delta[j])
            M = matmul(M, prop)

    r_total = M[1, 0] / M[0, 0]
    t_total = 1.0 / M[0, 0]

    R = np.abs(r_total) ** 2
    if polarization == "s":
        factor = (n[-1] * cos_theta[-1]).real / (n[0] * cos_theta[0]).real
    else:
        factor = ((np.conj(n[-1]) * cos_theta[-1]).real
                  / (np.conj(n[0]) * cos_theta[0]).real)
    T = np.abs(t_total) ** 2 * factor
    T = np.where(np.isfinite(T), T, 0.0)
    A = 1.0 - R - T

    layer_abs = None
    if want_layer_absorption:
        layer_abs = _layer_absorption(n, cos_theta, delta, lam, polarization,
                                      r_total)
    return TMMResult(lam, R.real, T.real, A.real, r_total, t_total, layer_abs)


def _layer_absorption(n, cos_theta, delta, lam, polarization, r_total):
    """Absorptance in each finite layer, by forward propagation of the field.

    Useful for the design question the brief raises about where visible loss
    happens -- in the metal, or in the oxide. It is computed by rebuilding
    the partial transfer matrices, which costs another chain pass, so it is
    off by default.
    """
    n_media = n.shape[0]
    n_layers = n_media - 2
    absorption = np.zeros((n_layers, lam.size))

    # forward/backward amplitudes at the top of each finite layer
    v = np.ones(lam.size, dtype=complex)
    w = np.asarray(r_total, dtype=complex)
    for j in range(n_layers):
        r, t = fresnel(polarization, n[j], cos_theta[j], n[j + 1], cos_theta[j + 1])
        v_new = (v + r * w) / t
        w_new = (r * v + w) / t
        # Poynting-flux difference across the layer
        dj = delta[j]
        a = v_new * np.exp(-1j * dj)
        b = w_new * np.exp(1j * dj)
        if polarization == "s":
            coeff = (n[j + 1] * cos_theta[j + 1]).real
            top = coeff * (np.abs(v_new) ** 2 - np.abs(w_new) ** 2)
            bot = coeff * (np.abs(a) ** 2 - np.abs(b) ** 2)
        else:
            coeff = (np.conj(n[j + 1]) * cos_theta[j + 1]).real
            top = coeff * (np.abs(v_new) ** 2 - np.abs(w_new) ** 2)
            bot = coeff * (np.abs(a) ** 2 - np.abs(b) ** 2)
        norm = (n[0] * cos_theta[0]).real
        absorption[j] = np.maximum((top - bot) / norm, 0.0)
        v, w = a, b
    return absorption


def incoherent_sandwich(R_front, T_front, R_front_back, T_front_back,
                        internal_transmittance, R_back, T_back):
    """Combine a coherent front stack, a thick absorbing slab and a back surface.

    Intensity (not amplitude) bookkeeping with an infinite geometric series
    of internal bounces -- the correct treatment for a 4 mm glass pane, whose
    thickness vastly exceeds the coherence length of daylight.

    `R_front_back` and `T_front_back` are the front assembly illuminated from
    inside the glass, which differ from the outside-in values.
    """
    tau = np.asarray(internal_transmittance, dtype=float)
    denom = 1.0 - np.asarray(R_front_back) * tau ** 2 * np.asarray(R_back)
    denom = np.where(np.abs(denom) < 1e-12, 1e-12, denom)
    T = np.asarray(T_front) * tau * np.asarray(T_back) / denom
    R = (np.asarray(R_front)
         + np.asarray(T_front) * tau ** 2 * np.asarray(R_back)
         * np.asarray(T_front_back) / denom)
    A = 1.0 - R - T
    return R, T, A


def hemispherical_from_angles(values, angles_deg, weight: str = "cosine") -> float:
    """Integrate a directional quantity into a hemispherical one.

        X_hemi = 2 INT_0^{pi/2} X(theta) cos(theta) sin(theta) d(theta)

    Used to cross-check the EN 673 polynomial for hemispherical emissivity
    against a direct angular integration.
    """
    theta = np.deg2rad(np.asarray(angles_deg, dtype=float))
    vals = np.asarray(values, dtype=float)
    if weight != "cosine":
        raise ValueError("only cosine (Lambertian) weighting is implemented")
    w = np.cos(theta) * np.sin(theta)
    return float(2.0 * np.trapezoid(vals * w, theta))


__all__ = ["TMMResult", "solve", "fresnel", "incoherent_sandwich",
           "hemispherical_from_angles"]
