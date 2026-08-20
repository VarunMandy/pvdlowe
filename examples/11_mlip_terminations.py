"""How much does the surface termination change the answer?

Example 10 ranked dielectrics by adatom wetting and took whichever slab the
generator returned first. For a polar surface that is a silent choice with
consequences: ZnO(0001) terminates on either a Zn plane or an O plane, and a
metal adatom sees very different chemistry in each case.

This runs every distinct termination of ZnO(0001), then extends the dielectric
comparison to GZO and ITO, which are in the candidate set but were never tested.

The question to answer: is the spread ACROSS terminations of one surface
smaller than the spread BETWEEN dielectrics? If not, example 10's ranking was
resolving termination choice rather than material.

    export MP_API_KEY=...
    python -u examples/11_mlip_terminations.py

Runtime: a few minutes per surface.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pvdlowe.ml import (MLIPSurrogate, termination_spread, validate_against_mp,
                        wetting_comparison)

sur = MLIPSurrogate()
print(f"backend: {sur.name}\n")

v = validate_against_mp(sur)
print("=== gate ===")
print(v.to_string(index=False))
print(f"verdict: {v.attrs['verdict']}\n")

print("=== ZnO(0001) terminations, Ag adatom ===")
COLS = ["termination", "n_terminations", "dE_wet_eV", "site_spread_eV",
        "n_slab_atoms", "regime"]
t = termination_spread(sur, "Ag", "AZO")
print(t[[c for c in COLS if c in t.columns]].to_string(index=False))
term_range = t.attrs.get("termination_range_eV")
print(f"\n{t.attrs.get('note', 'only one termination found')}")

print("\n=== full dielectric comparison, Ag ===")
DCOLS = ["dielectric", "proxy", "miller", "termination", "dE_wet_eV",
         "site_spread_eV", "reliable", "regime"]
ag = wetting_comparison(sur, "Ag", ("AZO", "GZO", "ITO", "SnO2", "TiO2", "Si3N4"))
print(ag[[c for c in DCOLS if c in ag.columns]].to_string(index=False))
print(f"\n{ag.attrs.get('verdict','')}")
if ag.attrs.get("failures"):
    print(f"failed: {ag.attrs['failures']}")

if term_range is not None and "dE_wet_eV" in ag:
    trusted = ag[ag.reliable] if "reliable" in ag else ag
    if len(trusted) > 1:
        between = float(trusted.dE_wet_eV.max() - trusted.dE_wet_eV.min())
        print(f"\nspread ACROSS ZnO terminations : {term_range:.3f} eV")
        print(f"spread BETWEEN dielectrics     : {between:.3f} eV")
        print("verdict: " + (
            "the dielectric ranking is resolving material, not termination."
            if term_range < 0.5 * between else
            "TERMINATION CHOICE DOMINATES. The dielectric ranking in example 10 "
            "cannot be trusted -- it reflects which slab the generator happened "
            "to return."))

print("\nMeasured ordering (Carretero, 10 nm Ag, emissivity, lower is better):")
print("  AZO 0.058  <  ZnO 0.064  <  SiAlNx 0.067  <  SnO2 0.083")
