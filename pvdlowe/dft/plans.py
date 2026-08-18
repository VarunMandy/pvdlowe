"""Planning the first-principles work: the brief's sections 9, 14 and 15.

This module does not run DFT. It generates the inputs, writes a job manifest,
and -- more importantly -- decides what is worth calculating.

That last part deserves saying plainly, because the brief's proposed matrix
is larger than it needs to be. Calculating a full property suite for twelve
compositions is a lot of compute spent to answer a question whose shape is
already known: the interesting quantity for Ag-Cu is the *mixing energy*, and
it is a single scalar per composition obtainable from ordinary static
calculations. Band structures, dielectric tensors and elastic constants for
every composition can wait until one composition has been selected.

So the plan is staged:

  Stage A   mixing energies across the Ag-Cu series.
            Cheap. Answers "does the alloy want to exist?"
  Stage B   interface energies, AZO against the two or three surviving
            metal compositions. Expensive slab calculations, but this is where
            the brief's real novelty claim lives -- section 10 is right that
            interface energy matters more here than bulk alloy energy.
  Stage C   optical and elastic properties for the single chosen composition.

Stage A is worth doing regardless. Stage B only if Stage A leaves a choice.
Stage C only after the experiment has confirmed the film is what you think.

A warning the brief itself raises and this module enforces: ordinary PBE-GGA
handles Cu 3d states poorly and can misplace alloy formation energies. Every
generated plan requests a functional comparison rather than a single
calculation, because a mixing energy that changes sign between PBE and
PBE+U is a mixing energy you cannot draw a conclusion from.
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..provenance import Provenance, Quantity

#: Lattice parameters of the fcc parents, in angstrom. Experimental values;
#: DFT relaxation will shift them by a per cent or two depending on functional.
FCC_LATTICE = {"Ag": 4.085, "Cu": 3.615, "Al": 4.050, "Au": 4.078}

#: Functionals to compare, per the brief's section 6 warning about Cu 3d.
FUNCTIONALS = ("PBE", "PBE+U", "r2SCAN")


@dataclass
class Calculation:
    """One planned calculation."""

    name: str
    stage: str
    kind: str               # 'static' | 'relax' | 'dos' | 'optics' | 'elastic' | 'slab'
    composition: dict
    functional: str
    supercell: tuple = (2, 2, 2)
    purpose: str = ""
    estimated_core_hours: float = 0.0

    def directory(self) -> str:
        comp = "".join(f"{s}{int(round(f * 100))}"
                       for s, f in sorted(self.composition.items(),
                                          key=lambda t: -t[1]))
        return f"{self.stage}/{comp}_{self.functional.replace('+', 'p')}_{self.kind}"


def fcc_supercell_poscar(composition: dict, supercell=(2, 2, 2),
                         lattice_a: float | None = None, seed: int = 0,
                         comment: str = "") -> str:
    """POSCAR for a substitutionally disordered fcc solid solution.

    Sites are decorated by a seeded deterministic shuffle, which gives a
    reproducible random solid solution. That is adequate for a first mixing
    energy but it is *not* a special quasi-random structure: an SQS matches
    the target correlation functions of a truly random alloy and a shuffled
    cell does not. For publication-grade mixing energies, generate SQS cells
    with ATAT's mcsqs or icet and feed them through the same workflow.

    Vegard's law sets the lattice parameter, which for Ag-Cu is a real
    approximation -- the 13% size mismatch means the true relaxed volume
    deviates from linear -- so the ISIF=3 relaxation in the generated INCAR
    matters more here than it would for a well-matched system.
    """
    nx, ny, nz = supercell
    n_sites = 4 * nx * ny * nz
    if lattice_a is None:
        lattice_a = sum(f * FCC_LATTICE.get(s, 4.0) for s, f in composition.items())

    counts = {}
    remaining = n_sites
    symbols = sorted(composition, key=lambda s: -composition[s])
    for sym in symbols[:-1]:
        counts[sym] = int(round(composition[sym] * n_sites))
        remaining -= counts[sym]
    counts[symbols[-1]] = remaining
    if any(c < 0 for c in counts.values()):
        raise ValueError(
            f"supercell of {n_sites} sites cannot represent {composition}; "
            "use a larger supercell")

    basis = np.array([[0.0, 0.0, 0.0], [0.0, 0.5, 0.5],
                      [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]])
    positions = []
    for i, j, k in itertools.product(range(nx), range(ny), range(nz)):
        for b in basis:
            positions.append((b + np.array([i, j, k])) / np.array([nx, ny, nz]))
    positions = np.array(positions)

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(positions))
    assigned, cursor = [], 0
    for sym in symbols:
        idx = order[cursor:cursor + counts[sym]]
        assigned.append((sym, positions[idx]))
        cursor += counts[sym]

    lines = [comment or f"fcc solid solution {composition} seed={seed}",
             "1.0",
             f"  {lattice_a * nx:.8f}   0.00000000   0.00000000",
             f"  0.00000000   {lattice_a * ny:.8f}   0.00000000",
             f"  0.00000000   0.00000000   {lattice_a * nz:.8f}",
             "  " + "  ".join(sym for sym, _ in assigned),
             "  " + "  ".join(str(len(pos)) for _, pos in assigned),
             "Direct"]
    for _, pos in assigned:
        for p in pos:
            lines.append(f"  {p[0]:.8f}  {p[1]:.8f}  {p[2]:.8f}")
    return "\n".join(lines) + "\n"


INCAR_TEMPLATES = {
    "relax": """SYSTEM = {name}
