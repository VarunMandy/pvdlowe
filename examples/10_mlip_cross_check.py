"""Cross-check the mixing energies against a second interatomic potential.

MACE-MP-0 under-predicted both Materials Project hull distances by 20-40%,
and both in the same direction. With one model there is no way to tell whether
that bias is specific to MACE or inherited from the Materials Project data all
these potentials are trained on.

    Same bias in both  -> inherited from the training data; correct dE_mix
                          upward rather than treating it as a lower bound.
    Different biases   -> the spread between models is the real uncertainty,
                          and it is larger than either model's stated error.

**A caveat on independence.** CHGNet and MACE-MP-0 are trained on the same
Materials Project relaxation trajectories. Agreement therefore shows the bias
is *consistent*, not that it is absent. SevenNet is closer to independent but
is GPU-oriented; it is included here and skipped cleanly if unavailable.

    pip install mace-torch chgnet ase pymatgen mp-api
    export MP_API_KEY=...
    python -u examples/10_mlip_cross_check.py

Runtime: a few minutes per backend on CPU.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from pvdlowe.ml import (MLIPSurrogate, SurrogateUnavailable, mixing_energy_series,
                        validate_against_mp)

BACKENDS = ("mace", "chgnet", "sevenn")
gates, series, used = {}, {}, []

for backend in BACKENDS:
    try:
        sur = MLIPSurrogate(backend=backend)
    except (SurrogateUnavailable, Exception) as exc:      # noqa: BLE001
        print(f"--- {backend}: unavailable ({type(exc).__name__}), skipping")
        continue
    name = sur.name
    used.append(name)
    print(f"\n=== {name}: validation gate ===")
    g = validate_against_mp(sur)
    print(g[["formula", "mp_e_above_hull", "surrogate_formation",
             "abs_error"]].to_string(index=False))
    print(f"verdict: {g.attrs['verdict']}")
    gates[name] = g

    print(f"\n=== {name}: Ag-Cu mixing energy series ===")
    s = mixing_energy_series(sur)
    print(s[["Ag_fraction", "E_mix_eV_per_atom", "spread_eV",
             "vs_kT_300K"]].to_string(index=False))
    series[name] = s

if len(used) < 2:
    print(f"\nOnly {len(used)} backend(s) available — no cross-check possible.")
    raise SystemExit(0)

print("\n" + "=" * 68)
print("CROSS-CHECK")
print("=" * 68)

print("\nValidation error against the two known MP hull distances:")
rows = []
for name, g in gates.items():
    for _, r in g.iterrows():
        rows.append({"backend": name, "formula": r.formula,
                     "mp": r.mp_e_above_hull,
                     "surrogate": r.surrogate_formation,
                     "signed_error": round(r.surrogate_formation - r.mp_e_above_hull, 4)})
gate_df = pd.DataFrame(rows)
print(gate_df.to_string(index=False))

signs = gate_df.groupby("backend").signed_error.apply(lambda x: (x < 0).all())
print("\n  every backend under-predicts:", bool(signs.all()))
if signs.all():
    print("  -> the bias is shared, so it is inherited from the Materials Project")
    print("     training data rather than specific to one model. dE_mix values")
    print("     should be corrected upward, not merely read as lower bounds.")
else:
    print("  -> the backends disagree in sign; the spread between them is the")
    print("     honest uncertainty and is larger than either model claims.")

print("\nMixing energies compared:")
merged = None
for name, s in series.items():
    col = s[["Ag_fraction", "E_mix_eV_per_atom"]].rename(
        columns={"E_mix_eV_per_atom": name})
    merged = col if merged is None else merged.merge(col, on="Ag_fraction")
cols = [c for c in merged.columns if c != "Ag_fraction"]
merged["range_eV"] = (merged[cols].max(axis=1) - merged[cols].min(axis=1)).round(4)
print(merged.to_string(index=False))

peak_range = float(merged.range_eV.max())
print(f"\n  largest between-model spread: {peak_range:.4f} eV/atom")
print(f"  kT at 550 K (deposition)    : 0.0474 eV/atom")
print("\n  The section 5.6 conclusion is that dE_mix falls BELOW kT at")
print("  deposition for Ag 5-15 at.%. That conclusion survives if the")
print("  between-model spread is smaller than the margin, which at Ag 10%")
print("  is 0.0474 - 0.0258 = 0.0216 eV.")
print(f"  Spread {peak_range:.4f} vs margin 0.0216 -> "
      + ("conclusion HOLDS" if peak_range < 0.0216 else
         "conclusion is SENSITIVE to model choice; report the spread"))
