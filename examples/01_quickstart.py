"""Evaluate a single coating and print its performance."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.optics.integrate import performance_summary
from pvdlowe.optics.stack import dmd

coating = dmd("Ag", metal_thickness_nm=12.0, tco_thickness_nm=40.0)
print(coating.describe())

for key, value in performance_summary(coating).items():
    if isinstance(value, float):
        print(f"  {key:28s} {value:10.4f}")
    else:
        print(f"  {key:28s} {value}")
