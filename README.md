# pvdlowe

A computational screening and optimisation framework for sustainable
low-emissivity PVD coatings on float glass, implementing the workflow set out
in `PVD_Usecase.docx`: element screening → Materials Project → optical
multilayer modelling → design of experiments → multi-objective ranking.

The central research question it exists to answer is the brief's own: **how
much silver can be removed from an AZO/Ag/AZO Low-E stack before the visible
transmittance, sheet resistance or far-infrared reflectance stops meeting
specification?**

---

## What it does

```bash
python -m pvdlowe evaluate          # score every candidate architecture
python -m pvdlowe evaluate --targets data/targets_cooling.yaml   # cooling climate
python -m pvdlowe series            # composition series, geometry re-optimised
python -m pvdlowe silver            # the silver-reduction trade-off curve
python -m pvdlowe optimise --metal Ag
python -m pvdlowe validate          # model vs literature + consistency checks
python -m pvdlowe check-weights     # criteria independence, and a weight sweep
python -m pvdlowe calibrate --runsheet out.csv   # sputter run sheet
python -m pvdlowe surrogate         # Ag-Cu mixing energies from an MLIP
python -m pvdlowe doe -o runsheet.csv
python -m pvdlowe dft -o dft/
python -m pvdlowe report -o report.md
```

```python
from pvdlowe.optics.stack import dmd
from pvdlowe.optics.integrate import performance_summary

coating = dmd("Ag", metal_thickness_nm=12.0, tco_thickness_nm=40.0)
print(performance_summary(coating))
# T_vis 0.855, emissivity_normal 0.041, R_sheet 3.18 ohm/sq, U_g 1.13 W/m2K
```

## Installation

Pure Python. Requires `numpy`, `scipy`, `pandas`, `pyyaml`; `matplotlib` for
plots and `openpyxl` for Excel export are optional. Nothing needs to be
compiled and nothing needs network access to run.

```bash
python tests/run_tests.py     # 126 tests, no pytest required
pytest tests/                 # identical, if pytest is available
```

## What it found

Six substantive results, in descending order of confidence. Full account in
`docs/SUMMARY.md`.

| | Finding |
|---|---|
| 1 | **The climate decides the answer**, and the brief does not specify one. The two top-ten lists share one candidate out of ten. |
| 2 | **The composition optimum is 5–15 at.% Ag, not the brief's 70%** — supported on three independent grounds. |
| 3 | **No single-metal architecture reaches solar-control performance.** Best LSG is 1.37 against ~2.0 commercial; two metal layers reach 1.76. |
| 4 | **Six defects in the proposed weighting**, one of which let the optimiser return **29% more silver than the incumbent at a perfect score**. |
| 5 | **Two citations cannot be traced to any source**, and one measurement contradicts a model-independent electrodynamic limit. |
| 6 | **The dielectric changes the metal, not just the interference stack** — confirmed by TEM in the patent literature, and the cause of the framework's largest error. |

**A ranking is meaningless without its weighting file.** The heating and
cooling profiles disagree on the winner and on nine of ten top-ten positions,
and the silver weight alone moves the winner three times across a plausible
range. Always quote `data/targets.yaml` or `data/targets_cooling.yaml`
alongside, and run `pvdlowe check-weights` to see the sweep.

## Scope — read this before using any number

Every performance figure this framework produces is a **model output**. In
particular:

- **Optical constants** come from published Lorentz-Drude fits (Rakić et al.
  1998), with the free-electron damping re-anchored to DC resistivity. In the
  far infrared, where emissivity lives, this is reliable: the response is
  pure Drude and pinned to a measured resistivity. In the visible it is good
  to a few per cent at best. Substitute your own ellipsometry via
  `TabulatedIndex` if visible accuracy matters.
- **Thin-film resistivity** uses Fuchs–Sondheimer and Mayadas–Shatzkes with a
  fitted specularity and grain-boundary reflection. These are fitting
  parameters. Re-fit them to a measured R_s-versus-thickness series before
  trusting an absolute sheet resistance.
- **Percolation thresholds** are calibrated to two literature values (Ag
  continuous near 10 nm, Cu near 11 nm) transcribed from the brief. Neither
  has been checked against its primary source.
- **Prices** are estimates with an as-of date and move by more than a factor
  of two. `price_sensitivity()` exists for this reason.
