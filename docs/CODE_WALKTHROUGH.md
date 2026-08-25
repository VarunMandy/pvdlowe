# Code walkthrough

For a 35–45 minute session with the code open. Every block below is real and
runnable; nothing is pseudocode. Commands assume the repo root.

**Setup before the meeting:**

```bash
git clone https://github.com/VarunMandy/pvdlowe.git && cd pvdlowe
pip install -e .
python tests/run_tests.py        # 110 passed
```

---

## 0. Shape of the thing (3 min)

9,198 lines, 11 subpackages, 127 tests. The dependency order runs one way:

```
constants  provenance  spectra          ← no dependencies
     │
materials/  ── dispersion, metals, alloys, tco, glass
     │
electrical/ ── thinfilm, calibrate      ← size effect, percolation
     │
optics/     ── tmm, stack, integrate    ← the transfer matrix and standards
     │
screening/  ── elements, scoring, pareto, candidates
     │
optimize/   ── thickness, sweep         ← searches over the above
     │
report/  validate/  cli/                ← presentation
```

Off to one side and independent: `doe/` (run sheets), `dft/` (VASP inputs),
`mp/` (Materials Project), `ml/` (interatomic potentials), `characterise/`
(predicted XRD).

> **Say:** "Nothing below optics knows anything about coatings. `tmm.py` solves
> a stack of complex indices — it would work for a laser mirror. The domain
> knowledge lives in the layers above it."

---

## 1. The design decision that matters most (8 min)

**This is the block to spend time on.** Everything else is implementation.

`pvdlowe/optics/stack.py`, lines 185–212:

```python
@property
def size_effect_ratio(self) -> float:
    """How much more resistive the film is than bulk, at this thickness."""
    return float(min(self.transport.ratio(self.metal_thickness_nm), 50.0))

@property
def film_resistivity_uohm_cm(self) -> float:
    return float(self.metal_alloy.bulk_resistivity_uohm_cm
                 * self.size_effect_ratio * self.growth_factor)
```

and then, in `metal_dispersion()`:

```python
disp = alloy.dispersion(alloy.bulk_resistivity_uohm_cm * ratio)
```

**The point:** the electrical model feeds the *optical* one. Film resistivity
sets the Drude damping, so a metal layer too thin to conduct is automatically a
layer that reflects badly.

**Why it matters.** Without the coupling, optimising for visible transmittance
drives silver thickness toward zero and the model reports an excellent coating.
With it, thinning the metal is penalised twice — in sheet resistance and in
emissivity — because those are two faces of the same free-carrier physics.

**Demonstrate it:**

```bash
python -c "
from pvdlowe.optimize.thickness import build
from pvdlowe.optics.integrate import performance_summary
from pvdlowe.materials.tco import tco
for d in (6, 8, 10, 14):
    r = performance_summary(build('Ag', d, 35., 35., tco('AZO')))
    print(f'{d:3d} nm  T_vis {r[\"T_vis\"]:.3f}  eps_h {r[\"emissivity_hemispherical\"]:.4f}  R_s {r[\"R_sheet\"]:5.2f}')
"
```

Transmittance rises as the silver thins; emissivity and sheet resistance both
worsen. The trade-off is the physics, not a penalty term someone added.

`test_thin_film_penalised_in_both_optics_and_transport` exists to catch a
refactor that decouples them — which would leave every interface test passing
while the model became nonsense.

---

## 2. The optics core (6 min)

`pvdlowe/optics/tmm.py`. A vectorised transfer-matrix solver: arbitrary layer
count, complex indices, both polarisations, oblique incidence, incoherent thick
substrate.

```python
def solve(wavelength_nm, indices, thicknesses_nm, angle_deg=0.0,
          polarization="both", want_layer_absorption=False):
```

It takes arrays, not scalars — a whole spectrum in one call, which is why a
composition sweep over 21 compositions × re-optimised geometry finishes in
minutes rather than hours.

**How we know it is right.** Not by inspection — by four checks against
closed-form answers:

| Test | What it pins |
|---|---|
| `test_bare_interface_matches_fresnel` | one interface, no film → exact Fresnel |
| `test_quarter_wave_antireflection` | λ/4 at √(n₁n₂) → exact zero reflectance |
| `test_energy_conservation` | R + T + A = 1 to 1e-10 on absorbing stacks |
| `test_polarisation_agrees_at_normal_incidence` | s and p must coincide at 0° |

