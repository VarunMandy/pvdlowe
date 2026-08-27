# Code walkthrough

For a session with the code open. **35–45 minutes** at full length; a
fifteen-minute path is marked at the end. Bracketed text is guidance, not
speech. Every block below is real and runnable.

**Setup:**

```bash
git clone https://github.com/VarunMandy/pvdlowe.git && cd pvdlowe
pip install -e .
python tests/run_tests.py        # 136 passed
```

Two companion HTML views open in a browser with no install:
`docs/project_map.html` (what every file is) and `docs/loc_review.html` (ten
places worth stopping on). `docs/INTERACTIVE_SCRIPT.md` scripts those.

---

## 0. Shape of it (3 min)

9,586 lines, 12 subpackages, 136 tests. **The dependency order runs one way:**

```
constants  provenance  spectra          ← no dependencies
     │
materials/  ── dispersion, metals, alloys, tco, glass
     │
electrical/ ── thinfilm, calibrate      ← size effect, percolation
     │
optics/     ── tmm, stack, integrate    ← transfer matrix, standards
     │
screening/  ── elements, scoring, pareto, candidates
     │
optimize/   ── thickness, sweep
     │
report/  validate/  cli/
```

Independent of the stack: `doe/`, `dft/`, `mp/`, `ml/`, `characterise/`, `api/`.

> **Say:** "Nothing below optics knows what a coating is. `tmm.py` solves a
> stack of complex indices — it would work for a laser mirror. The domain
> knowledge lives above it, and that is why the optics could be validated
> against closed-form answers rather than against my expectations of what a
> Low-E stack should do."

---

## 1. The design decision everything rests on (8 min)

**Spend the time here.** Everything else is implementation.

`pvdlowe/optics/stack.py`:

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

and in `metal_dispersion()`:

```python
disp = alloy.dispersion(alloy.bulk_resistivity_uohm_cm * ratio)
```

**The electrical model feeds the optical one.** Film resistivity sets the Drude
damping, so a metal layer too thin to conduct is automatically one that reflects
badly.

**Demonstrate it:**

```bash
python -c "
from pvdlowe import dmd, performance_summary
for d in (6, 8, 10, 14):
    r = performance_summary(dmd('Ag', metal_thickness_nm=d))
    print(f'{d:3d} nm  T_vis {r[\"T_vis\"]:.3f}  eps_h {r[\"emissivity_hemispherical\"]:.4f}  R_s {r[\"R_sheet\"]:6.2f}')
"
```

```
  6 nm  T_vis 0.714  eps_h 0.3987  R_s  71.33
  8 nm  T_vis 0.799  eps_h 0.2797  R_s  29.89
 10 nm  T_vis 0.876  eps_h 0.0603  R_s   4.18
 14 nm  T_vis 0.825  eps_h 0.0389  R_s   2.53
```

> **The counterintuitive part, and the point of the demo:** transmittance
> *peaks* at 10 nm. Thinning below that makes the film less transparent, not
> more. Below percolation it is discontinuous islands that scatter and absorb
> rather than a mirror that transmits.
>
> Without the coupling, optimising for transmittance drives the silver to zero
> and the model reports an excellent coating. **Decouple these two and every
> interface test still passes while the model becomes nonsense.**

`test_thin_film_penalised_in_both_optics_and_transport` exists to catch that.

---

## 2. How we know the optics is right (6 min)

`pvdlowe/optics/tmm.py` — vectorised transfer matrix: arbitrary layers, complex
indices, both polarisations, oblique incidence, incoherent thick substrate. It
takes arrays rather than scalars, which is why a 168-point composition series
with geometry re-optimised at every point finishes in minutes.

**Not validated by inspection — against four closed-form answers:**

| Check | Expected | Got |
|---|---|---|
| Bare glass interface | Fresnel 0.04258 | **0.04258** |
| Quarter-wave at √(n₁n₂) | exact null | to 1e-15 |
| Absorbing stack | R + T + A = 1 | to 1e-10 |
| Normal incidence | s = p identically | identical |

> **Say:** "These are the tests worth having. They check the model obeys
> physical law, not that a function returns the right type. A test asserting
> `T_vis == 0.876` would pass forever while the physics rotted underneath it."

`optics/integrate.py` then applies the standards: EN 410 / ISO 9050 for
transmittance, EN 12898 for emissivity against a 283 K Planck radiance, EN 673
for the U-value.

---

