"""Machine-learned interatomic potentials as a surrogate for the DFT stages.

The brief's §12 asks for first-principles mixing energies across the Ag-Cu
series and §10 for AZO/metal interface energies. `pvdlowe.dft` generates VASP
inputs for both, but running them needs a licence and an HPC allocation
(`docs/VERTEX_AI.md` §DFT). This module offers the cheaper route.

**What these models are.** Universal machine-learning interatomic potentials --
CHGNet, MACE-MP-0, M3GNet, MatterSim -- are graph neural networks trained on
the same Materials Project DFT corpus this framework already queries. They
predict energy and forces for an arbitrary structure in milliseconds on a CPU,
against core-hours for the DFT they approximate. Reported accuracy on held-out
MP data is of order 30 meV/atom on energies, which is comparable to the
functional-choice uncertainty the brief itself flags in §6.

**What they are not.** They are not language models, and they do not reason
about chemistry -- they interpolate a potential-energy surface. More
importantly for this project, **they inherit the Materials Project's
limitations exactly**, because that is their training data: 0 K, ordered
crystalline phases, no kinetics. A surrogate cannot tell you whether a
magnetron-sputtered film is a metastable solid solution any more than the
convex hull could. It answers the equilibrium question faster, not a different
question.

**Where that still helps.** The equilibrium question is worth answering
properly, and DFT cost is why it usually is not. A surrogate makes tractable:

* a *composition sweep* rather than the five or six points a DFT budget allows,
  which is what §5.1's dilute-silver optimum needs to be checked against;
* *configurational averaging* over several random decorations per composition,
  which is the difference between a mixing energy and one supercell's mixing
  energy;
* *interface energies* over several terminations and registries, where the DFT
  plan in `dft/plans.py` could afford only one or two.

**What it cannot do at all.** Band gaps, dielectric functions and optical
constants require electronic structure, which these models do not compute. The
brief's §9 stage-2 transparency screen therefore still needs the Materials
Project or real DFT. Elastic constants are obtainable by finite differences but
are not implemented here.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

#: Models this module knows how to load, in order of preference. Each entry is
#: (import path, human label, install command).
BACKENDS = (
    ("chgnet", "CHGNet", "pip install chgnet"),
    ("mace", "MACE-MP-0", "pip install mace-torch"),
    ("matgl", "M3GNet", "pip install matgl"),
)

#: Rough energy MAE on held-out Materials Project data, meV/atom, as reported
#: by each model's authors. LITERATURE_UNVERIFIED -- used only to caveat the
#: output, never to weight it.
REPORTED_MAE_MEV = {"CHGNet": 30.0, "MACE-MP-0": 33.0, "M3GNet": 35.0}


class SurrogateUnavailable(RuntimeError):
    """No supported potential is installed."""


def available_backends() -> list:
    """Which surrogates can actually be loaded in this environment."""
    import importlib.util
    return [(mod, label, cmd) for mod, label, cmd in BACKENDS
            if importlib.util.find_spec(mod) is not None]


@dataclass
class Surrogate:
    """A loaded interatomic potential with a uniform interface.

    Deliberately thin. The point is not to abstract over the models but to
    make swapping them trivial, because **agreement between two independently
    trained potentials is the only cheap check on either of them.** A single
    surrogate result should not be reported; two agreeing results can be.
    """

    label: str = ""
    _calc: object = field(default=None, repr=False)

    @classmethod
    def load(cls, prefer: str | None = None) -> "Surrogate":
        avail = available_backends()
        if not avail:
            raise SurrogateUnavailable(
                "no ML potential installed. Install one of:\n  " +
                "\n  ".join(f"{c}   # {l}" for _, l, c in BACKENDS))
        if prefer:
            avail = [a for a in avail if prefer.lower() in a[0].lower()] or avail
        mod, label, _ = avail[0]

        if mod == "chgnet":
            from chgnet.model.dynamics import CHGNetCalculator
            calc = CHGNetCalculator()
        elif mod == "mace":
            from mace.calculators import mace_mp
            calc = mace_mp(model="medium", default_dtype="float64")
        else:
            import matgl
            from matgl.ext.ase import PESCalculator
            calc = PESCalculator(matgl.load_model("M3GNet-MP-2021.2.8-PES"))
        return cls(label=label, _calc=calc)

    # -- energies --------------------------------------------------------
    def energy_per_atom(self, atoms) -> float:
        """Total energy per atom, eV. `atoms` is an ASE Atoms object."""
        atoms = atoms.copy()
        atoms.calc = self._calc
        return float(atoms.get_potential_energy() / len(atoms))

    def relax(self, atoms, fmax: float = 0.05, steps: int = 200):
        """Relax geometry before taking an energy.

        Skipping this is the most common way a surrogate mixing energy comes
        out wrong: an unrelaxed Ag-Cu supercell carries the strain of a 13%
        size mismatch that relaxation would remove, and that strain energy is
        indistinguishable from a positive mixing energy.
        """
        from ase.optimize import BFGS
        from ase.filters import FrechetCellFilter
        atoms = atoms.copy()
        atoms.calc = self._calc
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opt = BFGS(FrechetCellFilter(atoms), logfile=None)
            opt.run(fmax=fmax, steps=steps)
        return atoms


def _fcc_atoms(composition: dict, supercell=(2, 2, 3), seed: int = 0):
    """Build an ASE Atoms fcc solid solution using the framework's decoration."""
    from ase import Atoms
    from ..dft.plans import FCC_LATTICE

    nx, ny, nz = supercell
    n_sites = 4 * nx * ny * nz
    a = sum(f * FCC_LATTICE.get(s, 4.0) for s, f in composition.items())

    basis = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]])
    pos = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                for b in basis:
                    pos.append((b + [i, j, k]) * a)
    pos = np.array(pos)

    syms = sorted(composition, key=lambda s: -composition[s])
    counts, rem = {}, n_sites
    for s in syms[:-1]:
        counts[s] = int(round(composition[s] * n_sites))
        rem -= counts[s]
    counts[syms[-1]] = rem
    if any(c < 0 for c in counts.values()):
        raise ValueError(f"{composition} not representable in {n_sites} sites")

    rng = np.random.default_rng(seed)
    order = rng.permutation(n_sites)
    labels = [None] * n_sites
    cur = 0
    for s in syms:
        for idx in order[cur:cur + counts[s]]:
            labels[idx] = s
        cur += counts[s]

    return Atoms(symbols=labels, positions=pos,
                 cell=[a * nx, a * ny, a * nz], pbc=True)


