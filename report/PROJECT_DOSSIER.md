# Project dossier

**Everything found, why it was pursued, what it produced, and what it means.**

Saint-Gobain Research India · Varun Mandy, Research Intern
`pvdlowe` v0.1.0 · 9,586 lines · 136 tests · 38 candidate architectures
https://github.com/VarunMandy/pvdlowe

---

## How to read this

Every section answers four questions in the same order: **what** was done,
**why** it was worth doing, **what** came out, and **what** it means. Sections
are ordered by how much they matter, not by when they happened.

**The single caveat that governs everything.** No films were deposited. Every
performance figure is a model output; median error against traceable literature
is 30.6%. The largest known error — an eightfold under-prediction of sputtered
copper sheet resistance — sits in the material most leading candidates use.

**Parts II and III do not depend on any measurement.** They are audits of the
brief's method and evidence, and they stand alone.

---

# PART I — THE ANSWER

## 1. What was asked

**What.** The brief proposed a materials-by-design programme for low-emissivity
coatings on float glass: a dielectric/metal/dielectric stack, AZO/Ag/AZO, asking
how much silver could be removed while holding visible transmittance, sheet
resistance and far-infrared reflectance.

**Why.** Silver dominates both the cost and the supply risk of Low-E glazing. At
roughly 0.105 g/m² for a 10 nm layer it is the single largest materials cost in
the stack.

**Result.** The question turned out to be underspecified in a way that changes
the answer, and the framework's most useful output was identifying that.

## 2. On the brief's own terms, almost no silver can be removed

**What.** Thin the silver in AZO/Ag/AZO; hold everything else.

**Result.**

| Ag nm | T_vis | ε_h | R_s | Status |
|---|---|---|---|---|
| 10.5 | 0.872 | 0.057 | 3.88 | OK |
| **10.0** | 0.876 | 0.060 | **4.18** | **OK — the limit** |
| 9.5 | 0.876 | 0.080 | 5.90 | **discontinuous** |

**Percolation is the binding constraint, not any of the three specified
properties.** A 5% thickness reduction costs 41% in sheet resistance.
Re-optimising both oxides at every thickness does not move it — the wall is in
the metal.

**Conclusion.** The literal answer is **about half a nanometre**. That is a
negative result and should be stated plainly. The 82–86% reduction reported below
comes from changing the **composition**, not the thickness.

## 3. The answer depends on a question the brief did not ask

**What.** The brief specifies no climate, and the weighting does not constrain
solar heat gain — which silently encodes a heating-dominated assumption, in a
project run at Saint-Gobain Research **India**.

**Result.** Adding the EN 410 / ISO 9050 solar-gain metrics and re-scoring gives
two rankings that **share one candidate out of ten**.

| | Heating-dominated | Cooling-dominated (India) |
|---|---|---|
| Lead candidate | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ (E10e) | AZO/Cu/AZO (M6) |
| T_vis | 0.877 | 0.738 |
| Emissivity ε_h | 0.051 | 0.046 |
| Sheet resistance | 3.13 Ω/sq | 2.87 Ω/sq |
| Solar heat gain g | 0.758 | 0.558 |
| Silver | 0.015 g/m² (**−86%**) | **zero** |
| Meets spec | **yes** | **no** — T_vis 0.738 < 0.80 |

Benchmark: AZO/Ag/AZO at 10 nm — T_vis 0.876, ε_h 0.060, R_s 4.18, 0.105 g/m².

**The mechanism is physical.** AZO is a *transparent conductive oxide*: free
carriers put a screened plasma edge at 1.25 µm, inside the solar band. Si₃N₄ is a
passive insulator. Same 11 nm copper layer, transmittance at 1200/1600/2000 nm:
AZO 0.240/0.115/0.068 against nitride 0.509/0.259/0.151.

**Conclusion.** A results table is meaningless without its weighting file. **The
climate must be specified before any recommendation is made.**

## 4. The composition optimum is 5–15 at.% Ag, not 70%

**What.** Eight composition curves — Ag 0–100% in 5% steps, geometry
re-optimised at every point, two microstructure models, two dielectrics, two
climates.

