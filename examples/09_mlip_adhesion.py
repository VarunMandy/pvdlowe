"""Does adhesion energy explain the measured dielectric ordering?

Cueva & Carretero measured that silver on AZO gives lower emissivity than
silver on SiAlNx, and attributed it to silver growing more efficiently on AZO.
The framework encodes that as an empirical `metal_growth_factor` with no
mechanism attached. Work of adhesion is the first-principles quantity behind
"grows better", so if it follows the same ordering, the empirical factor
acquires a physical basis.

    pip install mace-torch ase pymatgen mp-api
    export MP_API_KEY=...
    python examples/09_mlip_adhesion.py

Runtime: a few minutes per interface on GPU, considerably longer on CPU.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.ml import (MLIPSurrogate, adhesion_comparison, validate_against_mp,
                        what_mlips_cannot_do)

sur = MLIPSurrogate()
print(f"backend: {sur.name}\n")

print("=== gate: reproduce two known MP hull distances ===")
v = validate_against_mp(sur)
print(v.to_string(index=False))
print(f"verdict: {v.attrs['verdict']}\n")

print("=== work of adhesion: Ag on four dielectrics ===")
ag = adhesion_comparison(sur, "Ag", ("AZO", "Si3N4", "SnO2", "TiO2"))
print(ag[["dielectric","proxy","miller","W_adh_J_per_m2",
          "lattice_mismatch_pct","n_atoms"]].to_string(index=False))
print(f"\n{ag.attrs.get('verdict','')}")
if ag.attrs.get("failures"):
    print(f"failed: {ag.attrs['failures']}")

print("\n=== and for copper, which is untested in the measurement ===")
cu = adhesion_comparison(sur, "Cu", ("AZO", "Si3N4"))
print(cu[["dielectric","W_adh_J_per_m2","lattice_mismatch_pct"]].to_string(index=False))
print(f"\n{cu.attrs.get('verdict','')}")

print("\nMeasured ordering to compare against (10 nm Ag, emissivity):")
print("  AZO 0.058  <  ZnO 0.064  <  SiAlNx 0.067  <  SnO2 0.083")
print("  lower emissivity = better growth, so adhesion should rank AZO highest")
print(f"\n{what_mlips_cannot_do()['implication']}")