## 3. The material models, and the most instructive bug (5 min)

`materials/metals.py` — Lorentz–Drude from Rakić et al. (1998), with one
deliberate departure:

```python
# Rakic's fitted Gamma_0 for silver implies rho = 4.4 uohm.cm against a true
# 1.587, because in the visible the Drude term trades off against the
# interband oscillators. Using the published value AND a thin-film
# size-effect multiplier counts the same scattering twice.
```

> **Say:** "A factor of 2.8. The published damping is a fitting parameter, not
> a physical one. I used it and multiplied by a size-effect ratio — that
> **inflated modelled emissivity roughly threefold.** It is in METHODOLOGY §2
> because anyone building on published optical fits will hit exactly this."

`electrical/thinfilm.py` — full Fuchs–Sondheimer, Mayadas–Shatzkes, and
percolation below a critical thickness. The magnitude is easy to
underestimate: **a 10 nm silver film is 2.79× more resistive than bulk.**

That single fact caught one of the brief's transcribed values — 1.59 µΩ·cm
quoted for a 10 nm film, when bulk silver is 1.587 and the mean free path is
53 nm.

---

## 4. Scoring, and the diagnostics that audit it (7 min)

`screening/scoring.py` — Derringer–Suich desirability, **geometric**
aggregation.

> **Say:** "Geometric, not a weighted sum, and that is the whole point. The
> brief asks that the weighting prevent a candidate winning 'simply because it
> has excellent conductivity while being unacceptable optically'. A weighted
> sum cannot do that — a zero forfeits only that criterion's weight. A
> geometric mean sends the whole score to zero."

**The valuable part is that it audits its own inputs:**

```bash
python -m pvdlowe check-weights | tail -25
```

Six defects were found this way. The correlations to show:

| Pair | r |
|---|---|
| emissivity ↔ sheet resistance | 0.978 |
| silver mass ↔ metal cost | **1.000** |
| silver mass ↔ supply risk | 0.991 |

> **Say:** "Three criteria that are one physical quantity, carrying 36% of the
> effective weight between them. Silver dominates metal cost so completely that
> cost is the same number in different units."

**And the residual that cannot be corrected**, in the same output:

> "The silver weight of 0.15 is a judgement, not a measurement, and it selects
> the answer. At zero the winner carries 0.065 g/m²; at 0.30 it carries none,
> and it changes three times in between. Five of eight settings separate first
> from second by under half a point. So the honest output is the sweep, not a
> ranking — and choosing among them is a decision about how much silver
> consumption matters to Saint-Gobain."

---

## 5. Provenance as a type (4 min)

`pvdlowe/provenance.py` — eleven evidence grades, from `MEASURED` down to
`HYPOTHESIS`, and `assert_reportable()` refuses hypothesis-grade values in
headline tables.

> **Say:** "The brief itself cautions against putting DFT numbers for the dilute
> titanium ternary into a thesis as though they were established. This makes
> that a type constraint rather than a footnote, so it survives contact with a
> spreadsheet. It did real work — it is what kept those predictions out of the
> results tables when I was tempted."

```bash
python -m pvdlowe validate | tail -14
python -c "
from pvdlowe.validate import validate_model
print('default :', validate_model().attrs['median_rel_error_pct'], '%')
print('audit   :', validate_model(include_disputed=True).attrs['median_rel_error_pct'], '%  <- do not quote')
"
```

> "30.6% against 14.7%. The lower figure includes two benchmarks whose numbers
> match no locatable source — and they happen to be the model's three closest
> agreements. Excluding them is the conservative choice, and a test fails if
> that exclusion ever starts *lowering* the reported error."

---

## 6. Functions that refuse rather than guess (3 min)

| Location | Refuses to |
|---|---|
| `doe/sputter.py` | give an absolute deposition rate before calibration |
| `mp/client.py` | invent data when offline with a cold cache |
| `ml/surrogate.py` | fall back to an empirical potential with no MLIP installed |
| `ml/surrogate.py` | compute adhesion above 4% lattice mismatch |

The last was added **after** the function returned 9.6 J/m² for Ag/Si₃N₄ —
three times any physical metal/oxide adhesion.

> **Say:** "Each of these was tempting to make helpful. Each would have produced
> fabricated data."

---

## 7. The review, and what fixing it found (4 min)

`docs/CODE_REVIEW.md`. **Every finding is closed**, and two of the fixes found
defects the review had missed — which is the part worth mentioning.