! full relaxation -- ISIF=3 matters for Ag-Cu, the 13% size mismatch means
! Vegard's law is not a good guess for the alloy volume
ISTART = 0
ICHARG = 2
ENCUT  = 520
PREC   = Accurate
EDIFF  = 1E-6
EDIFFG = -0.01
NSW    = 100
IBRION = 2
ISIF   = 3
ISMEAR = 1
SIGMA  = 0.10
LREAL  = .FALSE.
LWAVE  = .FALSE.
LCHARG = .TRUE.
{functional_tags}""",
    "static": """SYSTEM = {name}
! static total energy for the mixing-energy series -- must use identical
! ENCUT, k-point density and functional across every member of the series,
! otherwise the energy differences are meaningless
ISTART = 0
ICHARG = 2
ENCUT  = 520
PREC   = Accurate
EDIFF  = 1E-7
NSW    = 0
IBRION = -1
ISMEAR = -5
LREAL  = .FALSE.
LORBIT = 11
LWAVE  = .FALSE.
LCHARG = .TRUE.
{functional_tags}""",
    "dos": """SYSTEM = {name}
ISTART = 1
ICHARG = 11
ENCUT  = 520
PREC   = Accurate
EDIFF  = 1E-7
NSW    = 0
IBRION = -1
ISMEAR = -5
NEDOS  = 3001
LORBIT = 11
{functional_tags}""",
    "optics": """SYSTEM = {name}
! frequency-dependent dielectric function. NBANDS must be raised well above
! the default or the high-energy tail of eps_2 is truncated, which quietly
! corrupts the Kramers-Kronig transform and hence n(omega) in the visible.
ISTART = 0
ICHARG = 2
ENCUT  = 520
PREC   = Accurate
EDIFF  = 1E-8
NSW    = 0
IBRION = -1
ISMEAR = 0
SIGMA  = 0.05
LOPTICS = .TRUE.
CSHIFT = 0.100
NEDOS  = 3000
NBANDS = {nbands}
{functional_tags}""",
    "elastic": """SYSTEM = {name}
ISTART = 0
ICHARG = 2
ENCUT  = 600
PREC   = Accurate
EDIFF  = 1E-8
IBRION = 6
ISIF   = 3
NFREE  = 2
POTIM  = 0.015
NSW    = 1
ISMEAR = 1
SIGMA  = 0.10
{functional_tags}""",
    "slab": """SYSTEM = {name}
