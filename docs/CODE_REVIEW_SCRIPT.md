# Walkthrough script — code review

For a 20–25 minute session with whoever inherits `pvdlowe`, or a technical
colleague reviewing it. Bracketed text is guidance, not speech.

**Have open:** `docs/CODE_REVIEW.md`, and a terminal in the repo root.

---

## 0. Framing (1 min)

> This is a review of my own code, so treat it accordingly — I found these,
> which means the ones I didn't find are still in there.
>
> Nine thousand lines, ninety-seven tests, twenty-two modules. Three medium
> findings, one new one, four low, and five things I'd ask you not to break.
>
> None of it blocks handover. One will produce a wrong number, but only after
> someone does something specific, and I'll show you what.

[Reviewing your own work invites the question "so what did you miss?" Get ahead
of it rather than being asked.]

---

## 1. The one that will bite (5 min) — M1

> Open `screening/candidates.py`, the `evaluate` function. That builds the
> record every candidate gets scored on.
>
> Now `optimize/sweep.py`, `composition_series`. It builds its own:

```python
r = performance_summary(coating)
r["cost_usd_per_m2"] = coating_material_cost(masses)["total_usd_per_m2"]
r["supply_risk"] = composition_supply_risk(coating.metal_alloy)
```

> That copy is missing ten keys. Three of them are **scored criteria** —
> structural stability, thermal stability, deposition efficiency — and they
> carry 0.30 of the total weight in `targets.yaml`.
>
> Right now it's harmless. All three are `None`, the scoring scheme
> renormalises over whatever's present, and both paths give an identical 64.95
> for the benchmark. I checked.

[Run it live if they want proof — it takes two seconds:]

```bash
python -c "
from pvdlowe.screening.candidates import evaluate
from pvdlowe.screening.scoring import ScoringScheme
from pvdlowe.optimize.thickness import build
from pvdlowe.materials.tco import tco
sc = ScoringScheme.from_yaml()
print(sc.score(evaluate(build('Ag',10.,35.,35.,tco('AZO'))))['score'])
"
```

> But the whole point of those three fields is that someone will populate them.
> The moment they do, a composition series and the candidate table are scoring
> on **different criteria subsets**, and nothing flags it. You'd get two tables
> that look comparable and aren't.
>
> Half an hour to fix: one shared `record_for(coating)` function, both callers
> use it, one test asserting the key sets match.

[This is the item to spend time on. Everything else is hygiene.]

---

## 2. Two things that look like safety and aren't (4 min) — M2, M3

> `optimize/thickness.py`, line 98:

```python
except Exception:
    return 1e3
```

> That looks like it's rejecting unphysical designs. It isn't. Sub-percolation
> coatings don't raise — they return finite scores, 4.72 at 0.1 nanometres.
> The rejection is actually coming from the desirability functions scoring
> badly, which is correct.
>
> So that branch only ever fires on a genuine bug, which it then hides.
>
> Second one: `LowECoating._cache` and `MultiMetalCoating._cache`. Declared as
> fields, reset in three `replace()` calls, **never read or written anywhere.**
> Only `Alloy._cache` is real.
>
> That's worse than useless, because it advertises memoisation that doesn't
> exist. If you were optimising the sweeps you'd reasonably assume `stack()`
> is cached. It isn't — it rebuilds every dispersion on every call, and it's
> the actual hot path.
>
> Either delete it, ten minutes, or implement it, which would measurably speed
> the composition series.

---

## 3. The part with no execution evidence (4 min) — N1

> `pvdlowe/ml/` is 436 lines and **no line that touches a real interatomic
> potential has ever run.** The development environment had no network, so I
> couldn't install MACE or download weights.
>
> The two tests it has verify the *absence* path and the documented boundary.
> Neither verifies a calculation.
>
> I shipped it anyway because the alternative was omitting the capability, and
> it fails loudly with install instructions rather than silently. The entry
> point also gates every prediction behind reproducing two known Materials
> Project hull distances, so a silently wrong answer is unlikely.
>
> But the honest status is: written, syntax-checked, never run. Don't cite a
> number from it until someone has executed
> `examples/09_mlip_adhesion.py` once.

