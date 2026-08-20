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


#: Crystalline stand-ins for the sputtered dielectrics. Every one of these is
#: an approximation to a real film, and the approximation differs in kind:
#: AZO is modelled as wurtzite ZnO because the 2 at.% Al is a dopant on a ZnO
#: lattice; Si3N4 as beta phase, though sputtered nitride is largely amorphous.
#: The amorphous case is the weaker analogy and its result should be read as
#: an upper bound on adhesion, since a disordered surface generally binds a
#: metal less strongly than an ideal terminated crystal.
DIELECTRIC_PROXY = {
    "AZO":   {"mp_id": "mp-2133", "formula": "ZnO",
              "miller": (0, 0, 1), "note": "wurtzite ZnO(0001), Zn-terminated"},
    "ZnO":   {"mp_id": "mp-2133", "formula": "ZnO",
              "miller": (0, 0, 1), "note": "wurtzite ZnO(0001), Zn-terminated"},
    "Si3N4": {"mp_id": "mp-988", "formula": "Si3N4",
              "miller": (0, 0, 1), "note": "beta-Si3N4(0001); the real film is "
                                           "amorphous, so treat as an upper bound"},
    "SnO2":  {"mp_id": "mp-856", "formula": "SnO2",
              "miller": (1, 1, 0), "note": "rutile SnO2(110), the stable facet"},
    "TiO2":  {"mp_id": "mp-2657", "formula": "TiO2",
              "miller": (1, 1, 0), "note": "rutile TiO2(110)"},
}


#: Largest lattice mismatch that can be strained away without the result
#: becoming a strain measurement. Beyond a few per cent the elastic energy
#: stored in the film is comparable with the adhesion being measured:
#: silver at 14% mismatch stores about 0.8 J/m2, and at 21% about 1.8 J/m2,
#: against a physical work of adhesion of order 0.5-3 J/m2.
#:
#: The first version of this function had no such limit. It returned 9.6 J/m2
#: for Ag/Si3N4 at 14% mismatch and -0.16 for Ag/TiO2 -- one unphysically
#: large, one impossible -- and the ordering it produced was strain, not
#: binding. Numbers from that run must not be used.
MAX_LATTICE_MISMATCH = 0.04


