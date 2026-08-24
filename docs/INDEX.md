# Documentation index

Fifteen documents, grouped by why you would open them.

## Start here

| File | What it is |
|---|---|
| [`SUMMARY.md`](SUMMARY.md) | Executive summary — the recommendation, six findings, and what must happen before any of it counts as a result |
| [`FINDINGS.md`](FINDINGS.md) | Full findings, organised by conclusion. The main document |
| [`../report/TECHNICAL_REPORT.md`](../report/TECHNICAL_REPORT.md) | The written report, 17 pages, for a supervisor |

## How the model works

| File | What it is |
|---|---|
| [`METHODOLOGY.md`](METHODOLOGY.md) | The physics implemented, the approximations made, and where each one breaks |
| [`PROVENANCE.md`](PROVENANCE.md) | The evidence-grading system, and why it is a type rather than a footnote |

## Evidence, and what checking it produced

Read in this order — each corrected something.

| File | What it established |
|---|---|
| [`REFERENCES.md`](REFERENCES.md) | All fourteen of the brief's claims and what became of each. Two are disputed |
| [`CARRETERO_COMPARISON.md`](CARRETERO_COMPARISON.md) | The measurement that **reversed** the dielectric finding and added `metal_growth_factor` |
| [`NUCLEATION_MECHANISM.md`](NUCLEATION_MECHANISM.md) | Why the underlayer changes the metal — and that it is the same effect as the copper discrepancy |
| [`LITERATURE_CALIBRATION.md`](LITERATURE_CALIBRATION.md) | Why no published scattering parameters explain the 8× copper gap |
| [`MLIP_MIXING_ENERGY.md`](MLIP_MIXING_ENERGY.md) | Ag–Cu mixing energies, and two nucleation calculations that failed |

## Doing the experiment

| File | What it is |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | The experimental programme, in dependency order |
| [`../experiments/BENCH_cu_series.md`](../experiments/BENCH_cu_series.md) | Printable bench procedure for the copper series |
| [`../experiments/PROTOCOL_cu_series.md`](../experiments/PROTOCOL_cu_series.md) | Pre-registered decision rules, written before any data exists |

## Development and deployment

| File | What it is |
|---|---|
| [`CODE_WALKTHROUGH.md`](CODE_WALKTHROUGH.md) | Guided tour of the implementation, with runnable blocks — for a handover session |
| [`CODE_REVIEW.md`](CODE_REVIEW.md) | Self-review: three medium findings, one new, four low, five things not to break |
| [`VERTEX_AI.md`](VERTEX_AI.md) | Running the framework, and the ML surrogate, on Google Cloud |

---

**One rule that applies to every results table in these documents:** a ranking
is meaningless without its weighting file. The heating and cooling profiles
disagree on the winner and on nine of ten top-ten positions. Always quote
`data/targets.yaml` or `data/targets_cooling.yaml` alongside.