**Result.** **Every one peaks between 0 and 10 at.% Ag**, and the segregated/AZO
curve is flat from 5 to 40 at.% — a forgiving production window.

**It is a sustainability result, not a performance one.** Emissivity and sheet
resistance keep improving up to 50 at.% Ag. The score falls anyway because silver
mass carries weight: about 0.005 in emissivity for an 87% cut in silver.

**Conclusion.** Ag₇₀Cu₃₀ is outperformed in all eight combinations. **And the
brief's own basis for it does not transfer** — it traces to a 2022 paper
supporting 70/30 at 10 nm, but on **polycarbonate**, for first-surface coatings.
Given §9, that optimum does not carry to a glass line unchecked.

## 5. Two metal layers break a ceiling one cannot

**Why it was tested.** The best light-to-solar-gain ratio across all 38
single-metal candidates is **1.37**, against roughly 2.0 commercial. Under the
cooling profile no single-metal stack met the transmittance target at all. That
is an architectural limit, and no compositional search could have found it.

**Result.**

| Architecture | Metal | Dielectric | Geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| Single | Cu | AZO | 35/12/35 | 0.738 | 0.558 | 1.32 | 0.046 | 2.87 |
| **Double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.025 | 1.67 |
| Double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.024 | **1.33** |

**LSG 1.76 against a ceiling of 1.37 — 28% better.** A single film trades
transmittance against infrared reflectance along one curve; the dielectric
*between* two metals adds an interference degree of freedom.

Note the optimum geometry: **thin outer, thick middle**. A symmetric guess misses
it.

**A third layer is not worth adding** — LSG goes 1.33 → 1.76 → 1.81, and for
copper it collapses transmittance to 0.437.

**Conclusion.** The architecture argument stops at two layers, and silver
consumption doubles.

## 6. No candidate meets the Indian building code

**What.** Two criteria the brief left unspecified, anchored to ECBC 2017 rather
than invented: SHGC ≤ 0.27, assembly U ≤ 3.0 W/m²K.

**Basis warning.** ECBC specifies *assembly* values. The framework computes
centre-of-glass, single-pane. The conversion must be stated.

**Result.** Chaining a clear second pane (T_sol 0.83):

| | g single | g DGU | vs 0.27 |
|---|---|---|---|
| M6, the best | 0.558 | **0.463** | fails by +0.19 |
| N35e, the worst | 0.793 | 0.658 | fails by +0.39 |

**Not one of the 38 meets it, and the best misses by seventy per cent.**

**And the two targets are mutually incompatible.** Across 990 double-metal
designs, ECBC's 0.27 is reachable — at T_vis 0.644. The brief asks for 0.80.
Since ECBC's own visible minimum is 0.27, the conflict is with the brief's
**self-imposed** target, written for a heating climate.

**Conclusion.** External regulatory confirmation of §5. For Indian glazing the
single-metal architecture is not merely suboptimal — **it is non-compliant**, and
the double-metal stack becomes a requirement.

---

# PART II — THE AUDIT

## 7. Six defects in the proposed weighting

**Why this matters more than it sounds.** A scoring function is where every
physical result becomes a ranking. A defect here corrupts everything downstream
while leaving the physics untouched and every test passing.

**Four in the table as proposed:**

**(a) Silver consumption carried zero weight.** §14 has no line for it, though
§17 and §20 both name minimising silver as an objective.

> The thickness optimiser exploited this immediately, returning a design using
> **29% more silver than the benchmark, at a perfect 100/100.**

**(b) Emissivity and sheet resistance double-count** at **r = 0.996** — the same
free-carrier response of the same layer, 0.40 of the total on one quantity.

**(c) Targets at the specification minimum.** Setting T_vis's target to 0.80 —
the brief's *floor* — made the criterion flat where candidates differ. Across 181
oxide pairs clearing 0.80, transmittance spanned 0.800–0.881 while the **score
went down**.

**(d) The supply-risk band could not discriminate** — every silver-bearing
composition scored 0.1–0.28.

**Two more, found by re-auditing the fixes for (a) and (b):**

