# pvdlowe

**Computational screening of sustainable low-emissivity PVD coatings on float
glass.** Built at Saint-Gobain Research India to execute a materials-by-design
brief, and used to audit that brief's method and evidence.

9,586 lines · 136 tests · 38 candidate architectures · no external services
required for the core.

---

## What it found

Six results, in descending order of confidence. Full account in
[`docs/SUMMARY.md`](docs/SUMMARY.md) and [`docs/FINDINGS.md`](docs/FINDINGS.md).

| | Finding |
|---|---|
| 1 | **The climate decides the answer**, and the brief does not specify one. The two top-ten lists share one candidate out of ten. |
| 2 | **The composition optimum is 5–15 at.% Ag, not the brief's 70%** — supported on three independent grounds. |
| 3 | **No single-metal architecture reaches solar control.** Best LSG is 1.37 against ~2.0 commercial; two metal layers reach 1.76. |
| 4 | **Six defects in the proposed weighting**, one of which let the optimiser return **29% more silver than the incumbent at a perfect score**. |
| 5 | **Two citations cannot be traced to any source**, and one measurement contradicts a model-independent electrodynamic limit. |
| 6 | **The dielectric changes the metal, not just the interference stack** — confirmed by TEM in the patent literature, and the cause of the framework's largest error. |

**And the answer to the question as literally asked:** thinning the silver in
AZO/Ag/AZO, holding everything else, buys **about half a nanometre** before
percolation. The 86% reduction comes from changing the *composition*, not the
thickness.

> **A ranking is meaningless without its weighting file.** The heating and
> cooling profiles disagree on the winner and on nine of ten top-ten positions,
> and the silver weight alone moves the winner three times across a plausible
> range. Always quote `data/targets.yaml` or `data/targets_cooling.yaml`
> alongside, and run `pvdlowe check-weights` to see the sweep.

---

## Scope — read this before using any number

**No films were deposited.** Every performance figure is a model output. Median
error against traceable literature is **30.6%**.

**The framework's largest known error is an approximately eightfold
under-prediction of sputtered copper sheet resistance**, and six of the leading
candidates are copper-based. §6 of the technical report specifies the experiment
that resolves it.

**The principal structural weakness**, because it governs the rest: the framework
models each metal layer as though the layer beneath it did not shape its
microstructure. That single omission accounts for both the empirical
`metal_growth_factor` and the copper discrepancy — one effect appearing twice.
See [`docs/NUCLEATION_MECHANISM.md`](docs/NUCLEATION_MECHANISM.md).

**Percolation thresholds** are taken from literature and one of them is
contested: a patent read in full claims continuous silver down to **8 nm** on a
ZnO seed, against the **10 nm** assumed here — a 20% difference that would move
every silver-consumption figure.

---

## Install and run

```bash
git clone https://github.com/VarunMandy/pvdlowe.git && cd pvdlowe
pip install -e .
python tests/run_tests.py     # 136 tests, no pytest required
```

Core dependencies are numpy, scipy, pandas and PyYAML. Optional extras:
`pip install -e ".[mp]"` for Materials Project access, `".[ml]"` for the
interatomic-potential surrogate, `".[api]"` for the HTTP interface.

### Thirty seconds

```python
import pvdlowe

coating = pvdlowe.dmd("Ag", metal_thickness_nm=10.0)
print(pvdlowe.performance_summary(coating))
# T_vis 0.876, emissivity_hemispherical 0.060, R_sheet 4.18 ohm/sq, U_g 1.18
```

### Command line

```bash
python -m pvdlowe screen            # element and compound pre-screen
python -m pvdlowe evaluate          # score every candidate architecture
python -m pvdlowe evaluate --targets data/targets_cooling.yaml   # cooling climate
python -m pvdlowe series            # composition series, geometry re-optimised
python -m pvdlowe sweep             # thickness sweep at fixed composition
python -m pvdlowe silver            # the silver-reduction trade-off curve
python -m pvdlowe optimise --metal Ag
python -m pvdlowe validate          # model vs literature, plus consistency checks
python -m pvdlowe check-weights     # criteria independence, and a weight sweep
python -m pvdlowe calibrate --runsheet out.csv
python -m pvdlowe surrogate         # Ag-Cu mixing energies from an MLIP
python -m pvdlowe doe -o runsheet.csv
python -m pvdlowe dft -o dft/
python -m pvdlowe report -o report.md
```

---

## How it works

The dependency order runs one way, and **nothing below optics knows what a
coating is** — the solver takes a stack of complex indices and would work for a
laser mirror.

| Layer | Package | What it does |
|---|---|---|
| leaf | `pvdlowe/` | constants, evidence grading, CIE and solar weighting curves |
| 1 | `materials/` | dispersion, metals, alloys, TCOs, glass |
| 2 | `electrical/` | Fuchs–Sondheimer, Mayadas–Shatzkes, percolation |
| 3 | `optics/` | transfer-matrix solver, EN 410 / 673 / 12898 |
| 4 | `screening/` | elements, Derringer–Suich scoring, Pareto, candidates |
| 5 | `optimize/` | thickness optimisation, composition series |

