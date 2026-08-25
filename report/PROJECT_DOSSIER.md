# Project dossier — computational screening of sustainable Low-E PVD coatings

**Everything found, why it was pursued, what it produced, and what it means.**

Saint-Gobain Research India · Varun Mandy, Research Intern
Framework: `pvdlowe` v0.1.0 · https://github.com/VarunMandy/pvdlowe
8,995 lines · 112 tests · 38 candidate architectures

---

## How to read this document

Every section answers four questions in the same order: **what** was done,
**why** it was worth doing, **what came out**, and **what it means**. Sections
are ordered by how much they matter, not by when they happened.

**The single most important caveat, stated once here and assumed throughout:**
no films were deposited. Every performance figure is a model output. The
framework's own validation puts its median error at 30.6% against traceable
literature, and its largest known error — an eightfold under-prediction of
sputtered copper sheet resistance — sits in the material most leading
candidates use.

---

# PART I — THE ANSWER

## 1. What the project was asked

**What.** The brief `PVD_Usecase.docx` proposed a materials-by-design programme
for low-emissivity coatings on float glass: a dielectric/metal/dielectric stack,
AZO/Ag/AZO, with the question of how much silver could be removed while holding
visible transmittance, sheet resistance and far-infrared reflectance.

**Why.** Silver dominates both the cost and the supply risk of Low-E glazing.
At roughly 0.105 g/m² for a 10 nm layer it is the single largest materials cost
in the stack, and its supply is concentrated and volatile.

**Result.** The question turned out to be underspecified in a way that changes
the answer, and the framework's most useful output was identifying that.

**Conclusion.** See §2.

## 2. The answer depends on a question the brief did not ask

**What.** The brief specifies no climate, and the weighting derived from it does
not constrain solar heat gain. That omission silently encodes a heating-dominated
assumption.

**Why it matters.** Saint-Gobain Research *India*. If the target application is
Indian architectural glazing, the unstated assumption is the wrong one.

**Result.** Adding the EN 410 / ISO 9050 solar-gain metrics and re-scoring
produces two rankings that share **one candidate out of ten**.

| | Heating-dominated | Cooling-dominated (India) |
|---|---|---|
| Lead candidate | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ (E10e) | AZO/Cu/AZO (M6) |
| T_vis | 0.877 | 0.738 |
| Emissivity ε_h | 0.0511 | 0.0463 |
| Sheet resistance | 3.13 Ω/sq | 2.87 Ω/sq |
| Solar heat gain g | 0.758 | 0.558 |
| Silver | 0.015 g/m² (**−86%**) | **zero** |
| Meets full spec | yes | **no** — T_vis 0.738 < 0.80 |

Benchmark for comparison — AZO/Ag/AZO at 10 nm: T_vis 0.876, ε_h 0.060,
R_s 4.18 Ω/sq, 0.105 g/m² Ag, $0.85/m².

**The mechanism is physical, not a scoring artifact.** AZO is a *transparent
conductive oxide*: its free carriers give a screened plasma wavelength at
1.25 µm, inside the solar band, so it rejects solar near-infrared. Si₃N₄ is a
passive insulator, transparent throughout.

| λ (nm) | 1200 | 1600 | 2000 | 2400 |
|---|---|---|---|---|
| Transmittance, AZO stack | 0.240 | 0.115 | 0.068 | 0.046 |
| Transmittance, Si₃N₄ stack | 0.509 | 0.259 | 0.151 | 0.099 |

Same 11 nm copper layer in both. The conductive oxide is doing solar-control
work the nitride cannot.

**Conclusion.** A results table is meaningless without its weighting file.
**The climate must be specified before any recommendation is made.** For a
heating climate the nitride stack at 5–10 at.% Ag beats the benchmark on
transmittance, emissivity and sheet resistance simultaneously while using an
eighth of the silver. For India, no single-metal architecture in the set meets
the specification, and the framework is ranking near-misses.

## 3. The composition optimum is 5–15 at.% Ag, not 70%