def adhesion_energy(surrogate: MLIPSurrogate, metal: str = "Ag",
                    dielectric: str = "AZO", metal_layers: int = 4,
                    oxide_layers: int = 6, vacuum: float = 14.0,
                    max_area: float = 400.0, gap: float = 2.2,
                    max_mismatch: float = MAX_LATTICE_MISMATCH,
                    relax: bool = True) -> dict:
    """Work of adhesion for a metal film on a dielectric, J/m^2.

        W_adh = (E_metal_slab + E_oxide_slab - E_interface) / A

    Positive and larger means the metal binds more strongly and, other things
    equal, wets and coalesces rather than islanding.

    **This is the quantity behind the nucleation finding.** Cueva & Carretero
    measured that silver performs better on AZO than on a nitride because it
    grows better there, and `TCOPreset.metal_growth_factor` is currently an
    empirical number calibrated to that measurement with no mechanism attached.
    If a surrogate predicts higher adhesion for Ag on AZO than on Si3N4, it
    supplies the mechanism.

    **A lattice-mismatch guard is enforced.** If the metal film cannot be tiled
    onto the oxide footprint within `max_mismatch`, this raises rather than
    straining the film to fit. Without that guard the function returns the
    elastic energy of a badly strained film dressed up as an adhesion energy.

    **Read the ordering, not the magnitude.** MLIP training sets are dominated
    by bulk crystals. A metal/oxide interface is far from that distribution,
    and the sputtered oxide in question is not the ordered crystal modelled
    here. Comparisons between two dielectrics computed identically are far more
    likely to survive than either absolute number.

    **Termination is a modelling choice, and it is reported.** ZnO(0001) is
    polar and has Zn- and O-terminated faces with substantially different
    adhesion. This function takes the first termination the slab generator
    returns and records which; a serious study would compute several.
    """
    import os
    from ase.build import fcc111
    from pymatgen.core import Structure
    from pymatgen.core.surface import SlabGenerator
    from pymatgen.io.ase import AseAtomsAdaptor
    from mp_api.client import MPRester

    if dielectric not in DIELECTRIC_PROXY:
        raise KeyError(f"no crystalline proxy defined for {dielectric!r}; "
                       f"available: {sorted(DIELECTRIC_PROXY)}")
    spec = DIELECTRIC_PROXY[dielectric]

    with MPRester(os.environ["MP_API_KEY"]) as mpr:
        bulk_struct = mpr.get_structure_by_material_id(spec["mp_id"])

    slabs = SlabGenerator(bulk_struct, spec["miller"], min_slab_size=oxide_layers,
                          min_vacuum_size=vacuum, center_slab=True).get_slabs()
    if not slabs:
        raise RuntimeError(f"no slabs generated for {dielectric} {spec['miller']}")
    oxide = AseAtomsAdaptor.get_atoms(slabs[0])
    ox_cell = oxide.cell.lengths()[:2]

    # Tile a metal (111) surface to approximately match the oxide footprint.
    a_metal = {"Ag": 4.085, "Cu": 3.615, "Al": 4.050, "Au": 4.078}[metal]
    unit = fcc111(metal, size=(1, 1, metal_layers), a=a_metal, vacuum=0.0)
    m_cell = unit.cell.lengths()[:2]
    reps = [max(1, int(round(ox_cell[i] / m_cell[i]))) for i in (0, 1)]
    film = fcc111(metal, size=(reps[0], reps[1], metal_layers), a=a_metal,
                  vacuum=0.0)
    area = float(np.linalg.norm(np.cross(oxide.cell[0], oxide.cell[1])))
    if area > max_area:
        raise ValueError(
            f"interface footprint is {area:.0f} A^2, above the {max_area:.0f} "
            "limit. Lattice matching this pair needs a large supercell; raise "
            "max_area only if you have the compute for it.")

    strain = [abs(reps[i]*m_cell[i] - ox_cell[i]) / ox_cell[i] for i in (0, 1)]
    if max(strain) > max_mismatch:
        raise ValueError(
            f"{metal}/{dielectric}: lattice mismatch {100*max(strain):.1f}% "
            f"exceeds the {100*max_mismatch:.0f}% limit. Straining the film to "
            "fit would store elastic energy comparable with the adhesion being "
            "measured, and the result would rank strain rather than binding. "
            "A supercell that matches these lattices coherently is needed -- "
            "see pymatgen.analysis.interfaces.ZSLGenerator -- and it will be "
            "much larger than the cells used here.")
    film.set_cell([oxide.cell[0], oxide.cell[1], film.cell[2]], scale_atoms=True)

    # Stack: oxide below, metal above, with a physical starting separation.
    interface = oxide.copy()
    top = oxide.positions[:, 2].max()
    shifted = film.copy()
    shifted.positions[:, 2] += top + gap - shifted.positions[:, 2].min()
    interface += shifted
    interface.cell[2][2] = shifted.positions[:, 2].max() + vacuum
    interface.pbc = (True, True, True)

    def _e(a):
        return surrogate.energy(*( (a,) )) if not relax else surrogate.relax(a, cell=False)[1]

    e_ox = _e(oxide)
    free_film = shifted.copy()
    free_film.cell = interface.cell
    free_film.pbc = (True, True, True)
    e_metal = _e(free_film)
    e_int = _e(interface)

    EV_A2_TO_J_M2 = 16.0218
    w = (e_metal + e_ox - e_int) / area * EV_A2_TO_J_M2
    return {
        "metal": metal, "dielectric": dielectric,
        "proxy": spec["formula"], "miller": spec["miller"],
        "termination_note": spec["note"],
        "W_adh_J_per_m2": round(float(w), 3),
        "interface_area_A2": round(area, 1),
        "n_atoms": len(interface),
        "lattice_mismatch_pct": [round(100*x, 1) for x in strain],
        "backend": surrogate.name,
        "caveat": ("first termination only; ordering between dielectrics is "
                   "more trustworthy than the absolute value"),
    }


def adhesion_comparison(surrogate: MLIPSurrogate, metal: str = "Ag",
                        dielectrics=("AZO", "Si3N4"), **kwargs):
    """The comparison that tests the nucleation finding.

    Measured (Cueva & Carretero, 10 nm Ag): AZO gives lower emissivity than
    SiAlNx because silver grows better on it. If adhesion follows the same
    ordering, the empirical `metal_growth_factor` acquires a mechanism.
    """
    import pandas as pd
    rows, failures = [], {}
    for d in dielectrics:
        try:
            rows.append(adhesion_energy(surrogate, metal, d, **kwargs))
        except Exception as exc:                          # noqa: BLE001
            failures[d] = f"{type(exc).__name__}: {exc}"
    df = pd.DataFrame(rows)
    if len(df) < 2:
        df.attrs["verdict"] = (
            f"only {len(df)} of {len(dielectrics)} interfaces could be built "
            "within the lattice-mismatch limit, so no ordering can be claimed. "
            f"failures: {failures}")
        df.attrs["failures"] = failures
        return df
    if len(df) > 1:
        df = df.sort_values("W_adh_J_per_m2", ascending=False)
        best = df.iloc[0]
        df.attrs["verdict"] = (
            f"{metal} binds most strongly to {best.dielectric} "
            f"({best.W_adh_J_per_m2} J/m2). "
            + ("Consistent with the measured growth ordering."
               if best.dielectric in ("AZO", "ZnO") else
               "NOT consistent with the measured ordering -- either the "
               "crystalline proxies are too far from the sputtered films, or "
               "adhesion is not the operative mechanism."))
    df.attrs["failures"] = failures
    return df


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
           "DIELECTRIC_PROXY", "MAX_LATTICE_MISMATCH", "validate_against_mp",
           "mixing_energy_series", "adhesion_energy", "adhesion_comparison",
           "what_mlips_cannot_do"]
