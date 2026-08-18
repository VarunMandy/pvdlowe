"""Check the brief's own numbers against physics."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.validate import report

print(report())
