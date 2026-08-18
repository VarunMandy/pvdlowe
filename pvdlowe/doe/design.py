"""Design of experiments over the sputter parameter space (brief section 14).

The brief lists sixteen process variables across the metal layer, the AZO
layers and the multilayer geometry. Sixteen variables at two levels is 65536
runs, so the first job of a DoE is to decide what *not* to vary.

Three practical points this module is built around.

**Screen before you optimise.** A resolution-IV fractional factorial in
seven factors costs sixteen runs and tells you which three or four actually
matter. Fitting a response surface in seven factors costs about eighty runs
and mostly measures noise. :func:`fractional_factorial` generates the
screen; :func:`box_behnken` and :func:`central_composite` are for afterwards,
on the survivors.

**Resolution is not a detail.** In a resolution-III design main effects are
confounded with two-factor interactions, so a real interaction between
pressure and power can appear as a main effect of temperature. This module
reports the resolution and prints the alias structure rather than leaving it
implicit — :func:`alias_structure` is worth reading before committing tool
time.

**Randomise and block.** A sputter tool drifts: target erosion changes the
rate over a campaign, and chamber conditioning changes with time since the
last vent. Running the design in standard order confounds every effect with
that drift. :func:`randomise` and the blocking helpers exist because this is
the single most common way a well-designed experiment produces a wrong
answer.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

#: The brief's section 14 parameter space, with plausible ranges for a
#: laboratory magnetron. Ranges are ESTIMATE grade -- narrow them to what
#: your tool can actually reach before generating a design.
SPUTTER_FACTORS = {
    # metal layer
    "metal_thickness_nm": (8.0, 15.0, "nm", "metal"),
    "metal_power_w": (50.0, 200.0, "W", "metal"),
    "metal_pressure_mtorr": (2.0, 10.0, "mTorr", "metal"),
    "substrate_temperature_c": (25.0, 250.0, "degC", "shared"),
    "target_distance_mm": (60.0, 120.0, "mm", "shared"),
    # AZO layers
    "azo_thickness_nm": (25.0, 45.0, "nm", "azo"),
    "azo_al_percent": (1.0, 5.0, "at.%", "azo"),
    "azo_power_w": (100.0, 300.0, "W", "azo"),
    "azo_pressure_mtorr": (2.0, 12.0, "mTorr", "azo"),
    "oxygen_fraction_pct": (0.0, 5.0, "% of total flow", "azo"),
    # multilayer
    "anneal_temperature_c": (25.0, 400.0, "degC", "multilayer"),
}


@dataclass
class Factor:
    """One experimental factor with its range."""

    name: str
    low: float
    high: float
    unit: str = ""
    group: str = ""

    def decode(self, coded):
        """Coded [-1, +1] -> physical units."""
        centre = 0.5 * (self.low + self.high)
        half = 0.5 * (self.high - self.low)
        return centre + np.asarray(coded, dtype=float) * half

    def encode(self, physical):
        centre = 0.5 * (self.low + self.high)
        half = 0.5 * (self.high - self.low)
        return (np.asarray(physical, dtype=float) - centre) / half


@dataclass
class Design:
    """A generated design matrix, in coded and physical units."""

    factors: list
    coded: np.ndarray
    kind: str
    resolution: str = ""
    generators: tuple = ()
    notes: list = field(default_factory=list)

    @property
    def n_runs(self) -> int:
        return int(self.coded.shape[0])

    @property
    def names(self) -> list:
        return [f.name for f in self.factors]

    def to_frame(self, physical: bool = True) -> pd.DataFrame:
        if not physical:
            return pd.DataFrame(self.coded, columns=self.names)
        data = {f.name: f.decode(self.coded[:, i])
                for i, f in enumerate(self.factors)}
        return pd.DataFrame(data)

    def randomise(self, seed: int = 0) -> "Design":
        """Shuffle the run order. Do this. Always."""
        rng = np.random.default_rng(seed)
        order = rng.permutation(self.n_runs)
        return Design(self.factors, self.coded[order], self.kind,
                      self.resolution, self.generators,
                      self.notes + [f"randomised with seed {seed}"])

    def with_run_sheet(self, seed: int = 0, replicates_at_centre: int = 3
                       ) -> pd.DataFrame:
        """A run sheet ready to take to the tool.

        Adds centre-point replicates, which do two jobs at once: they give a
        pure-error estimate independent of the model, and repeated across the
        campaign they detect tool drift.
        """
        design = self.randomise(seed)
        df = design.to_frame()
        if replicates_at_centre > 0:
            centre = {f.name: 0.5 * (f.low + f.high) for f in self.factors}
            centres = pd.DataFrame([centre] * replicates_at_centre)
            # interleave centre points through the campaign, not all at the end
            step = max(len(df) // (replicates_at_centre + 1), 1)
            pieces, ci = [], 0
            for start in range(0, len(df), step):
                pieces.append(df.iloc[start:start + step])
                if ci < replicates_at_centre:
                    pieces.append(centres.iloc[[ci]])
                    ci += 1
            df = pd.concat(pieces, ignore_index=True)
        df.insert(0, "run", range(1, len(df) + 1))
        df["is_centre"] = [
            all(abs(row[f.name] - 0.5 * (f.low + f.high)) < 1e-9
                for f in self.factors)
            for _, row in df.iterrows()]
        for col in ("T_vis", "R_sheet_ohm_sq", "emissivity", "notes"):
            df[col] = ""
        return df


def _factors(names, ranges=None) -> list:
    out = []
    for name in names:
        if ranges and name in ranges:
            lo, hi = ranges[name][:2]
            unit = ranges[name][2] if len(ranges[name]) > 2 else ""
            group = ranges[name][3] if len(ranges[name]) > 3 else ""
        elif name in SPUTTER_FACTORS:
            lo, hi, unit, group = SPUTTER_FACTORS[name]
        else:
            raise KeyError(f"no range known for factor {name!r}; pass one in")
        out.append(Factor(name, float(lo), float(hi), unit, group))
    return out


def full_factorial(names, levels: int = 2, ranges=None) -> Design:
    """Full factorial at the given number of levels."""
    facs = _factors(names, ranges)
    coded_levels = np.linspace(-1, 1, levels)
    coded = np.array(list(itertools.product(coded_levels, repeat=len(facs))))
    notes = []
    if len(coded) > 64:
        notes.append(f"{len(coded)} runs is a lot of tool time; consider "
                     "fractional_factorial for screening")
    return Design(facs, coded, f"full factorial {levels}^{len(facs)}",
                  resolution="full", notes=notes)


#: Standard minimum-aberration generators, keyed by (n_factors, n_base).
#: Each entry maps an added factor to the product of base columns that
#: defines it.
_GENERATORS = {
    (4, 3): (("D", (0, 1, 2)),),                      # 2^(4-1) IV
    (5, 4): (("E", (0, 1, 2, 3)),),                   # 2^(5-1) V
    (5, 3): (("D", (0, 1)), ("E", (0, 2))),           # 2^(5-2) III
    (6, 4): (("E", (0, 1, 2)), ("F", (1, 2, 3))),     # 2^(6-2) IV
    (7, 4): (("E", (0, 1, 2)), ("F", (0, 1, 3)),      # 2^(7-3) IV
             ("G", (0, 2, 3))),
    (8, 4): (("E", (1, 2, 3)), ("F", (0, 2, 3)),      # 2^(8-4) IV
             ("G", (0, 1, 3)), ("H", (0, 1, 2))),
}


def fractional_factorial(names, n_base: int | None = None, ranges=None) -> Design:
    """Fractional factorial screening design.

    Picks a standard minimum-aberration generator set. The returned Design
    records its resolution; call :func:`alias_structure` to see exactly what
    is confounded with what before you interpret the results.

    Resolution III means main effects are aliased with two-factor
    interactions — usable for a first screen, dangerous for conclusions.
    Resolution IV means main effects are clear of two-factor interactions but
    those interactions are aliased with each other. Resolution V is clean
    enough to fit interactions.
    """
    facs = _factors(names, ranges)
    k = len(facs)
    if k <= 3:
        return full_factorial(names, 2, ranges)
    if n_base is None:
        n_base = 4 if k >= 5 else 3
    key = (k, n_base)
    if key not in _GENERATORS:
        raise ValueError(
            f"no standard generator for {k} factors in 2^{n_base} runs; "
            f"available: {sorted(_GENERATORS)}")
    gens = _GENERATORS[key]
    base = np.array(list(itertools.product([-1, 1], repeat=n_base)))
    cols = [base[:, i] for i in range(n_base)]
    for _, sources in gens:
        col = np.ones(len(base))
        for s in sources:
            col = col * base[:, s]
        cols.append(col)
    coded = np.column_stack(cols[:k])
    resolution = {(4, 3): "IV", (5, 4): "V", (5, 3): "III", (6, 4): "IV",
                  (7, 4): "IV", (8, 4): "IV"}[key]
    notes = [f"2^({k}-{k - n_base}) resolution {resolution}"]
    if resolution == "III":
        notes.append("RESOLUTION III: main effects are aliased with "
                     "two-factor interactions. Screen only -- do not draw "
                     "mechanistic conclusions from this design alone.")
    return Design(facs, coded, f"2^({k}-{k - n_base}) fractional factorial",
                  resolution=resolution, generators=gens, notes=notes)


def alias_structure(design: Design, max_order: int = 2) -> pd.DataFrame:
    """Which effects are confounded with which, computed from the design.

    Derived from the actual columns rather than from the generator algebra,
    so it stays correct even for a design assembled by hand.
    """
    names = design.names
    X = design.coded
    effects = {}
    for order in range(1, max_order + 1):
        for combo in itertools.combinations(range(len(names)), order):
            col = np.ones(len(X))
            for i in combo:
                col = col * X[:, i]
            effects[":".join(names[i] for i in combo)] = col
    keys = list(effects)
    rows, seen = [], set()
    for i, a in enumerate(keys):
        if a in seen:
            continue
        group = [a]
        for b in keys[i + 1:]:
            if np.allclose(effects[a], effects[b]) or \
               np.allclose(effects[a], -effects[b]):
                group.append(b)
                seen.add(b)
        if len(group) > 1:
            rows.append({"effect": a, "aliased_with": ", ".join(group[1:]),
                         "n_aliases": len(group) - 1})
    return pd.DataFrame(rows)


def box_behnken(names, ranges=None) -> Design:
    """Box-Behnken response-surface design.

    Three levels, no corner points — which matters here because the corners
    of a sputter parameter space are often where the process misbehaves
    (highest power at lowest pressure will arc). Needs at least 3 factors.
    """
    facs = _factors(names, ranges)
    k = len(facs)
    if k < 3:
        raise ValueError("Box-Behnken needs at least 3 factors")
    rows = []
    for i, j in itertools.combinations(range(k), 2):
        for a, b in itertools.product([-1, 1], repeat=2):
            row = np.zeros(k)
            row[i], row[j] = a, b
            rows.append(row)
    n_centre = {3: 3, 4: 3, 5: 6, 6: 6, 7: 6}.get(k, 6)
    rows.extend(np.zeros(k) for _ in range(n_centre))
    return Design(facs, np.array(rows), f"Box-Behnken ({k} factors)",
                  resolution="response surface",
                  notes=["avoids extreme-corner combinations, which is "
                         "usually what you want on a sputter tool"])


def central_composite(names, alpha: str | float = "rotatable",
                      n_centre: int = 4, face_centred: bool = False,
                      ranges=None) -> Design:
    """Central composite design: factorial + axial + centre points.

    `face_centred=True` sets alpha = 1, keeping every run inside the original
    factor ranges. Use it when the ranges are hard limits of the tool, since
    a rotatable alpha for 4 factors is 2.0 — which would ask for double the
    stated range on each axis.
    """
    facs = _factors(names, ranges)
    k = len(facs)
    factorial = np.array(list(itertools.product([-1, 1], repeat=k)))
    if face_centred:
        a = 1.0
    elif alpha == "rotatable":
        a = float(len(factorial)) ** 0.25
    elif alpha == "orthogonal":
        a = float(len(factorial)) ** 0.5
    else:
        a = float(alpha)
    axial = []
    for i in range(k):
        for sign in (-a, a):
            row = np.zeros(k)
            row[i] = sign
            axial.append(row)
    coded = np.vstack([factorial, np.array(axial), np.zeros((n_centre, k))])
    notes = [f"alpha = {a:.3f}"]
    if not face_centred and a > 1.0:
        notes.append(f"axial points sit {a:.2f}x beyond the stated factor "
                     "range; use face_centred=True if those are hard limits")
    return Design(facs, coded, f"central composite ({k} factors)",
                  resolution="response surface", notes=notes)


def latin_hypercube(names, n_samples: int = 30, seed: int = 0,
                    ranges=None) -> Design:
    """Latin hypercube sample — space-filling, for surrogate model fitting.

    Use when the response is expected to be non-polynomial, or when the
    design will feed a Gaussian-process or other flexible surrogate rather
    than a quadratic response surface.
    """
    facs = _factors(names, ranges)
    k = len(facs)
    rng = np.random.default_rng(seed)
    cut = np.linspace(0, 1, n_samples + 1)
    coded = np.zeros((n_samples, k))
    for i in range(k):
        u = rng.uniform(cut[:n_samples], cut[1:])
        coded[:, i] = 2.0 * rng.permutation(u) - 1.0
    return Design(facs, coded, f"Latin hypercube ({n_samples} samples)",
                  resolution="space-filling")


def recommended_screening() -> Design:
    """The design this framework would actually run first.

    Seven factors chosen because they plausibly move the response and can be
    set independently on a typical tool. Deliberately excludes AZO power and
    target distance: at fixed thickness, power mostly changes time rather
    than film properties, and distance is rarely adjustable run to run.

    Sixteen runs plus three centre points. That is a week of tool time, not a
    quarter, and it identifies the two or three factors worth a response
    surface.
    """
    d = fractional_factorial([
        "metal_thickness_nm", "metal_power_w", "metal_pressure_mtorr",
        "substrate_temperature_c", "azo_thickness_nm", "azo_al_percent",
        "oxygen_fraction_pct",
    ], n_base=4)
    d.notes.append(
        "confirm the alias structure before interpreting: at resolution IV "
        "the two-factor interactions are aliased in pairs, so a "
        "pressure-power interaction cannot be separated from whichever pair "
        "it aliases with")
    return d


__all__ = ["SPUTTER_FACTORS", "Factor", "Design", "full_factorial",
           "fractional_factorial", "alias_structure", "box_behnken",
           "central_composite", "latin_hypercube", "recommended_screening"]