| Finding | What it was | What the fix exposed |
|---|---|---|
| **M1** | two builders for the scoreable record, differing by ten keys | fixing construction was not enough — the emitted frame renamed a criterion and dropped three others, so re-scoring a series would have lost 0.25 of the weight |
| **M2** | bare `except Exception` returning a sentinel | the branch was unreachable. Now counted: **0 failures in 1,284 evaluations** |
| **M3** | `_cache` declared, reset, never used | implemented rather than deleted; `stack()` was the hot path. **200 calls now take 1 ms** |
| **N1** | `ml/` had no numerical coverage | extracting `judge_wetting()` found a third tie-handling defect |

**Demonstrate the last:**

```bash
python -c "
import pandas as pd
from pvdlowe.ml import judge_wetting
M = pd.DataFrame([
  {'dielectric':'Si3N4','proxy':'Si3N4','dE_wet_eV':-0.502,'site_spread_eV':0.2149},
  {'dielectric':'GZO','proxy':'ZnO','dE_wet_eV':0.6962,'site_spread_eV':0.0124},
  {'dielectric':'AZO','proxy':'ZnO','dE_wet_eV':0.6962,'site_spread_eV':0.0124}])
d = judge_wetting(M, 'Ag')
print(d.attrs['verdict']); print(); print(d.attrs['tied'])
"
```

Those are the figures measured on Vertex AI. The nitride is excluded because its
site spread is 43% of its binding energy — the adatom was falling into
dangling-bond pockets on an artificially cleaved surface — and AZO and GZO are
reported as tied rather than ranked, because they share a proxy and return
identical energies.

> **Say:** "Two of the four fixes found something the review had missed. That is
> the argument for writing the test rather than reading the code — I had read
> that wetting function three times and corrected it twice by eye."

---

## 8. What it produced, and the one thing to take away (5 min)

`pvdlowe/characterise/xrd.py`:

```bash
python -c "
from pvdlowe.characterise import microstructure_signatures, grain_size_ladder
print(microstructure_signatures(0.05, 15.0).to_string(index=False))
print()
print(grain_size_ladder(metal='Cu').to_string(index=False))
"
```

> **The framework's principal structural weakness: it models each metal layer as
> though the layer beneath it did not shape its microstructure.**
>
> That one omission accounts for both the empirical `metal_growth_factor` and
> the eightfold under-prediction of sputtered copper sheet resistance. They are
> one effect appearing twice, not two separate caveats.
>
> And one XRD scan measures it. Scherrer width gives the grain size; peak count
> discriminates the microstructure hypotheses by a second independent route;
> the (111)/(200) intensity ratio tests the templating mechanism. **Three
> answers, one film, one afternoon.**

---

# Questions to expect

**"Why not use an existing TMM library?"**
> Several exist and are good. The reason to write it is the coupling in §1 — the
> transport model has to feed the optical one, and a library takes indices as
> given. It is also 250 lines and pinned by four closed-form tests.

**"How much would I need to understand to change something?"**
> `optics/stack.py` for the central object, `electrical/thinfilm.py` for the
> coupling, `screening/scoring.py` for how candidates rank. That is most of it.
> The DoE, DFT, ML and XRD subpackages are optional and independent — nothing in
> the core imports them.

**"136 tests on 9,586 lines — is that enough?"**
> It is not a coverage figure and I would not claim it as one. The physics
> assertions are the valuable ones, plus a guard for every fixed defect.
> `report/` and `cli.py` are thinly covered, and the geometry code in `ml/` is
> exercised by runs on Vertex AI rather than by the suite — stated in the review
> rather than glossed.

**"Which defect worried you most?"**
> M1, because it was invisible. Everything scored identically, every test
> passed, and it would have stayed that way until someone populated a criterion.
> Nothing about the output would have looked wrong.

**"What is the worst bug you found?"**
> The Rakić damping double-count in §3 — it inflated emissivity threefold. The
> most recent was three separate copies of the ML surrogate module, each written
> before the previous was found. Consolidated to one, with the old import path
> left as a shim that warns.

**"What would you change if you started again?"**
> Generate the report tables at build time instead of pasting them. They drifted
> from the computed values three times. `pvdlowe report` already does this
> correctly for machine-generated output; the written report should have used
> the same path.

---

# If the session is cut to fifteen minutes

**§1** the coupling, **§4** the scoring audit, **§8** the structural weakness
and the scan. Those are the design decision, the audit, and the handover.
