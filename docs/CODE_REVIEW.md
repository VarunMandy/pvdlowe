# Code review — pvdlowe v0.1.0

A review of my own code. Treat it accordingly: the defects I did not find are
still in there.

**Scope:** 9,586 lines across 44 modules; 136 tests passing.
**Permalinks** are pinned to [`a9c4b31`](https://github.com/VarunMandy/pvdlowe/commit/a9c4b31),
the commit reviewed. **For findings marked FIXED they show the code as it was**,
not as it is — the finding and its evidence are kept together deliberately.
Current code is on `master`.

---

## Status

**Every finding is closed.**

| Severity | Open | Notes |
|---|---|---|
| High | 0 | none were found |
| Medium | **0** | M1, M2, M3 all fixed and guarded |
| Low | 1 | L2 partly addressed by documented judgement; L1, L3, L4, L5 closed |
| Untested | **0** | N1 fixed by extracting the logic that had defects |

**Two of the fixes found defects this review had missed**, which is the most
useful thing in it:

- Fixing **M1**'s duplicated record builder was not sufficient — the emitted
  frame renamed a criterion and dropped three others, so re-scoring a
  composition series would have silently lost 0.25 of the weight.
- Fixing **N1** by extracting `judge_wetting()` exposed a third tie-handling
  defect: two dielectrics sharing a crystalline proxy return identical energies,
  so the verdict named the wrong one and declared "NOT consistent" when the
  measured winner was tied with it.

**Both were found by writing the test, not by reading the code.** That function
had been read three times and corrected twice by eye before a test caught the
third problem.

---

## Repository map

| Path | Lines | Role |
|---|---|---|
| `pvdlowe/optics/` | 1,249 | TMM solver, stacks, standards integration |
| `pvdlowe/materials/` | 1,303 | dispersion, metals, alloys, TCOs, glass |
| `pvdlowe/screening/` | ~900 | elements, scoring, Pareto, candidates |
| `pvdlowe/electrical/` | 671 | size effect, percolation, calibration |
| `pvdlowe/optimize/` | 529 | thickness optimisation, sweeps, series |
| `pvdlowe/doe/` | 637 | factorial designs, sputter rate model |
| `pvdlowe/ml/` | 699 | ML interatomic potential surrogate |
| `pvdlowe/dft/` | 461 | VASP input generation |
| `pvdlowe/mp/` | ~350 | Materials Project client and screening |
| `pvdlowe/characterise/` | ~200 | predicted XRD signatures |
| `pvdlowe/validate.py` | 310 | model vs literature, consistency checks |
| `tests/` | — | 136 tests, physics-level assertions |

**Where to start reading:** `optics/stack.py` for the central object, then
`electrical/thinfilm.py` for the coupling described under P1, then
`screening/scoring.py`.

---

# Findings

## M1 — Record construction was duplicated — **FIXED**

**What it was.** `screening/candidates.evaluate()` built the canonical scoreable
record; `optimize/sweep.composition_series()` built its own, omitting ten keys of
which three were scored criteria.

**Why it was harmless.** Those three were `None` for every candidate and
`ScoringScheme` renormalises over what is present — both paths scored an
identical 64.95 for the benchmark.

**Why it would not have stayed harmless.** The moment any of them is populated —
which is the explicit intent, they are defined in `targets.yaml` — the two paths
would silently score on different criteria subsets. A composition series would
become non-comparable with the candidate table, and nothing would flag it.

**The fix.** Record construction extracted into
`candidates.record_for(coating, …)`, the single place a scoreable record is
built. `evaluate()` is now a thin wrapper supplying the two things a `Candidate`
has that a bare coating does not — identifier and provenance.

**The hazard the fix exposed.** Fixing construction was not sufficient. The
emitted frame *renamed* `emissivity_hemispherical` to `emissivity_h` and dropped
the three unpopulated criteria. Anyone re-scoring that CSV — a natural thing to
do with a 168-row composition series — would have had emissivity silently
dropped as missing, **losing 0.25 of the weight**, and scored on a different
subset from the candidate table.

That is the same class of defect one layer further out: not two builders, but one
builder and an output schema that did not match it. Re-scoring an emitted row now
reproduces the emitted score exactly.

**Guards.** `test_all_scoreable_records_come_from_one_builder`,
`test_composition_series_records_match_the_candidate_table` (the one that caught
the renaming), and `test_no_weight_on_criteria_that_are_never_populated`.

---

## M2 — The optimiser swallowed all exceptions — **FIXED**

**What it was.** `optimize/thickness.py` caught bare `Exception` and returned a
1e3 sentinel, making a genuine bug indistinguishable from a poor design: the
optimiser would steer away from the region and report a converged result either
way.

**And the guard was not doing what it appeared to.** Sub-percolation coatings do
not raise — they return finite scores, 4.72 at 0.1 nm, 3.45 at 5 nm — so the
physical rejection was coming from the desirability functions all along. The
branch was close to unreachable, which means a failure there is almost certainly
a bug.

**The fix.** Narrowed to `ValueError`, `KeyError`, `ZeroDivisionError` and
`FloatingPointError`; failures counted and returned as `n_failed_evaluations`
with the first ten in `failures`. A full silver optimisation reports **0 failures
across 1,284 evaluations**, confirming the branch was dead protection.

**Guard.** `test_optimiser_reports_failed_evaluations_rather_than_absorbing_them`.

---

## M3 — `_cache` was dead — **FIXED**

**What it was.** `LowECoating._cache` and `MultiMetalCoating._cache` were declared
as fields and reset in three `replace()` calls, but never read or written. Only
`Alloy._cache` was real.

Worse than useless: it advertised memoisation that did not exist, while
`stack()` — the actual hot path — rebuilt every dispersion object on every call.
A composition series calls it tens of thousands of times.

**The fix — implemented rather than deleted**, because the cost was real.
`stack()` is now memoised. **200 repeat calls take 1 ms.**

Safe because `LowECoating` is only modified through `dataclasses.replace`, which
produces a new instance; the `_cache={}` arguments at those call sites now have
a purpose.

**Guard.** `test_stack_is_memoised_and_the_cache_is_not_dead`, which asserts both
that repeat calls return the same object and that a `replace()` does not serve
the parent's stack.

---

## N1 — The `ml/` subpackage had no numerical coverage — **FIXED**

**What it was.** 699 lines, and no line touching a real interatomic potential had
ever executed. MACE and CHGNet cannot be installed in the environment the suite
runs in, so the two tests that existed verified the *absence* path and the
documented boundary — neither verified a calculation.

**The insight that made it fixable.** The defects in this module were never in
the energy evaluations; those are the model's job and are gated at runtime against
known Materials Project values. They were in the **judgement applied to the
results**, and that judgement is pure logic over tables. It does not need a
backend to test.

**The fix.** `judge_wetting()` extracted from `wetting_comparison()`, and
`MAX_SITE_SPREAD_FRACTION` replaces a literal buried in a filter. Eight tests in
`tests/test_ml_numerics.py` exercise it against **the figures actually produced
on Vertex AI** — each case is a run that happened, which is stronger evidence
than synthetic data.

**And writing them found a third defect.** AZO and GZO share the ZnO(0001) proxy
and return identical energies, so which sorts first is arbitrary — and the
verdict named GZO and concluded "NOT consistent with the measured ordering", when
AZO, the measured winner, was tied with it at the same value. Consistency is now
judged against the whole tied set.

That is the third time this function's judgement was wrong, and **the first time
a test caught it** rather than a manual reading of output.

**What is still not covered**, and cannot be here: slab construction, adatom
placement, relaxation and the energies themselves. Those need a machine with a
backend, and `examples/06_mlip_validate.py` gates them at runtime against two
known hull distances.

---

## L1 — Top-level exports — **FIXED**

`import pvdlowe` exposed only `Provenance`, `Quantity` and `Record`. Thirteen
entry points are now re-exported at the top level — `dmd`, `dmdmd`,
`LowECoating`, `MultiMetalCoating`, `performance_summary`, `ScoringScheme`,
`evaluate`, `evaluate_all`, `record_for`, `load_candidates`, `tco`, `metal`,
`validate_model`.

**Deliberately lazy**, via `__getattr__`. Importing optics eagerly would pull
scipy and every dispersion model into any `import pvdlowe`, including callers
that only want `Provenance`.

---

## L2 — Function length — **PARTLY FIXED, by judgement**

`silver_reduction_curve` was the one worth splitting: 112 lines containing a
nested grid search, a Nelder–Mead refinement, a bisection and result assembly,
and the bisection in it was the source of a real bug during development. Row
assembly is extracted to `_reduction_row` — previously three near-identical dict
literals differing only in the `note` column. **112 → 83 lines**, output
identical.

The rest stay, for stated reasons:

| Lines | Function | Why it stays |
|---|---|---|
| 116 | `ml.adhesion_energy` | the module is experimental; splitting untested code adds risk without reducing it |
| 94 | `cli.build_parser` | argparse is inherently long and linear |
| 89 | `optics.tmm.solve` | dense but cohesive, pinned by four closed-form tests |
| 89 | `validate.check_consistency` | three independent checks; each is short and the grouping is the point |

---

## L3 — Return annotations — **IMPROVED, 85% → 91%**

324 of 355 public functions annotated. The CLI's fourteen `cmd_*` functions and
`constants.py`'s nine physical helpers were the bulk of the gap.

**One correction worth recording.** `constants.py` was first annotated
`-> float`, which is wrong: those functions accept arrays and return `ndarray`.
They are now `-> "float | np.ndarray"`. **A misleading annotation is worse than
none**, because it invites a caller to assume a scalar.

The remaining 31 are mostly in `ml/` and `dft/`, returning heterogeneous dicts
that would need `TypedDict` to annotate honestly.

---

## L4 — Function-local imports — **FIXED**

Three distinct reasons, none previously stated. Now each is:

- **`cli.py`** — one module-level note covering all fourteen. Every `cmd_*`
  imports at call time so that `python -m pvdlowe --help` or a single subcommand
  does not pay for loading the optics solver, the Materials Project client and
  the ML surrogate.
- **Cycle-breaking** — `materials/glass.py`, `optics/integrate.py`,
  `pvdlowe/report/export.py`, `electrical/calibrate.py`, `optimize/sweep.py` each
  import from a package above them in the dependency order. Individually noted.
- **Leaf constants** — `dispersion.py`, `tco.py`, `integrate.py` pull numeric
  constants where used, keeping `constants` a leaf. Noted once per file.

---

## L5 — Nineteen public functions referenced by nothing — **DOCUMENTED**

A scan for public functions whose name appears exactly once across the package,
tests and examples combined:

| Group | Functions |
|---|---|
| Immutable-update builders | `with_metal_thickness`, `with_tco_thickness`, `with_alloy`, `with_thickness`, `with_value`, `with_resistivity`, `with_damping_scale` |
| Trivial accessors | `total_thickness_nm`, `silver_fraction`, `absolute_error`, `relative_error`, `resample` |
| Provenance helpers | `provenance_record`, `score_quantity`, `resistivity_quantity` |
| Query helpers | `by_id`, `by_stage`, `cached_queries`, `evaluate_one` |

**Why this is not simply dead code.** The builders are the immutable-update idiom
a caller would reach for first, and they are correct — each resets `_cache` so a
modified coating does not inherit the parent's memoised stack.

**That correctness was unguarded.** Nothing referenced them, so a later edit
dropping the `_cache={}` would have produced a coating reporting 14 nm of silver
while being evaluated as 10 — silently, with every other number consistent with
the wrong one. **That hazard exists only because the memoisation was added after
the builders were written.**

**Action taken.** The three coating builders and `Stack.with_thickness` are now
covered by `test_with_builders_do_not_serve_a_stale_cache` and
`test_stack_with_thickness_returns_a_new_stack`. One deliberately checks that a
bare `replace()` *does* serve a stale cache, so that if the memoisation is ever
removed the test says so rather than passing vacuously.

**Remaining.** The other twelve are one- to three-line accessors with no
behaviour to get wrong. They are kept: deleting API surface a successor might
reasonably expect is a worse trade than carrying twelve short functions, and this
entry records that the choice was made rather than overlooked.

---

# Worth preserving through any refactor

**P1 — The optics–transport coupling.** Film resistivity feeds the Drude damping,
so a layer too thin to conduct is automatically one that reflects poorly.
**Decouple these and every interface test still passes while the model becomes
nonsense** — optimising for transmittance would drive the silver to zero and
report an excellent coating.
`test_thin_film_penalised_in_both_optics_and_transport` exists to catch exactly
that.

**P2 — Tests that encode physics, not interfaces.** Energy conservation to
1e-10, exact Fresnel at a bare interface, an exact quarter-wave null, s and p
agreeing at normal incidence, the impedance round-trip, the conductive oxide
rejecting solar near-infrared. These check the model obeys physical law. It is
why the suite is worth running after an environment change, not just a code
change.

**P3 — Provenance as a type.** Every quantity carries an evidence grade and
`assert_reportable` refuses hypothesis-grade values in headline tables. It did
real work: it is what kept the titanium ternary predictions out of the results
tables.

**P4 — Functions that refuse rather than guess.** `SputterModel.rate_nm_per_min`
raises when uncalibrated. `MPClient` raises when offline with a cold cache.
`MLIPSurrogate` will not fall back to an empirical potential. `adhesion_energy`
refuses above 4% lattice mismatch. **Each was tempting to make helpful; each
would have produced fabricated data.**

**P5 — Docstrings that record why, not what.** The Rakić damping double-count,
the reason for geometric aggregation, the basis warnings on `g_value` — these
carry reasoning a reader cannot reconstruct from the code.

**P6 — The empirical parameter that carries its own provenance.**
`metal_growth_factor` was added after measurement contradicted a model
prediction. Its docstring states what the model got wrong, which paper corrected
it, and that the values are fitted on silver with copper untested. That is the
right shape for an empirical fudge factor: not hidden, not defended, explicit
about its domain.

---

# What remains

**Nothing in this review.** Every finding is closed or documented as a judgement.

**The residual risk is not a code defect** and is stated plainly: no films have
been deposited, and the geometry code in `ml/` is exercised only by runs on
Vertex AI rather than by the suite.

**If picking this up**, the order I would suggest:

1. Run `docs/build_interactive.py` and `python -m pvdlowe validate` first — they
   report the current state rather than what this file says about it.
2. Read `docs/METHODOLOGY.md` §2 before touching `materials/dispersion.py`.
3. Do not decouple P1.
