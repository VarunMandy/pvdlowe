# Experimental roadmap

The framework exists to reduce experimental work, so this is the shortest
sequence of experiments that decides the project's direction. Each phase has
an explicit decision point; if a phase does not change what you do next,
it should not be run.

---

## Phase 0 — verification, before any deposition

**Cost:** two days of reading. **Highest value in the whole programme.**

1. Obtain the primary source for the AZO(40)/Cu/AZO(40) result (T_vis 87.7%,
   R_s 9.96 Ω/sq, ε 0.055). Confirm both numbers come from the same film and
   check whether the emissivity is normal or hemispherical. The brief's
   central recommendation depends entirely on this.
2. Obtain the source for the §7 resistivity table; determine whether the
   1.59 µΩ·cm silver entry is a measurement or a bulk reference.
3. Verify the remaining twelve claims in `docs/REFERENCES.md`. Set
   `verified: true` in `data/benchmarks.yaml` as you go.

**Decision:** if the Cu result holds, the programme is "can Ag-free reach Ag
performance?". If it does not, the programme reverts to "how much Ag can be
removed?". These are different projects.

## Phase 1 — calibrate the models against your own tool

**Cost:** roughly one week. Nothing downstream is quantitative without it.

| Run | Purpose |
|---|---|
| Ag thickness series, 6–20 nm, 2 nm steps, fixed AZO | fit specularity, grain-boundary reflection, percolation d_c |
| Cu thickness series, same | same, for Cu |
| AZO alone, 3 thicknesses | Hall for N and µ; ellipsometry for n, k |
| Ag and Cu, one thickness each | ellipsometry; replace the Rakić fits with measured optical constants |
| Rate calibration, one film per target | `SputterModel.calibrate()` |

Measure R_s (four-point probe), T(λ) 300–2500 nm, and FTIR reflectance
2.5–25 µm. Re-fit and re-run `python -m pvdlowe validate`.

**Decision:** if the calibrated model still under-predicts Cu sheet
resistance by a large factor (see FINDINGS §8), that gap is the real obstacle
to the Cu route, and Phase 3 becomes the priority.

## Phase 2 — settle the microstructure question

**Cost:** one deposition run plus one measurement.

Deposit AZO/Ag₇₀Cu₃₀/AZO at 10 nm from a co-sputtered or alloy target and
measure sheet resistance. The two hypotheses predict 6.4 Ω/sq (metastable
solid solution) versus 2.6 Ω/sq (segregated) — a gap far outside probe
resolution.

Confirm with XRD (one fcc peak set versus two) and, if available, TEM or
APT. Then anneal at 200, 300 and 400 °C and re-measure: a metastable solid
solution should show resistivity *falling* as Cu precipitates out.

**Decision:** which alloy model the rest of the programme uses. Almost every
downstream prediction depends on this, so it is worth doing before the
composition series rather than after.

## Phase 3 — why is sputtered Cu so resistive?

Run only if Phase 1 confirms the Cu discrepancy.

Vary, one at a time: base pressure before deposition; substrate temperature;
a 0.5 nm Ti or ZnO seed layer; deposition rate. Measure R_s and XPS depth
profile for oxygen content.

**Decision:** if better vacuum or a seed layer closes most of the gap, the Cu
route is an engineering problem and the programme should pursue it. If the
gap persists under clean conditions, it is intrinsic and silver reduction is
the right target after all.

## Phase 4 — composition and thickness series

Only now, with calibrated models and a settled microstructure.

Use `python -m pvdlowe silver` to generate the trade-off curve, then deposit
the three or four compositions the curve identifies as being near the knee —
not all seven. The framework's job is to make this series small.

Include the **Ti barrier variant (B1)** alongside the Ti ternary (T1). The
model predicts the barrier wins clearly (81.9 vs 75.9), and if that holds it
saves a great deal of work on the ternary route (FINDINGS §6).

## Phase 5 — process optimisation

`python -m pvdlowe doe -o runsheet.csv` generates a 16-run resolution-IV
screen over seven factors, plus centre points, randomised. Read the alias
structure before interpreting. Follow with a Box–Behnken response surface on
whichever two or three factors survive.

## Phase 6 — durability

Nothing in the framework predicts any of this. Thermal cycling to 300–500 °C,
damp heat (85 °C / 85% RH), Taber abrasion, adhesion by scratch or tape.
Silver-based Low-E coatings usually fail here rather than optically, and a
composition that wins on Phases 1–5 and fails Phase 6 is not a candidate.

---

## First-principles work, in parallel

The framework generates the inputs (`python -m pvdlowe dft -o dft/`), staged
so that expensive calculations are only run if cheap ones leave a question
open.

- **Stage A** — Ag–Cu mixing energies, 20-site cell, PBE and PBE+U. ~730
  core-hours. Answers "does the alloy want to exist?" Compare functionals;
  a mixing energy that changes sign between them is not a result.
- **Stage A2** — dilute ternaries, 108-site cell (1 at.% is not representable
  in anything smaller). ~440 core-hours.
- **Stage B** — AZO/metal interface slabs. Expensive, and where the genuine
  novelty is: the brief's §10 is right that interface energy matters more
  here than bulk alloy energy. Run only for compositions that survive Phase 4.
- **Stage C** — optical and elastic properties for the single selected
  composition. Last, and only after experiment confirms what the film is.

For publication-grade mixing energies, replace the seeded-shuffle supercells
with proper SQS structures from ATAT `mcsqs` or `icet`; the workflow is
otherwise unchanged.
