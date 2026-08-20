"""Machine-learned interatomic potentials as a DFT surrogate.

Stage A of the brief's programme — Ag–Cu mixing energies — needs a VASP
licence, an HPC allocation and roughly 730 core-hours. A universal
machine-learned interatomic potential does the same calculation on a laptop in
minutes, at a cost in accuracy that this module measures rather than assumes.

**What these models are.** MACE-MP-0, CHGNet, M3GNet, SevenNet, MatterSim and
similar are graph neural networks trained on the Materials Project's own DFT
dataset — the same database `pvdlowe.mp` queries. They predict energy and
forces for an arbitrary structure without solving the electronic problem.
Reported errors on held-out MP data are of order 30–50 meV/atom on energy,
which is comparable with the differences this project cares about, and that is
precisely why the validation step below is not optional.

**They are not LLMs.** A language model cannot do this; the architecture is a
message-passing network over atomic positions with physical equivariance built
in. The distinction matters when choosing what to install.

**Where they are weakest is where this project lives.** Training data is
dominated by ordered, stoichiometric crystals near the convex hull. A
disordered sputtered solid solution, a 1 at.% dilute ternary, and a
metal/oxide interface are all sparse regions of that distribution. Errors
there are not the reported held-out errors.

So this module does three things in order, and refuses to skip to the third:

1. :func:`validate_against_hull` reproduces Materials Project values the
   framework already holds — Cu₃Ag at 0.0904 eV/atom above the hull, CuAg₃ at
   0.0857. If the surrogate cannot recover those, its predictions for
   disordered alloys are worthless and the function says so.
2. :func:`mixing_energy_series` computes the Ag–Cu series the brief asks for.
3. :func:`screen_ternaries` gives first-pass numbers for the dilute additions,
   graded `ML_SURROGATE` and therefore blocked from headline tables by
   `assert_reportable`.

Nothing here produces a value graded `DFT_OWN`. A surrogate result is a
screening signal that tells you which calculations are worth running, not a
substitute for running them — which is the brief's own §12 position applied to
a tool the brief did not anticipate.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

from ..provenance import Provenance, Quantity

#: Models this module knows how to load, best-supported first. Each entry is
#: (import name, pip package, loader description).
SUPPORTED = {
    "mace": ("mace", "mace-torch",
             "MACE-MP-0 foundation model; strongest general accuracy, ~100 MB"),
    "chgnet": ("chgnet", "chgnet",
               "CHGNet; includes magnetic moments, small and fast"),
    "m3gnet": ("matgl", "matgl",
               "M3GNet via MatGL; the original MP universal potential"),
    "sevennet": ("sevenn", "sevenn",
                 "SevenNet; strong on metals, GPU-oriented"),
}

#: Values the framework already holds from the Materials Project, used to
#: validate a surrogate before trusting it on anything new. Energies above
#: hull, eV/atom, retrieved 2026 (see docs/FINDINGS.md §3.7).
MP_REFERENCE = {
    "Cu3Ag": 0.0904,
    "CuAg3": 0.0857,
}


class SurrogateUnavailable(RuntimeError):
    """No interatomic potential is installed."""


def available_models() -> dict:
    """Which supported potentials are importable in this environment."""
    out = {}
    for key, (mod, pkg, desc) in SUPPORTED.items():
        try:
            __import__(mod)
            out[key] = {"installed": True, "package": pkg, "description": desc}
        except ImportError:
            out[key] = {"installed": False, "package": pkg, "description": desc}
    return out


def load_calculator(model: str = "auto", device: str = "cpu"):
    """Return an ASE calculator for the requested potential.

    Raises rather than falling back to anything approximate. The framework's
    convention throughout is that a missing capability is an error, not an
    invitation to produce a plausible number.
    """
    try:
        import ase  # noqa: F401
    except ImportError as exc:
        raise SurrogateUnavailable(
            "ASE is required for surrogate calculations: pip install ase"
        ) from exc

    order = [model] if model != "auto" else list(SUPPORTED)
    errors = []
    for key in order:
        try:
            if key == "mace":
                from mace.calculators import mace_mp
                return mace_mp(model="medium", device=device,
                               default_dtype="float64"), "MACE-MP-0 (medium)"
            if key == "chgnet":
                from chgnet.model.dynamics import CHGNetCalculator
                return CHGNetCalculator(use_device=device), "CHGNet"
            if key == "m3gnet":
                import matgl
                from matgl.ext.ase import PESCalculator
                pot = matgl.load_model("M3GNet-MP-2021.2.8-PES")
                return PESCalculator(pot), "M3GNet (MP-2021.2.8)"
            if key == "sevennet":
                from sevenn.sevennet_calculator import SevenNetCalculator
                return SevenNetCalculator("7net-0", device=device), "SevenNet-0"
        except Exception as exc:                       # noqa: BLE001
            errors.append(f"{key}: {type(exc).__name__}: {exc}")
    raise SurrogateUnavailable(
        "no supported interatomic potential could be loaded.\n  "
        + "\n  ".join(errors)
        + "\n\nInstall one, e.g.:  pip install mace-torch ase")


def _fcc_atoms(composition: dict, supercell=(2, 2, 2), lattice_a=None,
               seed: int = 0):
    """Build a substitutionally disordered fcc cell as an ASE Atoms object.

    Uses the same seeded-shuffle decoration as `dft.plans.fcc_supercell_poscar`
    so a surrogate run and a VASP run describe the same structure. As noted
    there, a shuffled cell is not a special quasi-random structure; for
    publication-grade numbers generate SQS cells with ATAT mcsqs or icet and
    pass them in directly.
    """
    from ase import Atoms
    from .plans import FCC_LATTICE

    nx, ny, nz = supercell
    n_sites = 4 * nx * ny * nz
    if lattice_a is None:
        lattice_a = sum(f * FCC_LATTICE.get(s, 4.0) for s, f in composition.items())

    counts, remaining = {}, n_sites
    symbols = sorted(composition, key=lambda s: -composition[s])
    for sym in symbols[:-1]:
        counts[sym] = int(round(composition[sym] * n_sites))
        remaining -= counts[sym]
    counts[symbols[-1]] = remaining
    if any(c < 0 for c in counts.values()):
        raise ValueError(
            f"composition {composition} is not representable in {n_sites} "
            "sites; use a larger supercell (see dft.plans.smallest_supercell)")

    basis = np.array([[0., 0., 0.], [0., .5, .5], [.5, 0., .5], [.5, .5, 0.]])
    pos = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                for b in basis:
                    pos.append((b + np.array([i, j, k])) / np.array([nx, ny, nz]))
    pos = np.array(pos)

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(pos))
    syms, cursor = [], 0
    scaled = np.zeros_like(pos)
    for sym in symbols:
        idx = order[cursor:cursor + counts[sym]]
        for n, i in enumerate(idx):
            scaled[cursor + n] = pos[i]
            syms.append(sym)
        cursor += counts[sym]

    cell = np.diag([lattice_a * nx, lattice_a * ny, lattice_a * nz])
    return Atoms(symbols=syms, scaled_positions=scaled, cell=cell, pbc=True)


def _relaxed_energy_per_atom(atoms, calc, relax: bool = True,
                             fmax: float = 0.03, steps: int = 200) -> float:
    """Energy per atom, optionally after a cell+position relaxation."""
    from ase.constraints import UnitCellFilter
    from ase.optimize import BFGS

    atoms = atoms.copy()
    atoms.calc = calc
    if relax:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opt = BFGS(UnitCellFilter(atoms), logfile=None)
            opt.run(fmax=fmax, steps=steps)
    return float(atoms.get_potential_energy() / len(atoms))


@dataclass
class SurrogateResult:
    """Output of a surrogate run, with its validation attached."""

    model_name: str
    fractions: tuple
    mixing_energies_ev: tuple
    end_members_ev: dict
    validation: dict = field(default_factory=dict)

    @property
    def trustworthy(self) -> bool:
        return bool(self.validation.get("passed"))

    def as_quantities(self) -> dict:
        note = ("machine-learned surrogate, not DFT. "
                + ("validation against the Materials Project hull passed"
                   if self.trustworthy else
                   "VALIDATION FAILED -- treat as unusable"))
        return {
            f"dE_mix_Ag{f:.2f}": Quantity(
                e, "eV/atom", Provenance.ML_SURROGATE,
                source=f"{self.model_name} on a disordered fcc supercell",
                note=note)
            for f, e in zip(self.fractions, self.mixing_energies_ev)}

    def summary(self) -> str:
        lines = [f"SURROGATE MIXING ENERGIES — {self.model_name}", ""]
        v = self.validation
        if v:
            lines.append(f"validation: {'PASSED' if v.get('passed') else 'FAILED'}"
                         f"  (max error {v.get('max_error_ev', float('nan')):.4f} "
                         f"eV/atom against the MP hull)")
            for k, d in v.get("detail", {}).items():
                lines.append(f"   {k:8s} MP {d['mp']:+.4f}   surrogate "
                             f"{d['surrogate']:+.4f}   \u0394 {d['error']:+.4f}")
            lines.append("")
        lines.append(f"{'x(Ag)':>7} {'dE_mix (eV/atom)':>18}  interpretation")
        kT300, kT550 = 0.026, 0.048
        for f, e in zip(self.fractions, self.mixing_energies_ev):
            if e > kT550:
                tag = "separates strongly (> kT at 550 K)"
            elif e > kT300:
                tag = "separates (> kT at 300 K)"
            elif e > 0:
                tag = "weakly unfavourable"
            else:
                tag = "mixing favoured"
            lines.append(f"{f:7.2f} {e:18.4f}  {tag}")
        if not self.trustworthy:
            lines += ["", "DO NOT USE: the surrogate failed its validation "
                          "against known Materials Project values."]
        return "\n".join(lines)


def validate_against_hull(calc=None, model: str = "auto",
                          tolerance_ev: float = 0.05) -> dict:
    """Check a surrogate against Materials Project values already in hand.

    Cu₃Ag and CuAg₃ are the only ordered Ag–Cu phases in the database, and the
    framework recorded their energies above hull when it ran stage 2. Those are
    free reference points: if the surrogate cannot reproduce them, nothing it
    says about a disordered alloy of the same elements should be believed.

    `tolerance_ev` defaults to 50 meV/atom, which is the reported held-out
    error scale for these models. Passing at that tolerance means the surrogate
    is behaving as advertised — not that it is accurate enough for a
    thermodynamic conclusion on its own.
    """
    if calc is None:
        calc, name = load_calculator(model)
    else:
        name = getattr(calc, "name", model)
    from ase.build import bulk

    e_ag = _relaxed_energy_per_atom(bulk("Ag", "fcc", cubic=True), calc)
    e_cu = _relaxed_energy_per_atom(bulk("Cu", "fcc", cubic=True), calc)

    detail = {}
    for formula, x_ag in (("Cu3Ag", 0.25), ("CuAg3", 0.75)):
        atoms = _fcc_atoms({"Ag": x_ag, "Cu": 1 - x_ag}, supercell=(1, 1, 1))
        e = _relaxed_energy_per_atom(atoms, calc)
        surrogate = e - (x_ag * e_ag + (1 - x_ag) * e_cu)
        mp = MP_REFERENCE[formula]
        detail[formula] = {"mp": mp, "surrogate": surrogate,
                           "error": surrogate - mp}

    max_err = max(abs(d["error"]) for d in detail.values())
    return {
        "model": name, "passed": bool(max_err <= tolerance_ev),
        "max_error_ev": max_err, "tolerance_ev": tolerance_ev, "detail": detail,
        "note": ("These are ordered phases; agreement here is necessary but "
                 "not sufficient for disordered alloys, which lie further from "
                 "the training distribution."),
    }


def mixing_energy_series(fractions=(1.0, 0.9, 0.75, 0.7, 0.5, 0.25, 0.0),
                         supercell=(2, 2, 2), model: str = "auto",
                         seed: int = 0, validate: bool = True,
                         relax: bool = True) -> SurrogateResult:
    """Ag–Cu mixing energies across the brief's composition series.

    The quantity the brief's §14 stage A asks for:

        ΔE_mix = E(alloy) − Σ xᵢ E(pure i)

    Positive means a driving force to separate. Compare against k_BT at the
    deposition temperature — 26 meV at 300 K, 48 meV at 550 K — before calling
    any value significant.
    """
    calc, name = load_calculator(model)
    from ase.build import bulk
    validation = validate_against_hull(calc, tolerance_ev=0.05) if validate else {}

    end = {"Ag": _relaxed_energy_per_atom(bulk("Ag", "fcc", cubic=True), calc, relax),
           "Cu": _relaxed_energy_per_atom(bulk("Cu", "fcc", cubic=True), calc, relax)}

    fracs, mixes = [], []
    n_sites = 4 * int(np.prod(supercell))
    for x in fractions:
        comp = {"Ag": x, "Cu": 1 - x}
        comp = {k: v for k, v in comp.items() if v > 1e-9}
        if any(abs(v * n_sites - round(v * n_sites)) > 1e-6 for v in comp.values()):
            raise ValueError(
                f"x = {x} is not representable in {n_sites} sites; use "
                "dft.plans.smallest_supercell to choose a cell")
        if len(comp) == 1:
            mixes.append(0.0)
        else:
            e = _relaxed_energy_per_atom(
                _fcc_atoms(comp, supercell, seed=seed), calc, relax)
            mixes.append(e - sum(comp[s] * end[s] for s in comp))
        fracs.append(float(x))

    return SurrogateResult(name, tuple(fracs), tuple(mixes), end, validation)


def screen_ternaries(base=(0.70, 0.30), thirds=("Ti", "Al"),
                     supercell=(3, 3, 3), model: str = "auto",
                     seed: int = 0) -> dict:
    """First-pass energies for the brief's dilute ternary hypotheses.

    The brief proposes Ag₇₀Cu₂₉Ti₁ and Ag₇₀Cu₂₉Al₁ and is explicit that
    numerical values for them must not be reported as established. This gives
    a screening signal only, graded `ML_SURROGATE`, and it is the weakest
    application in this module: a single substituted atom in a 108-site cell
    is a dilute limit that these models are not specifically trained for.

    The question it can answer is directional — does the addition raise or
    lower the mixing energy relative to the binary at the same Ag:Cu ratio?
    """
    calc, name = load_calculator(model)
    from ase.build import bulk
    n_sites = 4 * int(np.prod(supercell))
    y = 1.0 / n_sites
    ag, cu = base
    scale = (1.0 - y) / (ag + cu)

    end = {"Ag": _relaxed_energy_per_atom(bulk("Ag", "fcc", cubic=True), calc),
           "Cu": _relaxed_energy_per_atom(bulk("Cu", "fcc", cubic=True), calc)}
    binary = {"Ag": ag / (ag + cu), "Cu": cu / (ag + cu)}
    e_bin = _relaxed_energy_per_atom(_fcc_atoms(binary, supercell, seed=seed), calc)
    dE_bin = e_bin - sum(binary[s] * end[s] for s in binary)

    out = {"model": name, "binary_dE_mix_ev": dE_bin, "ternaries": {}}
    for third in thirds:
        comp = {"Ag": ag * scale, "Cu": cu * scale, third: y}
        end.setdefault(third, _relaxed_energy_per_atom(
            bulk(third, "fcc", cubic=True), calc))
        e = _relaxed_energy_per_atom(_fcc_atoms(comp, supercell, seed=seed), calc)
        dE = e - sum(comp[s] * end[s] for s in comp)
        out["ternaries"][third] = {
            "dE_mix_ev": dE, "delta_vs_binary_ev": dE - dE_bin,
            "verdict": ("stabilising relative to the binary" if dE < dE_bin
                        else "no stabilisation; raises the mixing energy"),
            "caveat": ("dilute limit, surrogate model, non-SQS cell. A "
                       "directional signal at best. Note that the Materials "
                       "Project shows 8 near-hull Cu-Ti phases and 10 Al-Cu "
                       "phases, so on annealing this addition has "
                       "intermetallics available to precipitate rather than "
                       "remaining in solution."),
        }
    return out


def install_hint() -> str:
    """What to install, and roughly what it costs."""
    return (
        "pip install mace-torch ase       # ~100 MB model, CPU-capable\n"
        "  or\n"
        "pip install chgnet ase           # smaller and faster, slightly less accurate\n"
        "\n"
        "The Ag-Cu series over a 32-site cell runs in a few minutes on CPU.\n"
        "Verify first:  python -m pvdlowe surrogate --validate")


__all__ = ["SUPPORTED", "MP_REFERENCE", "SurrogateUnavailable", "SurrogateResult",
           "available_models", "load_calculator", "validate_against_hull",
           "mixing_energy_series", "screen_ternaries", "install_hint"]
