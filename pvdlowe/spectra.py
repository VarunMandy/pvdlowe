"""Spectral grids and the weighting functions the glazing standards use.

Three integrals matter for this project:

* visible transmittance  T_vis   -- D65 illuminant x photopic response,
  380-780 nm  (EN 410 / ISO 9050)
* solar factor           T_sol   -- AM1.5 global, 300-2500 nm
* normal emissivity      eps_n   -- 283 K black body, 5-50 um (EN 12898)

Only the third one is needed for the headline Low-E number, and it needs no
external data at all: a Planck function is exact. That is deliberate --
emissivity, the metric the brief cares about most, is the metric this
package can compute without shipping anyone else's tabulated spectra.

T_vis and T_sol use analytic approximations by default, which are good to
roughly a percent for smooth coating spectra but are *not* the tabulated
standard weights. Load the real tables with
:meth:`Weighting.from_csv` before quoting a number in a report; the
default objects report provenance MODEL for exactly this reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .constants import planck_spectral_radiance_wavelength
from .provenance import Provenance, Quantity

# --- standard wavelength grids ------------------------------------------

def visible_grid(step_nm: float = 5.0) -> np.ndarray:
    """380-780 nm, the EN 410 visible range."""
    return np.arange(380.0, 780.0 + 1e-9, step_nm)


def solar_grid(step_nm: float = 10.0) -> np.ndarray:
    """300-2500 nm, the ISO 9050 solar range."""
    return np.arange(300.0, 2500.0 + 1e-9, step_nm)


def infrared_grid(n_points: int = 400) -> np.ndarray:
    """5-50 um in nm, the EN 12898 emissivity range.

    Logarithmic spacing: the 283 K Planck peak sits near 10 um and the band
    spans a decade, so log spacing puts samples where the weight is.
    """
    return np.logspace(np.log10(5_000.0), np.log10(50_000.0), n_points)


def full_grid() -> np.ndarray:
    """One grid spanning UV to far IR, for whole-stack spectra plots."""
    return np.unique(np.concatenate([
        np.arange(300.0, 780.0, 5.0),
        np.arange(780.0, 2500.0, 20.0),
        np.logspace(np.log10(2500.0), np.log10(50_000.0), 300),
    ]))


# --- photopic response ---------------------------------------------------

def _piecewise_gauss(x, mu, sigma_lo, sigma_hi):
    """Asymmetric Gaussian used by the Wyman-Sloan-Shirley CMF fit."""
    x = np.asarray(x, dtype=float)
    sigma = np.where(x < mu, sigma_lo, sigma_hi)
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def photopic_response(wavelength_nm) -> np.ndarray:
    """CIE 1931 V(lambda), multi-lobe analytic fit.

    Wyman, Sloan & Shirley, "Simple Analytic Approximations to the CIE XYZ
    Color Matching Functions", J. Computer Graphics Techniques 2(2), 2013.
    Accurate to about 1% of peak; replace with the tabulated CIE data via
    :meth:`Weighting.from_csv` for reporting-grade numbers.
    """
    lam = np.asarray(wavelength_nm, dtype=float)
    v = (0.821 * _piecewise_gauss(lam, 568.8, 46.9, 40.5)
         + 0.286 * _piecewise_gauss(lam, 530.9, 16.3, 31.1))
    return np.where((lam >= 360.0) & (lam <= 830.0), v, 0.0)


def d65_approx(wavelength_nm) -> np.ndarray:
    """Approximation to the D65 illuminant as a 6504 K Planckian.

    D65 is a *daylight* illuminant, not a black body: it carries Fraunhofer
    structure and a UV shoulder that a Planckian misses. Because the visible
    integral is dominated by the narrow V(lambda) window, the resulting T_vis
    error for a smooth coating spectrum is small -- but it is an
    approximation, and it is flagged as one.
    """
    return planck_spectral_radiance_wavelength(wavelength_nm, 6504.0)


def am15g_approx(wavelength_nm) -> np.ndarray:
    """Crude AM1.5G stand-in: 5778 K Planckian with a flat air-mass factor.

    This misses the H2O and CO2 absorption bands entirely, so solar-factor
    numbers from it are indicative only. Load ASTM G173 with
    :meth:`Weighting.from_csv` before using T_sol quantitatively.
    """
    lam = np.asarray(wavelength_nm, dtype=float)
    body = planck_spectral_radiance_wavelength(lam, 5778.0)
    # Rayleigh-ish short-wavelength roll-off, normalised out later anyway.
    atten = np.clip(1.0 - 0.35 * (350.0 / np.maximum(lam, 200.0)) ** 4, 0.0, 1.0)
    return body * atten


def blackbody_283k(wavelength_nm) -> np.ndarray:
    """283 K Planck weighting for EN 12898 normal emissivity. Exact."""
    return planck_spectral_radiance_wavelength(wavelength_nm, 283.0)


# --- weighting container -------------------------------------------------

@dataclass
class Weighting:
    """A normalised spectral weighting function on a fixed grid."""

    name: str
    wavelength_nm: np.ndarray
    weight: np.ndarray
    provenance: Provenance = Provenance.MODEL
    citation: str = ""

    def __post_init__(self):
        self.wavelength_nm = np.asarray(self.wavelength_nm, dtype=float)
        self.weight = np.asarray(self.weight, dtype=float)
        if self.wavelength_nm.shape != self.weight.shape:
            raise ValueError("grid and weight must have the same shape")
        if np.any(self.weight < 0):
            raise ValueError("weights must be non-negative")
        total = np.trapezoid(self.weight, self.wavelength_nm)
        if total <= 0:
            raise ValueError(f"weighting {self.name!r} integrates to zero")
        self._norm = float(total)

    def apply(self, spectrum) -> float:
        """Weighted average of `spectrum` sampled on this grid."""
        spectrum = np.asarray(spectrum, dtype=float)
        if spectrum.shape != self.wavelength_nm.shape:
            raise ValueError(
                f"spectrum has shape {spectrum.shape}, weighting "
                f"{self.name!r} expects {self.wavelength_nm.shape}. "
                "Evaluate the stack on weighting.wavelength_nm.")
        return float(np.trapezoid(spectrum * self.weight,
                                  self.wavelength_nm) / self._norm)

    def as_quantity(self, spectrum, unit: str = "", source: str = "") -> Quantity:
        return Quantity(self.apply(spectrum), unit, self.provenance,
                        source=source or self.name, citation=self.citation)

    @classmethod
    def from_csv(cls, path, name: str, provenance: Provenance = Provenance.LITERATURE,
                 citation: str = "", wavelength_column: int = 0,
                 weight_column: int = 1, wavelength_unit: str = "nm") -> "Weighting":
        """Load a tabulated weighting (EN 410 table, ASTM G173, CIE V(lambda)).

        Expects a two-column CSV with a one-line header. Wavelength unit may
        be 'nm' or 'um'.
        """
        data = np.genfromtxt(Path(path), delimiter=",", skip_header=1)
        lam = data[:, wavelength_column].astype(float)
        w = data[:, weight_column].astype(float)
        if wavelength_unit == "um":
            lam = lam * 1000.0
        elif wavelength_unit != "nm":
            raise ValueError("wavelength_unit must be 'nm' or 'um'")
        order = np.argsort(lam)
        return cls(name, lam[order], w[order], provenance, citation)

    def resample(self, wavelength_nm) -> "Weighting":
        lam = np.asarray(wavelength_nm, dtype=float)
        w = np.interp(lam, self.wavelength_nm, self.weight, left=0.0, right=0.0)
        return Weighting(self.name, lam, w, self.provenance, self.citation)


# --- ready-made weightings ----------------------------------------------

def visible_weighting(step_nm: float = 5.0) -> Weighting:
    """D65 x V(lambda), the T_vis weighting of EN 410 / ISO 9050."""
    lam = visible_grid(step_nm)
    return Weighting(
        "D65 x V(lambda) [analytic]", lam, d65_approx(lam) * photopic_response(lam),
        Provenance.MODEL,
        "EN 410 weighting approximated: Wyman et al. 2013 V(lambda) fit x 6504 K Planckian",
    )


def solar_weighting(step_nm: float = 10.0) -> Weighting:
    """AM1.5G weighting for the ISO 9050 solar transmittance."""
    lam = solar_grid(step_nm)
    return Weighting(
        "AM1.5G [analytic]", lam, am15g_approx(lam), Provenance.MODEL,
        "ISO 9050 solar weighting approximated by an attenuated 5778 K Planckian",
    )


def emissivity_weighting(n_points: int = 400) -> Weighting:
    """283 K black-body weighting, 5-50 um, per EN 12898.

    Unlike the other two this is exact -- Planck's law is the standard's
    definition, not an approximation to a measured spectrum.
    """
    lam = infrared_grid(n_points)
    return Weighting(
        "283 K black body (EN 12898)", lam, blackbody_283k(lam),
        Provenance.LITERATURE,
        "EN 12898: normal emissivity weighted by a 283 K black body over 5-50 um",
    )


__all__ = [
    "visible_grid", "solar_grid", "infrared_grid", "full_grid",
    "photopic_response", "d65_approx", "am15g_approx", "blackbody_283k",
    "Weighting", "visible_weighting", "solar_weighting", "emissivity_weighting",
]