**What.** The brief nominates Ag₇₀Cu₃₀ as the priority composition. Eight
composition curves were run — Ag 0–100% in 5% steps, geometry re-optimised at
every point, across two microstructure models, two dielectrics and two climates.

**Why.** If the optimum is elsewhere, the entire experimental programme is
pointed at the wrong composition.

**Result.** Every one of the eight curves peaks between 0 and 10 at.% Ag.

| Profile | Microstructure | Dielectric | Optimum Ag | Plateau |
|---|---|---|---|---|
| Heating | Segregated | Si₃N₄ | **0.05** | 0.00–0.20 |
| Heating | Segregated | AZO | **0.10** | **0.05–0.40** |
| Cooling | Either | Either | 0.00 | 0.00–0.15 |

**And it is a sustainability result, not a performance one.** Emissivity and
sheet resistance keep *improving* up to 50 at.% Ag — 0.0386 and 2.59 Ω/sq, the
best in the series. The score falls anyway because silver mass carries weight.
The trade is about 0.005 in emissivity for an 87% cut in silver, and it is only
the right trade because silver was decided to matter.

**Plateau width matters more than peak position for a production process.** The
segregated/AZO curve is flat from 5 to 40 at.% Ag — a forgiving window.

**Conclusion.** Ag₇₀Cu₃₀ is outperformed in all eight combinations. Design at
5–15 at.% Ag. The brief's own justification for 70/30 traces to a 2022 paper
that does support it — but on **polycarbonate**, for first-surface coatings, and
§9 establishes that the underlayer determines metal grain structure, so that
optimum does not transfer to a glass line unchecked.

## 4. Two metal layers break a ceiling one cannot

**What.** `MultiMetalCoating` generalises the architecture to n metal layers
separated by n+1 dielectrics.

**Why.** The best light-to-solar-gain ratio across all 38 single-metal
candidates is **1.37**, against roughly 2.0 for commercial solar-control
glazing. Under the cooling profile no single-metal stack met the transmittance
target at all. That is an architectural limit, and no compositional search
could have found it.

**Result.**

| Architecture | Metal | Dielectric | Geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| Single | Cu | AZO | 45/12/45 | 0.738 | 0.558 | 1.32 | 0.046 | 2.87 |
| **Double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.025 | 1.67 |
| Double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.024 | **1.33** |

**LSG 1.76 against a ceiling of 1.37 — 28% better.**

**Why one layer cannot.** A single film trades transmittance against infrared
reflectance along one curve; thickness moves along it but never off it. The
dielectric *between* two metals adds an interference degree of freedom — the two
reflections can cancel in the visible while adding in the infrared.

Note the optimum geometry: **thin outer dielectrics (15 nm), thick middle
(60 nm)**. A symmetric guess misses it.

**A third layer was tested and is not worth adding.** LSG goes 1.33 → 1.76 →
1.81 for n = 1, 2, 3. The third buys 0.05 for a 25% silver increase, and for
copper it is actively harmful — transmittance collapses to 0.437.

**Conclusion.** The architecture argument stops at two layers. Silver
consumption doubles, since each layer must independently clear percolation near
10 nm, so double-Ag scores badly on the sustainability profiles despite being
the best solar-control design found.

---

# PART II — THE AUDIT

## 5. Four defects in the proposed weighting

**What.** The brief's §14 specifies criteria and weights. Encoding that table
literally produced a scoring function that did not measure the project's stated
objective. All four defects were found by the framework's own diagnostics
(`pvdlowe check-weights`).

**Why this matters more than it sounds.** A scoring function is where every
physical result gets converted into a ranking. A defect here corrupts everything
downstream while leaving the physics untouched and every test passing.

**Result.**

**(a) Silver consumption carried zero weight.** §14's table has no line for it,
although §17 and §20 both name minimising silver as an objective. Silver mass
was computed, displayed, even reported as the limiting criterion — and
contributed nothing to the score.

> The thickness optimiser exploited this immediately, returning a design using
> **29% more silver than the benchmark, at a perfect 100/100.**

