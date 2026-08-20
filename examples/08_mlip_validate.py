"""Validate an ML interatomic potential before trusting it.

The gate: reproduce two Ag-Cu hull distances the Materials Project already
computed at DFT level. If the surrogate cannot recover numbers inside its own
training distribution, its predictions for anything else are not usable.

    pip install mace-torch ase pymatgen mp-api
    export MP_API_KEY=...
    python examples/08_mlip_validate.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.ml import MLIPSurrogate, validate_against_mp, mixing_energy_series

sur = MLIPSurrogate()
print(f"backend: {sur.name}\n")

df = validate_against_mp(sur)
print(df.to_string(index=False))
print(f"\nverdict: {df.attrs['verdict']}\n")

if df.abs_error.max() >= 0.05:
    print("Stopping. The surrogate's error is comparable with the 86-90 meV/atom")
    print("hull distances this project needs to resolve, so a mixing-energy")
    print("series from it would not be interpretable.")
    raise SystemExit(1)

print("=== Ag-Cu mixing energy series ===")
series = mixing_energy_series(sur)
print(series.to_string(index=False))
print(f"\n{series.attrs['note']}")
print("\nPositive E_mix means a driving force to separate. The Materials Project")
print("convex hull already says Ag-Cu has no stable ordered compound; this")
print("extends that to the disordered solid solution the sputtered film may be.")
