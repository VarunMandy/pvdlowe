"""Deposition rate and the brief's section 15 efficiency figure of merit.

The brief makes a good point in its section 15: maximising deposition rate is
the wrong objective, because rate is bought with power, and power buys
defects, roughness and target heating along with throughput. It proposes

    deposition efficiency = performance / deposition energy

which is the right shape. This module makes it computable.

**On the rate model.** Deposition rate in a magnetron scales roughly as

    R  ~  Y(E) * P / (d^2 * p^a)

sputter yield times power, divided by throw distance squared and a weak
pressure term from gas-phase scattering. The constants in that expression
depend on the magnetron geometry, the magnet strength, the target erosion
state and the gas flow pattern. None of them is predictable from first
principles to better than a factor of two.

So :class:`SputterModel` ships with *scaling laws and no absolute
calibration*, and :meth:`SputterModel.calibrate` fits the one free constant
to a single measured rate. Before calibration it will give you ratios --
"Cu deposits about 1.3x faster than Ag at the same power" -- and refuses to
give absolute nm/min. That refusal is deliberate. An uncalibrated absolute
deposition rate looks authoritative and is worthless.

Sputter yields are for Ar+ at normal incidence and are LITERATURE grade with
scatter of tens of per cent between sources; they set the *ratios*, so a
systematic error mostly cancels in the efficiency comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..provenance import Provenance, Quantity

#: Sputter yield in atoms per incident Ar+ ion, at 500 eV, normal incidence.
#: LITERATURE grade; sources disagree by 10-30%. Used for ratios.
SPUTTER_YIELD_500EV = {
    "Ag": 3.12, "Cu": 2.35, "Au": 2.43, "Al": 1.05, "Ti": 0.51,
    "Ni": 1.45, "Cr": 1.30, "Zn": 4.20, "Sn": 1.40,
}

#: Molar mass, g/mol -- needed to convert atom flux to thickness.
MOLAR_MASS = {"Ag": 107.87, "Cu": 63.55, "Au": 196.97, "Al": 26.98,
              "Ti": 47.87, "Ni": 58.69, "Cr": 52.00, "Zn": 65.38,
              "Sn": 118.71, "ZnO": 81.38, "AZO": 81.0}

#: Bulk density, g/cm^3.
DENSITY = {"Ag": 10.49, "Cu": 8.96, "Au": 19.30, "Al": 2.70, "Ti": 4.51,
           "Ni": 8.91, "Cr": 7.19, "Zn": 7.14, "Sn": 7.31,
           "ZnO": 5.61, "AZO": 5.60}

AVOGADRO = 6.02214076e23


@dataclass
class SputterModel:
    """Semi-empirical deposition-rate model for one target material.

    Parameters
    ----------
    material : element symbol, or 'AZO'/'ZnO' for the oxide targets
    rate_constant : the one lumped calibration constant, in
        nm/min per (W / mm^2 / mTorr^-a). None means uncalibrated, and
        absolute rates will raise rather than return a fabricated number.
    pressure_exponent : a in the p^-a scattering term. Around 0.3-0.5 for a
        typical throw distance; higher at long throw or high pressure.
    reference_distance_mm : distance at which rate_constant was measured.
    """

    material: str
    rate_constant: float | None = None
    pressure_exponent: float = 0.4
    reference_distance_mm: float = 80.0
    reference_pressure_mtorr: float = 5.0
    calibration_note: str = ""

    @property
    def yield_500ev(self) -> float:
        if self.material in SPUTTER_YIELD_500EV:
            return SPUTTER_YIELD_500EV[self.material]
        if self.material in ("AZO", "ZnO"):
            # oxide targets sputter far more slowly than the metal; this is a
            # lumped effective value, not a real yield
            return 0.35
        raise KeyError(f"no sputter yield for {self.material!r}")

    @property
    def is_calibrated(self) -> bool:
        return self.rate_constant is not None

    def relative_rate(self, power_w: float, area_cm2: float = 20.0,
                      pressure_mtorr: float = 5.0,
                      distance_mm: float = 80.0) -> float:
        """Dimensionless rate factor. Always available, calibrated or not."""
        power_density = power_w / max(area_cm2, 1e-6)
        volume_per_atom = (MOLAR_MASS[self.material]
                           / (DENSITY[self.material] * AVOGADRO))
        geometry = (self.reference_distance_mm / max(distance_mm, 1.0)) ** 2
        scatter = (self.reference_pressure_mtorr
                   / max(pressure_mtorr, 0.1)) ** self.pressure_exponent
        return float(self.yield_500ev * power_density * volume_per_atom * 1e21
                     * geometry * scatter)

    def rate_nm_per_min(self, power_w: float, **kwargs) -> float:
        """Absolute deposition rate. Requires calibration."""
        if not self.is_calibrated:
            raise RuntimeError(
                f"{self.material} deposition rate is not calibrated. Measure "
                "one thickness at one power on your own tool and call "
                ".calibrate(...). An uncalibrated absolute rate would be a "
                "fabricated number.")
        return float(self.rate_constant * self.relative_rate(power_w, **kwargs))

    def calibrate(self, measured_rate_nm_per_min: float, power_w: float,
                  note: str = "", **kwargs) -> "SputterModel":
        """Fit the lumped constant to one measured rate."""
        ref = self.relative_rate(power_w, **kwargs)
        if ref <= 0:
            raise ValueError("reference rate factor is zero")
        return SputterModel(
            self.material, float(measured_rate_nm_per_min / ref),
            self.pressure_exponent, kwargs.get("distance_mm",
                                               self.reference_distance_mm),
            kwargs.get("pressure_mtorr", self.reference_pressure_mtorr),
            note or f"calibrated to {measured_rate_nm_per_min:g} nm/min "
                    f"at {power_w:g} W")

    def energy_per_area(self, thickness_nm: float, power_w: float,
                        substrate_area_cm2: float = 100.0, **kwargs) -> float:
        """Deposition energy in J per m^2 of coated substrate.

        This is the denominator of the brief's efficiency FOM. It captures
        the real trade: doubling power roughly doubles rate, so energy per
        unit deposited is roughly flat — but only until the extra ion
        bombardment starts costing film quality, which is what the DoE is
        for.
        """
        rate = self.rate_nm_per_min(power_w, **kwargs)
        minutes = float(thickness_nm) / max(rate, 1e-9)
        joules = power_w * minutes * 60.0
        return float(joules / (substrate_area_cm2 * 1e-4))


def deposition_efficiency(performance_score: float, energy_j_per_m2: float,
                          reference_energy_j_per_m2: float = 1e5) -> Quantity:
    """The brief's section 15 figure of merit, normalised.

        efficiency = performance / (energy / reference_energy)

    Normalising by a reference energy keeps the result near 1 for a typical
    process, so it can sit in the same 0-1 desirability scale as the other
    criteria instead of dominating them by sheer magnitude.
    """
    if energy_j_per_m2 <= 0:
        return Quantity(0.0, "", Provenance.MODEL, "deposition efficiency")
    value = performance_score / (energy_j_per_m2 / reference_energy_j_per_m2)
    return Quantity(
        float(value), "", Provenance.MODEL,
        source="brief section 15 deposition-efficiency FOM",
        note=f"normalised to {reference_energy_j_per_m2:g} J/m2; "
             "requires a calibrated rate model")


def stack_deposition_time(coating, models: dict,
                          powers: dict | None = None,
                          substrate_area_cm2: float = 100.0) -> pd.DataFrame:
    """Layer-by-layer deposition time and energy for a full stack.

    Usually a surprise the first time: the two AZO layers dominate both time
    and energy, because they are three to four times thicker than the metal
    and sputter far more slowly. Any throughput argument that focuses on the
    silver layer is looking at the wrong layer.
    """
    powers = powers or {}
    rows = []
    layers = [
        ("bottom TCO", coating.bottom_tco.key.split("_")[0],
         coating.bottom_thickness_nm),
        ("metal", coating.metal_alloy.symbols[0], coating.metal_thickness_nm),
        ("top TCO", coating.top_tco.key.split("_")[0], coating.top_thickness_nm),
    ]
    for label, material, thickness in layers:
        key = "AZO" if material in ("AZO", "GZO", "ZnO") else material
        model = models.get(key)
        if model is None or not model.is_calibrated:
            rows.append({"layer": label, "material": material,
                         "thickness_nm": thickness, "power_w": None,
                         "time_min": None, "energy_J_per_m2": None,
                         "status": "uncalibrated"})
            continue
        power = powers.get(key, 150.0)
        rate = model.rate_nm_per_min(power)
        minutes = thickness / max(rate, 1e-9)
        energy = model.energy_per_area(thickness, power,
                                       substrate_area_cm2)
        rows.append({"layer": label, "material": material,
                     "thickness_nm": thickness, "power_w": power,
                     "rate_nm_per_min": round(rate, 2),
                     "time_min": round(minutes, 2),
                     "energy_J_per_m2": round(energy, 1), "status": "ok"})
    return pd.DataFrame(rows)


def rate_ratios(materials=("Ag", "Cu", "Al", "Ti", "AZO"), **kwargs) -> pd.DataFrame:
    """Relative deposition rates at equal power — available without calibration.

    The useful uncalibrated output. Tells you how process time reallocates
    when you change the metal, which is what matters for a throughput
    comparison between candidates.
    """
    rows = []
    ref = SputterModel("Ag").relative_rate(150.0, **kwargs)
    for m in materials:
        try:
            r = SputterModel(m).relative_rate(150.0, **kwargs)
        except KeyError:
            continue
        rows.append({"material": m,
                     "sputter_yield_500eV": SPUTTER_YIELD_500EV.get(m),
                     "relative_rate_vs_Ag": round(r / ref, 3)})
    df = pd.DataFrame(rows)
    df.attrs["note"] = ("ratios only; absolute rates require calibration "
                        "against a measured thickness on your own tool")
    return df


def quality_penalty(power_density_w_cm2: float, pressure_mtorr: float,
                    threshold_w_cm2: float = 10.0) -> dict:
    """Qualitative flag for process conditions that risk film quality.

    Not a quantitative model — there isn't one that transfers between tools.
    It encodes the brief's section 15 concern as a checklist so a DoE point
    that will produce a bad film gets flagged before it is run rather than
    after.
    """
    flags = []
    if power_density_w_cm2 > threshold_w_cm2:
        flags.append("high power density: target heating, possible arcing, "
                     "and energetic bombardment that roughens the growing film")
    if pressure_mtorr < 2.0:
        flags.append("low pressure: energetic neutral reflection from the "
                     "target can damage the film and raise compressive stress")
    if pressure_mtorr > 12.0:
        flags.append("high pressure: gas-phase thermalisation gives porous, "
                     "columnar, low-density films with poor conductivity")
    if power_density_w_cm2 < 1.0:
        flags.append("very low power density: long deposition, higher "
                     "contamination incorporation from residual gas")
    return {"acceptable": not flags, "flags": flags,
            "note": "heuristic checklist, not a validated model"}


__all__ = ["SPUTTER_YIELD_500EV", "MOLAR_MASS", "DENSITY", "SputterModel",
           "deposition_efficiency", "stack_deposition_time", "rate_ratios",
           "quality_penalty"]