! metal/AZO interface slab. Dipole correction is not optional for an
! asymmetric slab -- without it the vacuum potential is not flat and the
! interface energy is wrong.
ISTART = 0
ICHARG = 2
ENCUT  = 520
PREC   = Accurate
EDIFF  = 1E-6
EDIFFG = -0.02
NSW    = 200
IBRION = 2
ISIF   = 2
ISMEAR = 0
SIGMA  = 0.05
LDIPOL = .TRUE.
IDIPOL = 3
LVTOT  = .TRUE.
{functional_tags}""",
}

FUNCTIONAL_TAGS = {
    "PBE": "GGA = PE",
    "PBE+U": ("GGA = PE\nLDAU = .TRUE.\nLDAUTYPE = 2\n"
              "! U on the Cu and Zn 3d states. The brief's section 6 point:\n"
              "! plain GGA can misplace Cu-alloy formation energies.\n"
              "LDAUL = 2 2\nLDAUU = 4.0 0.0\nLDAUJ = 0.0 0.0\nLMAXMIX = 4"),
    "r2SCAN": "METAGGA = R2SCAN\nLASPH = .TRUE.\nLMIXTAU = .TRUE.",
}


@dataclass
class DFTPlan:
    """A staged set of calculations with a manifest."""

    calculations: list = field(default_factory=list)
    title: str = "Low-E materials DFT plan"

    def add(self, calc: Calculation) -> None:
        self.calculations.append(calc)

    def by_stage(self, stage: str) -> list:
        return [c for c in self.calculations if c.stage == stage]

    @property
    def total_core_hours(self) -> float:
        return float(sum(c.estimated_core_hours for c in self.calculations))

    def manifest(self) -> list:
        return [{"name": c.name, "stage": c.stage, "kind": c.kind,
                 "functional": c.functional, "directory": c.directory(),
                 "composition": c.composition, "purpose": c.purpose,
                 "est_core_hours": c.estimated_core_hours}
                for c in self.calculations]

    def write(self, root: Path, supercell=(2, 2, 2), seed: int = 0) -> Path:
        """Write POSCAR, INCAR, KPOINTS and a manifest for every calculation."""
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        for calc in self.calculations:
            d = root / calc.directory()
            d.mkdir(parents=True, exist_ok=True)
            if calc.kind != "slab":
                (d / "POSCAR").write_text(fcc_supercell_poscar(
                    calc.composition, calc.supercell, seed=seed,
                    comment=calc.name))
            n_atoms = 4 * int(np.prod(calc.supercell))
            tags = FUNCTIONAL_TAGS.get(calc.functional, "GGA = PE")
            (d / "INCAR").write_text(INCAR_TEMPLATES[calc.kind].format(
                name=calc.name, functional_tags=tags, nbands=max(8 * n_atoms, 64)))
            (d / "KPOINTS").write_text(
                "Gamma-centred automatic\n0\nGamma\n"
                f"{max(12 // calc.supercell[0], 3)} "
                f"{max(12 // calc.supercell[1], 3)} "
                f"{max(12 // calc.supercell[2], 3)}\n0 0 0\n")
            (d / "README.md").write_text(
                f"# {calc.name}\n\nStage {calc.stage} / {calc.kind} / "
                f"{calc.functional}\n\n{calc.purpose}\n\n"
                "POTCAR is not generated: it is licensed and must be assembled "
                "from your own VASP distribution, in the element order given in "
                "line 6 of POSCAR.\n")
        (root / "manifest.json").write_text(json.dumps(
            {"title": self.title, "total_core_hours": self.total_core_hours,
             "calculations": self.manifest()}, indent=2))
        return root


def smallest_supercell(fractions, max_sites: int = 256,
                       tolerance: float = 1e-6) -> tuple:
    """Smallest fcc supercell in which every fraction is an exact site count.

    Worth doing rather than guessing. A 2x2x2 fcc cell holds 32 sites, so it
    can express 25%, 50% and 75% exactly and cannot express 70% or 90% at all
    -- a rounded 22/32 is 68.75%, and comparing a 68.75% cell against a
    nominal 70% composition puts a systematic error straight into the mixing
    energy. This searches for a cell that needs no rounding.
    """
    candidates = []
    for nx in range(1, 6):
        for ny in range(nx, 6):
            for nz in range(ny, 8):
                n_sites = 4 * nx * ny * nz
                if n_sites > max_sites:
                    continue
                if all(abs(f * n_sites - round(f * n_sites)) < tolerance * n_sites
                       for f in fractions):
                    candidates.append((n_sites, (nx, ny, nz)))
    if not candidates:
        raise ValueError(
            f"no fcc supercell under {max_sites} sites represents {fractions} "
            "exactly; either change the compositions to representable values "
            "or accept rounding and record the achieved composition")
    return min(candidates)[1]


def ag_cu_series_plan(fractions=(1.0, 0.90, 0.75, 0.70, 0.50, 0.25, 0.0),
                      functionals=("PBE", "PBE+U"),
                      supercell=None) -> DFTPlan:
    """Stage A: mixing energies across the Ag-Cu series.

    Includes both end members in every functional, because the mixing energy
    is a difference against them, and mixing end-member energies computed with
    different settings is the most common way this calculation goes wrong.

    The supercell is chosen automatically so every composition is exactly
    representable; pass one explicitly to override.
    """
    if supercell is None:
        supercell = smallest_supercell(tuple(fractions))
    plan = DFTPlan(title=f"Stage A -- Ag-Cu mixing energies "
                         f"({4 * int(np.prod(supercell))}-site cell)")
    n_sites = 4 * int(np.prod(supercell))
    for x in fractions:
        comp = {"Ag": x, "Cu": 1.0 - x}
        comp = {k: v for k, v in comp.items() if v > 0}
        if any(abs(v * n_sites - round(v * n_sites)) > 1e-6 for v in comp.values()):
            raise ValueError(
                f"composition {comp} is not representable in {n_sites} sites; "
                f"call smallest_supercell({tuple(fractions)}) for a cell that works")
        for fn in functionals:
            for kind, hours in (("relax", 40.0), ("static", 12.0)):
                plan.add(Calculation(
                    name=f"AgCu x={x:.2f} {fn} {kind}", stage="A", kind=kind,
                    composition=comp, functional=fn, supercell=supercell,
                    purpose="mixing energy of the Ag-Cu solid solution; "
                            "sign decides whether the alloy is metastable",
                    estimated_core_hours=hours))
    return plan


def stabiliser_plan(base=(0.70, 0.29), thirds=("Ti", "Al"),
                    functionals=("PBE+U",), supercell=(3, 3, 3)) -> DFTPlan:
    """Stage A2: dilute ternary additions, the brief's section 13 hypothesis.

    A 3x3x3 fcc cell has 108 sites, so one substituted atom is 0.93 at.% --
    close to the 1% the brief proposes and the smallest cell in which that
    concentration is even representable. A 2x2x2 cell cannot express 1%.
    """
    plan = DFTPlan(title="Stage A2 -- dilute ternary stabilisers")
    n_sites = 4 * int(np.prod(supercell))
    y = 1.0 / n_sites
    ag, cu = base
    scale = (1.0 - y) / (ag + cu)
    for third in thirds:
        comp = {"Ag": ag * scale, "Cu": cu * scale, third: y}
        for fn in functionals:
            plan.add(Calculation(
                name=f"Ag-Cu-{third} {fn} relax", stage="A2", kind="relax",
                composition=comp, functional=fn, supercell=supercell,
                purpose=f"does dilute {third} lower the mixing energy or is it "
                        f"simply along for the ride? A 1% addition that does "
                        f"not change the energetics is not a stabiliser.",
                estimated_core_hours=220.0))
    return plan


def mixing_energy(alloy_energy_per_atom: float, end_members: dict,
                  composition: dict) -> Quantity:
    """Mixing energy per atom, in eV.

        dE_mix = E(alloy) - sum_i x_i E(pure i)

    Negative means the mixed state is favoured over separated pure phases at
    that composition. Positive means a driving force to separate -- which,
    for a sputtered film, still permits a kinetically trapped solid solution.
    The magnitude matters: a few meV/atom is within the noise of a
    non-SQS supercell, while 50 meV/atom is a real driving force.
    """
    ref = sum(composition[s] * end_members[s] for s in composition)
    value = float(alloy_energy_per_atom - ref)
    return Quantity(
        value, "eV/atom", Provenance.DFT_OWN,
        source=f"mixing energy for {composition}",
        note=("compare against k_B T at the deposition temperature "
              "(0.026 eV at 300 K, 0.048 eV at 550 K) before calling it "
              "significant; and check it does not change sign between "
              "functionals"))


def interface_energy(slab_energy: float, metal_energy: float,
                     oxide_energy: float, area_angstrom2: float) -> Quantity:
    """Interface formation energy per unit area, in J/m^2.

        gamma = (E_slab - E_metal - E_oxide) / (2 A)

    for a slab with two equivalent interfaces; drop the factor of two for a
    single-interface geometry with a dipole correction. More negative means
    stronger adhesion, which is the quantity relevant to the brief's claims
    about film continuity and thermal stability -- and the one that most
    plausibly distinguishes a Ti-containing stack from a plain one.
    """
    ev_per_a2_to_j_per_m2 = 16.0218
    value = (slab_energy - metal_energy - oxide_energy) / (2.0 * area_angstrom2)
    return Quantity(
        float(value * ev_per_a2_to_j_per_m2), "J/m2", Provenance.DFT_OWN,
        source="interface formation energy",
        note="depends on the chosen interface termination and registry; "
             "report which, and test at least two terminations")


def what_dft_cannot_give() -> dict:
    """The brief's section 17 distinction, as a checkable dictionary."""
    return {
        "from_dft": ["formation energy", "energy above hull", "mixing energy",
                     "crystal stability", "band gap", "density of states",
                     "dielectric function", "refractive index",
                     "elastic constants", "interface energy",
                     "surface and adhesion energetics"],
        "approximate_from_dft": ["electrical conductivity (needs a transport "
                                 "calculation and a scattering model)",
                                 "emissivity (needs the multilayer, not the "
                                 "material)",
                                 "thermal durability (kinetic, not thermodynamic)"],
        "experiment_only": ["deposition rate", "film thickness", "roughness",
                            "film continuity", "adhesion", "cost",
                            "agglomeration and dewetting kinetics",
                            "damp-heat and abrasion durability"],
    }


__all__ = ["Calculation", "DFTPlan", "fcc_supercell_poscar", "smallest_supercell",
           "ag_cu_series_plan",
           "stabiliser_plan", "mixing_energy", "interface_energy",
           "what_dft_cannot_give", "FCC_LATTICE", "FUNCTIONALS",
           "INCAR_TEMPLATES", "FUNCTIONAL_TAGS"]