**(e) A triple-count.** Silver mass, metal cost and supply risk correlate at
**r = 1.000** and **0.991** — cost is silver in different units, and supply risk
in this set *is* silver's. Together **36% of the effective weight** on one
property.

**(f) Weight on criteria never populated.** Three criteria carried **0.30 of a
0.90 nominal total while being `None` for every candidate**, renormalising away
silently — a file stating emissivity at 0.25 was applying 0.42. One of them had
**no criterion definition at all**.

**And a seventh issue: aggregation.** The brief asks its weighting to prevent a
candidate "winning simply because it has excellent conductivity while being
unacceptable optically." A weighted sum cannot; a geometric mean can.

**A residual that cannot be corrected, only disclosed.** The silver weight of
0.15 is a judgement and it selects the answer — the winner is a 0.065 g/m² design
at weight 0 and silver-free at 0.30, changing three times in between. **Five of
eight settings separate first from second by under half a point.**

`weight_sweep()` reports the transitions instead of a single ranking. **The honest
recommendation is E10e at 0.15, E5e at 0.20–0.25, and the silver-free N6 at 0.30
and above — and choosing among them is a decision about how much silver
consumption matters to Saint-Gobain, not one the framework can make.**

**Conclusion.** Four corrected, two found and corrected on re-audit, one residual
disclosed. **General rules: a desirability target should be an aspiration, not a
specification minimum; and a weight that changes the winner should be reported as
a sweep, not a value.**

## 8. The evidence base: eight of fourteen claims changed

**Why.** Every citation carried `utm_source=chatgpt.com` — LLM-surfaced rather
than read from a publisher. Not necessarily wrong, but unchecked.

| Status | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — located, confirmed against abstract | 4 |
| **Disputed — appear in no locatable source** | **2** |
| Supported — corroborated independently | 3 |
| Not located after searching | 1 |

**Two citations cannot be supported** and should not be cited.

> **An uncomfortable corollary.** These two are the model's three *closest*
> agreements — 0.3%, 1.0%, 1.2% relative error. Excluding them, the median
> validation error rises from **14.7% to 30.6%**. `validate_model()` now excludes
> them by default, and a test fails if that exclusion ever starts *lowering* the
> reported error.

**One transcription question resolved the other way.** The brief quotes
1.59 µΩ·cm for a 10 nm Ag film. The journal states 1.59 — **the brief is
faithful** — while the group's own patent states 1.29, below bulk silver and
impossible. Both are anomalous by a factor of three: Fuchs–Sondheimer gives 4.74,
this framework 4.44, an independent 12 nm measurement 4.8.

## 9. A measurement that contradicts a model-independent limit

**What.** *Applied Surface Science* **578** (2022) reports AZO/Cu/AZO with T_vis
87.7%, R_s 9.96 Ω/sq and ε 0.055. **The brief's §16 conclusion rests entirely on
it.**

**Why it can be judged without any model.** For a sheet much thinner than the
wavelength, far-infrared reflectance is fixed by sheet resistance alone through
the impedance of free space. At 9.96 Ω/sq the floor is **ε ≥ 0.096**.

**Six explanations tested and eliminated:**

| Explanation | Outcome |
|---|---|
| Different samples | Abstract attributes all three to one sample |
| Transcription | Confirmed against the abstract |
| Far-IR glass index | Limit is 0.091–0.097 for n = 1.5–4.0 |
| Band-limited emissometer | Reads 5–8% **higher** — wrong direction |
| The framework's own convention | An industrial formula since 2000 agrees |
| **Measurement basis** | **Hemispherical fails by 51% rather than 42%** |

**And the two copper measurements sit in opposite positions:**

| | Technique | R_s | ε | Floor | |
|---|---|---|---|---|---|
| Miao 2014, HK PolyU | RF | 16.60 | 0.330 | 0.150 | **consistent** |
| ApSS 2022, Xi'an | DC | 9.96 | 0.055 | 0.096 | **below floor** |

**The measurement that obeys the limit is the one that contradicts this
framework**, by a factor of 7.7. The one that agrees with the model's optimism is
impossible. That contrast is stronger than either alone.

**Conclusion.** §16's conclusion should not be used until settled.

---

# PART III — WHERE THE MODEL WAS WRONG