[Volunteer the three specific things you expect to break — slab generation
assuming a non-empty result, the nearest-integer tiling not reporting lattice
mismatch as an error, and the convoluted `_e()` call form. Naming them shows
you read your own code rather than just shipping it.]

---

## 4. What I'd ask you not to break (5 min)

> Five things, and one of them will silently destroy the physics if a refactor
> touches it.
>
> **The optics–transport coupling.** Film resistivity feeds into the Drude
> damping. A layer too thin to conduct is automatically one that reflects
> poorly. Decouple those and every interface test still passes while the model
> becomes nonsense — optimising for transmittance would drive the silver to
> zero and report an excellent coating.
> `test_thin_film_penalised_in_both_optics_and_transport` exists to catch
> exactly that.
>
> **The provenance system.** Every quantity carries an evidence grade and
> `assert_reportable` refuses hypothesis-grade values in headline tables. It
> did real work — it's what kept the titanium ternary predictions from being
> quoted as results.
>
> **Tests that encode physics, not interfaces.** Energy conservation,
> quarter-wave nulls, the impedance round-trip, the conductive oxide rejecting
> solar near-infrared. These check that the model obeys physical law. That's
> why the suite is worth running after any environment change, not just after
> code changes.
>
> **Functions that refuse rather than guess.** `SputterModel.rate_nm_per_min`
> raises when uncalibrated. `MPClient` raises when offline with a cold cache.
> `MLIPSurrogate` won't fall back to an empirical potential. All three were
> tempting to make helpful; all three would have produced fabricated data.
>
> **And `metal_growth_factor`.** That one's an empirical fudge factor, and its
> docstring says so — what the model got wrong, which paper corrected it, and
> that it's fitted on silver with copper untested. If you add more parameters
> like it, document them the same way.

---

## 5. Order of work (2 min)

> If you're picking this up:
>
> 1. Run the `ml/` module once against a real backend. It's the only part with
>    no execution evidence.
> 2. Extract the shared record builder. Half an hour, prevents a wrong number.
> 3. Delete or implement `_cache`.
> 4. Narrow the exception handling and report the failure count.
> 5. Top-level re-exports, so the first five minutes are easier.
>
> Nothing there blocks you using it today.

---

# Anticipated questions

**"Why didn't you just fix these?"**
> M1 and M3 I could have. I prioritised getting the findings and the experiment
> specified over code hygiene, on the view that a wrong scientific conclusion
> costs more than a dead field. If you disagree, M1 is half an hour.

**"How much of this do I need to understand to use it?"**
> `optics/stack.py` for the central object, `electrical/thinfilm.py` for the
> coupling, `screening/scoring.py` for how candidates are ranked. That's most
> of it. The DoE, DFT and ML subpackages are optional and independent.

**"Is 97 tests a lot or a little for 9,000 lines?"**
> It's not a coverage number and I wouldn't claim it as one. What matters is
> what they test — the physics assertions are the valuable ones. There are
> whole modules with thin coverage, `report/` and `cli.py` especially, and the
> `ml/` module has effectively none.

**"What's the worst bug you found during development?"**
> The Rakić damping double-count. Published optical fits inflate Drude damping
> because it trades against the interband oscillators, so multiplying that by a
> thin-film size-effect ratio counts the same scattering twice. It inflated
> modelled emissivity roughly threefold. It's in `METHODOLOGY.md` §2 because
> anyone building on this will hit the same trap.

**"Would you write it the same way again?"**
> Mostly. The one thing I'd change is generating the report tables at build
> time instead of pasting them — they went stale three times, and
> `pvdlowe report` already does it correctly for the machine-generated output.

---

# Delivery notes

**Lead with "these are my own findings".** It sets the right frame and pre-empts
the obvious question.

**Run M1 live if there's a terminal.** Two seconds, and "it gives the same
answer today, and here's why it won't tomorrow" lands better than describing it.

**Don't oversell the test count.** 97 tests on 9,000 lines is respectable, not
impressive, and the coverage is uneven. Saying so is more credible than not.

**If cut to ten minutes:** M1, N1, and the optics–transport warning. Those are
the wrong number, the untested code, and the thing a refactor will break.
