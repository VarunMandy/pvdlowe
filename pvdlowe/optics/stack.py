"""Layer stacks and the Low-E coating design object.

:class:`LowECoating` is the object the rest of the framework optimises,
scores and hands to the DoE. It holds a dielectric/metal/dielectric design
and, importantly, keeps the optical and electrical descriptions of the metal
layer tied together: the thin-film resistivity model produces a damping
multiplier which is applied to the metal's Drude term, so a layer that is too
thin to conduct well is also, automatically, a layer that reflects the far
infrared poorly.

Without that coupling you can make the emissivity as low as you like by
thinning the silver, which is exactly the wrong answer and exactly the answer
an uncoupled model gives.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from ..electrical.thinfilm import (DEFAULT_ALLOY_PERCOLATION, PERCOLATION,
                                   ThinFilmResistivity, parallel_sheet_resistance)
from ..materials.alloys import Alloy, ag_cu
from ..materials.dispersion import BruggemanEMA, ConstantIndex, Dispersion
from ..materials.glass import FLOAT_GLASS
from ..materials.metals import metal
from ..materials.tco import AZO_TYPICAL, TCOPreset
from ..provenance import Provenance, Quantity, Record
from . import tmm

AIR = ConstantIndex(1.0, 0.0, "air")


@dataclass
class Layer:
    """One finite layer."""

    material: Dispersion
    thickness_nm: float
    name: str = ""
    role: str = ""          # 'tco' | 'metal' | 'barrier' | 'protective'

    def __post_init__(self):
        if self.thickness_nm < 0:
            raise ValueError("thickness must be non-negative")
        if not self.name:
            self.name = getattr(self.material, "name", "layer")

    def index(self, wavelength_nm) -> np.ndarray:
        return np.atleast_1d(self.material(wavelength_nm))


@dataclass
class Stack:
    """Ambient / finite layers / semi-infinite substrate."""

    layers: list
    substrate: Dispersion = field(default_factory=lambda: FLOAT_GLASS)
    ambient: Dispersion = field(default_factory=lambda: AIR)
    label: str = ""

    @classmethod
    def bare_substrate(cls, substrate: Dispersion | None = None) -> "Stack":
        return cls([], substrate or FLOAT_GLASS, AIR, "uncoated substrate")

    @property
    def thicknesses(self) -> np.ndarray:
        return np.array([lyr.thickness_nm for lyr in self.layers], dtype=float)

    @property
    def total_thickness_nm(self) -> float:
        return float(sum(lyr.thickness_nm for lyr in self.layers))

    def indices(self, wavelength_nm) -> np.ndarray:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        rows = [np.atleast_1d(self.ambient(lam))]
        rows += [lyr.index(lam) for lyr in self.layers]
        rows.append(np.atleast_1d(self.substrate(lam)))
        return np.stack([np.broadcast_to(r, lam.shape) for r in rows])

    def evaluate(self, wavelength_nm, angle_deg: float = 0.0,
                 polarization: str = "both",
                 want_layer_absorption: bool = False) -> tmm.TMMResult:
        lam = np.atleast_1d(np.asarray(wavelength_nm, dtype=float))
        return tmm.solve(lam, self.indices(lam), self.thicknesses, angle_deg,
                         polarization, want_layer_absorption)

    # -- variants --------------------------------------------------------
    def with_substrate(self, substrate: Dispersion) -> "Stack":
        return Stack(list(self.layers), substrate, self.ambient, self.label)

    def with_thickness(self, layer_index: int, thickness_nm: float) -> "Stack":
        layers = list(self.layers)
        layers[layer_index] = replace(layers[layer_index],
                                      thickness_nm=float(thickness_nm))
        return Stack(layers, self.substrate, self.ambient, self.label)

    def reversed_illumination(self) -> "Stack":
        """The same coating seen from inside the glass -- needed for glazing."""
        return Stack(list(reversed(self.layers)), self.ambient, self.substrate,
                     f"{self.label} (from substrate)")

    def describe(self) -> str:
        parts = [f"air | "]
        parts += [f"{lyr.name} {lyr.thickness_nm:.1f}nm | " for lyr in self.layers]
        parts.append(getattr(self.substrate, "name", "substrate"))
        return "".join(parts)


# --- the Low-E design object --------------------------------------------

@dataclass
class LowECoating:
    """A dielectric / metal / dielectric Low-E coating on float glass.

    The architecture of the brief's section 13:

        air | (protective) | top TCO | metal | bottom TCO | float glass

    Optional thin barrier layers may be placed either side of the metal --
    the standard industrial trick for stopping oxygen reaching a silver layer
    during reactive deposition of the upper oxide, and the natural place to
    test the brief's dilute-Ti hypothesis in a form that does not require the
    Ti to be alloyed into the metal at all.
    """

    metal_alloy: Alloy = field(default_factory=lambda: ag_cu(1.0))
    metal_thickness_nm: float = 10.0
    bottom_tco: TCOPreset = AZO_TYPICAL
    bottom_thickness_nm: float = 35.0
    top_tco: TCOPreset = AZO_TYPICAL
    top_thickness_nm: float = 35.0
    barrier_metal: str | None = None
    barrier_thickness_nm: float = 0.0
    substrate: Dispersion = field(default_factory=lambda: FLOAT_GLASS)
    # thin-film transport parameters
    specularity: float = 0.5
    grain_boundary_reflection: float = 0.25
    grain_size_ratio: float = 3.0
    label: str = ""
    _cache: dict = field(default_factory=dict, repr=False)

    #: Minimum manufacturable dielectric thickness, nm. The top layer is the
    #: metal's only mechanical and chemical protection; industrial Low-E uses
    #: 25-40 nm. Without this bound an optimiser will walk the top oxide to
    #: 15 nm, which is optically defensible and would not survive handling.
    min_dielectric_nm: float = 0.0

    def manufacturability(self) -> dict:
        """Flag geometries that are optically fine and physically implausible."""
        issues = []
        floor = self.min_dielectric_nm or 25.0
        if 0 < self.top_thickness_nm < floor:
            issues.append(
                f"top dielectric {self.top_thickness_nm:.1f} nm is below the "
                f"{floor:.0f} nm needed for scratch and diffusion protection")
        if 0 < self.bottom_thickness_nm < 10.0:
            issues.append(
                f"bottom dielectric {self.bottom_thickness_nm:.1f} nm is too "
                "thin to seed the metal layer reliably")
        if not self.is_continuous:
            issues.append("metal layer is below percolation")
        return {"manufacturable": not issues, "issues": issues}

    def __post_init__(self):
        if not self.label:
            self.label = (f"{self.bottom_tco.key}/{self.metal_alloy.label}/"
                          f"{self.top_tco.key}")

    # -- electrical ------------------------------------------------------
    @property
    def transport(self) -> ThinFilmResistivity:
        perc = PERCOLATION.get(self.metal_alloy.symbols[0]) \
            if self.metal_alloy.is_pure else DEFAULT_ALLOY_PERCOLATION
        return ThinFilmResistivity(
            bulk_resistivity_uohm_cm=self.metal_alloy.bulk_resistivity_uohm_cm,
            mean_free_path_nm=self.metal_alloy.mean_free_path_nm,
            specularity=self.specularity,
            grain_boundary_reflection=self.grain_boundary_reflection,
            grain_size_ratio=self.grain_size_ratio,
            percolation=perc)

    @property
    def size_effect_ratio(self) -> float:
        """rho_film / rho_bulk from surface, grain-boundary and percolation
        scattering. Capped so a sub-percolation layer stays numerically
        finite; the `is_continuous` flag carries that information instead."""
        return float(min(self.transport.ratio(self.metal_thickness_nm), 50.0))

    @property
    def growth_factor(self) -> float:
        """Resistivity penalty from nucleation on this underlayer.

        The metal grows on the BOTTOM dielectric, so that is the one that
        matters. Taken from `TCOPreset.metal_growth_factor`, calibrated to
        measurement (see docs/CARRETERO_COMPARISON.md).
        """
        return float(getattr(self.bottom_tco, "metal_growth_factor", 1.0))

    @property
    def film_resistivity_uohm_cm(self) -> float:
        """Resistivity of the metal layer as deposited, uohm.cm.

        Three multiplicative contributions: bulk resistivity, the classical
        size effect, and a nucleation penalty set by the underlayer. The third
        was absent from the first version of this framework and its omission
        produced a wrong ranking of dielectrics.
        """
        return float(self.metal_alloy.bulk_resistivity_uohm_cm
                     * self.size_effect_ratio * self.growth_factor)

    @property
    def is_continuous(self) -> bool:
        perc = self.transport.percolation
        return True if perc is None else perc.is_continuous(self.metal_thickness_nm)

    def sheet_resistance(self) -> float:
        """Coating sheet resistance in ohm/sq, metal and TCOs in parallel."""
        metal_rs = self.transport.sheet_resistance(self.metal_thickness_nm)
        return parallel_sheet_resistance(
            metal_rs,
            self.bottom_tco.sheet_resistance(self.bottom_thickness_nm),
            self.top_tco.sheet_resistance(self.top_thickness_nm))

    def sheet_resistance_quantity(self) -> Quantity:
        return Quantity(
            self.sheet_resistance(), "ohm/sq", Provenance.MODEL,
            source=f"{self.label}, d_metal={self.metal_thickness_nm:g} nm",
            note="FS-MS size effect with fitted specularity; validate against "
                 "a four-point-probe series")

    # -- optical ---------------------------------------------------------
    def metal_dispersion(self) -> Dispersion:
        """Metal dispersion including size-effect broadening and, below
        percolation, an island-composite effective medium."""
        disp = self.metal_alloy.dispersion(self.film_resistivity_uohm_cm)
        perc = self.transport.percolation
        if perc is not None and not perc.is_continuous(self.metal_thickness_nm):
            fill = perc.fill_fraction(self.metal_thickness_nm)
            host = self.bottom_tco.dispersion()
            disp = BruggemanEMA(disp, host, fill,
                                f"{self.metal_alloy.label} islands (f={fill:.2f})")
        return disp

    def stack(self) -> Stack:
        """Assemble the layer stack.

        Memoised in `_cache`. This is the hot path: a composition series
        re-optimises geometry at every composition and calls this tens of
        thousands of times, each call otherwise rebuilding every dispersion
        object from scratch.

        The cache is safe because `LowECoating` is only ever modified through
        `dataclasses.replace`, which produces a new instance; the `_cache={}`
        arguments at those call sites exist to reset it. Mutating a field in
        place would stale the cache, which is why none of the accessors do.
        """
        cached = self._cache.get("stack")
        if cached is not None:
            return cached
        layers = []
        if self.top_thickness_nm > 0:
            layers.append(Layer(self.top_tco.dispersion(), self.top_thickness_nm,
                                self.top_tco.key, "tco"))
        if self.barrier_metal and self.barrier_thickness_nm > 0:
            layers.append(Layer(metal(self.barrier_metal).dispersion(),
                                self.barrier_thickness_nm,
                                f"{self.barrier_metal} barrier", "barrier"))
        layers.append(Layer(self.metal_dispersion(), self.metal_thickness_nm,
                            self.metal_alloy.label, "metal"))
        if self.barrier_metal and self.barrier_thickness_nm > 0:
            layers.append(Layer(metal(self.barrier_metal).dispersion(),
                                self.barrier_thickness_nm,
                                f"{self.barrier_metal} seed", "barrier"))
        if self.bottom_thickness_nm > 0:
            layers.append(Layer(self.bottom_tco.dispersion(),
                                self.bottom_thickness_nm,
                                self.bottom_tco.key, "tco"))
        built = Stack(layers, self.substrate, AIR, self.label)
        self._cache["stack"] = built
        return built

    def evaluate(self, wavelength_nm, angle_deg: float = 0.0, **kwargs):
        return self.stack().evaluate(wavelength_nm, angle_deg, **kwargs)

    # -- materials accounting -------------------------------------------
    def silver_areal_mass(self) -> float:
        """g of Ag per m^2 of coating -- the brief's Ag-consumption metric."""
        return self.metal_alloy.element_areal_mass(
            self.metal_thickness_nm).get("Ag", 0.0)

    def element_areal_mass(self) -> dict:
        return self.metal_alloy.element_areal_mass(self.metal_thickness_nm)

    # -- variants --------------------------------------------------------
    def with_metal_thickness(self, thickness_nm: float) -> "LowECoating":
        return replace(self, metal_thickness_nm=float(thickness_nm), _cache={})

    def with_tco_thickness(self, bottom_nm: float | None = None,
                           top_nm: float | None = None) -> "LowECoating":
        return replace(
            self,
            bottom_thickness_nm=float(bottom_nm) if bottom_nm is not None
            else self.bottom_thickness_nm,
            top_thickness_nm=float(top_nm) if top_nm is not None
            else self.top_thickness_nm,
            _cache={})

    def with_alloy(self, alloy: Alloy) -> "LowECoating":
        return replace(self, metal_alloy=alloy, label="", _cache={})

    def provenance_record(self) -> Record:
        rec = Record()
        rec.add("metal_composition", self.metal_alloy.as_quantity())
        for key, q in self.bottom_tco.as_quantities().items():
            rec.add(f"bottom_tco.{key}", q)
        for key, q in self.top_tco.as_quantities().items():
            rec.add(f"top_tco.{key}", q)
        rec.add("sheet_resistance", self.sheet_resistance_quantity())
        rec.add("metal_thickness", Quantity(
            self.metal_thickness_nm, "nm", Provenance.MODEL, "design variable"))
        return rec

    def describe(self) -> str:
        lines = [f"{self.label}",
                 f"  air",
                 f"  {self.top_tco.key:<10} {self.top_thickness_nm:6.1f} nm"]
        if self.barrier_metal and self.barrier_thickness_nm > 0:
            lines.append(f"  {self.barrier_metal + ' barrier':<10} "
                         f"{self.barrier_thickness_nm:6.1f} nm")
        lines += [f"  {self.metal_alloy.label:<10} {self.metal_thickness_nm:6.1f} nm"
                  + ("" if self.is_continuous else "   <-- BELOW PERCOLATION"),
                  f"  {self.bottom_tco.key:<10} {self.bottom_thickness_nm:6.1f} nm",
                  f"  float glass",
                  f"  R_s = {self.sheet_resistance():.2f} ohm/sq"
                  f"   Ag = {self.silver_areal_mass():.3f} g/m2"]
        return "\n".join(lines)


