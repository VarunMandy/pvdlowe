"""Does adatom binding explain the measured dielectric ordering?

A better-posed question than the bulk adhesion attempt in example 09, which
failed because lattice matching a metal film to an oxide cell left 5-21%
strain and the calculation measured elastic energy rather than binding.

Nucleation is not about a continuous film's adhesion. It is about whether an
arriving adatom sticks to the oxide or prefers to join its own metal:

    dE_wet = E(slab + adatom) - E(slab) - E_bulk_per_atom

Negative means the atom prefers the oxide, so the film spreads (Frank-van der
Merwe). Positive means it prefers its own kind, so the film islands
(Volmer-Weber). A single adatom needs no lattice matching at all.

    pip install mace-torch ase pymatgen mp-api
    export MP_API_KEY=...
    python -u examples/08_mlip_wetting.py

Runtime: a few minutes per surface on CPU -- far cheaper than example 09.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.ml import (MLIPSurrogate, validate_against_mp, wetting_comparison,
                        what_mlips_cannot_do)

sur = MLIPSurrogate()
print(f"backend: {sur.name}\n")

print("=== gate: reproduce two known MP hull distances ===")
v = validate_against_mp(sur)
print(v.to_string(index=False))
print(f"verdict: {v.attrs['verdict']}\n")

COLS = ["dielectric", "proxy", "miller", "dE_wet_eV", "site_spread_eV",
        "n_sites_converged", "regime"]

print("=== silver: does it wet the oxide or island? ===")
ag = wetting_comparison(sur, "Ag", ("AZO", "Si3N4", "SnO2", "TiO2"))
print(ag[[c for c in COLS if c in ag.columns]].to_string(index=False))
print(f"\n{ag.attrs.get('verdict','')}")
if ag.attrs.get("failures"):
    print(f"failed: {ag.attrs['failures']}")

print("\n=== copper, untested in the measurement ===")
cu = wetting_comparison(sur, "Cu", ("AZO", "Si3N4"))
print(cu[[c for c in COLS if c in cu.columns]].to_string(index=False))
print(f"\n{cu.attrs.get('verdict','')}")

print("\nMeasured ordering to reproduce (10 nm Ag, emissivity, lower is better):")
print("  AZO 0.058  <  ZnO 0.064  <  SiAlNx 0.067  <  SnO2 0.083")
print("  better growth = more negative dE_wet, so AZO should rank first")
print("\nRead the ORDERING, not the magnitudes. The proxies are crystalline")
print("stand-ins for sputtered films, and beta-Si3N4 in particular is a poor")
print("analogy for an amorphous nitride.")
print(f"\n{what_mlips_cannot_do()['implication']}")
