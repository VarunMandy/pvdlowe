"""Thin-film resistivity: the classical size effect, and percolation.

At the 8-15 nm thicknesses this project works in, bulk resistivity is the
wrong number by a factor of two to five. Two mechanisms do it:

* **Fuchs-Sondheimer** -- diffuse scattering at the two surfaces, governed
  by the specularity p and the ratio of bulk mean free path to thickness.
  Ag has a 53 nm mean free path, so a 10 nm Ag film is deep in this regime.
* **Mayadas-Shatzkes** -- reflection at grain boundaries, governed by the
  grain size D (in a sputtered film, comparable to the thickness) and the
  boundary reflection coefficient R.

Below a critical thickness the film is not continuous at all: Volmer-Weber
growth on an oxide gives islands that coalesce only above some d_c, and
resistivity diverges. The brief's own literature supplies two anchors for
this -- Ag on AZO becoming continuous near 10 nm, Cu on AZO near 11 nm --
and :class:`PercolationModel` is calibrated to them.

The same resistivity ratio is fed back into the optics as a Drude damping
multiplier, so a film that is too thin is penalised twice over, once in
sheet resistance and once in emissivity. That coupling is the whole point:
it is what makes "how thin can the silver go" a question the framework can
actually answer instead of a parameter you have to guess.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import integrate

from ..provenance import Provenance, Quantity


def fuchs_sondheimer_ratio(thickness_nm: float, mean_free_path_nm: float,
                           specularity: float = 0.5) -> float:
    """rho_film / rho_bulk from surface scattering (full FS integral).

        rho_0/rho = 1 - (3/(2k))(1-p) * INT_1^inf (1/t^3 - 1/t^5)
                        (1 - exp(-k t)) / (1 - p exp(-k t)) dt

    with k = d / lambda. Solved numerically rather than using the
    large-k series, because at d/lambda ~ 0.2 the series is not valid.

    Parameters
    ----------
    thickness_nm : film thickness d
    mean_free_path_nm : bulk electron mean free path lambda
    specularity : p in [0, 1]. p=1 is fully specular (no size effect),
        p=0 fully diffuse. Sputtered metal on an oxide is usually taken
        between 0.2 and 0.5; it is a fitting parameter, not a constant.
    """
    d = float(thickness_nm)
    lam = float(mean_free_path_nm)
    p = float(np.clip(specularity, 0.0, 1.0 - 1e-12))
    if d <= 0:
        return np.inf
    kappa = d / lam
    if kappa > 50:
        return 1.0

    def integrand(t):
        ex = np.exp(-kappa * t)
        return (1.0 / t ** 3 - 1.0 / t ** 5) * (1.0 - ex) / (1.0 - p * ex)

    val, _ = integrate.quad(integrand, 1.0, np.inf, limit=200)
    inv_ratio = 1.0 - (3.0 / (2.0 * kappa)) * (1.0 - p) * val
    if inv_ratio <= 1e-6:
        return np.inf
    return float(1.0 / inv_ratio)


def mayadas_shatzkes_ratio(grain_size_nm: float, mean_free_path_nm: float,
                           reflection: float = 0.3) -> float:
    """rho_film / rho_bulk from grain-boundary scattering.

        rho_0/rho = 3 [ 1/3 - alpha/2 + alpha^2 - alpha^3 ln(1 + 1/alpha) ]
        alpha = (lambda / D) * R / (1 - R)
    """
    d_g = float(grain_size_nm)
    lam = float(mean_free_path_nm)
    r = float(np.clip(reflection, 0.0, 1.0 - 1e-9))
    if d_g <= 0:
        return np.inf
    alpha = (lam / d_g) * r / (1.0 - r)
    if alpha < 1e-9:
        return 1.0
    inv = 3.0 * (1.0 / 3.0 - alpha / 2.0 + alpha ** 2
                 - alpha ** 3 * np.log(1.0 + 1.0 / alpha))
    if inv <= 1e-9:
        return np.inf
    return float(1.0 / inv)


@dataclass
class PercolationModel:
    """Island-to-continuous transition for a metal growing on an oxide.

    Below `critical_thickness_nm` the layer is a set of disconnected
    islands: DC conduction is effectively absent and the optical response is
    that of a nanoparticle composite, not a mirror. Just above it the film
    conducts but with excess scattering that decays over a coalescence
    width.

    The DC part follows percolation scaling,

        sigma ~ (d - d_p)^t  for d > d_p,

    with t = 1.3 for a 2D system. `critical_thickness_nm` is the thickness
    at which the film is regarded as usefully continuous, taken slightly
    above the percolation threshold d_p.

    This model is EMPIRICAL and calibrated, not derived. Its parameters are
    the ones to re-fit first once you have your own R_s versus thickness
    series from the sputter tool.
    """

    critical_thickness_nm: float
    percolation_thickness_nm: float | None = None
    exponent: float = 1.3
    coalescence_width_nm: float = 3.0
    provenance: Provenance = Provenance.CALIBRATED
    citation: str = ""

    def __post_init__(self):
        if self.percolation_thickness_nm is None:
            self.percolation_thickness_nm = 0.75 * self.critical_thickness_nm

    def is_continuous(self, thickness_nm: float) -> bool:
        return float(thickness_nm) >= self.critical_thickness_nm

    def fill_fraction(self, thickness_nm: float) -> float:
        """Metal volume fraction of the nominal layer, for the optical EMA."""
        d = float(thickness_nm)
        d_p = float(self.percolation_thickness_nm)
        if d >= self.critical_thickness_nm:
            return 1.0
        if d <= 0:
            return 0.0
        # smooth ramp from a bare-nucleation floor up to full coverage
        frac = 0.45 + 0.55 * (d / self.critical_thickness_nm)
        if d < d_p:
            frac = 0.45 * (d / d_p) ** 0.5
        return float(np.clip(frac, 0.0, 1.0))

    def resistivity_multiplier(self, thickness_nm: float) -> float:
        """Extra resistivity factor on top of the FS-MS size effect.

        Normalised so it is exactly 1 at the continuity thickness -- above
        d_c the classical size effect alone describes the film -- and
        diverges as d approaches the percolation threshold d_p, following
        the 2D percolation exponent.
        """
        d = float(thickness_nm)
        d_p = float(self.percolation_thickness_nm)
        d_c = float(self.critical_thickness_nm)
        if d <= d_p:
            return np.inf
        if d >= d_c:
            return 1.0
        return float(((d - d_p) / (d_c - d_p)) ** (-self.exponent))


#: Percolation anchors from the literature the brief cites. Both are
#: LITERATURE_UNVERIFIED: they are the thicknesses at which those papers
#: report continuity, transcribed from the brief, not re-measured.
PERCOLATION = {
    "Ag": PercolationModel(
        critical_thickness_nm=10.0, coalescence_width_nm=2.5,
        citation="AZO/Ag/AZO trilayer, Ag continuous near 10 nm "
                 "(brief section 3; verify against Ceram. Int. source)"),
    "Cu": PercolationModel(
        critical_thickness_nm=11.0, coalescence_width_nm=3.0,
        citation="AZO/Cu/AZO multilayer, Cu continuity from about 11 nm "
                 "(brief section 8; verify against PolyU record)"),
    "Au": PercolationModel(critical_thickness_nm=9.0),
    "Al": PercolationModel(critical_thickness_nm=8.0),
}

#: Ag-Cu and other alloys nucleate differently from either parent -- a
#: Cu-containing Ag film generally wets an oxide better and percolates
#: thinner. Verifying that is one of the experiments in the DoE.
DEFAULT_ALLOY_PERCOLATION = PercolationModel(
    critical_thickness_nm=9.0, coalescence_width_nm=2.5,
    provenance=Provenance.HYPOTHESIS,
    citation="hypothesis: Cu addition improves wetting on AZO and lowers d_c")


@dataclass
class ThinFilmResistivity:
    """Combined size-effect resistivity model for one metal layer."""

    bulk_resistivity_uohm_cm: float
    mean_free_path_nm: float
    specularity: float = 0.5
    grain_boundary_reflection: float = 0.25
    grain_size_ratio: float = 3.0        # lateral grain size D as a multiple of d
    percolation: PercolationModel | None = None

    def ratio(self, thickness_nm: float) -> float:
        """rho_film / rho_bulk, all mechanisms combined."""
        d = float(thickness_nm)
        if d <= 0:
            return np.inf
        r_fs = fuchs_sondheimer_ratio(d, self.mean_free_path_nm, self.specularity)
        r_ms = mayadas_shatzkes_ratio(max(self.grain_size_ratio * d, 1e-3),
                                      self.mean_free_path_nm,
                                      self.grain_boundary_reflection)
        # Matthiessen-like addition of the excess resistivities
        total = 1.0 + (r_fs - 1.0) + (r_ms - 1.0)
        if self.percolation is not None:
            total *= self.percolation.resistivity_multiplier(d)
        return float(total)

    def resistivity(self, thickness_nm: float) -> float:
        """Film resistivity in uohm.cm."""
        return self.bulk_resistivity_uohm_cm * self.ratio(thickness_nm)

    def sheet_resistance(self, thickness_nm: float) -> float:
        """R_s = rho / d, in ohm/sq."""
        d = float(thickness_nm)
        if d <= 0:
            return np.inf
        rho_ohm_cm = self.resistivity(d) * 1e-6      # uohm.cm -> ohm.cm
        return float(rho_ohm_cm / (d * 1e-7))        # d in cm

    def sheet_resistance_quantity(self, thickness_nm: float) -> Quantity:
        return Quantity(
            self.sheet_resistance(thickness_nm), "ohm/sq", Provenance.MODEL,
            source=f"FS-MS size-effect model, d={thickness_nm:g} nm",
            note="specularity and grain-boundary reflection are fitting "
                 "parameters; re-fit to a measured R_s(d) series")

    @classmethod
    def for_metal(cls, metal_data, **kwargs) -> "ThinFilmResistivity":
        """Build from a :class:`~pvdlowe.materials.metals.MetalData`."""
        perc = kwargs.pop("percolation", PERCOLATION.get(metal_data.symbol))
        return cls(metal_data.resistivity_bulk_uohm_cm,
                   metal_data.mean_free_path_nm, percolation=perc, **kwargs)


def parallel_sheet_resistance(*sheet_resistances: float) -> float:
    """Combine conducting layers in a stack -- they conduct in parallel.

    The TCO layers are not insulators: AZO at 2.6e-3 ohm.cm and 40 nm is
    about 650 ohm/sq, which shunts a 4 ohm/sq silver layer by only a
    fraction of a percent -- but the calculation should still be done, and
    it matters for the Cu-only and sub-percolation cases.
    """
    inv = 0.0
    for rs in sheet_resistances:
        if rs is None or not np.isfinite(rs) or rs <= 0:
            continue
        inv += 1.0 / rs
    return float(1.0 / inv) if inv > 0 else np.inf


__all__ = [
    "fuchs_sondheimer_ratio", "mayadas_shatzkes_ratio", "PercolationModel",
    "PERCOLATION", "DEFAULT_ALLOY_PERCOLATION", "ThinFilmResistivity",
    "parallel_sheet_resistance",
]
