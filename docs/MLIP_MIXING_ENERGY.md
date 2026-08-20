# Ag–Cu mixing energies from an ML interatomic potential

**Computed** on Vertex AI Workbench with MACE-MP-0 (medium, float64), 32-site
fcc supercells, three random decorations per composition, cell and positions
relaxed. Reproduce with `python examples/08_mlip_validate.py`.

**Grade:** `MODEL`. A surrogate for DFT, not DFT, and its error is quantified
below rather than assumed.

---

## 1. The validation gate

Before any prediction, the surrogate was required to reproduce two Materials
Project results computed at DFT level:

| | MP (DFT) | MACE | error |
|---|---|---|---|
| Cu₃Ag | 0.0904 | 0.0719 | 0.0185 |
| CuAg₃ | 0.0857 | 0.0517 | 0.0340 |

Passed, but **read the margin.** MACE under-predicts both by 20–40%, and both
errors point the same way — that is a systematic bias, not scatter. Every
number below should be treated as a lower bound, with a plausible true value
20–40% higher.

## 2. The series

| Ag fraction | ΔE_mix (eV/atom) | spread | ×kT (300 K) |
|---|---|---|---|
| 1.00 | 0.0000 | 0.0000 | — |
| 0.75 | 0.0479 | 0.0030 | 1.85 |
| 0.50 | **0.0721** | 0.0011 | 2.78 |
| 0.25 | 0.0591 | 0.0043 | 2.28 |
| 0.00 | 0.0000 | 0.0000 | — |

End members return exactly zero, which is the arithmetic working. The spread
across three random decorations is 1–4 meV/atom — an order of magnitude below
the signal, so the configurational sampling is converged even without proper
SQS structures.

**A regular-solution model fits within ±6 meV/atom:**

```
dE_mix = 0.287 · x · (1 − x)      eV/atom
```

## 3. What this adds to the Materials Project result

FINDINGS §3.7 established from the convex hull that Ag–Cu has **no stable
ordered compound**. That is an equilibrium statement about *ordered* phases,
and a sputtered film is neither ordered nor at equilibrium.

This extends it to the **disordered solid solution** the film might actually
be. ΔE_mix is positive across the whole range, so the disordered alloy is also
unstable against separation into pure phases.

**And the surrogate is internally consistent on the point that matters.** At
Ag 25 at.%, it gives 0.0719 eV/atom for the *ordered* Cu₃Ag compound and
0.0591 for the *disordered* solution — the disordered state is 13 meV/atom
**lower**. There is no ordering tendency at all, which is exactly what an
empty convex hull implies, arrived at by a different route.

## 4. The finding that matters for the design

Driving force against thermal energy, from the fitted model:

| Ag at.% | ΔE_mix | ×kT (300 K) | ×kT (550 K) | ×kT (673 K) |
|---|---|---|---|---|
| 90 | 0.0258 | 1.00 | 0.54 | 0.45 |
| 70 | 0.0602 | 2.33 | 1.27 | 1.04 |
| 50 | 0.0717 | 2.77 | 1.51 | 1.24 |
| 30 | 0.0602 | 2.33 | 1.27 | 1.04 |
| **15** | **0.0366** | 1.41 | **0.77** | 0.63 |
| **10** | **0.0258** | 1.00 | **0.54** | 0.45 |
| **5** | **0.0136** | 0.53 | **0.29** | 0.23 |

**In the dilute-silver corner the driving force to separate falls below
thermal energy at deposition.** At Ag 5–15 at.% it is 0.3–0.8 kT at 550 K,
against 1.3–1.5 kT at the brief's Ag₇₀Cu₃₀.

This is an independent corroboration of §3.1. That section found the two
microstructure hypotheses converge in the dilute corner — 2.5 score points
apart at Ag₅Cu₉₅ against 9–14 at Ag₇₀Cu₃₀ — and treated that as a robustness
argument. **The thermodynamics now supply the reason:** at 5–15 at.% Ag there
is barely any driving force to segregate, so the film is far more likely to
stay as deposited, and it matters much less which hypothesis is right.

The dilute-silver optimum is therefore favoured on three separate grounds:
lowest silver consumption, best score under the corrected weighting, and now
the weakest thermodynamic tendency to phase-separate.

## 5. What it says about the microstructure experiment

Even at the 50:50 peak the driving force is only ~1.5 kT at 550 K. That is
modest. A magnetron-sputtered film quenched from the vapour can plausibly trap
a metastable solid solution against a driving force of that size.

**So both microstructure hypotheses remain physically viable**, which
retrospectively justifies the framework modelling both rather than choosing.
It also sharpens the prediction for the annealing experiment in §8.3: the
driving force is real but not overwhelming, so precipitation on annealing
should be observable but may need elevated temperature or extended time rather
than appearing immediately.

## 6. Limitations

- **Systematic under-prediction of 20–40%**, established by the gate. Correct
  the peak upward and ΔE_mix is 0.086–0.101 eV/atom.
- **Random decorations, not SQS.** The spread is small, but a seeded shuffle
  does not match the correlation functions of a truly random alloy. ATAT
  `mcsqs` or `icet` would settle it.
- **0 K energies, no vibrational or configurational entropy.** Configurational
  entropy at 550 K contributes roughly kT·ln2 ≈ 33 meV/atom at 50:50, which is
  comparable with ΔE_mix itself and would stabilise the solution further.
  Including it would push the mixing free energy toward zero across the range,
  strengthening §4's conclusion rather than weakening it.
- **32-site cells.** Adequate for a mixing energy; too small for anything
  involving clustering or short-range order.

## 7. What the same tooling could not do

An attempt at metal/dielectric adhesion energies with the same surrogate
**failed and produced no usable result** — lattice mismatches of 5–21% meant
the calculation measured elastic strain rather than binding, returning
9.6 J/m² for Ag/Si₃N₄ and −0.16 J/m² for Ag/TiO₂. Neither is physical. The
module now raises above 4% mismatch rather than returning such numbers.

Mixing energies sit in the regime these models handle best — bulk metals,
ordered supercells, no surfaces. Interfaces do not.