## 10. The dielectric finding was reversed by measurement

**What.** The framework concluded Si₃N₄ beats AZO on transmittance by up to nine
points, on index matching. Cueva & Carretero (*Coatings* **13**, 1709, 2023,
open access, **full text read**) deposited five dielectrics under identical
conditions.

**Result — the opposite.** **AZO wins on emissivity (0.058) and transmittance,
despite the lowest refractive index of the five.** The authors' reason: silver
grows more efficiently on AZO.

**What was missing.** The model treated the dielectric purely as an interference
layer. The optical inputs were sound. What was absent is that **the underlayer
determines the quality of the metal grown on it.**

**The correction.** `metal_growth_factor` per underlayer, calibrated to that
series. The model now reproduces the measured ordering to 4–8%.

**The productive outcome is a hybrid** — AZO beneath for nucleation, nitride
above for durability — which is what industry already does:

| ID | Stack | T_vis | ε_h | Heating |
|---|---|---|---|---|
| **H1** | AZO/Ag/Si₃N₄ | **0.918** | 0.057 | 69.6 |
| M0 | AZO/Ag/AZO (benchmark) | 0.876 | 0.060 | 66.6 |
| **H2** | AZO/Cu/Si₃N₄ (silver-free) | 0.788 | **0.042** | 77.6 |

**H2 is the only architecture in both climate top-tens.**

## 11. The mechanism, and the principal structural weakness

**What.** Two ML surrogate calculations were run to find the mechanism behind
`metal_growth_factor`. **Both failed**, each documented with the diagnostic that
caught it:

| Attempt | Failed on | Diagnostic |
|---|---|---|
| Bulk adhesion | 5–21% lattice mismatch — measured elastic strain | unphysical 9.6 and −0.16 J/m² |
| Adatom wetting | termination changed the answer by 2.1 eV against 0.46 eV between materials | explicit termination sweep |

**A literature search found it in under an hour.** US 7,632,572 B2 (AFG → AGC →
Cardinal CG; **full text read**) deposited 16 nm Ag on amorphous TiOx and on a
5 nm ZnO seed over the same TiOx:

- **25 nm grains on ZnO against 15 nm on a-TiOx**
- {111}-oriented grains **two to three times larger** on ZnO
- the film on bare amorphous titania **clearly discontinuous**

**The inventors name the mechanism:** ZnO grows {0001}, orienting the silver to
grow {111}, and the epitaxial lattice match lowers sheet resistance and improves
adhesion.

**An unexpected validation.** The patent reports four-point sheet resistance —
**5.68 Ω/□ with the ZnO seed against 7.56 without**, ratio **1.331**.
`metal_growth_factor`, calibrated independently from a different group's
*emissivity* series, gives **1.250**. **Agreement to 6%** — a parameter fitted to
one dataset reproducing another it never saw.

> **The most consequential statement in this work.** The framework models each
> metal layer as though the layer beneath it did not shape its microstructure.
> That single omission accounts for **both** `metal_growth_factor` **and** the
> eightfold copper under-prediction. They are one effect appearing twice.

## 12. A seed layer may account for most of the copper discrepancy

**Result.** Six further AZO/Cu/AZO studies located:

| Film | Seed | R_s |
|---|---|---|
| AZO/**Ti**/Cu/AZO, *Opt. Lett.* 2017 | 1–2 nm Ti | **4.31 Ω/sq** |
| AZO/Cu/AZO, ApSS 2022 | none | 9.96 |
| AZO/Cu/AZO, Miao 2014 | none | 16.6 |
| **this framework, 15 nm Cu** | — | **2.16** |

**The framework is eightfold optimistic against unseeded copper and roughly
twofold against seeded copper.** So the model is not wrong about copper as a
material — **it is wrong about poorly nucleated copper.**

Same mechanism as §11, now visible in three independent places.

**Conclusion.** The thickness series should include a seeded arm. One extra
target converts the largest known error from an anomaly into a process variable.

## 13. Corrections to the project's own conclusions

Five conclusions stated during this work were overturned **by the work itself**,
and are recorded rather than quietly fixed.