Independent, and nothing in the core imports them:

| Package | What it does |
|---|---|
| `mp/` | Materials Project client — refuses to invent data when offline |
| `ml/` | ML interatomic potential surrogate (needs `mace-torch`) |
| `dft/` | VASP input generation |
| `doe/` | factorial designs, sputter-rate model |
| `characterise/` | predicted XRD signatures for the experiments |
| `report/` | tables, plots, markdown / CSV / Excel export |
| `api/` | HTTP interface |

**The design decision that matters.** Film resistivity feeds the Drude damping,
so a metal layer too thin to conduct is automatically one that reflects poorly.
Without that coupling, optimising for transmittance drives the silver to zero and
reports an excellent coating that does not exist.

**How the optics is validated** — against closed-form answers, not by
inspection: exact Fresnel at a bare interface, an exact null for a quarter-wave
layer, energy conservation to 10⁻¹⁰, and s and p polarisation agreeing at normal
incidence.

---

## Evidence and provenance

Every quantity carries one of eleven evidence grades, and `assert_reportable()`
refuses hypothesis-grade values in headline tables. It is a type constraint
rather than a footnote, which is why it survived contact with a spreadsheet.

The brief's citations were LLM-surfaced — every URL carried
`utm_source=chatgpt.com` — so all began as `LITERATURE_UNVERIFIED`. Checking them
changed eight of fourteen:

| State | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — source located, figures confirmed against abstract | 4 |
| **Disputed — figures appear in no locatable source; do not cite** | **2** |
| Supported — corroborated independently | 3 |
| Not located after searching | 1 |

Two of the brief's transcribed values also fail model-independent consistency
checks, and one of those carries the brief's central recommendation.

```bash
python -m pvdlowe validate
```

> The two disputed entries are the model's three *closest* agreements. Excluding
> them raises the median validation error from 14.7% to 30.6%.
> `validate_model()` excludes them by default, and a test fails if that
> exclusion ever starts *lowering* the reported error.

---

## Documentation

Full index: [`docs/INDEX.md`](docs/INDEX.md). Read in this order:

1. [`docs/SUMMARY.md`](docs/SUMMARY.md) — the recommendation, six findings, and
   what must happen before any of it counts as a result
2. [`docs/FINDINGS.md`](docs/FINDINGS.md) — full findings, organised by
   conclusion
3. [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — the physics, the
   approximations, and where they break
4. [`report/TECHNICAL_REPORT.md`](report/TECHNICAL_REPORT.md) — the written
   report, for a supervisor

**Evidence** — read in this order; each corrected something:

- [`docs/REFERENCES.md`](docs/REFERENCES.md) — all fourteen claims, and what
  became of each
- [`docs/CARRETERO_COMPARISON.md`](docs/CARRETERO_COMPARISON.md) — the
  measurement that reversed the dielectric finding
- [`docs/NUCLEATION_MECHANISM.md`](docs/NUCLEATION_MECHANISM.md) — why the
  underlayer changes the metal
- [`docs/LITERATURE_CALIBRATION.md`](docs/LITERATURE_CALIBRATION.md) — why no
  published scattering parameters explain the copper gap
- [`docs/AZO_CU_AZO_LITERATURE.md`](docs/AZO_CU_AZO_LITERATURE.md) — six further
  studies, one of which reframes that gap
- [`docs/MLIP_MIXING_ENERGY.md`](docs/MLIP_MIXING_ENERGY.md) — mixing energies,
  and two nucleation calculations that failed

**Practical**

- [`docs/ROADMAP.md`](docs/ROADMAP.md) — the experimental programme this feeds
- [`experiments/PROTOCOL_cu_series.md`](experiments/PROTOCOL_cu_series.md) —
  pre-registered decision rules, written before any data exists
- [`docs/CODE_REVIEW.md`](docs/CODE_REVIEW.md) — self-review; every finding
  closed
- [`docs/VERTEX_AI.md`](docs/VERTEX_AI.md) — running it on Google Cloud

**Interactive**, self-contained and needing no install:

- `docs/project_map.html` — what every file is, grouped by dependency order
- `docs/loc_review.html` — ten places in the code worth stopping on

Both are generated by `docs/build_interactive.py`; re-run it after changing the
package.

---

## What this is for

The framework's most useful output was not the candidate ranking. It was
identifying **which measurement would falsify it**: one X-ray diffraction scan,
one film, an afternoon — resolving the grain size that causes the largest known
error, testing the templating mechanism, and discriminating the microstructure
hypotheses by a second independent route.

That experiment is specified in
[`experiments/PROTOCOL_cu_series.md`](experiments/PROTOCOL_cu_series.md) with
decision rules fixed in advance, including the outcome where six candidates fall
over.

---

## Licence and status

Internship project, Saint-Gobain Research India. Research code: complete,
documented, and honest about what it cannot claim.
