"""Soda-lime float glass, the substrate.

Two spectral regions with different physics and different data quality:

**Visible and near IR (0.3-2.5 um).** Transparent, normal dispersion, well
described by a Sellmeier form. The coefficients here are a two-point fit to
the accepted soda-lime indices n(550 nm) = 1.5185 and n(1000 nm) = 1.5075,
so provenance is CALIBRATED, not LITERATURE.

**Far IR (5-50 um).** Silicate glass is strongly absorbing here through the
Si-O stretching, bending and rocking modes. This is why uncoated float glass
has a normal emissivity near 0.84 and why coating it is worth doing at all.
Getting these oscillators right from first principles would need
IR-ellipsometry data this package does not ship, so instead the oscillator
set is *calibrated* to reproduce the accepted uncoated-glass emissivity.

That calibration is legitimate and it is also limited. It fixes one integral
number, so the model reproduces the emissivity of bare glass by
construction and cannot be used as independent evidence about it. What it is
good for is the thing the project actually needs: once a metal layer thicker
than about 5 nm is present, far-IR reflectance is set by the metal and the
substrate contributes almost nothing, so residual error in these oscillators
does not propagate into the coated-stack result. :func:`substrate_sensitivity`
quantifies that claim for any given stack rather than asking you to take it
on trust.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..provenance import Provenance
from .dispersion import Dispersion, LorentzOscillators, Sellmeier

#: Accepted normal emissivity of uncoated soda-lime float glass, used as the
#: calibration target for the far-IR oscillators. EN 673 uses this value for
#: uncoated glass surfaces in centre-pane U-value calculations.
UNCOATED_GLASS_EMISSIVITY = 0.837

#: Two-point Sellmeier fit, (B, C) with C in um^2.
SODA_LIME_SELLMEIER = ((1.2587, 0.010914),)

#: Far-IR oscillators as (amplitude [eV^2], width [eV], centre [eV]).
#: Centres correspond to the Si-O asymmetric stretch (~9.3 um), the Si-O
#: bend (~12.5 um) and the O-Si-O rocking mode (~21 um). Amplitudes are the
#: calibrated quantity; centres and widths are physically motivated.
SILICATE_OSCILLATORS = (
    (0.01480, 0.0290, 0.1333),    # ~9.3 um, Si-O asymmetric stretch
    (0.00340, 0.0180, 0.0992),    # ~12.5 um, Si-O bend
    (0.00210, 0.0150, 0.0590),    # ~21 um, O-Si-O rocking
)

#: Global scale on the oscillator amplitudes. Fixed by running
#: :func:`calibrate_far_ir`, which solves for the value reproducing
#: UNCOATED_GLASS_EMISSIVITY. Re-run it if the oscillator centres or widths
#: are changed. Note the sign of the effect: stronger oscillators lower the
#: emissivity, because a deeper reststrahlen band reflects more.
FAR_IR_SCALE = 1.3566


@dataclass
class FloatGlass(Dispersion):
    """Soda-lime float glass across the whole 0.3-50 um range.

    The two regimes are blended over 2.5-5 um where neither description is
    quantitative; glazing standards do not evaluate anything in that window
    (the solar band stops at 2.5 um, the emissivity band starts at 5 um), so
    the blend affects no reported metric.
    """

    iron_absorption: float = 0.0     # extra visible k, for green low-iron variants
    far_ir_scale: float = FAR_IR_SCALE
    name: str = "soda-lime float glass"
    provenance: Provenance = Provenance.CALIBRATED

    def __post_init__(self):
        self._vis = Sellmeier(SODA_LIME_SELLMEIER, "soda-lime (Sellmeier)",
                              Provenance.CALIBRATED)
        scaled = tuple((amp * self.far_ir_scale, w, e)
                       for amp, w, e in SILICATE_OSCILLATORS)
        self._ir = LorentzOscillators(2.10, scaled, "silicate phonons",
                                      Provenance.CALIBRATED)

    def epsilon(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        eps_vis = np.atleast_1d(self._vis.epsilon(lam)).astype(complex)
        if self.iron_absorption:
            eps_vis = eps_vis + 2j * np.sqrt(eps_vis.real) * self.iron_absorption
        eps_ir = np.atleast_1d(self._ir.epsilon(lam)).astype(complex)
        # smooth crossover on log wavelength between 2.5 and 5 um
        t = np.clip((np.log10(lam) - np.log10(2500.0))
                    / (np.log10(5000.0) - np.log10(2500.0)), 0.0, 1.0)
        blend = t * t * (3.0 - 2.0 * t)     # smoothstep
        return (1.0 - blend) * eps_vis + blend * eps_ir


def calibrate_far_ir(target: float = UNCOATED_GLASS_EMISSIVITY,
                     bracket: tuple = (0.05, 20.0)) -> float:
    """Find the oscillator scale reproducing the uncoated-glass emissivity.

    Imported lazily to avoid a circular import with the optics package.
    """
    from scipy import optimize

    # Local import: materials/ is below optics/ in the dependency order, so a
    # module-level import here would be a cycle. Only the calibration path needs it.
    from ..optics.integrate import normal_emissivity
    from ..optics.stack import Stack

    def residual(scale):
        glass = FloatGlass(far_ir_scale=float(scale))
        stack = Stack.bare_substrate(glass)
        return normal_emissivity(stack) - target

    lo, hi = bracket
    try:
        return float(optimize.brentq(residual, lo, hi, xtol=1e-4))
    except ValueError as exc:                      # pragma: no cover
        raise RuntimeError(
            f"could not bracket the far-IR calibration between {lo} and {hi}: "
            f"residuals {residual(lo):+.3f} and {residual(hi):+.3f}") from exc


def substrate_sensitivity(stack, scales: tuple = (0.5, 1.0, 2.0)) -> dict:
    """How much does the coated stack's emissivity depend on the glass model?

    Recomputes emissivity with the far-IR oscillator amplitudes scaled up and
    down, and reports the spread. A well-shielded stack (metal thicker than
    about 5 nm) should show a spread far below the reporting precision,
    which is the evidence that the calibrated substrate model is good enough
    for coated results.
    """
    # Local import: same cycle as above.
    from ..optics.integrate import normal_emissivity

    values = {}
    for s in scales:
        variant = stack.with_substrate(FloatGlass(far_ir_scale=float(s)))
        values[float(s)] = float(normal_emissivity(variant))
    spread = max(values.values()) - min(values.values())
    return {
        "emissivity_by_scale": values,
        "spread": float(spread),
        "negligible": bool(spread < 0.005),
        "interpretation": (
            "substrate model contributes less than 0.005 to emissivity; "
            "the calibrated glass oscillators are adequate"
            if spread < 0.005 else
            "emissivity depends measurably on the glass model -- the metal "
            "layer is not shielding the substrate, so measured glass optical "
            "constants are needed before quoting this number"),
    }


#: Ready-made instances.
FLOAT_GLASS = FloatGlass()
LOW_IRON_GLASS = FloatGlass(iron_absorption=0.0, name="low-iron float glass")

AIR = None  # placeholder; the stack module supplies a vacuum ambient


__all__ = ["FloatGlass", "FLOAT_GLASS", "LOW_IRON_GLASS",
           "UNCOATED_GLASS_EMISSIVITY", "SODA_LIME_SELLMEIER",
           "SILICATE_OSCILLATORS", "calibrate_far_ir", "substrate_sensitivity"]