@dataclass
class MultiMetalCoating:
    """A Low-E coating with any number of metal layers.

        air | D0 | M0 | D1 | M1 | ... | M(n-1) | Dn | float glass

    n metal layers separated by n+1 dielectric layers. n = 1 reproduces the
    ordinary DMD architecture; n = 2 and n = 3 are the double- and
    triple-silver stacks that commercial solar-control glazing actually uses.

    **Why this architecture exists.** A single metal layer trades visible
    transmittance against infrared reflectance along one curve, and the
    framework's single-layer search topped out at a light-to-solar-gain ratio
    of 1.37 -- short of the ~2 that a cooling-dominated climate needs. Two
    thinner metal layers reach the same total sheet conductance as one thick
    one, but the dielectric between them adds an interference degree of
    freedom: the two metal reflections can be arranged to cancel in the
    visible while still adding in the infrared. That is not available with one
    layer at any thickness, which is why this is an architectural limit rather
    than a compositional one.

    **Electrically the layers are in parallel**, each with its own
    size-effect and percolation state. Two 7 nm layers are *not* equivalent to
    one 14 nm layer: each thin layer suffers its own surface scattering, so
    the pair is more resistive than the single film of equal total thickness,
    and both must individually clear percolation. The model makes you pay for
    that honestly.
    """

    metal_alloys: tuple = field(default_factory=lambda: (ag_cu(1.0), ag_cu(1.0)))
    metal_thicknesses_nm: tuple = (10.0, 10.0)
    #: n+1 dielectric layers, outermost first.
    dielectrics: tuple = ()
    dielectric_thicknesses_nm: tuple = ()
    substrate: Dispersion = field(default_factory=lambda: FLOAT_GLASS)
    specularity: float = 0.5
    grain_boundary_reflection: float = 0.25
    grain_size_ratio: float = 3.0
    label: str = ""
    _cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        n = len(self.metal_thicknesses_nm)
        if len(self.metal_alloys) == 1 and n > 1:
            self.metal_alloys = tuple(self.metal_alloys) * n
        if len(self.metal_alloys) != n:
            raise ValueError(
                f"{len(self.metal_alloys)} alloys for {n} metal layers; pass "
                "one per layer, or a single alloy to repeat")
        if not self.dielectrics:
            self.dielectrics = (AZO_TYPICAL,) * (n + 1)
        if len(self.dielectrics) == 1:
            self.dielectrics = tuple(self.dielectrics) * (n + 1)
        if len(self.dielectrics) != n + 1:
            raise ValueError(
                f"{len(self.dielectrics)} dielectrics for {n} metal layers; "
                f"need exactly {n + 1} -- one above each metal and one below "
                "the last")
        if not self.dielectric_thicknesses_nm:
            self.dielectric_thicknesses_nm = (35.0,) * (n + 1)
        if len(self.dielectric_thicknesses_nm) != n + 1:
            raise ValueError(
                f"{len(self.dielectric_thicknesses_nm)} dielectric thicknesses "
                f"for {n} metal layers; need {n + 1}")
        if not self.label:
            metals = "/".join(a.label for a in self.metal_alloys)
            self.label = f"{self.dielectrics[0].key}/{metals}/{n}M"

    # -- geometry --------------------------------------------------------
    @property
    def n_metal_layers(self) -> int:
        return len(self.metal_thicknesses_nm)

    @property
    def metal_thickness_nm(self) -> float:
        """Total metal thickness. Present so this class can stand in for
        LowECoating wherever a single number is expected -- but note it is a
        sum, and the layers are not interchangeable with one film of that
        thickness."""
        return float(sum(self.metal_thicknesses_nm))

    def transport_for(self, index: int) -> ThinFilmResistivity:
        alloy = self.metal_alloys[index]
        perc = (PERCOLATION.get(alloy.symbols[0]) if alloy.is_pure
                else DEFAULT_ALLOY_PERCOLATION)
        return ThinFilmResistivity(
            bulk_resistivity_uohm_cm=alloy.bulk_resistivity_uohm_cm,
            mean_free_path_nm=alloy.mean_free_path_nm,
            specularity=self.specularity,
            grain_boundary_reflection=self.grain_boundary_reflection,
            grain_size_ratio=self.grain_size_ratio,
            percolation=perc)

    # -- electrical ------------------------------------------------------
    @property
    def is_continuous(self) -> bool:
        """Every metal layer must individually clear percolation.

        The strict reading, and the right one: a discontinuous layer in a
        two-layer stack does not merely halve the conductance, it destroys the
        interference design the second layer was placed for.
        """
        for i, d in enumerate(self.metal_thicknesses_nm):
            perc = self.transport_for(i).percolation
            if perc is not None and not perc.is_continuous(d):
                return False
        return True

    def layer_continuity(self) -> tuple:
        out = []
        for i, d in enumerate(self.metal_thicknesses_nm):
            perc = self.transport_for(i).percolation
            out.append(True if perc is None else perc.is_continuous(d))
        return tuple(out)

    def sheet_resistance(self) -> float:
        """All metal layers and all dielectrics in parallel."""
        sheets = [self.transport_for(i).sheet_resistance(d)
                  for i, d in enumerate(self.metal_thicknesses_nm)]
        sheets += [die.sheet_resistance(t) for die, t
                   in zip(self.dielectrics, self.dielectric_thicknesses_nm)]
        return parallel_sheet_resistance(*sheets)

    def sheet_resistance_quantity(self) -> Quantity:
        return Quantity(
            self.sheet_resistance(), "ohm/sq", Provenance.MODEL,
            source=f"{self.label}, {self.n_metal_layers} metal layers",
            note="parallel combination; each layer carries its own size "
                 "effect, so splitting a film in two raises resistance")

    def metal_dispersion(self, index: int) -> Dispersion:
        alloy = self.metal_alloys[index]
        thickness = self.metal_thicknesses_nm[index]
        transport = self.transport_for(index)
        ratio = float(min(transport.ratio(thickness), 50.0))
        disp = alloy.dispersion(alloy.bulk_resistivity_uohm_cm * ratio)
        perc = transport.percolation
        if perc is not None and not perc.is_continuous(thickness):
            fill = perc.fill_fraction(thickness)
            disp = BruggemanEMA(disp, self.dielectrics[index].dispersion(), fill,
                                f"{alloy.label} islands (f={fill:.2f})")
        return disp

    # -- optical ---------------------------------------------------------
    def stack(self) -> Stack:
        layers = []
        for i in range(self.n_metal_layers):
            t = self.dielectric_thicknesses_nm[i]
            if t > 0:
                layers.append(Layer(self.dielectrics[i].dispersion(), t,
                                    self.dielectrics[i].key, "tco"))
            layers.append(Layer(self.metal_dispersion(i),
                                self.metal_thicknesses_nm[i],
                                self.metal_alloys[i].label, "metal"))
        t = self.dielectric_thicknesses_nm[-1]
        if t > 0:
            layers.append(Layer(self.dielectrics[-1].dispersion(), t,
                                self.dielectrics[-1].key, "tco"))
        return Stack(layers, self.substrate, AIR, self.label)

    def evaluate(self, wavelength_nm, angle_deg: float = 0.0, **kwargs):
        return self.stack().evaluate(wavelength_nm, angle_deg, **kwargs)

    # -- materials accounting -------------------------------------------
    def element_areal_mass(self) -> dict:
        total = {}
        for alloy, d in zip(self.metal_alloys, self.metal_thicknesses_nm):
            for el, m in alloy.element_areal_mass(d).items():
                total[el] = total.get(el, 0.0) + m
        return total

    def silver_areal_mass(self) -> float:
        return self.element_areal_mass().get("Ag", 0.0)

    @property
    def metal_alloy(self) -> Alloy:
        """Thickness-weighted mean composition.

        A convenience so supply-risk and cost helpers written against
        LowECoating keep working. It is a summary, not a material: if the two
        layers differ, no part of the coating has this composition.
        """
        total = sum(self.metal_thicknesses_nm) or 1.0
        comp = {}
        for alloy, d in zip(self.metal_alloys, self.metal_thicknesses_nm):
            for el, frac in alloy.composition.items():
                comp[el] = comp.get(el, 0.0) + frac * d / total
        return Alloy(comp, mixing_model=self.metal_alloys[0].mixing_model)

    def describe(self) -> str:
        lines = [self.label, "  air"]
        cont = self.layer_continuity()
        for i in range(self.n_metal_layers):
            lines.append(f"  {self.dielectrics[i].key:<10} "
                         f"{self.dielectric_thicknesses_nm[i]:6.1f} nm")
            lines.append(f"  {self.metal_alloys[i].label:<10} "
                         f"{self.metal_thicknesses_nm[i]:6.1f} nm"
                         + ("" if cont[i] else "   <-- BELOW PERCOLATION"))
        lines += [f"  {self.dielectrics[-1].key:<10} "
                  f"{self.dielectric_thicknesses_nm[-1]:6.1f} nm",
                  "  float glass",
                  f"  R_s = {self.sheet_resistance():.2f} ohm/sq"
                  f"   Ag = {self.silver_areal_mass():.3f} g/m2"]
        return "\n".join(lines)