**(b) Emissivity and sheet resistance double-count.** They correlate at
**r = 0.996** across the candidate set — both are the free-carrier response of
the same layer — so weights of 0.25 and 0.15 put 0.40 of the total on one
physical quantity.

**(c) Targets set at the specification minimum.** Derringer–Suich desirability
saturates at 1.0 once a target is reached. Setting T_vis's target to 0.80 — the
brief's *floor of acceptability* — made the criterion flat exactly where
candidates differ. Across 181 oxide pairs clearing 0.80, transmittance spanned
0.800–0.881 while the **score went down**, 74.99 to 73.30.

**(d) The supply-risk band could not discriminate.** At floor 8.0 against
candidate values of 4.5–7.5, every silver-bearing composition scored 0.1–0.28.

**A fifth issue: aggregation.** The brief states its weighting should prevent a
candidate "winning simply because it has excellent conductivity while being
unacceptable optically". A weighted arithmetic sum does not achieve this — a
candidate scoring zero on one criterion forfeits only that criterion's weight.
A geometric mean does.

**A fifth defect, found by re-auditing the fix for the second.** Zeroing sheet
resistance removed one double-count and left a triple-count untouched:

| Pair | r |
|---|---|
| Silver mass ↔ metal cost | **1.000** |
| Silver mass ↔ supply risk | 0.991 |

Silver dominates metal cost so completely that cost is the same quantity in
different units, and supply risk in this candidate set *is* silver's supply
risk. Together they carried **36% of the effective weight on one physical
property**. Both are now weighted 0.0 and reported as derived figures; the
effective concentration falls to 25%, and no criterion pair both carries weight
and correlates.

**And a residual that cannot be corrected, only disclosed.** The silver weight
of 0.15 is a judgement, not a measurement, and it selects the answer: the winner
is a 0.065 g/m² design at weight 0, and silver-free at 0.30. Five of eight
settings separate first from second by under 0.5 points, which means the ranking
is resolving noise in a value judgement rather than distinguishing candidates.

`weight_sweep()` reports the transitions instead of a single ranking. **The
honest recommendation is: E10e at weight 0.15, E5e at 0.20–0.25, and the
silver-free N6 at 0.30 and above — and choosing among them is a decision about
how much silver consumption matters to Saint-Gobain, not one the framework can
make.**

**A sixth, found by asking what the framework does not predict.** Three criteria
carried 0.30 of the 0.90 nominal weight while being `None` for every candidate,
so a third of the weight renormalised away silently — a file stating emissivity
at 0.25 was applying 0.42. One of them, `structural_stability`, had no criterion
definition at all and could never have scored. All three weighted 0.0; the
ranking is unchanged, which is the point.

`structural_stability` is now partly populatable from the Materials Project
screening and the surrogate mixing energies, and is deliberately left
unpopulated: doing so would change every ranking on values carrying 20–40%
systematic error, at a weight nobody derived. Populating a criterion and
choosing its weight are one decision, and it belongs to whoever continues.

**Conclusion.** Four defects corrected, two more found and corrected on
re-audit, and one residual disclosed rather than papered over. None applied silently.
**General rule extracted: a desirability target should be an aspiration, not a
specification minimum — and a weight that changes the winner should be reported
as a sweep, not a value.**

## 6. The evidence base: eight of fourteen claims changed

**What.** Every citation in the brief carried `utm_source=chatgpt.com`, meaning
the sources were surfaced by a language model rather than read from a publisher.
All fourteen claims were checked.

**Why.** Not because LLM-surfaced means wrong — several are reproduced well by
the model, which is weak evidence they are right — but because none had been
verified, and two carry load-bearing conclusions.

**Result.**

| Status | Count |
|---|---|
| Verified — full text read | 4 |
| Partial — source located, abstract confirmed | 6 |
| **Disputed — figures appear in no locatable source** | **2** |
| Supported — corroborated independently | 3 |
| Not located after searching | 1 |

