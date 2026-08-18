"""Generate a randomised sputter run sheet with centre points."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.doe.design import alias_structure, recommended_screening

design = recommended_screening()
sheet = design.with_run_sheet(seed=42)
sheet.to_csv("runsheet.csv", index=False)

print(f"{design.kind}, resolution {design.resolution}")
print(f"{len(sheet)} runs written to runsheet.csv\n")
print(sheet.head(10).to_string(index=False))
print("\nAlias structure -- read before interpreting results:")
print(alias_structure(design).to_string(index=False))