> **Say:** "These are the tests worth having. They check the model obeys physical
> law, not that a function returns the right type."

`optics/integrate.py` then wraps the standards: EN 410 / ISO 9050 for visible
and solar transmittance, EN 12898 for emissivity weighted by a 283 K Planck
radiance, EN 673 for the hemispherical correction and U-value.

---

## 3. The material models (5 min)

`materials/metals.py` — Lorentz–Drude from Rakić et al. (1998), **with one
deliberate departure**:

```python
# Rakic's fitted Gamma_0 for silver implies rho = 4.4 uohm.cm against a true
# 1.587, because in the visible the Drude term trades off against the interband
# oscillators. Using the published value AND a thin-film size-effect multiplier
# counts the same scattering twice.
```

That double-count inflated modelled emissivity roughly threefold in an early
build. It is the most instructive bug in the project and it is documented in
`METHODOLOGY.md` §2 because anyone building on this will hit the same trap.

`electrical/thinfilm.py` — the full Fuchs–Sondheimer integral for surface
scattering, Mayadas–Shatzkes for grain boundaries, and a percolation model
below a critical thickness.

`materials/tco.py` — and one field worth flagging:

```python
metal_growth_factor: float = 1.0
```

An empirical multiplier on the metal's resistivity, per underlayer, calibrated
to a measured series. It exists because the model got a prediction wrong and
measurement corrected it — §5 below.

---

## 4. Scoring, and how it was audited (6 min)

`screening/scoring.py`. Derringer–Suich desirability, geometric aggregation by
default.

```python
def score(self, record) -> dict:
    """Geometric mean of per-criterion desirabilities."""
```

**Geometric, not arithmetic, and that is the whole point.** The brief asks that
the weighting prevent a candidate "winning simply because it has excellent
conductivity while being unacceptable optically". A weighted sum does not do
that — a candidate scoring zero on one criterion forfeits only that criterion's
weight. A geometric mean sends the whole score to zero.

`test_geometric_mean_punishes_a_zero` and
`test_arithmetic_mean_does_not_punish_a_zero_as_hard` pin both halves.

**The diagnostics are the interesting part**, because they audit their own
inputs:

```bash
python -m pvdlowe check-weights
```

This found four defects in the proposed weighting. The one to show:

```bash
python -c "
from pvdlowe.screening.scoring import criterion_correlations
print(criterion_correlations().round(3).to_string())
"
```

Emissivity and sheet resistance correlate at **r = 0.996** — they are the same
free-carrier response of the same layer — so weighting them separately put 40%
of the total on one physical quantity.

**And re-auditing that fix found a fifth defect.** Zeroing sheet resistance left
a triple-count untouched: silver mass, metal cost and supply risk correlate at
r = 1.000 and 0.991, because silver dominates metal cost and the supply risk in
this candidate set *is* silver's. Together they carried 36% of the effective
weight. Both are now zeroed and reported as derived figures.

The diagnostic itself was also wrong — it flagged correlated pairs regardless of
whether both carried weight, which buries the cases that matter. It now reports
`active_double_count` separately.

**One residual cannot be corrected, only disclosed:**

```bash
python -m pvdlowe check-weights | tail -18
```

The silver weight of 0.15 is a judgement, and it selects the answer. The winner
changes three times across a plausible range, and five of eight settings
separate first from second by under half a point. `weight_sweep()` reports the
transitions instead of a single ranking.

---

## 5. Provenance: a type, not a footnote (5 min)

`pvdlowe/provenance.py`.

```python
class Provenance(Enum):
    MEASURED, LITERATURE, LITERATURE_UNVERIFIED, MP_API,
    DFT_OWN, ML_SURROGATE, MODEL, CALIBRATED, ESTIMATE, HYPOTHESIS
```

Every quantity carries a grade, and `assert_reportable()` refuses to admit
HYPOTHESIS-grade values into headline tables.

> **Say:** "The brief itself cautions against putting DFT numbers for
> Ag₇₀Cu₂₉Ti₁ into a thesis as though they were established. This makes that a
> type constraint rather than a footnote, so it survives contact with a
> spreadsheet."

**It did real work.** Run:

```bash
python -m pvdlowe validate
```