**Two citations cannot be supported.** The figures 85.4% T_vis / 3.21 Ω/sq /
97% FIR, and 78.7% T_vis / 2.7 Ω/sq, appear in neither located AZO/Ag/AZO study.
**Do not cite them.**

> **An uncomfortable corollary.** These two are the model's three *closest*
> agreements — 0.3%, 1.0%, 1.2% relative error. Excluding them, the median
> validation error rises from **14.7% to 30.6%**. The framework's apparent
> accuracy rested partly on figures that cannot be traced. `validate_model()`
> now excludes them by default, and a test fails if that exclusion ever starts
> *lowering* the reported error.

**Two transcription errors found.** The brief states Ag = 1.59 µΩ·cm for a 10 nm
film; the source patent (US 10,822,692) says **1.29**. Separately, an earlier
"correction" of mine — that the brief's 82.4% AZO transmittance should be 81.4%
— **was itself wrong**: the paper reports both, 82.4% in Results and 81.4% in
the abstract, and the brief quoted Results.

**Three factual corrections.** Deposition methods differ across the benchmark
set — RF for the AZO/Ag/AZO trilayers where §3 implies DC, medium-frequency for
the AZO single layer — so these sources cannot be pooled.

**Conclusion.** Checking citations changed eight of fourteen. That is a finding
in itself, and the mixed table is more informative than a clean one would be.

## 7. A measurement that contradicts a model-independent limit

**What.** *Applied Surface Science* **578** (2022) reports AZO/Cu/AZO with
T_vis 87.7%, R_s 9.96 Ω/sq and ε 0.055. **The brief's §16 conclusion — that a
silver-free stack may already meet a Low-E target — rests entirely on it.**

**Why.** For a conducting sheet much thinner than the wavelength, far-infrared
reflectance is fixed by sheet resistance alone:

```
r = (n₁ − n₂ − Z₀/R_s) / (n₁ + n₂ + Z₀/R_s),   ε = 1 − r²
```

with Z₀ = 376.73 Ω. **No fitted parameter enters.**

**Result.** At 9.96 Ω/sq the floor is **ε ≥ 0.096**. The reported 0.055 would
require about 5.5 Ω/sq. Five explanations were tested and eliminated:

| Explanation | Outcome |
|---|---|
| Different samples | Ruled out — abstract attributes all three to one sample |
| Transcription error | Ruled out — confirmed against the abstract |
| Far-IR glass index assumption | Ruled out — limit is 0.091–0.097 for n = 1.5–4.0 |
| Band-limited emissometer | **Ruled out — reads 5–8% *higher*, moving it the wrong way** |
| The framework's own convention | **Ruled out — an industrial formula agrees** |

That last one matters most. Cueva & Carretero compute emissivity from sheet
resistance as ε = 0.0106·R□, citing Gläser, *Large Area Glass Coating* (2000) —
in industrial use for two decades. It agrees with the framework's impedance
limit within 10% and gives **0.106** at 9.96 Ω/sq against the reported 0.055.

The same group reports the same ~0.6 ratio in two further papers, so it is
systematic rather than an isolated error.

**Conclusion.** The claim has hardened from "unverified" to **"inconsistent with
a model-independent electrodynamic limit, with every benign explanation tested
and eliminated"**. Untested: hemispherical versus normal basis, which would also
*raise* the reading. **§16's conclusion should not be used until this is
settled** — one line of a paywalled full text.

---

# PART III — WHERE THE MODEL WAS WRONG

## 8. The dielectric finding was reversed by measurement

**What.** The framework originally concluded that Si₃N₄ outperforms AZO on
transmittance by up to nine points, on index-matching grounds.

**Why it was tested.** Cueva & Carretero (*Coatings* **13**, 1709, 2023, open
access) deposited five dielectrics under identical conditions with 10 nm Ag.

**Result — the opposite.**

