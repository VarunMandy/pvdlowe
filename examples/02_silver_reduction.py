"""The brief's central question, as a trade-off curve.

For each Ag-Cu composition: the thinnest metal layer, with the oxides
re-optimised, that still meets the section 17 specification.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.optimize.thickness import silver_reduction_curve

df = silver_reduction_curve()
print(df.to_string(index=False))
print(f"\nspecification: {df.attrs['specification']}")
