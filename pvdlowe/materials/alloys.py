"""Binary and ternary metal alloys for the Low-E layer.

The brief's section 5 identifies the central materials-science ambiguity of
this project: Ag and Cu have roughly 13% lattice mismatch and a
thermodynamic tendency to segregate, yet a sputtered film may be
metastably mixed because deposition kinetics beat equilibrium. Those are two
*different physical states* with two different optical responses, and which
one you get is an experimental question.

So this module refuses to pick one. It implements both:

``mixing_model="solid_solution"``
    A single homogeneous metastable phase. One Drude term with an
    alloy-averaged plasma energy and a damping raised by Nordheim alloy
    scattering, plus composition-weighted interband structure.

``mixing_model="ema"``
    Ag-rich and Cu-rich domains, small compared with the wavelength,
    combined by the Bruggeman effective-medium approximation.

The two predictions diverge most in the near infrared, which makes the
difference measurable by spectrophotometry -- turning "is the sputtered
Ag-Cu layer mixed or segregated?" into a falsifiable prediction rather than
a discussion point. :func:`discriminating_wavelengths` reports where to look.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..constants import drude_damping_from_resistivity_ev
from ..provenance import Provenance, Quantity
from .dispersion import BruggemanEMA, Dispersion, LorentzDrude
from .metals import MetalData, metal

#: Nordheim coefficients for residual alloy scattering, in uohm.cm, such
#: that rho_excess = C x (1-x). The Ag-Cu value is set so the dilute limit
#: reproduces the accepted d(rho)/dc for Cu in Ag of roughly
#: 0.12 uohm.cm per at.%. ESTIMATE grade -- refit to your own Hall data.
NORDHEIM_COEFFICIENT: dict[frozenset, float] = {
    frozenset(("Ag", "Cu")): 12.0,
    frozenset(("Ag", "Al")): 20.0,
    frozenset(("Ag", "Ti")): 45.0,
    frozenset(("Cu", "Al")): 18.0,
    frozenset(("Cu", "Ti")): 50.0,
    frozenset(("Cu", "Zn")): 6.0,
}


def nordheim_resistivity(composition: dict[str, float],
                         coefficients: dict | None = None) -> float:
    """Bulk alloy resistivity in uohm.cm from Nordheim's rule.

        rho = sum_i x_i rho_i + sum_{i<j} C_ij x_i x_j

    Valid for a disordered substitutional solid solution. It does *not*
    describe a two-phase segregated microstructure -- for that the
    resistivity is closer to a parallel/percolative combination of the
    phases, generally lower than Nordheim predicts.
    """
    coeffs = NORDHEIM_COEFFICIENT if coefficients is None else coefficients
    symbols = list(composition)
    rho = sum(composition[s] * metal(s).resistivity_bulk_uohm_cm for s in symbols)
    for i, a in enumerate(symbols):
        for b in symbols[i + 1:]:
            c = coeffs.get(frozenset((a, b)), 25.0)
            rho += c * composition[a] * composition[b]
    return float(rho)


def alloy_mean_free_path(composition: dict[str, float]) -> float:
    """Effective mean free path, scaled down by the alloy resistivity increase.

    lambda ~ v_F tau and rho ~ 1/tau, so the alloy mean free path falls in
    proportion to the resistivity rise. Matters because it feeds the
    Fuchs-Sondheimer size effect: a resistive alloy is *less* sensitive to
    thickness than pure Ag, since its mean free path is already short.
    """
    lam_weighted = sum(composition[s] * metal(s).mean_free_path_nm
                       for s in composition)
    rho_weighted = sum(composition[s] * metal(s).resistivity_bulk_uohm_cm
                       for s in composition)
    rho_alloy = nordheim_resistivity(composition)
    if rho_alloy <= 0:
        return lam_weighted
    return float(lam_weighted * rho_weighted / rho_alloy)


def _interband_epsilon(m: MetalData, wavelength_nm) -> np.ndarray:
    """Bound-electron contribution to eps, with the vacuum term removed.

    Taken as the oscillator sum alone rather than as (full LD - Drude), so
    the result does not depend on which damping the free-electron term was
    built with.
    """
    interband = LorentzDrude(m.plasma_energy_ev, 0.0, 1.0, m.oscillators, 1.0,
                             f"{m.symbol} interband", Provenance.MODEL)
    return np.atleast_1d(interband.epsilon(wavelength_nm)).astype(complex) - 1.0


@dataclass
class AlloyDispersion(Dispersion):
    """Composition-averaged metal dispersion (metastable solid solution).

    Free-electron term: f0*wp^2 averaged by atomic fraction (proportional to
    conduction-electron density over effective mass), damping set by the
    Nordheim alloy resistivity so that Gamma_alloy/Gamma_avg =
    rho_alloy/rho_avg.

    Interband term: each parent's bound-electron contribution weighted by its
    fraction. This is a linear mixing of dielectric functions, appropriate to
    first order for a disordered alloy and *not* a substitute for a real
    calculation of the alloy band structure -- which is exactly the DFT work
    the brief proposes in its section 9.
    """

    composition: dict
    resistivity_uohm_cm: float | None = None
    name: str = "alloy"
    provenance: Provenance = Provenance.MODEL

    def __post_init__(self):
        total = sum(self.composition.values())
        if not np.isclose(total, 1.0, atol=1e-6):
            self.composition = {k: v / total for k, v in self.composition.items()}
        if not self.name or self.name == "alloy":
            self.name = format_composition(self.composition)

    @property
    def plasma_energy_ev(self) -> float:
        """sqrt of the fraction-weighted f0*wp^2."""
        val = sum(f * metal(s).f0 * metal(s).plasma_energy_ev ** 2
                  for s, f in self.composition.items())
        return float(np.sqrt(val))

    @property
    def bulk_resistivity_uohm_cm(self) -> float:
        return nordheim_resistivity(self.composition)

    @property
    def effective_resistivity_uohm_cm(self) -> float:
        return (self.bulk_resistivity_uohm_cm if self.resistivity_uohm_cm is None
                else float(self.resistivity_uohm_cm))

    @property
    def alloy_damping_ev(self) -> float:
        """Free-electron damping consistent with the alloy's resistivity."""
        return drude_damping_from_resistivity_ev(
            self.plasma_energy_ev, self.effective_resistivity_uohm_cm)

    def epsilon(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        drude = LorentzDrude(self.plasma_energy_ev, 1.0, self.alloy_damping_ev,
                             (), 1.0, "alloy Drude", Provenance.MODEL)
        eps = np.atleast_1d(drude.epsilon(lam)).astype(complex)
        for sym, frac in self.composition.items():
            eps = eps + frac * _interband_epsilon(metal(sym), lam)
        return eps

    def with_resistivity(self, resistivity_uohm_cm: float) -> "AlloyDispersion":
        return AlloyDispersion(dict(self.composition), float(resistivity_uohm_cm),
                               self.name)


@dataclass
class Alloy:
    """A named alloy composition with both microstructure hypotheses available."""

    composition: dict
    mixing_model: str = "solid_solution"     # or "ema"
    label: str = ""
    provenance: Provenance = Provenance.HYPOTHESIS
    note: str = ""
    _cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        total = sum(self.composition.values())
        if total <= 0:
            raise ValueError("composition must have positive total")
        self.composition = {k: v / total for k, v in self.composition.items()}
        if not self.label:
            self.label = format_composition(self.composition)
        if self.mixing_model not in ("solid_solution", "ema"):
            raise ValueError("mixing_model must be 'solid_solution' or 'ema'")

    # -- identity --------------------------------------------------------
    @property
    def symbols(self) -> list[str]:
        return sorted(self.composition, key=lambda s: -self.composition[s])

    @property
    def is_pure(self) -> bool:
        return len(self.composition) == 1 or max(self.composition.values()) > 0.999

    @property
    def silver_fraction(self) -> float:
        return float(self.composition.get("Ag", 0.0))

    # -- physical properties --------------------------------------------
    @property
    def bulk_resistivity_uohm_cm(self) -> float:
        if self.mixing_model == "ema" and not self.is_pure:
            # two-phase: conduction takes the easy path through the more
            # conductive phase, so parallel-weighted rather than Nordheim
            inv = sum(f / metal(s).resistivity_bulk_uohm_cm
                      for s, f in self.composition.items())
            return float(1.0 / inv)
        return nordheim_resistivity(self.composition)

    @property
    def mean_free_path_nm(self) -> float:
        return alloy_mean_free_path(self.composition)

    @property
    def density_g_cm3(self) -> float:
        """Volume-additive density from atomic fractions (Vegard-like)."""
        num = sum(f * metal(s).molar_mass_g_mol for s, f in self.composition.items())
        den = sum(f * metal(s).molar_mass_g_mol / metal(s).density_g_cm3
                  for s, f in self.composition.items())
        return float(num / den)

    def areal_mass(self, thickness_nm: float) -> float:
        """g/m^2 of alloy in a layer of the given thickness."""
        return self.density_g_cm3 * float(thickness_nm) * 1e-3

    def element_areal_mass(self, thickness_nm: float) -> dict:
        """g/m^2 of each element -- what the Ag-consumption metric needs."""
        total = self.areal_mass(thickness_nm)
        mass_frac_den = sum(f * metal(s).molar_mass_g_mol
                            for s, f in self.composition.items())
        return {s: total * f * metal(s).molar_mass_g_mol / mass_frac_den
                for s, f in self.composition.items()}

    # -- optics ----------------------------------------------------------
    def dispersion(self, resistivity_uohm_cm: float | None = None) -> Dispersion:
        """Optical dispersion, optionally anchored to a measured film resistivity.

        The resistivity sets the free-electron damping, so passing the
        thin-film value from the transport model is what links a resistive
        layer to a poor infrared mirror.
        """
        rho = (self.bulk_resistivity_uohm_cm if resistivity_uohm_cm is None
               else float(resistivity_uohm_cm))
        key = ("disp", self.mixing_model, round(rho, 6))
        if key in self._cache:
            return self._cache[key]
        if self.is_pure:
            sym = max(self.composition, key=self.composition.get)
            disp: Dispersion = metal(sym).dispersion(rho)
        elif self.mixing_model == "solid_solution":
            disp = AlloyDispersion(dict(self.composition), rho, self.label)
        else:
            syms = self.symbols
            if len(syms) > 2:
                raise NotImplementedError(
                    "EMA microstructure is implemented for binaries only; "
                    "use mixing_model='solid_solution' for ternaries")
            a, b = syms
            # each phase keeps its own resistivity, scaled by the same
            # size-effect factor the composite as a whole suffers
            scale = rho / self.bulk_resistivity_uohm_cm
            disp = BruggemanEMA(
                metal(a).dispersion(metal(a).resistivity_bulk_uohm_cm * scale),
                metal(b).dispersion(metal(b).resistivity_bulk_uohm_cm * scale),
                self.composition[a], f"{self.label} (Bruggeman)")
        self._cache[key] = disp
        return disp

    def alternative(self) -> "Alloy":
        """The same composition under the other microstructure hypothesis."""
        other = "ema" if self.mixing_model == "solid_solution" else "solid_solution"
        return Alloy(dict(self.composition), other, self.label, self.provenance,
                     self.note)

    def as_quantity(self) -> Quantity:
        return Quantity(self.label, "", self.provenance,
                        source=f"alloy composition ({self.mixing_model})",
                        note=self.note)


def format_composition(composition: dict) -> str:
    """Ag0.70Cu0.30 -> 'Ag70Cu30'."""
    parts = []
    for sym in sorted(composition, key=lambda s: -composition[s]):
        pct = composition[sym] * 100.0
        if pct >= 99.95:
            return sym
        if abs(pct - round(pct)) < 0.05:
            parts.append(f"{sym}{round(pct):d}")
        else:
            parts.append(f"{sym}{pct:.1f}")
    return "".join(parts)


def ag_cu(ag_atomic_fraction: float, mixing_model: str = "solid_solution",
          **kwargs) -> Alloy:
    """AgxCu(1-x) with x as an atomic fraction."""
    x = float(np.clip(ag_atomic_fraction, 0.0, 1.0))
    return Alloy({"Ag": x, "Cu": 1.0 - x}, mixing_model, **kwargs)


def ag_cu_ternary(ag: float, cu: float, third: str, amount: float,
                  mixing_model: str = "solid_solution") -> Alloy:
    """Ag-Cu-M with a dilute third element, per the brief's section 13.

    Marked HYPOTHESIS: no calculated or measured properties exist for these
    compositions, which is exactly the brief's own caution. The framework
    will refuse to put them in a headline results table without an explicit
    opt-in.
    """
    return Alloy({"Ag": ag, "Cu": cu, third: amount}, mixing_model,
                 provenance=Provenance.HYPOTHESIS,
                 note=f"dilute {third} stabiliser: hypothesis, requires DFT "
                      "(mixing energy, interface energy) and experiment")


def discriminating_wavelengths(alloy: Alloy, wavelength_nm,
                              threshold: float = 0.05) -> dict:
    """Where the two microstructure hypotheses disagree most.

    Returns the wavelength of maximum relative disagreement in n and in k
    between the solid-solution and EMA models, plus the size of the gap.
    Use it to choose the spectral window for the experiment that decides
    which microstructure the sputtered film actually has.
    """
    lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
    ss = Alloy(dict(alloy.composition), "solid_solution")
    ema = Alloy(dict(alloy.composition), "ema")
    nk_ss = np.atleast_1d(ss.dispersion()(lam))
    nk_ema = np.atleast_1d(ema.dispersion()(lam))
    scale_n = np.maximum(np.abs(nk_ss.real), 1e-6)
    scale_k = np.maximum(np.abs(nk_ss.imag), 1e-6)
    dn = np.abs(nk_ss.real - nk_ema.real) / scale_n
    dk = np.abs(nk_ss.imag - nk_ema.imag) / scale_k
    i_n, i_k = int(np.argmax(dn)), int(np.argmax(dk))
    return {
        "n_max_wavelength_nm": float(lam[i_n]),
        "n_relative_gap": float(dn[i_n]),
        "k_max_wavelength_nm": float(lam[i_k]),
        "k_relative_gap": float(dk[i_k]),
        "distinguishable": bool(max(dn.max(), dk.max()) > threshold),
        "threshold": threshold,
    }


__all__ = [
    "NORDHEIM_COEFFICIENT", "nordheim_resistivity", "alloy_mean_free_path",
    "AlloyDispersion", "Alloy", "format_composition", "ag_cu", "ag_cu_ternary",
    "discriminating_wavelengths",
]