- **Deposition rates** are refused outright until calibrated against a
  measurement on your own tool. Ratios between materials are available
  without calibration; absolute rates are not.

The framework is a tool for ranking candidates and designing experiments. It
does not replace depositing the films.

## What it deliberately will not predict

`pvdlowe.screening.candidates.not_predicted()` returns the list, and
`python -m pvdlowe provenance` prints it. Briefly: deposition rate, adhesion,
roughness, film continuity beyond the calibrated percolation model,
interdiffusion, thermal durability, and anything about a sputtered
metastable alloy that a 0 K ordered-crystal database cannot know.

## Provenance

Every physical quantity carries a `Provenance` grade — `MEASURED`,
`LITERATURE`, `LITERATURE_UNVERIFIED`, `MP_API`, `DFT_OWN`, `MODEL`,
`CALIBRATED`, `ESTIMATE`, `HYPOTHESIS` — and `assert_reportable()` refuses to
let a `HYPOTHESIS`-grade number into a headline table without an explicit
opt-in. This is the brief's own caution ("do not put numerical DFT values for
Ag₇₀Cu₂₉Ti₁ into a thesis as if they were established facts") implemented as
a type rather than a footnote.

The brief's citations were LLM-surfaced — every URL carried
`utm_source=chatgpt.com` — so all began as `LITERATURE_UNVERIFIED`. Checking
them changed eight of the fourteen:

| State | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — source located, abstract confirmed | 5 |
| **Disputed — figures appear in no locatable source; do not cite** | **2** |
| Supported — corroborated independently | 2 |
| Not pursued | 4 |

Two of the brief's transcribed values also fail model-independent consistency
checks, and one of those carries the brief's central recommendation. Run
`python -m pvdlowe validate`. Full account in `docs/REFERENCES.md` and
`docs/FINDINGS.md` §1.

## Package layout

| Module | Contents |
|---|---|
| `materials/` | dispersion models, metals, alloys, TCOs, float glass |
| `optics/` | transfer-matrix solver, stacks, EN 410 / EN 673 / ISO 9050 integration |
| `electrical/` | Fuchs–Sondheimer, Mayadas–Shatzkes, percolation |
| `screening/` | element filter, Derringer–Suich scoring, Pareto, candidates |
| `mp/` | Materials Project client (cached, network-gated) and stage-2 screening |
| `dft/` | VASP input generation, mixing and interface energies |
| `doe/` | factorial and response-surface designs, sputter rate model |
| `optimize/` | thickness optimisation, sweeps, composition series |
| `ml/` | ML interatomic potential surrogate (optional, needs `mace-torch`) |
| `characterise/` | predicted XRD signatures for the experiments in `experiments/` |
| `report/` | tables, plots, markdown/CSV/Excel export |
| `validate.py` | model-vs-literature and internal-consistency checks |

## Documentation

Full index: [`docs/INDEX.md`](docs/INDEX.md). Read in this order:

1. **`docs/SUMMARY.md`** — executive summary: the recommendation, six findings,
   and what must happen before any of it counts as a result
2. **`docs/FINDINGS.md`** — full findings, organised by conclusion: evidence
   audit, method audit, design-space results, limitations, corrections
3. `docs/METHODOLOGY.md` — the physics, the approximations, and where they break
4. `docs/METHODOLOGY.md` — the physics, the approximations, and where they break

**Evidence and verification**

- `docs/REFERENCES.md` — all fourteen of the brief's claims, with what became of each
- `docs/PROVENANCE.md` — the evidence-grading system
- `docs/CARRETERO_COMPARISON.md` — the measurement that reversed the dielectric finding
- `docs/NUCLEATION_MECHANISM.md` — why the underlayer changes the metal, resolved from literature
- `docs/LITERATURE_CALIBRATION.md` — why no published scattering parameters explain the copper gap
- `docs/MLIP_MIXING_ENERGY.md` — Ag–Cu mixing energies, and two failed nucleation calculations

**Practical**

- `docs/ROADMAP.md` — the experimental programme this is meant to feed
- `docs/CODE_REVIEW.md` — self-review: three medium findings, one new, four low
- `docs/VERTEX_AI.md` — running it on Google Cloud Vertex AI
- `experiments/BENCH_cu_series.md` — printable bench procedure
- `experiments/PROTOCOL_cu_series.md` — pre-registered decision rules