| Dielectric | Measured ε | n(550 nm) |
|---|---|---|
| SnO₂ | 0.083 | 2.00 |
| ZnO | 0.064 | 2.019 |
| **AZO** | **0.058** | **1.85** |
| SiAlNx | 0.067 | 2.09 |

**AZO wins on emissivity *and* transmittance despite having the lowest
refractive index of the five.** The authors give the reason: silver growth is
more efficient on AZO.

**What the model was missing.** It treated the dielectric purely as an
interference layer — index and thickness, nothing else. The optical inputs were
sound; their measured indices match the framework's closely. What was absent is
that the underlayer determines the *quality of the metal grown on it*.

**The correction.** `TCOPreset.metal_growth_factor` applies a resistivity
penalty per underlayer, calibrated to that series and normalised to AZO = 1.00:
ZnO 1.10, SiAlNx 1.16, ITO 1.20, TiO₂ 1.25, SnO₂ 1.43. The model now reproduces
the measured ordering and magnitudes to 4–8%.

**Conclusion, and the productive outcome.** The brief's framing did exclude
nitrides — it began from the periodic table and the Materials Project, both of
which surface oxides — and that observation stands. But the best answer is a
**hybrid**, which is what industry already does: AZO beneath for nucleation,
nitride above for durability through tempering. Two candidates were added:

| ID | Stack | T_vis | ε_h | Heating |
|---|---|---|---|---|
| **H1** | AZO/Ag/Si₃N₄ | **0.918** | 0.057 | 67.4 |
| M0 | AZO/Ag/AZO (benchmark) | 0.876 | 0.060 | 65.0 |
| **H2** | AZO/Cu/Si₃N₄ (silver-free) | 0.788 | **0.042** | 79.9 |

H2 now ranks **second on the cooling profile** and is the only architecture
appearing in both top-ten lists.

## 9. The mechanism, and the framework's principal structural weakness

**What.** Two ML surrogate calculations were run to find the mechanism behind
`metal_growth_factor`. Both failed. A literature search then found it in under
an hour.

**Why it was worth chasing.** An empirical multiplier with no mechanism is a
fitted fudge factor. With one, it becomes a physical parameter that can be
measured and predicted.

**Result — the failures, both diagnosed:**

| Attempt | Failed on | Diagnostic that caught it |
|---|---|---|
| Bulk interface adhesion | 5–21% lattice mismatch — measured elastic strain | unphysical outputs: 9.6 and −0.16 J/m² |
| Adatom wetting | ZnO(0001) termination changed the answer by 2.1 eV against 0.46 eV between materials | explicit termination sweep |

**Result — the mechanism.** US 7,632,572 B2 / US 8,512,883 B2 (AFG Industries →
AGC Flat Glass North America → Cardinal CG; **full text read**) deposited 16 nm
Ag on amorphous TiOx and on a 5 nm ZnO seed over the same TiOx, and examined
both by TEM:

- **25 nm grains on ZnO against 15 nm on a-TiOx**
- {111}-oriented grains **two to three times larger** on ZnO
- the film on bare amorphous titania **clearly discontinuous** where the
  ZnO-seeded film was continuous across the whole specimen

And the inventors name the mechanism: zinc oxide grows {0001}, which orients the
silver to grow {111}, and the **epitaxial lattice match between Ag{111} and
ZnO{0001}** lowers sheet resistance and improves adhesion.

**An unexpected validation.** The patent also reports four-point sheet
resistance: **5.68 Ω/□ with the ZnO seed against 7.56 without**, a ratio of
**1.331**. `metal_growth_factor` — calibrated independently from Carretero's
*emissivity* series, a different group, decade and measured quantity — gives
**1.250**. **Agreement to 6%.** A parameter fitted to one dataset reproducing
another it never saw.

**The conclusion, and it is the most consequential in the project:**

> **The framework models each metal layer as though the layer beneath it did not
> shape its microstructure.** That single omission accounts for *both*
> `metal_growth_factor` *and* the eightfold under-prediction of sputtered copper
> sheet resistance. They are one effect appearing twice, not two caveats.