| Claim | Overturned by |
|---|---|
| An optimum exists at Ag₆₀Cu₄₀ | A three-point artifact; at 5% resolution the curve is monotonic |
| The Ti barrier variant beats the ternary | An artifact of silver carrying zero weight |
| A band-limited emissometer explains the ApSS emissivity | Tested: it reads 5–8% *higher* |
| Adatom wetting reproduces the measured ordering | A termination sweep showed it resolved slab index |
| The brief mistranscribed a resistivity | The journal says 1.59; two publications disagree |

**Three of five are the same error: reading structure into too few points.**

**Two are a different error, and it recurred: holding a fragment of a source and
treating it as the source.** The project's own `LITERATURE` versus
`LITERATURE_UNVERIFIED` grading exists to prevent exactly this and was being
applied to data but not to reasoning.

---

# PART IV — WHAT WAS COMPUTED

## 14. Ag–Cu has no stable ordered compound

All fifteen nominated systems screened against the Materials Project convex hull.
Two intermediate Ag–Cu phases exist and **neither is stable**: Cu₃Ag at
**0.0904 eV/atom**, CuAg₃ at **0.0857** — well above k_BT at deposition.

**A second finding.** Cu–Ti has 8 near-hull phases and Al–Cu has 10, so a dilute
Ti or Al addition has stable intermetallics available to precipitate rather than
remaining in solution — a second mechanism for the ternary underperforming.

## 15. The dilute corner is thermodynamically favoured

MACE-MP-0 and CHGNet on 32-site fcc supercells, **gated against the two known
hull distances before any prediction was accepted**. Positive across the whole
range: **ΔE_mix = 0.287·x·(1−x)**, fitting to ±6 meV/atom.

**A self-check that matters more than the gate.** At Ag 25 at.% the disordered
solution sits 13 meV/atom **below** ordered Cu₃Ag — no ordering tendency at all,
exactly what an empty hull implies, reached independently.

| Ag at.% | ΔE_mix | ×kT (550 K) |
|---|---|---|
| 70 — the brief's priority | 0.0602 | 1.27 |
| 15 | 0.0366 | 0.77 |
| 10 | 0.0258 | 0.54 |
| 5 | 0.0136 | 0.29 |

**In the dilute corner the driving force to separate falls below thermal energy
at deposition.** §4 found the microstructure hypotheses converge there; the
thermodynamics supply the reason.

**The dilute optimum is supported three independent ways:** least silver, best
corrected score, weakest tendency to phase-separate.

**Cross-checked, with a caveat.** Both models under-predict, so the bias is
inherited from shared training data. **They are not independent** — agreement
shows the bias is consistent, not absent. And GGA itself underestimates
Cu–transition-metal formation energies by ~40%, so two errors act in series. The
conclusion **holds at 5–10 at.% Ag, marginal at 15%**.

## 16. What a surrogate cannot do

**Cannot, at all:** optical constants, dielectric functions, band gaps,
emissivity. These models carry no electronic structure.

**And a conductivity result does not transfer to an optical one.** The
emissivity–sheet resistance link assumes a low-damping Drude metal, a property of
*crystalline* silver. A conductivity gain from amorphisation cannot be assumed to
give the corresponding emissivity gain.

---

# PART V — WHAT REMAINS

## 17. The critical unknown

The framework validates against silver to within 0.4% and **fails on copper** by
roughly eightfold. **Six of the leading candidates are copper-based.**

**The classical size effect is eliminated.** An exhaustive scan over the entire
admissible range of published scattering parameters reaches only **4.42 Ω/sq
against the 16.6 to be explained** — short by a factor of 3.8. Grain structure is
the leading hypothesis; §12 adds that a seed layer recovers most of the gap.

**If that reading is right, copper's obstacle is film quality, not physics** — an
engineering problem with known levers.

## 18. The experiment that resolves it

**One XRD scan, one film, an afternoon — three questions answered.**

| Measurement | Question |
|---|---|
| Peak count and position | **Microstructure** — segregated gives two fcc sets, a solid solution one |
| Scherrer width | **Grain size**, and therefore `grain_size_ratio` |
| (111)/(200) vs the powder value of 2.2 | **Templating**, the mechanism of §11 |

