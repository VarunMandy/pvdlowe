"""Transparent conductive oxides: AZO, GZO, ITO, FTO and undoped ZnO.

Each TCO is described by three physical numbers -- carrier density N,
mobility mu, effective mass m* -- from which the model derives, consistently:

* the infrared plasma response (and so the TCO's own contribution to
  emissivity and to near-IR reflection),
* the Burstein-Moss widening of the optical gap with doping, which is the
  effect the brief cites from the AZO first-principles literature,
* the DC resistivity, rho = 1/(N e mu), and hence the layer's sheet
  resistance in parallel with the metal.

That is the point of parameterising it this way. A TCO fitted to one Hall
measurement is then automatically consistent everywhere it appears, and an
inconsistent literature entry -- an optical gap that does not match the
quoted carrier density, say -- shows up as a contradiction instead of
sitting quietly in a table.

The Al content itself does not enter as a variable. What Al doping *does*
is set N (each substitutional Al on a Zn site is a donor) and, above a few
per cent, degrade mu through ionised-impurity and neutral-defect
scattering. :func:`azo_from_al_content` makes that dependence explicit and
is the function to re-fit once you have a doping series of your own.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize

from ..constants import E_CHARGE, HC_EV_NM
from ..provenance import Provenance, Quantity
from .dispersion import Dispersion, DrudeSemiconductor


@dataclass
class _WithPhonons(Dispersion):
    """A dispersion plus far-infrared lattice absorption.

    Splitting this out rather than baking phonons into DrudeSemiconductor
    keeps the conductive oxides unchanged and makes the addition auditable:
    set `far_ir_phonons=()` on a preset and you get exactly the old model
    back, so the effect of the phonons on any result can be measured.
    """

    base: Dispersion
    phonons: tuple
    label: str = "dielectric+phonons"
    provenance: Provenance = Provenance.ESTIMATE

    def epsilon(self, wavelength_nm) -> np.ndarray:
        from ..constants import HC_EV_NM
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        eps = np.atleast_1d(self.base.epsilon(lam)).astype(complex)
        e = HC_EV_NM / lam
        for amp, width, centre in self.phonons:
            eps = eps + amp / (centre ** 2 - e ** 2 - 1j * e * width)
        return eps


@dataclass(frozen=True)
class TCOPreset:
    """A named TCO parameter set."""

    key: str
    name: str
    carrier_density_cm3: float
    mobility_cm2_vs: float
    effective_mass: float
    eps_inf: float
    gap_ev: float
    n_visible: float                 # refractive index at 550 nm, for calibration
    density_g_cm3: float
    provenance: Provenance = Provenance.LITERATURE_UNVERIFIED
    citation: str = ""
    note: str = ""
    #: Far-infrared phonon oscillators as (amplitude [eV^2], width [eV],
    #: centre [eV]). Matters for the nitride and titania dielectrics, whose
    #: lattice absorption sits inside the thermal band and therefore raises
    #: the emissivity of a stack built on them. AZO's phonons are weaker and
    #: further out, which is why the conductive oxides can ignore them.
    far_ir_phonons: tuple = ()

    @property
    def resistivity_ohm_cm(self) -> float:
        return 1.0 / (self.carrier_density_cm3 * E_CHARGE * self.mobility_cm2_vs)

    def sheet_resistance(self, thickness_nm: float) -> float:
        """R_s of a standalone layer, ohm/sq."""
        d_cm = float(thickness_nm) * 1e-7
        return float(self.resistivity_ohm_cm / d_cm) if d_cm > 0 else np.inf

    def dispersion(self, mobility_cm2_vs: float | None = None,
                   carrier_density_cm3: float | None = None) -> DrudeSemiconductor:
        """Build the dispersion, optionally overriding N or mu.

        The band-edge oscillator strength is calibrated so the model
        reproduces `n_visible` at 550 nm, which anchors the visible index to
        a measurable quantity rather than leaving it to an arbitrary
        oscillator amplitude.
        """
        n_carrier = self.carrier_density_cm3 if carrier_density_cm3 is None \
            else carrier_density_cm3
        mob = self.mobility_cm2_vs if mobility_cm2_vs is None else mobility_cm2_vs
        strength = calibrate_edge_strength(
            eps_inf=self.eps_inf, gap_ev=self.gap_ev,
            carrier_density_cm3=n_carrier, mobility_cm2_vs=mob,
            effective_mass=self.effective_mass, n_target=self.n_visible)
        base = DrudeSemiconductor(
            carrier_density_cm3=n_carrier, mobility_cm2_vs=mob,
            effective_mass=self.effective_mass, eps_inf=self.eps_inf,
            gap_ev=self.gap_ev, edge_strength=strength,
            name=self.name, provenance=Provenance.CALIBRATED)
        if not self.far_ir_phonons:
            return base
        return _WithPhonons(base, tuple(self.far_ir_phonons), self.name)

    def as_quantities(self) -> dict:
        return {
            "carrier_density": Quantity(self.carrier_density_cm3, "cm^-3",
                                        self.provenance, self.name, self.citation),
            "mobility": Quantity(self.mobility_cm2_vs, "cm^2/Vs",
                                 self.provenance, self.name, self.citation),
            "resistivity": Quantity(self.resistivity_ohm_cm, "ohm.cm",
                                    self.provenance, self.name, self.citation),
        }


def calibrate_edge_strength(eps_inf: float, gap_ev: float,
                            carrier_density_cm3: float, mobility_cm2_vs: float,
                            effective_mass: float, n_target: float,
                            wavelength_nm: float = 550.0) -> float:
    """Solve for the band-edge oscillator amplitude that gives n(550 nm) = n_target.

    Keeps the visible index tied to something you can measure with an
    ellipsometer instead of to a free parameter.
    """
    def residual(strength):
        d = DrudeSemiconductor(
            carrier_density_cm3=carrier_density_cm3,
            mobility_cm2_vs=mobility_cm2_vs, effective_mass=effective_mass,
            eps_inf=eps_inf, gap_ev=gap_ev, edge_strength=float(strength))
        return float(np.atleast_1d(d(wavelength_nm)).real[0]) - n_target

    try:
        return float(optimize.brentq(residual, 0.0, 20.0, xtol=1e-8))
    except ValueError:
        # target index unreachable with this eps_inf/gap: fall back, flagged
        return 0.75


# --- presets -------------------------------------------------------------

ZNO = TCOPreset(
    key="ZnO", name="ZnO (undoped)",
    carrier_density_cm3=1e17, mobility_cm2_vs=30.0, effective_mass=0.28,
    eps_inf=2.50, gap_ev=3.37, n_visible=1.95, density_g_cm3=5.61,
    provenance=Provenance.LITERATURE,
    citation="ZnO wurtzite reference; MP entry mp-2133",
    note="reference material, not a usable TCO on its own")

AZO_BRIEF = TCOPreset(
    key="AZO_brief", name="AZO (matched to brief section 2)",
    carrier_density_cm3=2.0e20, mobility_cm2_vs=12.0, effective_mass=0.28,
    eps_inf=2.50, gap_ev=3.37, n_visible=1.93, density_g_cm3=5.60,
    provenance=Provenance.LITERATURE_UNVERIFIED,
    citation="brief section 2: rho = 2.6e-3 ohm.cm, 68 ohm/sq, T_vis 82.4%",
    note="N and mu chosen to reproduce the quoted resistivity; the "
         "N/mu split is NOT from the source and needs a Hall measurement. "
         "Note also that 2.6e-3 ohm.cm at 68 ohm/sq implies a ~380 nm film, "
         "far thicker than the 30-40 nm layers used in the multilayer.")

AZO_TYPICAL = TCOPreset(
    key="AZO", name="AZO (good sputtered film)",
    carrier_density_cm3=5.0e20, mobility_cm2_vs=25.0, effective_mass=0.28,
    eps_inf=2.50, gap_ev=3.37, n_visible=1.90, density_g_cm3=5.60,
    provenance=Provenance.ESTIMATE,
    citation="representative magnetron-sputtered AZO",
    note="starting point for the DoE; refit to your own films")

GZO = TCOPreset(
    key="GZO", name="GZO (Ga-doped ZnO)",
    carrier_density_cm3=6.0e20, mobility_cm2_vs=22.0, effective_mass=0.28,
    eps_inf=2.50, gap_ev=3.37, n_visible=1.92, density_g_cm3=5.65,
    provenance=Provenance.ESTIMATE,
    citation="brief section 11; Ga solubility higher than Al but Ga is costlier")

ITO = TCOPreset(
    key="ITO", name="ITO (Sn-doped In2O3)",
    carrier_density_cm3=1.0e21, mobility_cm2_vs=35.0, effective_mass=0.35,
    eps_inf=3.20, gap_ev=3.75, n_visible=1.85, density_g_cm3=7.14,
    provenance=Provenance.ESTIMATE,
    citation="performance benchmark only; In supply risk rules it out per brief")

FTO = TCOPreset(
    key="FTO", name="FTO (F-doped SnO2)",
    carrier_density_cm3=4.0e20, mobility_cm2_vs=25.0, effective_mass=0.30,
    eps_inf=3.20, gap_ev=3.60, n_visible=1.90, density_g_cm3=6.95,
    provenance=Provenance.ESTIMATE,
    citation="brief section 5; pyrolytic FTO is the incumbent hard-coat route")

# --- passive high-index dielectrics --------------------------------------
#
# These are not transparent conductive oxides: they carry essentially no free
# carriers and contribute nothing to sheet resistance. They are included
# because the antireflection job around a metal layer is an index-matching
# problem, and a higher index does it better. Industrial Low-E stacks are
# built on exactly these two rather than on AZO.
#
# Modelled with a nominal carrier density of 1e16 cm^-3, which puts the
# plasma wavelength far outside the thermal band and makes them optically
# passive in the infrared -- as they should be. Their far-infrared phonon
# absorption is NOT modelled; at 40 nm against a 10 um wavelength that is a
# defensible omission, but it means these presets should not be used to model
# a thick dielectric stack.

TIO2 = TCOPreset(
    key="TiO2", name="TiO2 (sputtered, anatase-like)",
    carrier_density_cm3=1e16, mobility_cm2_vs=1.0, effective_mass=1.0,
    eps_inf=5.0, gap_ev=3.20, n_visible=2.45, density_g_cm3=4.00,
    # Anatase-like TO phonons near 262, 435 and 690 cm^-1 (0.0325, 0.0539,
    # 0.0855 eV). Titania's lattice absorption is strong -- static
    # permittivity is tens -- and sits squarely in the thermal band, which
    # is the hidden cost of choosing it for a Low-E dielectric.
    far_ir_phonons=((0.0180, 0.0035, 0.0325),
                    (0.0090, 0.0040, 0.0539),
                    (0.0060, 0.0050, 0.0855)),
    provenance=Provenance.ESTIMATE,
    citation="n(550 nm) ~ 2.4-2.6 depending on phase and density; "
             "phonon parameters are order-of-magnitude estimates",
    note="highest practical index for a sputtered Low-E dielectric; the "
         "standard industrial choice for the layer adjacent to silver")

SI3N4 = TCOPreset(
    key="Si3N4", name="Si3N4 (sputtered)",
    carrier_density_cm3=1e16, mobility_cm2_vs=1.0, effective_mass=1.0,
    eps_inf=4.0, gap_ev=5.00, n_visible=2.02, density_g_cm3=3.17,
    # The Si-N asymmetric stretch near 855 cm^-1 is 0.106 eV, i.e. 11.7 um --
    # inside the 283 K thermal band, so it raises stack emissivity. Amplitude
    # set so the static permittivity reaches about 7.5 against an optical 4.0,
    # which is the accepted split for amorphous silicon nitride.
    far_ir_phonons=((0.0390, 0.0130, 0.1060),
                    (0.0050, 0.0090, 0.0590)),
    provenance=Provenance.ESTIMATE,
    citation="n(550 nm) ~ 2.0 for reactively sputtered silicon nitride; "
             "phonon parameters estimated from the Si-N stretch position",
    note="the industry barrier/dielectric of choice: dense, an excellent "
         "diffusion barrier, and durable enough to survive tempering")

SNO2 = TCOPreset(
    key="SnO2", name="SnO2 (undoped)",
    carrier_density_cm3=1e18, mobility_cm2_vs=10.0, effective_mass=0.30,
    eps_inf=3.20, gap_ev=3.60, n_visible=2.00, density_g_cm3=6.95,
    provenance=Provenance.ESTIMATE,
    citation="harder and more chemically durable than ZnO")

TCOS: dict[str, TCOPreset] = {
    p.key: p for p in (ZNO, AZO_BRIEF, AZO_TYPICAL, GZO, ITO, FTO,
                       TIO2, SI3N4, SNO2)
}


def tco(key: str) -> TCOPreset:
    try:
        return TCOS[key]
    except KeyError:
        raise KeyError(f"unknown TCO {key!r}; available: {sorted(TCOS)}") from None


# --- doping relations ----------------------------------------------------

def azo_from_al_content(al_atomic_percent: float,
                        activation: float = 0.35,
                        mobility_max: float = 30.0,
                        mobility_decay_pct: float = 3.0) -> TCOPreset:
    """AZO parameters as a function of Al content.

    Two competing effects, which is why an optimum exists and why the brief
    is right that 3% Al should not simply be assumed:

    * each electrically active Al donates one electron, so N rises linearly
      with Al content times an activation fraction;
    * mobility falls as Al content rises, through ionised-impurity
      scattering and, above a few per cent, secondary-phase formation.

    The functional forms here are EMPIRICAL placeholders with plausible
    shapes. Replace `activation` and `mobility_decay_pct` with fits to your
    own Hall data before drawing conclusions about the optimum -- the
    optimum's *existence* is robust, its *location* is not.

    Parameters
    ----------
    al_atomic_percent : Al/(Al+Zn) in at.%
    activation : fraction of Al that is an electrically active donor
    mobility_max : mobility extrapolated to zero doping, cm^2/Vs
    mobility_decay_pct : Al content at which mobility falls to 1/e
    """
    x = max(float(al_atomic_percent), 0.0)
    n_zn_sites = 4.18e22          # cm^-3, Zn sites in wurtzite ZnO
    carriers = max(activation * (x / 100.0) * n_zn_sites, 1e17)
    mobility = max(mobility_max * np.exp(-x / mobility_decay_pct), 1.0)
    return TCOPreset(
        key=f"AZO_{x:g}pct", name=f"AZO ({x:g} at.% Al)",
        carrier_density_cm3=float(carriers), mobility_cm2_vs=float(mobility),
        effective_mass=0.28, eps_inf=2.50, gap_ev=3.37, n_visible=1.92,
        density_g_cm3=5.60, provenance=Provenance.MODEL,
        citation="empirical doping model; refit to measured Hall data",
        note="functional form is a placeholder, see azo_from_al_content docstring")


def optimal_al_content(bounds: tuple = (0.5, 10.0), **kwargs) -> dict:
    """Al content minimising AZO resistivity under the doping model.

    Returned with an explicit warning: the number is only as good as the
    empirical mobility decay it is built on.
    """
    def rho(x):
        return azo_from_al_content(float(x), **kwargs).resistivity_ohm_cm

    res = optimize.minimize_scalar(rho, bounds=bounds, method="bounded")
    preset = azo_from_al_content(float(res.x), **kwargs)
    return {
        "al_atomic_percent": float(res.x),
        "resistivity_ohm_cm": float(res.fun),
        "carrier_density_cm3": preset.carrier_density_cm3,
        "mobility_cm2_vs": preset.mobility_cm2_vs,
        "provenance": Provenance.MODEL,
        "warning": "location of the optimum depends entirely on the empirical "
                   "mobility-vs-doping model; treat as a hypothesis to test",
    }


def plasma_wavelength_um(preset: TCOPreset) -> float:
    """Screened plasma wavelength, where the TCO starts to reflect.

    Below about 1e20 cm^-3 this sits beyond 3 um and the TCO is optically
    passive in the near IR. Above 1e21 it moves into the solar band and
    starts costing solar transmittance -- the trade the brief describes
    when it warns against reading Low-E performance off a band gap.
    """
    d = preset.dispersion()
    return float(HC_EV_NM / (d.plasma_energy_ev / np.sqrt(preset.eps_inf)) / 1000.0)


__all__ = ["TCOPreset", "TCOS", "tco", "ZNO", "AZO_BRIEF", "AZO_TYPICAL",
           "GZO", "ITO", "FTO", "TIO2", "SI3N4", "SNO2", "calibrate_edge_strength",
           "azo_from_al_content", "optimal_al_content", "plasma_wavelength_um"]