def mixing_energy_series(surrogate: Surrogate, fractions=None,
                         elements=("Ag", "Cu"), supercell=(2, 2, 3),
                         n_configs: int = 4, relax: bool = True,
                         progress=None) -> pd.DataFrame:
    """Mixing energy across a binary series, averaged over decorations.

        dE_mix(x) = <E(alloy)> - x*E(A) - (1-x)*E(B)

    `n_configs` random decorations are averaged per composition, and their
    spread is reported. **That spread is the number to look at first**: a
    mixing energy whose configurational scatter exceeds its own magnitude is
    not a result, it is one supercell's accident. A single-configuration DFT
    calculation cannot show you this, which is precisely why the surrogate is
    useful here even though it is less accurate per point.
    """
    a_el, b_el = elements
    fracs = np.asarray(fractions if fractions is not None
                       else np.round(np.arange(0.0, 1.001, 0.1), 3), dtype=float)

    ends = {}
    for el in elements:
        at = _fcc_atoms({el: 1.0}, supercell, seed=0)
        if relax:
            at = surrogate.relax(at)
        ends[el] = surrogate.energy_per_atom(at)

    rows = []
    for x in fracs:
        if x >= 1.0:
            comp = {a_el: 1.0}
        elif x <= 0.0:
            comp = {b_el: 1.0}
        else:
            comp = {a_el: float(x), b_el: float(1 - x)}
        energies = []
        for seed in range(n_configs if 0 < x < 1 else 1):
            try:
                at = _fcc_atoms(comp, supercell, seed=seed)
            except ValueError:
                continue
            if relax:
                at = surrogate.relax(at)
            energies.append(surrogate.energy_per_atom(at))
        if not energies:
            continue
        ref = x * ends[a_el] + (1 - x) * ends[b_el]
        e = np.array(energies)
        rows.append({
            f"{a_el}_fraction": float(x),
            "E_mix_eV_per_atom": round(float(e.mean() - ref), 5),
            "config_spread_eV": round(float(e.std()), 5),
            "n_configs": len(e),
            "E_mix_meV_per_atom": round(float((e.mean() - ref) * 1000), 2),
        })
        if progress:
            progress(rows[-1])

    df = pd.DataFrame(rows)
    df.attrs["model"] = surrogate.label
    df.attrs["reported_mae_meV"] = REPORTED_MAE_MEV.get(surrogate.label)
    df.attrs["note"] = (
        "Equilibrium quantity at 0 K. Does NOT predict the as-deposited "
        "microstructure of a sputtered film -- it predicts what the film wants "
        "to do when annealed. Compare the mixing energy against k_B T at "
        "deposition: 26 meV at 300 K, 48 meV at 550 K.")
    return df