The default `grain_size_ratio` of 3.0 corresponds to 30 nm grains in a 10 nm
film — within 20% of the 25 nm the patent measured on ZnO. The assumption was
correct, but only for the underlayer it happened to be tuned against.

## 10. Corrections to the project's own conclusions

**What.** Four conclusions stated during this work were later overturned by the
work itself. They are recorded rather than quietly fixed.

**Why.** A methods section that shows its own corrections is more credible than
one that does not, and the common cause is transferable.

| Claim | Overturned by |
|---|---|
| An optimum exists at Ag₆₀Cu₄₀ | A three-point artifact. At 5% resolution the curve is monotonic |
| The Ti barrier variant beats the ternary | An artifact of silver carrying zero weight. Corrected, it ranks last |
| The band-emissometer explains the ApSS emissivity | Implemented and tested: it reads 5–8% *higher*, worsening the discrepancy |
| Adatom wetting reproduces the measured ordering | A termination sweep showed it was resolving slab index, not material |

**Conclusion.** Three of four are the same error — **reading structure into too
few points**. Three compositions in one case, one geometry per composition in
another, one untested hypothesis in a third. The framework's value came largely
from re-running things at finer resolution and watching earlier conclusions
dissolve.

---

# PART IV — WHAT WAS COMPUTED, AND WHAT IT COST

## 11. Thermodynamics: Ag–Cu has no stable ordered compound

**What.** All fifteen chemical systems from the brief's §9 were retrieved from
the Materials Project and screened within 50 meV/atom of the convex hull.

**Result.** Two intermediate Ag–Cu phases exist and **neither is stable**:
Cu₃Ag at 0.0904 eV/atom above the hull, CuAg₃ at 0.0857. Ag–Cu is the only
nominated binary with no stable intermediate phase.

The magnitude matters: 86–90 meV/atom is well above k_BT at deposition (26 meV
at 300 K, 48 meV at 550 K), so the driving force to separate is substantial.

**A second finding, bearing on the Ti hypothesis.** Cu–Ti has 8 near-hull phases
and Al–Cu has 10. A dilute Ti or Al addition to a Cu-bearing film therefore has
stable intermetallics available to precipitate rather than remaining in solution
as a stabiliser — a second, independent mechanism for the ternary
underperforming, alongside the Nordheim conductivity penalty.

**Conclusion.** The brief's §5 suspicion of phase separation, inferred from a
13% lattice mismatch, is now supported by first-principles data.

## 12. Mixing energies: the dilute corner is thermodynamically favoured

**What.** MACE-MP-0 and CHGNet on 32-site fcc supercells, three random
decorations per composition, gated against the two known hull distances.

**Why.** The convex hull is an equilibrium statement about *ordered* phases. A
sputtered film is neither ordered nor at equilibrium, so the disordered solid
solution needed separate treatment.

**Result.** Positive across the whole range, fitting a regular-solution form to
±6 meV/atom: **ΔE_mix = 0.287·x·(1−x)**.

**A self-check that matters more than the gate.** At Ag 25 at.% the surrogate
puts the *disordered* solution 13 meV/atom **below** the ordered Cu₃Ag compound.
No ordering tendency at all — precisely what an empty hull implies, reached
independently.

**The finding that bears on the design:**

| Ag at.% | ΔE_mix | ×kT (550 K) |
|---|---|---|
| 70 — the brief's priority | 0.0602 | 1.27 |
| 15 | 0.0366 | 0.77 |
| 10 | 0.0258 | 0.54 |
| 5 | 0.0136 | 0.29 |

**In the dilute-silver corner the driving force to separate falls below thermal
energy at deposition.** §3 found the two microstructure hypotheses converge
there and treated it as robustness; the thermodynamics now supply the reason.

**The dilute-silver optimum is therefore supported on three independent
grounds:** lowest silver consumption, highest score under the corrected
weighting, and the weakest tendency to phase-separate.

