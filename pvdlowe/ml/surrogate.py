"""Machine-learning interatomic potentials as a DFT surrogate.

**These are not language models.** They are equivariant graph neural networks
trained on large sets of DFT calculations -- mostly the Materials Project's own
data -- that predict total energy and forces for an arbitrary arrangement of
atoms. MACE-MP-0, CHGNet, M3GNet and SevenNet are the common open ones. They
run on a laptop CPU in seconds where the DFT they approximate would take hours
on a cluster, and they need no VASP licence.

Reported accuracy on energies is of order 30-50 meV/atom against the DFT they
were trained on. That is worth holding next to the numbers in this project:
the Ag-Cu hull distances are 86-90 meV/atom, so a surrogate can resolve them,
but not comfortably. Anything at the 20 meV/atom scale is below the noise.

**What they can do here**

- Mixing energies across the Ag-Cu series. Metals on ordered or quasi-random
  supercells is the regime these models handle best.
- Adhesion and interface energies -- metal on AZO against metal on Si3N4.
  This bears directly on `docs/CARRETERO_COMPARISON.md`: the measured reason
  silver performs better on AZO is that it *grows* better there, and adhesion
  energy is the first-principles quantity behind that.
- Surface and grain-boundary energies, which bear on the nanocrystalline
  hypothesis in `docs/LITERATURE_CALIBRATION.md`.

**What they cannot do, at all**

Optical constants, dielectric functions, band gaps, emissivity. These models
predict energies and forces from atomic positions; they carry no electronic
structure. Every optical number in this framework must still come from the
transfer-matrix model or from measurement. A surrogate cannot replace §5 of
the report -- only §5.5 and parts of §6.

**Validation is not optional and is built in.** Two Ag-Cu hull distances are
already known from the Materials Project at DFT level: Cu3Ag at 0.0904 eV/atom
and CuAg3 at 0.0857. :func:`validate_against_mp` reproduces those with the
surrogate before any new prediction is trusted. If it cannot recover numbers
that are in its own training distribution, its extrapolations are worthless.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

#: Known Materials Project DFT results for validation. Retrieved 2026 via
#: mp_api; see docs/FINDINGS.md section 3.7.
MP_REFERENCE = {
    "mp-1184011": {"formula": "Cu3Ag", "e_above_hull": 0.0904},
    "mp-984351": {"formula": "CuAg3", "e_above_hull": 0.0857},
}

#: Backends in preference order. MACE-MP-0 is the most broadly validated for
#: metals and interfaces; CHGNet is lighter and includes magnetic moments;
#: M3GNet is the oldest and least accurate but the easiest to install.
BACKENDS = ("mace", "chgnet", "matgl", "sevenn")


class SurrogateUnavailable(RuntimeError):
    """No MLIP backend is installed."""


@dataclass
class MLIPSurrogate:
    """Uniform wrapper over whichever interatomic potential is installed.

    Deliberately does not fall back to an empirical potential if no MLIP is
    present. An EAM or Lennard-Jones result would look like the same kind of
    number and be far less trustworthy, and this framework's rule is that a
    missing value is better than a fabricated one.
    """

    backend: str = "auto"
    device: str = "cpu"
    _calc: object = field(default=None, repr=False)

    def __post_init__(self):
        self._calc = self._load()

    def _load(self):
        order = BACKENDS if self.backend == "auto" else (self.backend,)
        errors = {}
        for name in order:
            try:
                if name == "mace":
                    from mace.calculators import mace_mp
                    return mace_mp(model="medium", device=self.device,
                                   default_dtype="float64")
                if name == "chgnet":
                    from chgnet.model.dynamics import CHGNetCalculator
                    return CHGNetCalculator()
                if name == "matgl":
                    import matgl
                    from matgl.ext.ase import PESCalculator
                    return PESCalculator(
                        matgl.load_model("M3GNet-MP-2021.2.8-PES"))
                if name == "sevenn":
                    from sevenn.calculator import SevenNetCalculator
                    return SevenNetCalculator()
            except Exception as exc:                      # noqa: BLE001
                errors[name] = f"{type(exc).__name__}: {exc}"
        raise SurrogateUnavailable(
            "no ML interatomic potential available. Install one:\n"
            "  pip install mace-torch      # recommended\n"
            "  pip install chgnet\n"
            "  pip install matgl\n"
            f"attempts: {errors}")

    @property
    def name(self) -> str:
        return type(self._calc).__module__.split(".")[0]

    # -- core ------------------------------------------------------------
    def energy(self, atoms) -> float:
        """Total energy of an ASE Atoms object, eV."""
        atoms = atoms.copy()
        atoms.calc = self._calc
        return float(atoms.get_potential_energy())

    def relax(self, atoms, fmax: float = 0.02, steps: int = 200,
              cell: bool = True):
        """Relax positions, and optionally the cell.

        Cell relaxation matters for Ag-Cu: the 13% size mismatch means a
        Vegard's-law starting volume is a poor guess, and holding it fixed
        would put the strain energy into the mixing energy.
        """
        from ase.optimize import BFGS
        atoms = atoms.copy()
        atoms.calc = self._calc
        target = atoms
        if cell:
            try:
                from ase.filters import FrechetCellFilter
                target = FrechetCellFilter(atoms)
            except ImportError:
                from ase.constraints import ExpCellFilter
                target = ExpCellFilter(atoms)
        BFGS(target, logfile=None).run(fmax=fmax, steps=steps)
        return atoms, float(atoms.get_potential_energy())

    def energy_per_atom(self, atoms, relax: bool = True) -> float:
        if relax:
            atoms, e = self.relax(atoms)
        else:
            e = self.energy(atoms)
        return float(e / len(atoms))


# -- validation ----------------------------------------------------------
def validate_against_mp(surrogate: MLIPSurrogate) -> "pd.DataFrame":
    """Reproduce two known Materials Project hull distances.

    The gate before any new prediction is believed. Both structures are
    ordered Ag-Cu intermetallics that sit in the surrogate's training
    distribution, so failure here is disqualifying rather than merely
    disappointing.
    """
    import pandas as pd
    from pymatgen.io.ase import AseAtomsAdaptor
    from mp_api.client import MPRester
    import os

    rows = []
    with MPRester(os.environ["MP_API_KEY"]) as mpr:
        ends = {}
        for el, mid in (("Ag", "mp-124"), ("Cu", "mp-30")):
            st = mpr.get_structure_by_material_id(mid)
            ends[el] = surrogate.energy_per_atom(
                AseAtomsAdaptor.get_atoms(st * (2, 2, 2)))
        for mid, ref in MP_REFERENCE.items():
            st = mpr.get_structure_by_material_id(mid)
            atoms = AseAtomsAdaptor.get_atoms(st)
            e = surrogate.energy_per_atom(atoms)
            comp = st.composition.fractional_composition
            ref_e = sum(comp[el] * ends[str(el)] for el in comp)
            rows.append({
                "material_id": mid, "formula": ref["formula"],
                "mp_e_above_hull": ref["e_above_hull"],
                "surrogate_formation": round(e - ref_e, 4),
                "abs_error": round(abs((e - ref_e) - ref["e_above_hull"]), 4)})
    df = pd.DataFrame(rows)
    df.attrs["verdict"] = (
        "usable" if df.abs_error.max() < 0.05 else
        "NOT usable for this problem -- the errors are comparable with the "
        "86-90 meV/atom hull distances being measured")
    return df


# -- the questions worth asking ------------------------------------------
def mixing_energy_series(surrogate: MLIPSurrogate, fractions=None,
                         supercell=(2, 2, 2), seed: int = 0,
                         n_configs: int = 3) -> "pd.DataFrame":
    """Ag-Cu mixing energy across composition.

    Several random decorations per composition, reported with a spread. A
    single decoration is not a random solid solution, and the spread is the
    honest error bar on treating it as one.

        dE_mix = E(alloy) - sum_i x_i E(pure i)

    Positive means a driving force to separate. Compare the magnitude against
    k_B T at deposition -- 26 meV at 300 K, 48 meV at 550 K -- before calling
    it significant, and against the surrogate's own validation error from
    `validate_against_mp`.
    """
    import pandas as pd
    from ase import Atoms
    from ase.build import bulk

    fracs = np.asarray(fractions if fractions is not None
                       else (1.0, 0.9, 0.75, 0.5, 0.25, 0.1, 0.0), dtype=float)
    nx, ny, nz = supercell
    n_sites = 4 * nx * ny * nz

    ends = {el: surrogate.energy_per_atom(bulk(el, "fcc", cubic=True) * supercell)
            for el in ("Ag", "Cu")}
    rng = np.random.default_rng(seed)
    rows = []
    for x in fracs:
        n_ag = int(round(x * n_sites))
        if abs(x * n_sites - n_ag) > 1e-6:
            continue                       # not representable; skip honestly
        vals = []
        for _ in range(1 if n_ag in (0, n_sites) else n_configs):
            a = 0.5 * (4.085 + 3.615) if 0 < x < 1 else (4.085 if x else 3.615)
            cell = bulk("Ag", "fcc", a=x * 4.085 + (1 - x) * 3.615,
                        cubic=True) * supercell
            syms = ["Ag"] * n_ag + ["Cu"] * (n_sites - n_ag)
            rng.shuffle(syms)
            cell.set_chemical_symbols(syms)
            vals.append(surrogate.energy_per_atom(cell))
        e = float(np.mean(vals))
        ref = x * ends["Ag"] + (1 - x) * ends["Cu"]
        rows.append({
            "Ag_fraction": float(x), "n_configs": len(vals),
            "E_mix_eV_per_atom": round(e - ref, 4),
            "spread_eV": round(float(np.std(vals)), 4) if len(vals) > 1 else 0.0,
            "vs_kT_300K": round((e - ref) / 0.0259, 2),
        })
    df = pd.DataFrame(rows)
    df.attrs["note"] = ("compare E_mix against the surrogate's validation error "
                        "before interpreting; both are of order 0.03-0.05 eV")
    return df


def adhesion_energy(surrogate: MLIPSurrogate, metal: str = "Ag",
                    dielectric: str = "AZO", n_metal_layers: int = 4,
                    vacuum: float = 12.0) -> dict:
    """Work of adhesion for a metal film on a dielectric, J/m^2.

        W_adh = (E_metal_slab + E_oxide_slab - E_interface) / A

    Positive and larger means the metal binds more strongly and, other things
    equal, wets and coalesces better rather than islanding.

    **This is the quantity behind the nucleation finding.** Cueva & Carretero
    measured that silver performs better on AZO than on a nitride because it
    grows better there, and the framework now carries an empirical
    `metal_growth_factor` calibrated to that measurement. If a surrogate
    predicts a higher work of adhesion for Ag on AZO than on Si3N4, that
    supplies the mechanism the empirical factor currently lacks.

    **Treat the absolute value with suspicion.** MLIP training sets are
    dominated by bulk crystals; interfaces between a metal and an amorphous or
    defective oxide are far from that distribution, and the sputtered oxide in
    question is not the ordered crystal modelled here. The *ordering* between
    two dielectrics is more likely to survive than either number.
    """
    from ase.build import fcc111, add_adsorbate       # noqa: F401
    raise NotImplementedError(
        "interface construction requires a specific oxide surface termination, "
        "which is a modelling decision rather than a default. See "
        "examples/09_mlip_adhesion.py for a worked AZO(0001)/Ag(111) case, and "
        "state the termination and registry in any result.")


def what_mlips_cannot_do() -> dict:
    """The boundary, stated so it travels with the results."""
    return {
        "can": [
            "total energy and forces for a given atomic arrangement",
            "structural relaxation, including cell",
            "mixing and formation energies for metals and simple oxides",
            "surface, interface and grain-boundary energies, with caveats",
            "molecular dynamics for diffusion and coalescence, at some cost",
        ],
        "cannot": [
            "optical constants n and k -- no electronic structure at all",
            "dielectric function, band gap, plasma frequency",
            "emissivity, transmittance, sheet resistance",
            "anything this framework's transfer-matrix model computes",
        ],
        "unreliable": [
            "amorphous or heavily defective phases, under-represented in training",
            "metal/oxide interfaces far from the training distribution",
            "energy differences below about 30 meV/atom",
            "systems containing elements sparsely covered by the training set",
        ],
        "implication": (
            "a surrogate can address section 5.5 and parts of section 6 of the "
            "technical report. It cannot address section 5, because every "
            "number there is optical and these models carry no electrons."),
    }


__all__ = ["MLIPSurrogate", "SurrogateUnavailable", "BACKENDS", "MP_REFERENCE",
           "validate_against_mp", "mixing_energy_series", "adhesion_energy",
           "what_mlips_cannot_do"]