def interpret(df: pd.DataFrame, temperature_k: float = 300.0) -> dict:
    """Turn a mixing-energy series into a statement about the alloy.

    Applies two tests the raw numbers do not: whether the signal exceeds the
    model's own stated error, and whether it exceeds thermal energy at the
    deposition temperature. A mixing energy that fails either is not evidence
    of anything.
    """
    if df.empty:
        return {"verdict": "no data"}
    kT = 8.617333e-5 * temperature_k * 1000.0      # meV
    mae = df.attrs.get("reported_mae_meV") or 30.0
    interior = df[(df.iloc[:, 0] > 0.02) & (df.iloc[:, 0] < 0.98)]
    if interior.empty:
        return {"verdict": "end members only"}

    peak = interior.loc[interior.E_mix_meV_per_atom.abs().idxmax()]
    mx = float(peak.E_mix_meV_per_atom)
    spread = float(interior.config_spread_eV.max() * 1000)

    if abs(mx) < max(mae, spread):
        verdict = ("indistinguishable from zero -- the signal is smaller than "
                   "the model error or the configurational scatter")
    elif mx > 0:
        verdict = "positive mixing energy: the system prefers to phase separate"
    else:
        verdict = "negative mixing energy: the mixed state is favoured"

    return {
        "model": df.attrs.get("model"),
        "peak_composition": float(peak.iloc[0]),
        "peak_E_mix_meV": mx,
        "max_config_spread_meV": round(spread, 1),
        "model_reported_mae_meV": mae,
        "kT_at_temperature_meV": round(kT, 1),
        "exceeds_model_error": bool(abs(mx) > mae),
        "exceeds_kT": bool(abs(mx) > kT),
        "verdict": verdict,
        "caveat": (
            "A surrogate trained on Materials Project data inherits its scope: "
            "0 K, ordered crystals, no kinetics. Agreement with the MP convex "
            "hull is therefore expected and is NOT independent confirmation. "
            "The only cheap independent check is a second, differently trained "
            "potential."),
    }


def cross_check(fractions=None, models=("chgnet", "mace"), **kwargs) -> dict:
    """Run the same series under two potentials and compare.

    The single most useful thing this module does. Universal potentials are
    trained on overlapping data but with different architectures and loss
    functions; where they agree, the result is probably a property of the
    training corpus rather than of one model's inductive bias. Where they
    disagree, neither should be quoted.
    """
    out, frames = {}, {}
    for m in models:
        try:
            s = Surrogate.load(prefer=m)
        except (SurrogateUnavailable, ImportError, Exception) as exc:
            out[m] = {"error": str(exc)[:160]}
            continue
        df = mixing_energy_series(s, fractions=fractions, **kwargs)
        frames[s.label] = df
        out[s.label] = interpret(df)

    if len(frames) >= 2:
        labels = list(frames)
        a, b = frames[labels[0]], frames[labels[1]]
        merged = a.merge(b, on=a.columns[0], suffixes=("_1", "_2"))
        diff = (merged.E_mix_meV_per_atom_1 - merged.E_mix_meV_per_atom_2).abs()
        out["agreement"] = {
            "models": labels,
            "max_abs_difference_meV": round(float(diff.max()), 1),
            "mean_abs_difference_meV": round(float(diff.mean()), 1),
            "consistent": bool(diff.max() < 40.0),
            "reading": ("the two potentials agree within their stated errors; "
                        "the result reflects the training corpus rather than "
                        "one model's bias"
                        if diff.max() < 40.0 else
                        "the potentials disagree by more than their stated "
                        "errors -- do not quote either without real DFT"),
        }
    out["frames"] = frames
    return out


def what_a_surrogate_cannot_answer() -> dict:
    """The scope limits, machine-readable, in the style of `not_predicted()`."""
    return {
        "can": ["total energy and forces for a given structure",
                "mixing energies across a composition sweep",
                "configurational averaging over decorations",
                "geometry relaxation",
                "interface and surface energies from slab totals",
                "relative stability of ordered phases"],
        "cannot": ["band gap, dielectric function, optical constants "
                   "(no electronic structure)",
                   "anything about a metastable sputtered microstructure "
                   "(0 K equilibrium only -- inherits the Materials Project's "
                   "scope, since that is the training data)",
                   "nucleation, wetting or grain growth -- the effects that "
                   "docs/CARRETERO_COMPARISON.md identifies as dominant",
                   "deposition kinetics, adhesion, durability",
                   "sheet resistance or emissivity of a thin film"],
        "bearing_on_this_project": (
            "The framework's two known failures -- the copper sheet-resistance "
            "discrepancy and the dielectric ordering -- are both "
            "microstructure effects. A surrogate does not address either. It "
            "makes the equilibrium thermodynamics cheap, which is worth having, "
            "but it is not the missing physics."),
    }


__all__ = ["BACKENDS", "REPORTED_MAE_MEV", "SurrogateUnavailable",
           "available_backends", "Surrogate", "mixing_energy_series",
           "interpret", "cross_check", "what_a_surrogate_cannot_answer"]