**Cross-checked, with a caveat.** Both models under-predict — MACE by 0.026,
CHGNet by 0.047 eV/atom — so the bias is inherited from shared Materials Project
training data rather than architecture-specific, meaning ΔE_mix should be
corrected *upward*. **They are not independent**: both are trained on the same
relaxation trajectories, so agreement shows the bias is consistent, not absent.

**And a compounded correction, from verifying one of the brief's own citations.**
GGA underestimates Cu–transition-metal formation energies by nearly 40%, because
it places Cu-3d bands too shallow (npj Comput. Mater. 2024). The MP hull is
GGA/GGA+U and both surrogates train on it, so two errors act in series. The
conclusion **holds at 5–10 at.% Ag and becomes marginal at 15%**.

## 13. What the surrogate could not do

**Cannot, at all:** optical constants, dielectric functions, band gaps,
emissivity. These models predict energies and forces from atomic positions and
carry no electronic structure. **Every optical number in this project must come
from the transfer-matrix model or from measurement.**

**Unreliable:** amorphous or defective phases, metal/oxide interfaces, and any
energy difference below about 30 meV/atom — which is comparable with the hull
distances being measured.

---

# PART V — WHAT REMAINS

## 14. The critical unknown

**What.** The framework validates well against silver in the infrared — within
0.4% on the benchmark it reproduces best — and **fails on copper**, under-
predicting sputtered sheet resistance by roughly eightfold.

**Why it matters.** Six of the leading candidates in both climate profiles are
copper-based.

**Result of the literature check.** Four independent published fits of the
scattering parameters give specularity 0.48–0.80 and grain-boundary reflection
0.16–0.43. The framework's assumed 0.50 and 0.25 sit inside that range, and
**an exhaustive scan over the entire admissible range reaches only 4.42 Ω/sq
against the 16.6 to be explained** — short by a factor of 3.8.

**So the classical size effect is eliminated**, and grain structure is the
leading hypothesis: grains at roughly half the film thickness give 14.1 Ω/sq.

**Conclusion.** If that reading is right, **copper's obstacle is film quality,
not physics** — an engineering problem with known levers (base pressure, seed
layers, substrate temperature) rather than a fundamental limit. That is far more
tractable than replacing silver's electronic structure.

## 15. The experiment that resolves it

**One XRD scan, one film, an afternoon — and it answers three questions.**

`pvdlowe/characterise/xrd.py` states in advance what the scan should show:

| Measurement | Question answered |
|---|---|
| Peak count and position | **Microstructure.** Segregated gives two fcc sets at 38.12° and 43.32°; a solid solution gives one at 39.54° — 1.42° from silver against a 0.59° width |
| Scherrer peak width | **Grain size**, and therefore `grain_size_ratio` — the framework's principal structural weakness |
| (111)/(200) intensity ratio vs the powder value of 2.2 | **Templating**, the mechanism of §9 |

**Scan to 2θ = 100°, not 60.** Separation grows faster than width with angle:
the (222) reflection separates at 4.8× its width against (111)'s 2.4×.

**A second, independent discriminator.** Sheet resistance separates the
microstructure hypotheses by a number — 6.4 against 2.6 Ω/sq. Diffraction
separates them by *peak count*. Two unrelated observables agreeing is far
stronger than either alone, and both come from one film.

**Pre-registered decision rules**, written before any data exists, in
`experiments/PROTOCOL_cu_series.md`. Four outcomes, each with what it means and
what to do — **including the one where the literature is right, six candidates
fall, and the project reverts to silver reduction.**

## 16. The open question only SGRI can answer

**What.** The report benchmarks against a 10 nm AZO/Ag/AZO at ε_h 0.060, taken
from the brief — whose citations for that stack are the two **disputed** entries.

**Why it matters.** Saint-Gobain's own patents (US 7,745,009) claim silver at
**12.5–16 nm targeting ε ≤ 0.038**. The model says that needs 14–16 nm.

| Ag nm | ε_h | Ag g/m² |
|---|---|---|
| **10.0** (current benchmark) | 0.060 | 0.105 |
| 14.0 | 0.039 | 0.147 |
| 16.0 | 0.033 | 0.168 |

