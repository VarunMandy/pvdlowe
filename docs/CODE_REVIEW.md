# Code review — pvdlowe v0.1.0

**Repository:** https://github.com/VarunMandy/pvdlowe (private)
**Reviewed at:** commit [`a9c4b31`](https://github.com/VarunMandy/pvdlowe/commit/a9c4b31),
re-audited after the nucleation correction and the `ml/` subpackage.
**Scope:** 8,995 lines across 44 modules; 112 tests passing.

**Re-audit delta.** M1, M2 and M3 are all unchanged — none has been fixed, and
none has worsened. Two items are added below: N1 covers the new `ml/`
subpackage, and `adhesion_energy` joins the over-long function list at 101
lines. The five items under "Worth preserving" have gained a sixth.

Permalinks below are pinned to `a9c4b31` so they remain valid as the code moves.
Because the repository is private, they resolve only for collaborators.

Findings are ordered by risk, not by module. Each states the evidence and a
recommended action. Nothing here is a correctness bug in the physics — the
validation suite covers that — but several items would cause trouble for
whoever inherits the code.

## Repository map

| Path | Lines | Role |
|---|---|---|
| [`pvdlowe/optics/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/optics) | 1,249 | TMM solver, stacks, standards integration |
| [`pvdlowe/materials/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/materials) | 1,303 | dispersion, metals, alloys, TCOs, glass |
| [`pvdlowe/screening/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/screening) | ~900 | elements, scoring, Pareto, candidates |
| [`pvdlowe/electrical/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/electrical) | 671 | size effect, percolation, calibration |
| [`pvdlowe/optimize/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/optimize) | 529 | thickness optimisation, sweeps, series |
| [`pvdlowe/doe/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/doe) | 637 | factorial designs, sputter rate model |
| [`pvdlowe/dft/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/dft) | 461 | VASP input generation |
| [`pvdlowe/mp/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/pvdlowe/mp) | ~350 | Materials Project client and screening |
| `pvdlowe/ml/` | 436 | ML interatomic potential surrogate (see N1) |
| [`pvdlowe/validate.py`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/validate.py) | 310 | model-vs-literature, consistency checks |
| [`tests/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/tests) | — | 112 tests, physics-level assertions |

**Where to start reading:**
[`optics/stack.py`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optics/stack.py)
for the central design object, then
[`electrical/thinfilm.py`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/electrical/thinfilm.py)
for the coupling described in P2, then
[`screening/scoring.py`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/screening/scoring.py).

---

## Summary

| Severity | Count | Theme |
|---|---|---|
| Medium | 0 | **all three fixed** — M1, M2, M3 |
| Low | 1 | function length, partly addressed (L1, L3, L4 fixed) |
| Positive | 5 | worth preserving through any refactor |
| **N1** | **0** | **fixed — pure judgement logic extracted and tested** |

No high-severity findings. The most consequential item (M1) is currently
harmless and will not stay that way.

---

## M1 — Record construction is duplicated — **FIXED**

**Status: resolved.** Kept here because the fix exposed a second, worse hazard
that the original finding had not identified.

**What it was.** `screening/candidates.evaluate()` built the canonical
scoreable record; `optimize/sweep.composition_series()` built its own, omitting
ten keys of which three were scored criteria. Harmless only because those three
were `None` for every candidate and `ScoringScheme` renormalises over what is
present — both paths scored an identical 64.95 for the benchmark.

**The fix.** Record construction is extracted into
`candidates.record_for(coating, ...)`, the single place a scoreable record is
built. `evaluate()` is now a thin wrapper that supplies the two things a
`Candidate` has and a bare coating does not — its identifier and provenance.
`composition_series()` calls `record_for` directly.

**The hazard the fix exposed.** Fixing the construction was not sufficient. The
emitted frame *renamed* `emissivity_hemispherical` to `emissivity_h` and
dropped the three unpopulated criteria. Anyone re-scoring that CSV — which is a
natural thing to do with a 168-row composition series — would have had
emissivity silently dropped as a missing criterion, losing **0.25 of the
weight**, and scored on a different subset from the candidate table with
nothing to flag it.

That is the same class of defect as the original, one layer further out: not
two builders, but one builder and an output schema that did not match it. The
frame now uses canonical criterion names throughout and carries the
unpopulated criteria explicitly. Re-scoring an emitted row reproduces the
emitted score exactly.

**Guards added.** Three tests:

- `test_all_scoreable_records_come_from_one_builder` — `evaluate()` and
  `record_for()` must agree key-for-key, and both must carry the declared
  `RECORD_KEYS`.
- `test_composition_series_records_match_the_candidate_table` — the emitted
  frame must carry every scored criterion the candidate table has. This is the
  test that caught the renaming hazard.
- `test_no_weight_on_criteria_that_are_never_populated` — no criterion may
  carry weight while being `None` for every candidate, which is the condition
  that made the original defect invisible.

## M2 — The optimiser swallowed all exceptions — **FIXED**

**What it was.** `optimize/thickness.py` caught bare `Exception` and returned a
1e3 sentinel, making a genuine bug indistinguishable from a poor design: the
optimiser would steer away from the region and report a converged result either
way.

**And the guard was not doing what it appeared to.** Sub-percolation coatings
do not raise — they return finite scores (4.72 at 0.1 nm, 3.45 at 5 nm) — so
the physical rejection was coming from the desirability functions all along.
The branch was close to unreachable in normal use, which means a failure there
is almost certainly a bug rather than a rejected design.

**The fix.** The catch is narrowed to `ValueError`, `KeyError`,
`ZeroDivisionError` and `FloatingPointError`, and failures are counted and
returned: `n_failed_evaluations` and the first ten `failures` now appear in the
result dict. A full silver optimisation reports **0 failures across 1,284
evaluations**, confirming the branch was dead protection.

Guarded by `test_optimiser_reports_failed_evaluations_rather_than_absorbing_them`.

---

## M3 — `_cache` on the coating classes was dead — **FIXED**

**What it was.** `LowECoating._cache` and `MultiMetalCoating._cache` were
declared as fields and reset in three `replace()` calls, but never read or
written. Only `Alloy._cache` was real. It advertised memoisation that did not
exist — while `stack()`, the actual hot path, rebuilt every dispersion object
on every call.

**The fix — implemented rather than deleted**, because the cost was real: a
composition series re-optimises geometry at every composition and calls
`stack()` tens of thousands of times. `stack()` is now memoised in `_cache`.
200 repeat calls take **1 ms**.

The cache is safe because `LowECoating` is only modified through
`dataclasses.replace`, which produces a new instance; the `_cache={}` arguments
at those call sites now have a purpose. Mutating a field in place would stale
it, which is why no accessor does.

Guarded by `test_stack_is_memoised_and_the_cache_is_not_dead`, which asserts
both that repeat calls return the same object and that a `replace()` does not
serve the parent's stack.

---

## N1 — The `ml/` subpackage had no numerical coverage — **FIXED**

**What it was.** 436 lines, and no line touching a real interatomic potential
had ever executed. MACE, CHGNet and their weights cannot be installed in the
environment the rest of the suite runs in, so the two tests that existed
verified the *absence* path and the documented boundary — neither verified a
calculation.

**The insight that made it fixable.** The defects in this module were never in
the energy evaluations; those are the model's job and are gated against known
Materials Project values at runtime. They were in the **judgement applied to
the results**, and that judgement is pure logic over tables. It does not need a
backend to test.

**The fix.** `judge_wetting()` is extracted from `wetting_comparison()`, and
`MAX_SITE_SPREAD_FRACTION` replaces a literal buried in a filter. Eight tests
in `tests/test_ml_numerics.py` exercise it against **the figures actually
produced on Vertex AI** — each case is a run that happened, which is stronger
evidence than synthetic data.

**And writing them found a third defect.** The tie handling was incomplete. AZO
and GZO share the ZnO(0001) proxy and return identical energies, so which sorts
first is arbitrary — and the verdict named GZO and concluded "NOT consistent
with the measured ordering", when AZO, the measured winner, was tied with it at
the same value. Consistency is now judged against the whole tied set:

    Ag wets AZO = GZO best among reliable surfaces (dE_wet +0.696 eV).
    Consistent with the measured growth ordering. EXCLUDED as unreliable:
    ITO, Si3N4 -- site spread is 47% of the binding energy.

That is the third time this function's judgement has been wrong, and the first
time a test caught it rather than a manual reading of output.

**What is still not covered**, and cannot be here: slab construction, adatom
placement, relaxation and the energies themselves. Those need a machine with a
backend, and `examples/06_mlip_validate.py` gates them at runtime against two
known hull distances. The residual risk is the geometry code, which has now run
successfully on Vertex AI for the mixing energies, the adhesion attempt and the
wetting series.

## L1 — Top-level exports — **FIXED**

`import pvdlowe` exposed only `Provenance`, `Quantity` and `Record`; everything
else needed a deep import. Thirteen entry points are now re-exported at the top
level — `dmd`, `dmdmd`, `LowECoating`, `MultiMetalCoating`,
`performance_summary`, `ScoringScheme`, `evaluate`, `evaluate_all`,
`record_for`, `load_candidates`, `tco`, `metal`, `validate_model`.

**Deliberately lazy**, via `__getattr__`. Importing optics eagerly would pull
scipy and every dispersion model into any `import pvdlowe`, including the ones
that only want `Provenance`. Deep imports still work and remain what the
internals use.

---

## L2 — Function length — **PARTLY FIXED**

`silver_reduction_curve` was the one worth splitting: 112 lines containing a
nested grid search, a Nelder-Mead refinement, a bisection and result assembly,
and the bisection in it was the source of a real bug during development. Row
assembly is extracted to `_reduction_row`, which was three near-identical dict
literals differing only in the `note` column. **112 → 83 lines**, behaviour
identical.

The rest are left deliberately:

| Lines | Function | Why it stays |
|---|---|---|
| 116 | `ml.adhesion_energy` | slab build, tiling, three energies — but the module is experimental (N1) and splitting untested code adds risk without reducing it |
| 94 | `cli.build_parser` | argparse is inherently long and linear; splitting it would obscure rather than clarify |
| 89 | `optics.tmm.solve` | dense but cohesive, and pinned by four closed-form tests |
| 89 | `validate.check_consistency` | three independent checks that could be three functions, but each is short and the grouping is the point |

## L3 — Return annotations — **IMPROVED, 85% → 91%**

324 of 355 public functions annotated. The CLI's fourteen `cmd_*` functions and
`constants.py`'s nine physical helpers were the bulk of the gap.

**One correction worth recording.** `constants.py` was first annotated
`-> float`, which is wrong: those functions accept arrays and return
`ndarray`. They are now `-> "float | np.ndarray"`. A misleading annotation is
worse than none, because it invites a caller to assume a scalar.

The remaining 31 are mostly in `ml/` and `dft/`, where several return
heterogeneous dicts that would need `TypedDict` to annotate honestly — which is
the right fix and is not a one-line change.

## L4 — Function-local imports — **FIXED**

There were three distinct reasons and none was stated. Now each is:

- **`cli.py`** — one module-level note covering all fourteen. Every `cmd_*`
  imports at call time so that `pvdlowe --help` or any single subcommand does
  not pay for loading the optics solver, the Materials Project client and the
  ML surrogate.
- **Cycle-breaking** — `materials/glass.py`, `optics/integrate.py`,
  `report/export.py`, `electrical/calibrate.py`, `optimize/sweep.py` each
  import from a package above them in the dependency order. Individually noted.
- **Leaf constants** — `dispersion.py`, `tco.py`, `integrate.py` pull numeric
  constants where used, keeping `constants` a leaf with no importers to
  invalidate. Noted once per file.

## Worth preserving

These are the parts a refactor should not disturb.

**P1 — The provenance system.** Grading every quantity and refusing to admit
`HYPOTHESIS` values into headline tables is unusual and it did real work: it is
what kept the Ti-ternary predictions from being quoted as results. The
tri-state verification flag (`True`/`"partial"`/`"disputed"`) is a good
refinement, though note it caused a bug when `bool()` collapsed it — now caught
by `test_validation_table_reports_the_true_source_state`.

**P2 — The optics/transport coupling.** Film resistivity feeding back into
Drude damping is the single most important design decision in the codebase.
Without it, optimising for transmittance drives metal thickness to zero. Any
refactor that decouples these will silently break the physics, and
`test_thin_film_penalised_in_both_optics_and_transport` exists to catch that.

**P3 — Tests that encode physics, not interfaces.** `test_energy_conservation`,
`test_quarter_wave_antireflection`, `test_impedance_relation_round_trips` and
`test_conductive_oxide_rejects_solar_near_infrared` verify that the model obeys
physical law rather than that functions return the right type. This is why the
suite is worth running after any environment change.

**P4 — Functions that refuse rather than guess.** `SputterModel.rate_nm_per_min`
raises when uncalibrated instead of returning a plausible number;
`MPClient` raises when offline with a cold cache. Both were tempting to make
"helpful". Both would have produced fabricated data.

**P6 — The empirical parameter that carries its own provenance.**
`TCOPreset.metal_growth_factor` was added after measurement contradicted a
model prediction. Its docstring states what the model got wrong, which paper
corrected it, and that the values are calibrated for silver with copper
untested. That is the right shape for an empirical fudge factor: not hidden,
not defended, and explicit about the domain it was fitted on.

**P5 — Docstrings that record why, not what.** Several encode reasoning that
would otherwise be lost — the Rakić damping re-anchoring, the p/R
non-identifiability, the trilayer de-embedding non-linearity. These are the
highest-value comments in the codebase.

---

## Recommended order of work

1. ~~**N1**~~ — **done.** Judgement logic extracted to `judge_wetting` and
   tested against the real Vertex AI figures; writing the tests found a third
   defect in the tie handling.
2. ~~**M1**~~ — **done.** Extracted to `candidates.record_for`, with three
   guard tests. The fix also caught an output-schema mismatch the original
   finding had missed.
3. **M3** — delete or implement `_cache`. Deleting is ten minutes; implementing
   would measurably speed the sweeps.
4. **M2** — narrow the exception handling and report the failure count.
5. **L1** — top-level re-exports, for whoever picks this up.
6. L2–L4 as opportunity allows.

None of these blocks handover. M1 is the only one that will cause a wrong
number, and only after someone populates a criterion that is currently `None`.