**A second, independent discriminator.** Sheet resistance separates the
hypotheses by a number; diffraction by *peak count*. Two unrelated observables
agreeing is far stronger than either — and both come from one film.

**Four requirements, all cheap:** scan to 2θ = 100° not 60; grazing incidence
rather than Bragg–Brentano, because a copper peak here is marginal and a null
would otherwise be ambiguous; a 30 nm uncapped calibration film; and a seeded
arm.

**Pre-registered decision rules** — four outcomes, each with what it means and
what to do, **including the one where six candidates fall over.**

## 19. The questions only SGRI can answer

**Which stack is the right baseline.** This work benchmarks against 10 nm Ag at
ε_h 0.060, from the brief — whose citations for it are the two **disputed**
entries. Saint-Gobain's own patents claim **12.5–16 nm targeting ε ≤ 0.038**,
which the model says needs 14–16 nm. **If production runs there, the reported
reductions are measured against a stack that would not meet SGRI's own spec.**

**Which transmittance target is real.** The brief's 0.80, or ECBC compliance at
0.644. §6 shows they cannot both be met.

---

# PART VI — WHAT WAS BUILT

## 20. The framework

9,586 lines, 136 tests, twelve subpackages, fourteen CLI commands.

**The design decision that matters.** Film resistivity feeds the Drude damping,
so a metal layer too thin to conduct is automatically one that reflects poorly.
Without that coupling, optimising for transmittance drives silver thickness to
zero and reports an excellent coating.

**Validated against closed-form answers**, not by inspection: exact Fresnel at a
bare interface, an exact null for a quarter-wave layer, energy conservation to
10⁻¹⁰, s and p agreeing at normal incidence.

**Provenance as a type.** Eleven evidence grades, and a guard that refuses
hypothesis-grade values in headline tables. It is what kept the Ti-ternary
predictions out of the results.

**Functions that refuse rather than guess.** The sputter model raises when
uncalibrated; the MP client raises when offline with a cold cache; the surrogate
refuses to fall back to an empirical potential; the adhesion calculation refuses
above 4% lattice mismatch. **Each was tempting to make helpful; each would have
produced fabricated data.**

## 21. Known limitations

**No experimental validation.** Median error 30.6% against traceable literature.

**The principal structural weakness**, restated because it governs the rest: the
framework models each metal layer as though the layer beneath it did not shape
its microstructure.

**Fitted parameters.** Specularity and grain-boundary reflection are fitted;
Si₃N₄ and TiO₂ optical constants are `ESTIMATE` grade.

**Illuminant approximation, quantified.** T_vis moves 0.1% over 5000–7500 K;
T_sol moves 8.3%. T_sol, g and LSG carry a 5–10% systematic.

**Scores are not portable.** They moved ~25 points as the §7 defects were fixed.
**A score is not a property of a material.**

**Not modelled at all:** roughness, interdiffusion, damp-heat and abrasion
durability, adhesion, agglomeration kinetics, amorphous metal layers.

---

# CONCLUSION

**What this project established.** A better composition — 5–15 at.% Ag rather
than 70%, on three independent grounds. A better material class — silicon
nitride, outside the brief's framing, with the hybrid arrangement industry
already uses. A better architecture — two metal layers reaching LSG 1.76 against
a ceiling of 1.37. And a specified climate dependency, with the two profiles
sharing one candidate out of ten.

**What it corrected.** Six defects in the proposed weighting, one of which let
the optimiser return **29% more silver than the incumbent at a perfect score**.
Two citations that cannot be traced. One measurement inconsistent with a
model-independent limit, six explanations eliminated. And five of its own
conclusions, overturned and recorded rather than hidden.

**What it cannot claim.** Nothing has been deposited. The rankings are hypotheses
ordered by physics. Their principal weakness is known, quantified, and addressed
by a specified experiment.

**The recommendation.** One XRD scan, one film, an afternoon.

**And two questions to Saint-Gobain:** which stack is the right baseline, and
which transmittance target is real.

> A model that identifies the measurement capable of falsifying it is more useful
> to an experimental programme than one that does not. That is what this
> framework is for, and it is what it delivered.