def dmdmd(metal="Ag", metal_thickness_nm: float = 8.0,
          tco: TCOPreset = AZO_TYPICAL, outer_nm: float = 35.0,
          middle_nm: float = 70.0, **kwargs) -> MultiMetalCoating:
    """Shorthand for a symmetric double-metal stack.

    The middle dielectric defaults to twice the outer thickness because it
    sits between two metals and does the optical work of two quarter-wave
    matching layers rather than one -- roughly a half-wave. Optimising it is
    the point of the architecture, so treat the default as a starting guess.
    """
    alloy = metal if isinstance(metal, Alloy) else Alloy({metal: 1.0})
    return MultiMetalCoating(
        metal_alloys=(alloy, alloy),
        metal_thicknesses_nm=(float(metal_thickness_nm),) * 2,
        dielectrics=(tco, tco, tco),
        dielectric_thicknesses_nm=(float(outer_nm), float(middle_nm),
                                   float(outer_nm)), **kwargs)


def dmd(metal_symbol_or_alloy="Ag", metal_thickness_nm: float = 10.0,
        tco: TCOPreset = AZO_TYPICAL, tco_thickness_nm: float = 35.0,
        **kwargs) -> LowECoating:
    """Shorthand for a symmetric dielectric/metal/dielectric coating."""
    alloy = (metal_symbol_or_alloy if isinstance(metal_symbol_or_alloy, Alloy)
             else Alloy({metal_symbol_or_alloy: 1.0}))
    return LowECoating(metal_alloy=alloy, metal_thickness_nm=metal_thickness_nm,
                       bottom_tco=tco, bottom_thickness_nm=tco_thickness_nm,
                       top_tco=tco, top_thickness_nm=tco_thickness_nm, **kwargs)


__all__ = ["Layer", "Stack", "LowECoating", "MultiMetalCoating",
           "dmd", "dmdmd", "AIR"]