**Conclusion.** If production runs at 12.5–16 nm, the reported silver reductions
are measured against a stack that would not meet SGRI's own emissivity
specification. **The baseline needs confirming before the percentages are
quoted.** This is the single highest-value question outstanding and only SGRI
can answer it.

---

# PART VI — WHAT WAS BUILT

## 17. The framework

8,995 lines, 112 tests, ten subpackages, nine CLI commands.

**The design decision that matters.** Film resistivity feeds the Drude damping,
so a metal layer too thin to conduct is automatically one that reflects poorly.
Without that coupling, optimising for transmittance drives silver thickness to
zero and the model reports an excellent coating.

**Validated against closed-form answers**, not by inspection: exact Fresnel for
a bare interface, exact null for a quarter-wave layer, energy conservation to
10⁻¹⁰, s and p agreeing at normal incidence.

**Provenance as a type, not a footnote.** Every quantity carries an evidence
grade, and a guard refuses HYPOTHESIS-grade values in headline tables. This is
what kept the Ti-ternary predictions from being quoted as results.

**Functions that refuse rather than guess.** The sputter model raises when
uncalibrated; the MP client raises when offline with a cold cache; the surrogate
refuses to fall back to an empirical potential; the adhesion calculation refuses
above 4% lattice mismatch. Each was tempting to make helpful; each would have
produced fabricated data.

## 18. Known limitations, stated plainly

**No experimental validation.** Every performance figure is a model output.

**Fitted parameters:** specularity and grain-boundary reflection are fitted, not
measured. Si₃N₄ and TiO₂ optical constants are ESTIMATE grade.

**Illuminant approximation, now quantified:** varying colour temperature over
5000–7500 K moves **T_vis by 0.1%** and **T_sol by 8.3%**. T_vis is reportable
as computed; T_sol, g and LSG carry a 5–10% systematic until tabulated AM1.5G
spectra are supplied.

**Scores are not portable.** Absolute scores moved by ~25 points as the §5
defects were fixed. A score is not a property of a material.

**Not modelled at all:** roughness, interdiffusion, damp-heat and abrasion
durability, adhesion, agglomeration kinetics, and any property of a metastable
sputtered alloy that a 0 K ordered-crystal database cannot supply.

---

# CONCLUSION

## What this project established

**A better composition.** 5–15 at.% Ag rather than 70%, supported on three
independent grounds — silver consumption, corrected score, and thermodynamic
stability against segregation.

**A better material class.** Silicon nitride was outside the brief's search
framing; the hybrid AZO/metal/Si₃N₄ arrangement beats both pure stacks and is
what industry already does.

**A better architecture.** Two metal layers reach LSG 1.76 against a
single-metal ceiling of 1.37 — an architectural limit no compositional search
could have found.

**A specified climate dependency.** The two profiles share one candidate out of
ten. The brief's silence on climate was a substantive omission, not a detail.

## What this project corrected

Four defects in the proposed weighting, one of which let the optimiser return
**29% more silver than the incumbent at a perfect score**. Two citations that
cannot be traced. Two transcription errors. One measurement inconsistent with a
model-independent physical limit. And four of its own conclusions, overturned by
finer resolution and recorded rather than hidden.

## What this project cannot claim

**Nothing has been deposited.** The candidate rankings are hypotheses ordered by
physics, suitable for directing experimental effort. Their principal weakness —
that the framework models each metal layer as though the layer beneath it did
not shape its microstructure — is known, quantified, and addressed by a
specified experiment.

## The recommendation

**One XRD scan, one film, an afternoon.** It measures the grain size that §9
identifies as the common cause of two separate limitations, tests the templating
mechanism directly, and discriminates the microstructure hypotheses by a second
independent route.

And **one question to SGRI**: which stack is the right baseline.

> A model that identifies the measurement capable of falsifying it is more
> useful to an experimental programme than one that does not. That is what this
> framework is for, and it is what it delivered.
