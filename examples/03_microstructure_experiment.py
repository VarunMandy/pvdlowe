"""Design the experiment that settles the Ag-Cu microstructure question.

The two hypotheses predict sheet resistances 3-4 ohm/sq apart, which one
four-point-probe measurement can distinguish.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from pvdlowe.materials.alloys import ag_cu, discriminating_wavelengths
from pvdlowe.optimize.sweep import microstructure_comparison

print(microstructure_comparison().to_string(index=False))

print("\nWhere the optical constants diverge most:")
for x in (0.9, 0.7, 0.5):
    res = discriminating_wavelengths(ag_cu(x), np.linspace(400, 2500, 400))
    print(f"  Ag{x*100:.0f}: n at {res['n_max_wavelength_nm']:.0f} nm "
          f"(gap {res['n_relative_gap']:.1%}), "
          f"k at {res['k_max_wavelength_nm']:.0f} nm "
          f"(gap {res['k_relative_gap']:.1%})")