Two of the brief's transcribed values fail model-independent consistency
checks, and the median error reported excludes two benchmarks whose figures
could not be traced to any source — because those two were the model's *closest*
agreements, and including them would have flattered it from 30.6% to 14.7%.

```bash
python -c "
from pvdlowe.validate import validate_model
print('default :', validate_model().attrs['median_rel_error_pct'], '%')
print('audit   :', validate_model(include_disputed=True).attrs['median_rel_error_pct'], '%  <- do not quote')
"
```

---

## 6. Functions that refuse rather than guess (4 min)

A convention worth naming, because it recurs:

| Location | Refuses to |
|---|---|
| `doe/sputter.py` | give an absolute deposition rate before calibration |
| `mp/client.py` | invent data when offline with a cold cache |
| `ml/surrogate.py` | fall back to an empirical potential when no MLIP is installed |
| `ml/surrogate.py` | compute adhesion above 4% lattice mismatch |

```python
raise ValueError(
    f"lattice mismatch {100*max(strain):.1f}% exceeds the {100*max_mismatch:.0f}% "
    "limit. Straining the film to fit would store elastic energy comparable "
    "with the adhesion being measured...")
```

That last one was added *after* the function returned 9.6 J/m² for Ag/Si₃N₄ —
three times any physical metal/oxide adhesion. The guard exists so the failure
recurs as an exception rather than as a plausible-looking number.

> **Say:** "Each of these was tempting to make helpful. Each would have produced
> fabricated data."

---

## 7. The ML surrogate, and what it did and didn't settle (5 min)

`pvdlowe/ml/surrogate.py`. This is what your 19 August question led to.

**Everything is gated:**

```python
def validate_against_mp(surrogate) -> DataFrame:
    """Reproduce two known Materials Project hull distances.
    The gate before any new prediction is believed."""
```

```bash
# on a machine with mace-torch installed
python examples/06_mlip_validate.py
```

**Result:** MACE-MP-0 and CHGNet both reproduce the gate, both under-predict by
20–47 meV/atom, and the Ag–Cu mixing energy is positive across the whole range,
fitting ΔE_mix = 0.287·x·(1−x).

**One correction to what I told you in August.** I described it as "two
independent models". They are not — MACE-MP-0 and CHGNet are trained on the same
Materials Project relaxation trajectories. Their agreement shows the bias is
*consistent*, not that it is absent. What it does establish is that the
under-prediction is inherited from the training data rather than being
architecture-specific, so ΔE_mix should be corrected upward rather than read as
a lower bound.

**And two calculations failed**, both documented with the diagnostic that caught
them:

| Attempt | Failed on |
|---|---|
| Interface adhesion | 5–21% lattice mismatch — measured elastic strain, not binding |
| Adatom wetting | ZnO(0001) termination changed the answer by 2.1 eV against 0.46 eV between materials |

The mechanism was then found by reading: a 2001 AGC patent measured 25 nm Ag
grains on crystalline ZnO against 15 nm on amorphous titania, by TEM, and named
the epitaxial Ag{111}/ZnO{0001} match as the cause.

---

## 7b. The review, and what fixing it found (3 min)

`docs/CODE_REVIEW.md` is a self-review, re-audited twice. **Every finding is now
closed**, and two of the fixes found defects the original review had missed —
which is the part worth mentioning.

| Finding | What it was | What the fix exposed |
|---|---|---|
| **M1** | two builders for the scoreable record, differing by ten keys | fixing construction was not enough: the emitted frame renamed a criterion and dropped three others, so re-scoring a composition series would have silently lost 0.25 of the weight |
| **M2** | bare `except Exception` returning a sentinel | the branch was unreachable — sub-percolation designs score badly rather than raising, so a failure there is a bug. Now counted: **0 in 1,284 evaluations** |
| **M3** | `_cache` declared, reset, never used | implemented rather than deleted; `stack()` was the hot path. 200 repeat calls now take **1 ms** |
| **N1** | `ml/` had no numerical coverage | extracting `judge_wetting()` found a third tie-handling defect: AZO and GZO share a proxy and return identical energies, so the verdict named GZO and declared "NOT consistent" when AZO — the measured winner — was tied with it |

