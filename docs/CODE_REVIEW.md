# Code review — pvdlowe v0.1.0

**Repository:** https://github.com/VarunMandy/pvdlowe (private)
**Reviewed at:** commit [`a9c4b31`](https://github.com/VarunMandy/pvdlowe/commit/a9c4b31),
re-audited after the nucleation correction and the `ml/` subpackage.
**Scope:** 9,124 lines across 22 modules; 97 tests passing.

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
| [`tests/`](https://github.com/VarunMandy/pvdlowe/tree/a9c4b31/tests) | — | 97 tests, physics-level assertions |

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
| Medium | 3 | latent divergence, silent failure, dead abstraction |
| Low | 4 | API surface, function length, annotation gaps, import placement |
| Positive | 5 | worth preserving through any refactor |

No high-severity findings. The most consequential item (M1) is currently
harmless and will not stay that way.

---

## M1 — Record construction is duplicated, and the copies are already divergent

**Evidence.** [`screening/candidates.evaluate()`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/screening/candidates.py#L84) builds the canonical scoreable
record. [`optimize/sweep.composition_series()`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optimize/sweep.py#L112-L193) builds its own:

```python
r = performance_summary(coating)
r["cost_usd_per_m2"] = coating_material_cost(masses)["total_usd_per_m2"]
r["supply_risk"] = composition_supply_risk(coating.metal_alloy)
```

The hand-rolled version omits ten keys that `evaluate()` supplies:
`structural_stability`, `thermal_stability_c`, `deposition_efficiency`,
`film_resistivity_uohm_cm`, `size_effect_ratio`, `metal_areal_mass_g_m2`,
`mixing_model`, `provenance`, `reportable`, `id`.

**Why it is currently harmless.** The three scored criteria among those
(`structural_stability`, `thermal_stability_c`, `deposition_efficiency`) are all
`None`, and `ScoringScheme` renormalises over available criteria. Both paths
score an identical 64.95 for the benchmark. Verified.

**Why it will not stay harmless.** The moment any of those three is populated —
which is the explicit intent, since they carry 0.30 of the weight in
`targets.yaml` — the two paths will silently score on different criteria
subsets. A composition series would then be non-comparable with the candidate
table, and nothing would flag it. The same pattern was reproduced in several
analysis scripts written during this project, which is how it propagates.

**Recommended.** Extract the record construction into one function, e.g.
`candidates.record_for(coating)`, and have both `evaluate()` and
`composition_series()` call it. Add a test asserting the two paths produce
identical key sets.

---

## M2 — The optimiser swallows all exceptions and returns a sentinel

**Evidence.** [`optimize/thickness.py#L98-L102`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optimize/thickness.py#L98-L102)

```python
try:
    return -objective_value(build(metal, m, b, t, preset), scheme, criteria)
except Exception:
    return 1e3
```

Any failure — a bad dispersion lookup, a malformed preset, an arithmetic
overflow — is indistinguishable from "this is a poor design". The optimiser
will steer away from the region and report a converged result.

**Compounding issue.** The guard is not doing what it appears to. Sub-percolation
coatings do **not** raise; they return finite scores:

```
metal 0.1 nm -> score 4.72
metal 1.0 nm -> score 4.53
metal 5.0 nm -> score 3.45
```

So the `except` branch is effectively unreachable in normal use, and the
physical rejection it seems to provide is actually coming from the desirability
functions scoring badly. That is fine, but it means the try/except is dead
protection that would only ever fire on a genuine bug, which it would then hide.

**Recommended.** Catch specific exceptions, count them, and surface the count in
the result dict. If more than a few per cent of evaluations fail, that is
information the caller needs.

---

## M3 — `_cache` on the coating classes is dead

**Evidence.** [`LowECoating._cache`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optics/stack.py#L142) and [`MultiMetalCoating._cache`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optics/stack.py#L347) are declared
as fields and reset in every `replace()` call:

```python
return replace(self, metal_thickness_nm=float(thickness_nm), _cache={})
```

They are never read or written anywhere. Only `Alloy._cache` is genuinely used
([`alloys.py#L247-L268`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/materials/alloys.py#L247-L268)).

**Why it matters.** It advertises memoisation that does not exist. Someone
optimising a hot loop would reasonably assume `stack()` is cached — it is not,
and it rebuilds every dispersion on every call, which is the actual hot path in
the sweeps. Meanwhile the `_cache={}` arguments are noise in three call sites.

**Recommended.** Either delete the field and the three `_cache={}` arguments, or
implement the memoisation the field implies. The second is worth doing: the
composition series calls `stack()` tens of thousands of times.

---

## N1 — The `ml/` subpackage ships untested against a real backend

**Evidence.** `pvdlowe/ml/surrogate.py` is 436 lines and no line of it that
touches an actual interatomic potential has ever executed. The development
environment had no network, so `mace-torch`, `chgnet` and `matgl` could not be
installed and the model weights could not be downloaded. The two tests that
exist —`test_mlip_surrogate_refuses_rather_than_falls_back` and
`test_mlip_boundary_excludes_optical_properties` — verify the *absence* path
and the documented boundary. Neither verifies a calculation.

**Why it is nonetheless shipped.** The alternative was to omit the capability
entirely. The module fails loudly with installation instructions when no
backend is present, and the entry-point example gates every prediction behind
reproducing two known Materials Project hull distances, so a silently wrong
result is unlikely. But the honest status is *written, syntax-checked,
never run*.

**Specific risks that first execution will probably surface:** the slab
construction in `adhesion_energy` assumes `SlabGenerator` returns at least one
slab for every proxy and takes the first without inspecting termination; the
metal-film tiling uses a nearest-integer repeat that could leave several per
cent lattice mismatch unreported as an error; and `_e()` uses a needlessly
convoluted call form that should simply branch.

**Recommended.** Run `examples/07_mlip_adhesion.py` once on a machine with a
backend installed, then either fix what breaks or mark the module
experimental in `README.md`. Do not cite any number from it until then.

---

## L1 — The top-level package exports almost nothing

[`pvdlowe/__init__.py#L12`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/__init__.py#L12)

```python
>>> import pvdlowe; pvdlowe.__all__
['Provenance', 'Quantity', 'Record', '__version__']
```

Everything else requires a deep import (`from pvdlowe.optics.stack import dmd`).
That is defensible for a library with a large surface, but it makes the
first five minutes harder than necessary and the README examples all use deep
paths.

**Recommended.** Re-export the dozen or so entry points people actually start
with: `dmd`, `dmdmd`, `LowECoating`, `MultiMetalCoating`, `performance_summary`,
`ScoringScheme`, `evaluate_all`.

## L2 — Several functions are too long to review comfortably

| Lines | Function | Source |
|---|---|---|
| 112 | `silver_reduction_curve` | [thickness.py#L158-L270](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optimize/thickness.py#L158-L270) |
| 89 | `solve` | [tmm.py#L73-L162](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optics/tmm.py#L73-L162) |
| 81 | `composition_series` | [sweep.py#L112-L193](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optimize/sweep.py#L112-L193) |
| 78 | `build_parser` | [cli.py#L279-L357](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/cli.py#L279-L357) |
| 101 | `adhesion_energy` | `ml/surrogate.py` — slab build, tiling, three energies and result assembly in one function; the clearest split candidate in the codebase |
| 87 | `check_consistency` | `validate.py` — three independent checks that could be three functions |
| 76 | `fit_series` | [calibrate.py#L216-L292](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/electrical/calibrate.py#L216-L292) |
| 72 | `diagnose` | [calibrate.py#L295-L367](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/electrical/calibrate.py#L295-L367) |
| 68 | `cmd_calibrate` | [cli.py#L151-L219](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/cli.py#L151-L219) |

`build_parser` is fine — argparse is inherently long and linear. `solve` is
dense but cohesive. **`silver_reduction_curve` is the one worth splitting**: it
contains a nested grid search, a Nelder–Mead refinement, a bisection, and result
assembly, and the bisection logic in it was the source of a real bug during
development (a conducting film was wrongly assumed to cap `d_c`).

## L3 — Return annotations at 86%

282 of 328 public functions annotated. The gaps are concentrated in `cli.py`
(where it matters least) and in a few `screening` helpers (where it matters
more, since they return heterogeneous dicts).

**Recommended.** `TypedDict` for the record and result dicts would document the
contract that M1 is currently violating implicitly.

## L4 — Function-local imports are used inconsistently

Some are deliberate and correct — `mp_api` in
[`client.py`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/mp/client.py),
avoiding a hard dependency; the four in
[`sweep.py#L131-L134`](https://github.com/VarunMandy/pvdlowe/blob/a9c4b31/pvdlowe/optimize/sweep.py#L131-L134),
avoiding a cycle. Others appear to
be habit. A reader cannot tell which is which.

**Recommended.** A one-line comment on the deliberate ones, e.g.
`# local import: optional dependency` or `# local import: breaks a cycle`.

---

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

1. **N1** — run the `ml/` subpackage once against a real backend. It is the
   only part of the codebase with no execution evidence at all.
2. **M1** — extract the shared record builder. Half an hour, prevents a silent
   correctness failure the moment the stability criteria are populated.
3. **M3** — delete or implement `_cache`. Deleting is ten minutes; implementing
   would measurably speed the sweeps.
4. **M2** — narrow the exception handling and report the failure count.
5. **L1** — top-level re-exports, for whoever picks this up.
6. L2–L4 as opportunity allows.

None of these blocks handover. M1 is the only one that will cause a wrong
number, and only after someone populates a criterion that is currently `None`.
