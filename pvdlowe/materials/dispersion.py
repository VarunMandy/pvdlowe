"""Dispersion models returning a complex refractive index.

Sign convention throughout the package: fields go as exp(-i omega t), so

    eps = eps1 + i eps2,   eps2 >= 0
    n_tilde = n + i k,     k >= 0    (k > 0 means absorption)

Every model is a callable object mapping wavelength in nm to a complex
array. Anything obeying that contract can be dropped into a stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..constants import wavelength_to_ev
from ..provenance import Provenance


def eps_to_nk(eps: np.ndarray) -> np.ndarray:
    """Complex permittivity -> complex refractive index with k >= 0."""
    eps = np.asarray(eps, dtype=complex)
    nk = np.sqrt(eps)
    # numpy's principal branch already gives Im >= 0 for Im(eps) >= 0, but
    # guard against round-off producing a tiny negative k.
    return np.where(nk.imag < 0, np.conj(nk), nk)


def nk_to_eps(nk: np.ndarray) -> np.ndarray:
    return np.asarray(nk, dtype=complex) ** 2


class Dispersion:
    """Base class: subclasses implement :meth:`epsilon`."""

    name: str = "dispersion"

    def epsilon(self, wavelength_nm) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def __call__(self, wavelength_nm) -> np.ndarray:
        return eps_to_nk(self.epsilon(wavelength_nm))

    def nk(self, wavelength_nm) -> np.ndarray:
        return self(wavelength_nm)

    def n(self, wavelength_nm) -> np.ndarray:
        return self(wavelength_nm).real

    def k(self, wavelength_nm) -> np.ndarray:
        return self(wavelength_nm).imag

    def __add__(self, other: "Dispersion") -> "SumDispersion":
        return SumDispersion([self, other])


@dataclass
class SumDispersion(Dispersion):
    """Sum of permittivity contributions minus the double-counted vacuum term."""

    parts: list
    name: str = "sum"

    def epsilon(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        total = np.zeros(lam.shape, dtype=complex)
        for i, p in enumerate(self.parts):
            eps = np.atleast_1d(p.epsilon(lam))
            total = total + (eps if i == 0 else eps - 1.0)
        return total


@dataclass
class ConstantIndex(Dispersion):
    """Non-dispersive index, useful for air and for quick sanity tests."""

    n_value: float = 1.0
    k_value: float = 0.0
    name: str = "constant"

    def epsilon(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        nk = complex(self.n_value, self.k_value)
        return np.full(lam.shape, nk ** 2, dtype=complex)


@dataclass
class LorentzDrude(Dispersion):
    """Lorentz-Drude model for metals.

        eps(E) = eps_inf
                 - f0 * wp^2 / (E^2 + i*G0*E)
                 + sum_j f_j * wp^2 / (E_j^2 - E^2 - i*E*Gamma_j)

    with all energies in eV. This is the Rakic et al. (1998) parameterisation
    form; see :mod:`pvdlowe.materials.metals` for the coefficients.

    Accuracy note that matters for this project: the free-electron term
    dominates below about 1 eV, so far-infrared reflectance -- and therefore
    emissivity -- is modelled well. Interband structure in the visible is
    reproduced only to within a few percent in n and k, so visible
    transmittance from this model is indicative. Substitute measured
    ellipsometry data (:class:`TabulatedIndex`) for reporting-grade T_vis.
    """

    plasma_energy_ev: float
    f0: float
    gamma0_ev: float
    oscillators: tuple = ()      # (f_j, Gamma_j [eV], E_j [eV])
    eps_inf: float = 1.0
    name: str = "lorentz-drude"
    provenance: Provenance = Provenance.LITERATURE_UNVERIFIED

    def epsilon(self, wavelength_nm) -> np.ndarray:
        e = np.atleast_1d(wavelength_to_ev(wavelength_nm)).astype(float)
        wp2 = self.plasma_energy_ev ** 2
        eps = np.full(e.shape, complex(self.eps_inf, 0.0))
        # free-electron (Drude) term
        eps = eps - self.f0 * wp2 / (e ** 2 + 1j * self.gamma0_ev * e)
        # bound-electron (Lorentz) terms
        for f_j, g_j, e_j in self.oscillators:
            eps = eps + f_j * wp2 / (e_j ** 2 - e ** 2 - 1j * e * g_j)
        return eps

    def with_damping_scale(self, scale: float) -> "LorentzDrude":
        """Copy with the free-electron damping multiplied by `scale`.

        This is the hook that couples the electrical thin-film model to the
        optics: a film whose resistivity is raised x3 by surface and
        grain-boundary scattering has its Drude damping raised x3, which is
        what degrades far-IR reflectance in a very thin metal layer.
        """
        return LorentzDrude(
            self.plasma_energy_ev, self.f0, self.gamma0_ev * float(scale),
            self.oscillators, self.eps_inf,
            f"{self.name} (damping x{scale:.2f})", Provenance.MODEL,
        )


@dataclass
class DrudeSemiconductor(Dispersion):
    """Degenerately doped oxide semiconductor: Drude + band-edge oscillator.

    Built for the transparent conductive oxides. One physical parameter set
    -- carrier density, mobility, effective mass -- drives *both* the
    infrared plasma response and the DC sheet resistance, so an AZO layer
    fitted to a measured Hall result is automatically consistent between the
    optical and electrical halves of the framework.

    The band edge shifts with doping through the Burstein-Moss term, which is
    the effect the brief cites from the DFT literature (Al substitution
    widening the ZnO optical gap).
    """

    carrier_density_cm3: float
    mobility_cm2_vs: float
    effective_mass: float = 0.28          # m*/m_e, typical for ZnO
    eps_inf: float = 2.50                 # deep-UV background, ABOVE the edge
    gap_ev: float = 3.37                  # undoped optical gap
    edge_strength: float = 0.75           # band-edge oscillator amplitude
    edge_width_ev: float = 0.35
    reduced_mass: float = 0.20            # m_r*/m_e for the Burstein-Moss term
    burstein_moss: bool = True
    name: str = "drude-semiconductor"
    provenance: Provenance = Provenance.MODEL

    # -- derived physical quantities ------------------------------------
    @property
    def plasma_energy_ev(self) -> float:
        from ..constants import drude_plasma_energy_ev
        return float(drude_plasma_energy_ev(
            self.carrier_density_cm3, self.effective_mass, 1.0))

    @property
    def damping_ev(self) -> float:
        from ..constants import drude_damping_energy_ev
        return float(drude_damping_energy_ev(
            self.mobility_cm2_vs, self.effective_mass))

    @property
    def resistivity_ohm_cm(self) -> float:
        """DC resistivity implied by the same N and mu. rho = 1/(N e mu)."""
        from ..constants import E_CHARGE
        return 1.0 / (self.carrier_density_cm3 * E_CHARGE * self.mobility_cm2_vs)

    @property
    def burstein_moss_shift_ev(self) -> float:
        """Filled-band blue shift, dE = (hbar^2 / 2 m_r) (3 pi^2 N)^(2/3)."""
        if not self.burstein_moss:
            return 0.0
        from ..constants import HBAR, M_E, E_CHARGE
        n_si = self.carrier_density_cm3 * 1e6
        kf = (3.0 * np.pi ** 2 * n_si) ** (1.0 / 3.0)
        return float(HBAR ** 2 * kf ** 2 / (2.0 * self.reduced_mass * M_E) / E_CHARGE)

    @property
    def optical_gap_ev(self) -> float:
        return self.gap_ev + self.burstein_moss_shift_ev

    @property
    def plasma_wavelength_um(self) -> float:
        """Screened plasma wavelength -- roughly where the TCO turns reflective."""
        from ..constants import HC_EV_NM
        e_screened = self.plasma_energy_ev / np.sqrt(self.eps_inf)
        return float(HC_EV_NM / e_screened / 1000.0)

    def epsilon(self, wavelength_nm) -> np.ndarray:
        e = np.atleast_1d(wavelength_to_ev(wavelength_nm)).astype(float)
        wp = self.plasma_energy_ev
        g = self.damping_ev
        eg = self.optical_gap_ev
        eps = np.full(e.shape, complex(self.eps_inf, 0.0))
        eps = eps - wp ** 2 / (e ** 2 + 1j * g * e)
        eps = eps + self.edge_strength * eg ** 2 / (
            eg ** 2 - e ** 2 - 1j * e * self.edge_width_ev)
        return eps


@dataclass
class Sellmeier(Dispersion):
    """Transparent dielectric, n^2 = 1 + sum B_i lam^2 / (lam^2 - C_i), lam in um."""

    coefficients: tuple    # ((B1, C1), (B2, C2), ...) with C in um^2
    name: str = "sellmeier"
    provenance: Provenance = Provenance.LITERATURE

    def epsilon(self, wavelength_nm) -> np.ndarray:
        lam_um = np.atleast_1d(np.asarray(wavelength_nm, dtype=float)) / 1000.0
        l2 = lam_um ** 2
        n2 = np.ones_like(l2)
        for b, c in self.coefficients:
            n2 = n2 + b * l2 / (l2 - c)
        return n2.astype(complex)


@dataclass
class LorentzOscillators(Dispersion):
    """Bare set of Lorentz oscillators on an eps_inf background.

    Used for infrared phonon (reststrahlen) bands, e.g. the Si-O stretch in
    silicate glass.
    """

    eps_inf: float
    oscillators: tuple      # (amplitude [eV^2], Gamma [eV], E_0 [eV])
    name: str = "lorentz"
    provenance: Provenance = Provenance.CALIBRATED

    def epsilon(self, wavelength_nm) -> np.ndarray:
        e = np.atleast_1d(wavelength_to_ev(wavelength_nm)).astype(float)
        eps = np.full(e.shape, complex(self.eps_inf, 0.0))
        for amp, g, e0 in self.oscillators:
            eps = eps + amp / (e0 ** 2 - e ** 2 - 1j * e * g)
        return eps


@dataclass
class TabulatedIndex(Dispersion):
    """Measured or published n,k on a wavelength grid, log-interpolated.

    This is the class to use once ellipsometry data exists. Values outside
    the tabulated range are held at the end points and
    :attr:`extrapolation_warned` records that it happened, because silently
    extrapolating optical constants from 2 um to 25 um is a good way to
    invent an emissivity.
    """

    wavelength_nm: np.ndarray
    n_values: np.ndarray
    k_values: np.ndarray
    name: str = "tabulated"
    provenance: Provenance = Provenance.MEASURED
    citation: str = ""
    extrapolation_warned: bool = field(default=False, repr=False)

    def __post_init__(self):
        self.wavelength_nm = np.asarray(self.wavelength_nm, dtype=float)
        self.n_values = np.asarray(self.n_values, dtype=float)
        self.k_values = np.asarray(self.k_values, dtype=float)
        order = np.argsort(self.wavelength_nm)
        self.wavelength_nm = self.wavelength_nm[order]
        self.n_values = self.n_values[order]
        self.k_values = self.k_values[order]

    @property
    def range_nm(self) -> tuple:
        return float(self.wavelength_nm[0]), float(self.wavelength_nm[-1])

    def __call__(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        lo, hi = self.range_nm
        if lam.min() < lo * 0.999 or lam.max() > hi * 1.001:
            self.extrapolation_warned = True
        n = np.interp(lam, self.wavelength_nm, self.n_values)
        k = np.interp(lam, self.wavelength_nm, self.k_values)
        return n + 1j * k

    def epsilon(self, wavelength_nm) -> np.ndarray:
        return nk_to_eps(self(wavelength_nm))

    @classmethod
    def from_csv(cls, path, name: str | None = None, citation: str = "",
                 wavelength_unit: str = "nm") -> "TabulatedIndex":
        """Load a 3-column CSV: wavelength, n, k (one header line).

        Matches the export format of refractiveindex.info and of most
        ellipsometry packages.
        """
        p = Path(path)
        data = np.genfromtxt(p, delimiter=",", skip_header=1)
        lam = data[:, 0].astype(float)
        if wavelength_unit == "um":
            lam *= 1000.0
        return cls(lam, data[:, 1].astype(float), data[:, 2].astype(float),
                   name or p.stem, Provenance.MEASURED, citation)


@dataclass
class BruggemanEMA(Dispersion):
    """Bruggeman effective-medium approximation for a two-phase mixture.

    Used two ways here:

    * a nominally-alloyed Ag-Cu layer that has phase separated into Ag-rich
      and Cu-rich domains much smaller than the wavelength -- which is what
      the brief warns is thermodynamically likely (13% lattice mismatch,
      segregation tendency);
    * a metal film below its percolation thickness, modelled as metal islands
      in a host.

    The EMA is a *mean-field* treatment. It cannot describe percolation
    correctly near the critical fill fraction, and it ignores island shape
    and plasmonic coupling, so treat sub-continuous films as qualitative.
    """

    phase_a: Dispersion
    phase_b: Dispersion
    fraction_a: float
    name: str = "bruggeman"
    provenance: Provenance = Provenance.MODEL

    def epsilon(self, wavelength_nm) -> np.ndarray:
        fa = float(np.clip(self.fraction_a, 0.0, 1.0))
        fb = 1.0 - fa
        ea = np.atleast_1d(self.phase_a.epsilon(wavelength_nm)).astype(complex)
        eb = np.atleast_1d(self.phase_b.epsilon(wavelength_nm)).astype(complex)
        # Bruggeman: fa (ea-e)/(ea+2e) + fb (eb-e)/(eb+2e) = 0
        # -> 2 e^2 + e (2 fa ea - fa eb + 2 fb eb - fb ea) - ea eb = 0
        b = (2.0 * fa - fb) * ea + (2.0 * fb - fa) * eb
        disc = np.sqrt(b ** 2 + 8.0 * ea * eb)
        root1 = (b + disc) / 4.0
        root2 = (b - disc) / 4.0
        # physical root: Im(eps) >= 0
        return np.where(root1.imag >= 0, root1, root2)


__all__ = [
    "Dispersion", "SumDispersion", "ConstantIndex", "LorentzDrude",
    "DrudeSemiconductor", "Sellmeier", "LorentzOscillators", "TabulatedIndex",
    "BruggemanEMA", "eps_to_nk", "nk_to_eps",
]