> **Say:** "Two of the four fixes found something the review had missed. That is
> the argument for writing the test rather than reading the code — I had read
> that wetting function three times and corrected it twice by eye."

Demonstrate the last one:

```bash
python -c "
import pandas as pd
from pvdlowe.ml import judge_wetting
M = pd.DataFrame([
  {'dielectric':'Si3N4','proxy':'Si3N4','dE_wet_eV':-0.502,'site_spread_eV':0.2149},
  {'dielectric':'GZO','proxy':'ZnO','dE_wet_eV':0.6962,'site_spread_eV':0.0124},
  {'dielectric':'AZO','proxy':'ZnO','dE_wet_eV':0.6962,'site_spread_eV':0.0124}])
d = judge_wetting(M, 'Ag')
print(d.attrs['verdict'])
print(d.attrs['tied'])
"
```

Those are the numbers measured on Vertex AI. The nitride is excluded because its
site spread is 43% of its binding energy — the adatom was falling into
dangling-bond pockets on an artificially cleaved surface — and AZO and GZO are
reported as tied rather than ranked.

## 8. What that produced, and the one thing to take away (4 min)

The patent also reports four-point sheet resistance on the two underlayers:
**5.68 Ω/□ with a ZnO seed against 7.56 without**, a ratio of 1.331.
`metal_growth_factor` was calibrated independently from a different group's
*emissivity* series and gives 1.250. **Agreement to 6%** — the first
independent validation of a parameter in this framework.

**And it identified the framework's principal structural weakness:**

> The model treats each metal layer as though the layer beneath it did not shape
> its microstructure.

That single omission accounts for **both** `metal_growth_factor` and the
eightfold under-prediction of sputtered copper sheet resistance. They are one
effect appearing twice, not two separate caveats.

**One XRD scan measures it.** `pvdlowe/characterise/xrd.py` says in advance what
the scan should show:

```bash
python -c "
from pvdlowe.characterise import microstructure_signatures, grain_size_ladder
print(microstructure_signatures(0.70, 15.0).to_string(index=False))
print()
print(grain_size_ladder().to_string(index=False))
"
```

Segregated Ag–Cu gives two fcc peak sets at 38.12° and 43.32°; a solid solution
gives one at 39.54°. Scherrer width gives the grain size. The (111)/(200)
intensity ratio tests templating. **Three answers, one film, one afternoon.**

---

# Questions I would expect

**"Why not use an existing TMM library?"**
> Several exist and are good. The reason to write it is the coupling in §1 —
> the transport model has to feed the optical one, and a library takes indices
> as given. It is also 250 lines and pinned by four closed-form tests.

**"How much of this would I have to understand to change something?"**
> `optics/stack.py` for the central object, `electrical/thinfilm.py` for the
> coupling, `screening/scoring.py` for how candidates rank. That is most of it.
> The DoE, DFT, ML and XRD subpackages are optional and independent — nothing
> in the core imports them.

**"127 tests on 9,198 lines — is that enough?"**
> It is not a coverage figure and I would not claim it as one. The physics
> assertions are the valuable ones — the four closed-form checks in §2, the
> optics–transport coupling in §1, and the guards that stop each fixed defect
> from regressing. `report/` and `cli.py` are still thinly covered.
>
> The `ml/` module was the weakest part: it shipped with no coverage of its
> numerical paths, because MACE cannot be installed in the environment the
> suite runs in. That is now fixed by a route worth mentioning — the defects
> there were never in the energy evaluations, which are the model's job and are
> gated at runtime, but in the *judgement applied to the results*, and that is
> pure logic over tables. Extracting `judge_wetting()` made it testable without
> a backend, and writing those tests found a third defect in it.

**"What is the worst bug you found?"**
> The Rakić damping double-count in §3 — it inflated emissivity threefold. The
> most recent was three separate copies of the ML surrogate module, because each
> was written before the earlier one was found. Consolidated to one, with the
> old import path left as a shim that warns.

**"What would you change if you started again?"**
> Generate the report tables at build time instead of pasting them. They drifted
> from the computed values three times. `pvdlowe report` already does this
> correctly for the machine-generated output; the written report should have
> used the same path.

---

# If the session is cut to fifteen minutes

§1 (the coupling), §4 (scoring and the r = 0.996 finding), §8 (the structural
weakness and the XRD scan). Those are the design decision, the audit, and the
handover.
