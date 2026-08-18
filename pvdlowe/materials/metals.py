"""Elemental metals: optical dispersion plus the transport data needed to
predict a thin-film sheet resistance.

Optical parameters follow the Lorentz-Drude parameterisation of

    A. D. Rakic, A. B. Djurisic, J. M. Elazar and M. L. Majewski,
    "Optical properties of metallic films for vertical-cavity
    optoelectronic devices", Applied Optics 37, 5271-5283 (1998).

They are transcribed here and carry provenance LITERATURE_UNVERIFIED until
someone checks them against the paper -- run
``python -m pvdlowe.cli validate-optics`` to see how the model compares with
the reference values it should reproduce.

Where the model is good and where it is not, for this project specifically:

* Far infrared (5-50 um), the band that sets emissivity: the free-electron
  term dominates and the model is reliable. This is the headline metric.
* Visible (380-780 nm): interband transitions matter, and the LD form is
  only a few-percent fit. Ag is decent; Cu sits right on its 2.1 eV
  interband edge and is the weakest case. Use measured n,k before quoting
  T_vis to two decimal places.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import drude_damping_from_resistivity_ev
from ..provenance import Provenance, Quantity
from .dispersion import LorentzDrude

_RAKIC = "Rakic et al., Appl. Opt. 37, 5271 (1998), Lorentz-Drude fit"


@dataclass(frozen=True)
class MetalData:
    """Everything the framework needs to know about an elemental metal."""

    symbol: str
    name: str
    # --- optical (Lorentz-Drude, energies in eV) ---
    plasma_energy_ev: float
    f0: float
    gamma0_ev: float
    oscillators: tuple
    # --- transport ---
    resistivity_bulk_uohm_cm: float      # 20 C
    mean_free_path_nm: float             # electron mfp at 300 K
    # --- physical / economic ---
    density_g_cm3: float
    melting_point_c: float
    molar_mass_g_mol: float
    citation_optical: str = _RAKIC
    citation_transport: str = "CRC Handbook of Chemistry and Physics, 97th ed."

    @property
    def free_electron_plasma_energy_ev(self) -> float:
        """sqrt(f0) * wp, the amplitude of the free-electron term alone."""
        return float(self.f0 ** 0.5 * self.plasma_energy_ev)

    def drude_damping_ev(self, resistivity_uohm_cm: float | None = None) -> float:
        """Free-electron damping consistent with a DC resistivity."""
        rho = (self.resistivity_bulk_uohm_cm if resistivity_uohm_cm is None
               else float(resistivity_uohm_cm))
        return drude_damping_from_resistivity_ev(
            self.free_electron_plasma_energy_ev, rho)

    def dispersion(self, resistivity_uohm_cm: float | None = None,
                   damping_mode: str = "resistivity",
                   damping_scale: float = 1.0) -> LorentzDrude:
        """Lorentz-Drude dispersion for this metal.

        Parameters
        ----------
        resistivity_uohm_cm :
            DC resistivity of the actual film. Supplied by the thin-film
            transport model, so a layer thin enough to be resistive is also
            a layer with broadened Drude damping and degraded infrared
            reflectance. Defaults to the bulk value.
        damping_mode :
            ``"resistivity"`` (default) derives Gamma_0 from the resistivity,
            which is right for the infrared and is the mode the Low-E metrics
            depend on. ``"rakic"`` keeps the published fitted damping, which
            reproduces published visible n,k more closely. The two differ by
            roughly 3x for silver -- see
            :func:`~pvdlowe.constants.drude_damping_from_resistivity_ev`.
        """
        if damping_mode == "resistivity":
            gamma = self.drude_damping_ev(resistivity_uohm_cm)
        elif damping_mode == "rakic":
            gamma = self.gamma0_ev
            if resistivity_uohm_cm is not None:
                gamma *= float(resistivity_uohm_cm) / self.resistivity_bulk_uohm_cm
        else:
            raise ValueError("damping_mode must be 'resistivity' or 'rakic'")
        ld = LorentzDrude(
            self.plasma_energy_ev, self.f0, gamma * float(damping_scale),
            self.oscillators, 1.0, f"{self.symbol} (Lorentz-Drude)",
            Provenance.LITERATURE_UNVERIFIED,
        )
        return ld

    def resistivity_quantity(self) -> Quantity:
        return Quantity(self.resistivity_bulk_uohm_cm, "uohm.cm",
                        Provenance.LITERATURE, f"{self.symbol} bulk resistivity",
                        self.citation_transport)

    def areal_mass(self, thickness_nm: float) -> float:
        """Mass of metal per square metre of coating, in g/m^2."""
        return self.density_g_cm3 * thickness_nm * 1e-7 * 1e4


# --- the metals the brief puts on the table ------------------------------
# Oscillator tuples are (f_j, Gamma_j [eV], E_j [eV]).

SILVER = MetalData(
    symbol="Ag", name="Silver",
    plasma_energy_ev=9.01, f0=0.845, gamma0_ev=0.048,
    oscillators=(
        (0.065, 3.886, 0.816),
        (0.124, 0.452, 4.481),
        (0.011, 0.065, 8.185),
        (0.840, 0.916, 9.083),
        (5.646, 2.419, 20.29),
    ),
    resistivity_bulk_uohm_cm=1.587, mean_free_path_nm=53.0,
    density_g_cm3=10.49, melting_point_c=961.8, molar_mass_g_mol=107.868,
)

COPPER = MetalData(
    symbol="Cu", name="Copper",
    plasma_energy_ev=10.83, f0=0.575, gamma0_ev=0.030,
    oscillators=(
        (0.061, 0.378, 0.291),
        (0.104, 1.056, 2.957),
        (0.723, 3.213, 5.300),
        (0.638, 4.305, 11.18),
    ),
    resistivity_bulk_uohm_cm=1.678, mean_free_path_nm=39.0,
    density_g_cm3=8.96, melting_point_c=1084.6, molar_mass_g_mol=63.546,
)

ALUMINIUM = MetalData(
    symbol="Al", name="Aluminium",
    plasma_energy_ev=14.98, f0=0.523, gamma0_ev=0.047,
    oscillators=(
        (0.227, 0.333, 0.162),
        (0.050, 0.312, 1.544),
        (0.166, 1.351, 1.808),
        (0.030, 3.382, 3.473),
    ),
    resistivity_bulk_uohm_cm=2.65, mean_free_path_nm=19.0,
    density_g_cm3=2.70, melting_point_c=660.3, molar_mass_g_mol=26.982,
)

GOLD = MetalData(
    symbol="Au", name="Gold",
    plasma_energy_ev=9.03, f0=0.760, gamma0_ev=0.053,
    oscillators=(
        (0.024, 0.241, 0.415),
        (0.010, 0.345, 0.830),
        (0.071, 0.870, 2.969),
        (0.601, 2.494, 4.304),
        (4.384, 2.214, 13.32),
    ),
    resistivity_bulk_uohm_cm=2.44, mean_free_path_nm=38.0,
    density_g_cm3=19.30, melting_point_c=1064.2, molar_mass_g_mol=196.967,
)

TITANIUM = MetalData(
    symbol="Ti", name="Titanium",
    plasma_energy_ev=7.29, f0=0.148, gamma0_ev=0.082,
    oscillators=(
        (0.899, 2.276, 0.777),
        (0.393, 2.518, 1.545),
        (0.187, 1.663, 2.509),
        (0.001, 1.762, 19.43),
    ),
    resistivity_bulk_uohm_cm=42.0, mean_free_path_nm=4.0,
    density_g_cm3=4.51, melting_point_c=1668.0, molar_mass_g_mol=47.867,
)

NICKEL = MetalData(
    symbol="Ni", name="Nickel",
    plasma_energy_ev=15.92, f0=0.096, gamma0_ev=0.048,
    oscillators=(
        (0.100, 4.511, 0.174),
        (0.135, 1.334, 0.582),
        (0.106, 2.178, 1.597),
        (0.729, 6.292, 6.089),
    ),
    resistivity_bulk_uohm_cm=6.99, mean_free_path_nm=5.0,
    density_g_cm3=8.91, melting_point_c=1455.0, molar_mass_g_mol=58.693,
)

CHROMIUM = MetalData(
    symbol="Cr", name="Chromium",
    plasma_energy_ev=10.75, f0=0.168, gamma0_ev=0.047,
    oscillators=(
        (0.151, 3.175, 0.121),
        (0.150, 1.305, 0.543),
        (1.149, 2.676, 1.970),
        (0.825, 1.335, 8.775),
    ),
    resistivity_bulk_uohm_cm=12.5, mean_free_path_nm=3.0,
    density_g_cm3=7.19, melting_point_c=1907.0, molar_mass_g_mol=51.996,
)

ZINC = MetalData(
    symbol="Zn", name="Zinc",
    plasma_energy_ev=9.60, f0=0.500, gamma0_ev=0.100,
    oscillators=((0.30, 1.50, 1.00), (0.60, 3.00, 5.00)),
    resistivity_bulk_uohm_cm=5.90, mean_free_path_nm=15.0,
    density_g_cm3=7.14, melting_point_c=419.5, molar_mass_g_mol=65.38,
    citation_optical="approximate Drude-Lorentz form; NOT from Rakic -- replace before use",
)

METALS: dict[str, MetalData] = {
    m.symbol: m for m in (SILVER, COPPER, ALUMINIUM, GOLD, TITANIUM,
                          NICKEL, CHROMIUM, ZINC)
}

#: Metals whose optical parameters come straight from Rakic et al.
RAKIC_VERIFIED = frozenset({"Ag", "Cu", "Al", "Au", "Ti", "Ni", "Cr"})


def metal(symbol: str) -> MetalData:
    try:
        return METALS[symbol]
    except KeyError:
        raise KeyError(
            f"unknown metal {symbol!r}; available: {sorted(METALS)}") from None


__all__ = ["MetalData", "METALS", "RAKIC_VERIFIED", "metal", "SILVER",
           "COPPER", "ALUMINIUM", "GOLD", "TITANIUM", "NICKEL", "CHROMIUM",
           "ZINC"]
