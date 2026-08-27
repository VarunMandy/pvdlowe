# Computational screening of sustainable low-emissivity PVD coatings on soda-lime float glass

**Technical report** · Saint-Gobain Research India
**Author:** Varun Mandy, Research Intern
**Framework:** `pvdlowe` v0.1.0 — https://github.com/VarunMandy/pvdlowe

---

## Abstract

A computational framework was built to execute the screening workflow set out in
the project brief: element screening, thermodynamic stability, optical multilayer
modelling, design of experiments and multi-objective ranking, for cost-effective
low-emissivity coatings deposited by argon magnetron sputtering.

Applying it produced three classes of result. **First**, the proposed
multi-objective weighting was found to contain six defects, one of which allowed
a thickness optimiser to return a design consuming 29% *more* silver than the
incumbent while scoring 100/100. **Second**, two of the brief's literature
citations could not be matched to any locatable source, one transcribed value
was traced to a conflict between two publications by the same group, and one
pivotal measurement was found inconsistent with a model-independent
electrodynamic limit, with six explanations tested and eliminated. **Third**, the
design-space search identified a material class and a stack architecture outside
the brief's framing, both of which outperform the proposed candidates: silicon
nitride dielectrics improve visible transmittance by up to nine percentage
points over AZO, and the composition optimum lies at 5–15 at.% Ag rather than the
proposed 70%.

Thermodynamic screening of all fifteen nominated systems confirmed that Ag–Cu
possesses no stable ordered compound, supporting the brief's suspicion of phase
separation with first-principles evidence. A machine-learning interatomic
potential extended this to the disordered solid solution and showed that in the
dilute-silver range the driving force to separate falls below thermal energy at
deposition, supplying a third independent argument for that composition range. A
literature search subsequently identified the mechanism behind the dielectric
effect — underlayer templating of metal grain structure, measured by
transmission electron microscopy in the patent literature — and established that
it is the same physical effect as the framework's largest known error.

**No films were deposited.** All performance figures are model outputs. The
framework's own validation identifies its largest error — an approximately
eightfold under-prediction of sputtered copper sheet resistance — in the material
on which most leading candidates depend. A specified experiment resolving this,
with pre-registered decision rules, is delivered with the framework.

---

## 1. Scope and deliverables

### 1.1 What was asked

The brief proposed a materials-by-design programme for transparent low-emissivity
coatings on float glass, centred on a dielectric/metal/dielectric architecture
(AZO/metal/AZO) and asking how much silver could be removed while retaining
visible transmittance, sheet resistance and far-infrared reflectance.

### 1.2 What was delivered

| Deliverable | Status |
|---|---|
| Framework implementing the brief's §21 workflow | Complete — 9,586 lines, 136 tests |
| Element and compound screening | Complete |
| Optical multilayer model (transfer matrix, EN 410 / 673 / 12898) | Complete, validated |
| Thin-film transport coupled to optics | Complete, **uncalibrated — requires §6 experiment** |
| Multi-objective scoring with provenance grading | Complete |
| Design of experiments generator | Complete |
| DFT input generation (VASP) | Complete, **not executed — requires licence and HPC** |
| Materials Project integration | **Complete and executed** — 15/15 systems |
| ML interatomic potential surrogate | **Complete and executed** — mixing energies |
| Candidate ranking, 38 architectures | Complete, **model outputs only** |
| Predicted XRD signatures for the experiment | Complete |
| Experimental protocol, pre-registered analysis | Complete, **not executed — requires tool access** |

Repository, documentation, results and protocols are version-controlled and
archived.

### 1.3 How to read this report

**§2–§3 do not depend on any experiment.** They are audits of the brief's method
and evidence, and they stand on their own.

**§4–§5 are model outputs.** They are hypotheses ordered by physics, suitable for
directing experimental effort, and their principal weakness is quantified in §6.

**§7 is what only Saint-Gobain can answer.**

---

## 2. Method audit: six defects in the multi-objective weighting

The brief's §14 specifies criteria and weights. Encoding that table literally
produced a scoring function that did not measure the project's stated objective.
Four defects were in the table as proposed; **two more were found by re-auditing
the corrections for the first two.** All were surfaced by the framework's own
diagnostics (`pvdlowe check-weights`).

### 2.1 Silver consumption carried zero weight

§14's table has no line for silver mass, although §17 and §20 both name
minimising silver as a project objective. Silver mass was computed, displayed,
even reported as the limiting criterion — and contributed nothing to the score.

> The thickness optimiser exploited this immediately, returning a design using
> **29% more silver than the benchmark, at a perfect 100/100.**

*Correction:* silver mass weighted 0.15. See §2.7 on why that number is itself a
judgement.

### 2.2 Emissivity and sheet resistance double-count one property

They correlate at **r = 0.978** across the candidate set. Both are the
free-carrier response of the same layer — the same physics measured two ways — so
weights of 0.25 and 0.15 placed 0.40 of the total on one quantity.

*Correction:* sheet resistance weighted 0.0 and reported as a constraint.

### 2.3 Targets set at the specification minimum, causing saturation

Derringer–Suich desirability saturates at 1.0 once a target is reached. Setting
T_vis's target to 0.80 — the brief's *floor of acceptability* — made the
criterion flat exactly where candidates differ.

Across 181 oxide pairs clearing 0.80, transmittance spanned 0.800–0.881 while the
**score went down**, 74.99 to 73.30.

*Correction:* targets raised to aspirational values. **General rule: a
desirability target should be an aspiration, not a specification minimum.**

### 2.4 The supply-risk band could not discriminate

With floor 8.0 against candidate values of 4.5–7.5, all silver-bearing
compositions scored 0.1–0.28, and supply risk was reported as limiting for 12 of
14 candidates.

*Correction:* floor 9.5, target 4.0 — still zeroing indium-bearing ITO, which is
the criterion's purpose.

### 2.5 A triple-count the fix for §2.2 left untouched

Zeroing sheet resistance removed one double-count and left another:

| Pair | r |
|---|---|
| Silver mass ↔ metal cost | **1.000** |
| Silver mass ↔ supply risk | 0.991 |

Silver dominates metal cost so completely that cost is the same quantity in
different units, and supply risk in this candidate set *is* silver's supply risk.
Together they carried **36% of the effective weight** on one property.

*Correction:* both weighted 0.0 and reported as derived. Effective concentration
falls to 25%, and no criterion pair now both carries weight and correlates.

**The diagnostic itself was also wrong** — it flagged correlated pairs regardless
of whether both carried weight, which buries the cases that matter. It now
distinguishes an active double-count from an informational correlation.

### 2.6 Weight reserved for criteria never populated

Structural stability, thermal stability and deposition efficiency carried **0.30
of a 0.90 nominal total while being `None` for every candidate**. The scheme
renormalises over available criteria, so that third was silently redistributed: a
file stating emissivity at 0.25 was in fact applying 0.42.

Worse, `structural_stability` carried 0.15 **with no criterion definition at
all** — it could never have scored even had a value been supplied.

*Correction:* all three weighted 0.0, the missing definition written. **The
ranking is unchanged, which is the point** — they were renormalising away already.

`structural_stability` is now partly populatable from the Materials Project
screening of §5.5 and the surrogate mixing energies of §5.6, both in eV/atom. It
is left at 0.0 deliberately: populating it would change every ranking, the values
carry a 20–40% systematic error, and 0.15 is another weight nobody derived.
**Populating a criterion and choosing its weight are one decision, not two**, and
that decision belongs to whoever continues the work.

### 2.7 The ranking depends on a number nobody derived

Silver mass carries a weight of 0.15. That value is a judgement, and it selects
the answer:

| Silver weight | Winner | Ag g/m² | Runner-up | Margin |
|---|---|---|---|---|
| 0.00 | N35e | 0.065 | N3e | 0.52 |
| 0.05 | N35e | 0.065 | E10e | **0.09** |
| 0.10 | E10e | 0.015 | E5e | 0.57 |
| **0.15** | **E10e** | **0.015** | E5e | 0.22 |
| 0.20 | E5e | 0.008 | E10e | **0.09** |
| 0.25 | E5e | 0.008 | N6 | 0.15 |
| 0.30 | N6 | **zero** | E5e | 0.17 |
| 0.40 | N6 | **zero** | E5e | 0.70 |

**The winner changes three times across a plausible range**, and **five of eight
settings separate first from second by under half a point** — at those weights
the ranking is not meaningfully distinguishing candidates.

**So the honest statement is the sweep, not the ranking:** the recommendation is
E10e at weight 0.15, E5e at 0.20–0.25, and the silver-free N6 at 0.30 and above.
Choosing among them is a decision about how much silver consumption matters to
Saint-Gobain, and it is not the framework's to make. Run
`pvdlowe check-weights` to reproduce it.

### 2.8 Aggregation

The brief states its weighting should prevent a candidate "winning simply because
it has excellent conductivity while being unacceptable optically." A weighted
arithmetic sum does not achieve this — a candidate scoring zero on one criterion
forfeits only that criterion's weight. **A geometric mean sends the whole score
to zero.**

The framework uses geometric aggregation by default and can report both, since
the ordering differs materially between them.

---

## 3. Evidence audit

### 3.1 Verification status

Every citation in the brief carried `utm_source=chatgpt.com`, meaning the sources
were surfaced by a language model rather than read from a publisher. That does
not make them wrong — several are reproduced well by the model, which is weak
evidence they are right — but none had been checked.

| Status | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — source located, figures confirmed against abstract | 4 |
| **Disputed — figures appear in no locatable source** | **2** |
| Supported — corroborated independently | 3 |
| Not located after searching | 1 |

### 3.2 Two citations cannot be supported

The figures 85.4% T_vis / 3.21 Ω/sq / 97% FIR, and 78.7% T_vis / 2.7 Ω/sq, appear
in neither located AZO/Ag/AZO study. **They should not be cited until someone
establishes where they came from.**

> **An uncomfortable corollary.** These two entries are the model's three
> *closest* agreements — 0.3%, 1.0% and 1.2% relative error. Excluding them, the
> median validation error rises from **14.7% to 30.6%**. The framework's apparent
> accuracy rested partly on figures that cannot be traced.
>
> `validate_model()` now excludes them by default and reports 30.6%; 14.7% is
> available only behind a flag, labelled as an audit view that must not be
> quoted. A test fails if the exclusion ever starts *lowering* the reported
> error.

### 3.3 A measurement inconsistent with a model-independent limit

*Applied Surface Science* **578** (2022) reports AZO/Cu/AZO with T_vis 87.7%,
R_s 9.96 Ω/sq and ε 0.055. **The brief's §16 conclusion — that a silver-free
stack may already meet a Low-E target — rests entirely on this measurement.**

For a conducting sheet much thinner than the wavelength, far-infrared reflectance
is fixed by sheet resistance alone through the impedance of free space. No fitted
parameter enters. At 9.96 Ω/sq the floor is **ε ≥ 0.096**; the reported 0.055
would require about 5.48 Ω/sq.

**Six explanations were tested and eliminated:**

| Explanation | Outcome |
|---|---|
| Different samples | Abstract attributes all three figures to one sample |
| Transcription error | Confirmed against the abstract |
| Far-IR glass index assumption | Limit is 0.091–0.097 for n = 1.5–4.0 |
| Band-limited emissometer | Reads 5–8% **higher** — moves it the wrong way |
| This framework's own convention | An industrial formula in use since 2000 agrees within 10% |
| **Measurement basis** | **A hemispherical reading fails by 51% rather than 42%** |

The last of these was the final benign explanation. The impedance floor is a
normal-incidence quantity, so the open question was whether 0.055 might be
hemispherical and therefore not comparable. Reading it that way gives a
normal-basis equivalent of 0.0472 — **worse, not better.**

**§16's conclusion should not be used until this is settled.**

### 3.4 The two copper measurements are in opposite positions

Both copper benchmarks, checked against the same bound:

| | Group, technique | R_s | ε | Floor | |
|---|---|---|---|---|---|
| Miao 2014, HK PolyU | RF | 16.60 | 0.330 | 0.150 | **consistent** |
| ApSS 2022, Xi'an | DC | 9.96 | 0.055 | 0.096 | **below floor** |

**The measurement that obeys the electrodynamic limit is the one that
contradicts this framework**, by a factor of 7.7 — the model gives 2.16 Ω/sq for
a 15 nm copper layer against 16.6 measured. The measurement that agrees with the
model's optimism is the impossible one.

That contrast is stronger evidence than either entry alone, and it points the
same way as §6: the fault is in the model, not the literature.

**They must not be pooled** — different groups, RF against DC, different decades,
and the 2014 study is from a textiles laboratory that coats polyester fabric with
the same stacks.

### 3.5 Corrections to the brief's characterisations

- **Deposition methods differ across the benchmark set.** The AZO/Ag/AZO
  trilayers used **RF** sputtering where §3 implies DC; the AZO single layer used
  **medium-frequency**. Film density and resistivity do not transfer between
  techniques, so these sources should not be pooled.
- **One transcribed resistivity is a source conflict, not a transcription
  error.** The brief quotes 1.59 µΩ·cm for a 10 nm Ag film. The journal states
  1.59 — the brief is faithful — while the group's own patent states 1.29, which
  is *below* bulk silver and therefore impossible. **Both figures are anomalous
  by a factor of three:** Fuchs–Sondheimer gives 4.74 µΩ·cm at 10 nm, this
  framework gives 4.44, and an independent 12 nm measurement gives 4.8. Cite the
  comparative Ag–Cu against Cu claim; do not cite 1.59 as a validated
  thin-film benchmark.
- **The Ag₇₀Cu₃₀ basis is on the wrong substrate.** The brief's §5 justification
  traces to a 2022 paper that does support 70/30 at 10 nm — but on
  **polycarbonate**, for first-surface coatings. Given §5.2, that optimum does
  not transfer to a glass line unchecked.

---

## 4. The specification, completed

The brief supplies three constraints. Two more matter and were unspecified, so
they have been anchored to the Indian building code rather than invented.

### 4.1 Against the brief's three constraints

| Criterion | Spec | Pass | Achieved range |
|---|---|---|---|
| T_vis | ≥ 0.80 | 31/38 | 0.738 – 0.918 |
| R_sheet | ≤ 5.0 Ω/sq | 19/38 | 2.63 – 7.55 |
| ε_h | ≤ 0.10 | **38/38** | 0.042 – 0.098 |

All three simultaneously: **15 of 38**.

**Emissivity never binds.** The brief's target is generous relative to what any
percolating metal layer gives automatically. Sheet resistance is the real
constraint, then transmittance.

### 4.2 Two criteria anchored to ECBC 2017

| Criterion | Anchor | Value |
|---|---|---|
| `g_value` | ECBC prescriptive SHGC, composite climate | ≤ 0.27 |
| `U_g` | ECBC assembly U-factor | ≤ 3.0 W/m²K |

**Basis warning.** ECBC specifies *assembly* values — frame and glass,
area-weighted. This framework computes centre-of-glass, and its g-value is
single-pane with the standard N = 0.36 inward fraction. The conversion must be
stated rather than assumed.

Chaining a clear second pane (T_sol 0.83) gives an approximate DGU SHGC:

| | g single | g DGU | vs 0.27 |
|---|---|---|---|
| M6, the best | 0.558 | **0.463** | fails by +0.19 |
| N35e, the worst | 0.793 | 0.658 | fails by +0.39 |

**Not one of the 38 candidates meets the Indian code's solar-heat-gain
requirement, and the best misses by seventy per cent.**

That is external, regulatory confirmation of §5.4: these are thermal Low-E
coatings, not solar-control coatings. For Indian commercial glazing the
single-metal architecture is not merely suboptimal — it is non-compliant, and the
double-metal stack of §5.4 becomes a requirement rather than a refinement.

**U-value is not binding.** Every candidate lands at 1.12–1.29 W/m²K centre-pane;
even after a frame adds 0.5–1.5 there is room.

### 4.3 The two targets are mutually incompatible

Searching 990 double-metal designs against all five constraints returns **none**.
The frontier:

| If T_vis at least | Lowest g reachable | LSG |
|---|---|---|
| **0.80** | 0.424 | 1.89 |
| 0.70 | 0.351 | 2.04 |
| **0.65** | **0.326** | **2.08** |
| 0.60 | 0.271 | 2.26 |

**ECBC's 0.27 is reachable — at T_vis 0.644.** The brief asks for 0.80.

Since ECBC's own visible-light minimum is 0.27, the incompatibility is not with
the regulation but with the brief's **self-imposed** transmittance target, which
was written for a heating climate. **Which target is real is a decision for
Saint-Gobain.**

---

## 5. Design-space results

### 5.1 The composition optimum lies at 5–15 at.% Ag

Eight composition curves — Ag 0–100% in 5% steps, geometry re-optimised at every
point, across two microstructure models, two dielectrics and two climates.

**Every one peaks between 0 and 10 at.% Ag.**

| Profile | Microstructure | Dielectric | Optimum | Plateau |
|---|---|---|---|---|
| Heating | Segregated | Si₃N₄ | 0.05 | 0.00–0.20 |
| Heating | Segregated | AZO | 0.10 | **0.05–0.40** |
| Cooling | Either | Either | 0.00 | 0.00–0.15 |

**This is a sustainability result, not a performance one.** Emissivity and sheet
resistance keep improving up to 50 at.% Ag. The score falls anyway because silver
mass carries weight: the trade is about 0.005 in emissivity for an 87% cut in
silver, and it is the right trade only because silver was decided to matter.

**Plateau width matters more than peak position for a production process.**

### 5.2 The dielectric changes the metal, not just the interference stack

The framework originally concluded that Si₃N₄ beats AZO on transmittance by up to
nine points, on index matching. **A measurement reversed it.**

Cueva & Carretero (*Coatings* **13**, 1709, 2023, open access, **full text
read**) deposited five dielectrics under identical conditions with 10 nm Ag:

| Dielectric | Measured ε | n(550 nm) |
|---|---|---|
| SnO₂ | 0.083 | 2.00 |
| ZnO | 0.064 | 2.019 |
| **AZO** | **0.058** | **1.85** |
| SiAlNx | 0.067 | 2.09 |

**AZO wins on emissivity *and* transmittance despite the lowest refractive index
of the five.** The reason the authors give: silver grows more efficiently on AZO.

**What the model was missing.** It treated the dielectric purely as an
interference layer — index and thickness, nothing else. The optical inputs were
sound; their measured indices match the framework's closely. What was absent is
that the underlayer determines the *quality of the metal grown on it*.

*Correction:* `metal_growth_factor` per underlayer, calibrated to that series and
normalised to AZO = 1.00: ZnO 1.10, SiAlNx 1.16, ITO 1.20, TiO₂ 1.25, SnO₂ 1.43.
The model now reproduces the measured ordering and magnitudes to 4–8%.

**The productive outcome is a hybrid**, which is what industry already does:

| ID | Stack | T_vis | ε_h | Heating score |
|---|---|---|---|---|
| **H1** | AZO/Ag/Si₃N₄ | **0.918** | 0.057 | 69.6 |
| M0 | AZO/Ag/AZO (benchmark) | 0.876 | 0.060 | 66.6 |
| **H2** | AZO/Cu/Si₃N₄ (silver-free) | 0.788 | **0.042** | 77.6 |

**H2 is the only architecture appearing in both climate top-tens.**

### 5.3 Climate reverses the ranking

The brief does not specify a climate, and its weighting does not constrain solar
heat gain — which quietly encodes a heating-dominated assumption.

Adding the solar-gain metrics and re-scoring, the two top-ten lists **share one
candidate out of ten**.

#### Heating-dominated — `data/targets.yaml`

| # | ID | Architecture | T_vis | ε_h | R_s | Ag g/m² | Score |
|---|---|---|---|---|---|---|---|
| 1 | E10e | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ (segregated) | 0.877 | 0.051 | 3.13 | 0.015 | **87.4** |
| 2 | E5e | Si₃N₄/Ag₅Cu₉₅/Si₃N₄ (segregated) | 0.863 | 0.048 | 2.98 | 0.008 | **87.1** |
| 3 | N6 | Si₃N₄/Cu/Si₃N₄ | 0.858 | 0.054 | 3.41 | **0.000** | **86.2** |
| 4 | E5 | Si₃N₄/Ag₅Cu₉₅/Si₃N₄ | 0.861 | 0.061 | 3.99 | 0.008 | 83.7 |
| 5 | N35e | Si₃N₄/Ag₆₀Cu₄₀/Si₃N₄ (segregated) | 0.903 | 0.050 | 3.04 | 0.065 | 81.5 |
| — | M0 | AZO/Ag/AZO (**benchmark**) | 0.876 | 0.060 | 4.18 | 0.105 | 66.6 |

#### Cooling-dominated (India) — `data/targets_cooling.yaml`

| # | ID | Architecture | T_vis | g | LSG | Ag g/m² | Score |
|---|---|---|---|---|---|---|---|
| 1 | M6 | AZO/Cu/AZO | 0.738 | 0.558 | 1.32 | **0.000** | **59.8** |
| 2 | H2 | AZO/Cu/Si₃N₄ (hybrid) | 0.788 | 0.631 | 1.25 | **0.000** | **55.8** |
| 3 | S10 | ITO/Ag₇₀Cu₃₀/ITO | 0.848 | 0.619 | 1.37 | 0.081 | 53.9 |
| 4 | M3ema | AZO/Ag₇₀Cu₃₀/AZO (segregated) | 0.840 | 0.635 | 1.32 | 0.081 | 53.7 |
| — | M0 | AZO/Ag/AZO (**benchmark**) | 0.876 | 0.646 | 1.35 | 0.105 | 50.6 |

**How to read these tables:**

1. **They are not a ranking until the silver weight is fixed** — see §2.7.
2. **They share one candidate out of ten**, H2.
3. **The benchmark appears in neither top ten.**
4. **All copper-bearing entries are contingent on §6.**
5. **Scores are not comparable between the two tables** — different weighting
   files, different criteria.
6. **No cooling-profile entry meets the transmittance specification.**

**The mechanism is physical.** AZO is a transparent conductive oxide: free
carriers put a screened plasma edge at 1.25 µm, inside the solar band. Si₃N₄ is a
passive insulator. Same 11 nm copper layer, transmittance at 1200/1600/2000 nm:
AZO 0.240/0.115/0.068 against nitride 0.509/0.259/0.151.

### 5.4 Single-metal architectures cannot achieve solar control

The best light-to-solar-gain ratio across all 38 single-metal candidates is
**1.37**, against roughly 2.0 for commercial solar-control glazing.

| Architecture | Metal | Dielectric | Geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| Single | Cu | AZO | 35/12/35 | 0.738 | 0.558 | 1.32 | 0.046 | 2.87 |
| **Double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.025 | 1.67 |
| Double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.024 | **1.33** |

**LSG 1.76 against a ceiling of 1.37 — 28% better.** A single film trades
transmittance against infrared reflectance along one curve; the dielectric
*between* two metals adds an interference degree of freedom, so the two
reflections can cancel in the visible while adding in the infrared.

Note the optimum geometry: **thin outer dielectrics, thick middle.** A symmetric
guess misses it.

**A third layer is not worth adding.** LSG goes 1.33 → 1.76 → 1.81 for
n = 1, 2, 3 — the third buys 0.05 for a 25% silver increase, and for copper it
collapses transmittance to 0.437.

**But silver consumption doubles**, since each layer must independently clear
percolation near 10 nm, so double-silver scores badly on sustainability despite
being the best solar-control design found.

### 5.5 Thermodynamic screening

All fifteen nominated systems retrieved from the Materials Project and screened
within 50 meV/atom of the convex hull.

Two intermediate Ag–Cu phases exist and **neither is stable**: Cu₃Ag at
**0.0904 eV/atom** above the hull, CuAg₃ at **0.0857**. Ag–Cu is the only
nominated binary with no stable intermediate phase, and 86–90 meV/atom is well
above k_BT at deposition.

**A second finding, bearing on the ternary hypothesis.** Cu–Ti has 8 near-hull
phases and Al–Cu has 10. A dilute Ti or Al addition therefore has stable
intermetallics available to precipitate rather than remaining in solution as a
stabiliser — a second, independent mechanism for the ternary underperforming,
alongside the Nordheim conductivity penalty.

**Conclusion.** The brief's §5 suspicion of phase separation, inferred from a 13%
lattice mismatch, is now supported by first-principles data.

### 5.6 Mixing energies: the dilute corner is thermodynamically favoured

§5.5 is an equilibrium statement about *ordered* phases. A sputtered film is
neither ordered nor at equilibrium, so the disordered solid solution needed
separate treatment.

MACE-MP-0 on 32-site fcc supercells, gated against the two known hull distances
before any prediction was accepted. Positive across the whole range, fitting a
regular-solution form to ±6 meV/atom: **ΔE_mix = 0.287·x·(1−x)**.

**A self-check that matters more than the gate.** At Ag 25 at.% the surrogate
puts the *disordered* solution 13 meV/atom **below** the ordered Cu₃Ag compound —
no ordering tendency at all, which is precisely what an empty hull implies,
reached independently.

| Ag at.% | ΔE_mix | ×kT (550 K) |
|---|---|---|
| 70 — the brief's priority | 0.0602 | 1.27 |
| 15 | 0.0366 | 0.77 |
| 10 | 0.0258 | 0.54 |
| 5 | 0.0136 | 0.29 |

**In the dilute-silver corner the driving force to separate falls below thermal
energy at deposition.** §5.1 found the two microstructure hypotheses converge
there and treated it as robustness; the thermodynamics supply the reason.

**The dilute optimum is therefore supported three independent ways:** lowest
silver consumption, highest corrected score, weakest tendency to phase-separate.

**Cross-checked.** CHGNet reproduces the shape; both models under-predict — MACE
by 0.026, CHGNet by 0.047 eV/atom — so the bias is inherited from shared training
data rather than architecture-specific, meaning ΔE_mix should be corrected
upward. **They are not independent**: both train on the same Materials Project
trajectories, so agreement shows the bias is consistent, not absent.

**A compounded correction.** Verifying the brief's own claim 7 established that
GGA underestimates Cu–transition-metal formation energies by nearly 40%, because
it places Cu-3d bands too shallow. The MP hull is GGA/GGA+U and both surrogates
train on it, so two errors act in series. The conclusion **holds at 5–10 at.% Ag
and becomes marginal at 15%**.

**What a surrogate cannot do.** Optical constants, dielectric functions, band
gaps, emissivity — these models carry no electronic structure. Every optical
number here comes from the transfer-matrix model or from measurement. And a
conductivity result does not transfer to an optical one: the emissivity–sheet
resistance link assumes a low-damping Drude metal, a property of *crystalline*
silver.

### 5.7 The nucleation mechanism, and a structural weakness it exposes

§5.2 established that the dielectric changes the metal's growth and encoded it
empirically. Two surrogate calculations were run to find the mechanism. **Both
failed:**

| Attempt | Failure mode |
|---|---|
| Bulk interface adhesion | 5–21% lattice mismatch — measured elastic strain, not binding |
| Adatom wetting | ZnO(0001) termination changed the result by 2.1 eV, against 0.46 eV between materials |

**A literature search resolved it in under an hour.** US 7,632,572 B2 /
US 8,512,883 B2 (AFG Industries → AGC → Cardinal CG; **full text read**)
deposited 16 nm Ag on amorphous TiOx and on a 5 nm ZnO seed over the same TiOx,
and examined both by TEM:

- **25 nm grains on ZnO against 15 nm on a-TiOx**
- {111}-oriented grains **two to three times larger** on ZnO
- the film on bare amorphous titania **clearly discontinuous** where the
  ZnO-seeded film was continuous across the whole specimen

**The inventors name the mechanism.** Zinc oxide grows {0001}, which orients the
silver to grow {111}, and the epitaxial lattice match between Ag{111} and
ZnO{0001} lowers sheet resistance and improves adhesion.

**And it validates this framework quantitatively.** The patent reports four-point
sheet resistance — **5.68 Ω/□ with the ZnO seed, 7.56 without**, a ratio of
**1.331**. The `metal_growth_factor` values of §5.2 were calibrated independently
from a different group's *emissivity* series and give **1.250**.

| | Ratio, titania-like : zinc-oxide-like |
|---|---|
| Patent, four-point sheet resistance, 16 nm Ag | 1.331 |
| This framework, calibrated to emissivity | 1.250 |
| **Agreement** | **93.9%** |

This is the first independent quantitative validation of a parameter in this
work: fitted to one dataset, it reproduces another it never saw. The comparison
is not exact — the patent contrasts a ZnO seed *over* titania against titania
alone — so it is corroboration rather than confirmation.

**A percolation datum follows.** The patent claims continuous, strongly adherent
silver **down to 8 nm** on a zinc oxide seed, against the 10 nm this framework
assumes. A 20% difference, and one that would move every silver-consumption
figure in §5.1.

> **The structural weakness.** The framework models each metal layer as though
> the layer beneath it did not shape its microstructure. That single omission
> accounts for **both** `metal_growth_factor` **and** the eightfold copper
> under-prediction of §6. They are one effect appearing twice, not two separate
> caveats.

**A successor should replace the empirical multiplier with a measured
`grain_size_ratio` per underlayer**, which is physically meaningful, directly
measurable, and feeds both the optical and electrical paths through the existing
Mayadas–Shatzkes term.

---

## 6. The critical unknown, and the experiment that resolves it

### 6.1 What is wrong

The framework validates well against silver in the infrared — within 0.4% on the
benchmark it reproduces best — and **fails on copper**, under-predicting
sputtered sheet resistance by roughly eightfold. **Six of the leading candidates
in both climate profiles are copper-based.**

**The classical size effect is eliminated.** Four independent published fits give
specularity 0.48–0.80 and grain-boundary reflection 0.16–0.43. This framework's
assumed 0.50 and 0.25 sit inside that range, and an exhaustive scan over the
entire admissible range reaches only **4.42 Ω/sq against the 16.6 to be
explained** — short by a factor of 3.8.

**Grain structure is the leading hypothesis:** grains at roughly half the film
thickness give 14.1 Ω/sq.

**And a seed layer recovers most of the gap.** Six further AZO/Cu/AZO studies were
located:

| Film | Seed | R_s |
|---|---|---|
| AZO/**Ti**/Cu/AZO, *Opt. Lett.* 2017 | 1–2 nm Ti | **4.31 Ω/sq** |
| AZO/Cu/AZO, ApSS 2022 | none | 9.96 |
| AZO/Cu/AZO, Miao 2014 | none | 16.6 |
| **this framework, 15 nm Cu** | — | **2.16** |

The framework is eightfold optimistic against unseeded copper and roughly
**twofold** against seeded copper. **So the model is not wrong about copper as a
material — it is wrong about poorly nucleated copper**, which is the same
mechanism as §5.7 in a third independent place.

**If that reading is right, copper's obstacle is film quality, not physics** — an
engineering problem with known levers rather than a fundamental limit.

### 6.2 The experiment

**One XRD scan, one film, an afternoon — and it answers three questions.**

| Measurement | Question answered |
|---|---|
| Peak count and position | **Microstructure.** Segregated gives two fcc sets; a solid solution gives one at a Vegard-interpolated angle |
| Scherrer peak width | **Grain size**, and therefore `grain_size_ratio` — the parameter §5.7 identifies as the common cause |
| (111)/(200) ratio vs the powder value of 2.2 | **Templating**, the mechanism of §5.7 |

`pvdlowe.characterise` states in advance what the scan should show under each
hypothesis, so it can be planned rather than interpreted afterwards.

**A second, independent discriminator.** Sheet resistance separates the
microstructure hypotheses by a number — 6.4 against 2.6 Ω/sq. Diffraction
separates them by *peak count*. Two unrelated observables agreeing is far
stronger than either alone, and both come from one film.

**Four requirements, all cheap:**

1. **Scan to 2θ = 100°, not 60.** Separation grows faster than width with angle.
2. **Grazing incidence, not Bragg–Brentano.** A 2010 study of this exact
   architecture reports *no detectable Cu peaks* for 3–13 nm layers, while ApSS
   2022 sees a weak (111) at 43.8° — matching this framework's predicted 43.32°.
   A copper peak here is **marginal**, and a null would otherwise be ambiguous
   between "nanocrystalline" and "insufficient signal".
3. **A 30 nm uncapped calibration film**, to prove the measurement works before
   applying it to the marginal case.
4. **A seeded arm** — one extra target, per §6.1.

**Pre-registered decision rules** are in `experiments/PROTOCOL_cu_series.md` —
four outcomes, each with what it means and what to do, **including the one where
the literature is right and six candidates fall over.**

---

## 7. The question only Saint-Gobain can answer

This report benchmarks against a 10 nm AZO/Ag/AZO at ε_h 0.060, taken from the
brief — **whose citations for that stack are the two disputed entries of §3.2.**

Saint-Gobain's own patents (US 7,745,009) claim silver at **12.5–16 nm targeting
ε ≤ 0.038**. This model says that needs 14–16 nm.

| Ag nm | ε_h | Ag g/m² |
|---|---|---|
| **10.0** (current benchmark) | 0.060 | 0.105 |
| 14.0 | 0.039 | 0.147 |
| 16.0 | 0.033 | 0.168 |

**If production runs at 12.5–16 nm, the silver reductions reported here are
measured against a stack that would not meet Saint-Gobain's own emissivity
specification.** The baseline needs confirming before the percentages are quoted.

Alongside it, §4.3: **which transmittance target is real** — the brief's 0.80, or
ECBC compliance at 0.644. They cannot both be met.

---

## 8. Limitations

### 8.1 No experimental validation

Every performance figure is a model output. Median error against traceable
literature is 30.6%.

### 8.2 The principal structural weakness

**The framework models each metal layer as though the layer beneath it did not
shape its microstructure.** §5.7 establishes that this single omission accounts
for both the empirical `metal_growth_factor` and the eightfold copper
under-prediction of §6. Grain size in a sputtered film is set substantially by
the underlayer — 25 nm on crystalline ZnO against 15 nm on an amorphous oxide,
measured by TEM — and grain size feeds directly into the Mayadas–Shatzkes term
the framework already contains.

### 8.3 Calibrated and fitted parameters

Specularity and grain-boundary reflection are fitted, not measured. Si₃N₄ and
TiO₂ optical constants are `ESTIMATE` grade. `metal_growth_factor` is calibrated
to one measured series, with copper untested — though §5.7 supplies independent
corroboration to 6%.

### 8.4 Illuminant approximation, quantified

Varying colour temperature over 5000–7500 K moves **T_vis by 0.1%** and **T_sol
by 8.3%**. T_vis is reportable as computed; T_sol, g-value and LSG carry a 5–10%
systematic until tabulated AM1.5G spectra are supplied.

### 8.5 Scores are not portable between weightings

Absolute scores moved by roughly 25 points as the §2 defects were fixed. **A
score is not a property of a material.** Always quote the weighting file.

### 8.6 Not modelled at all

Roughness, interdiffusion, damp-heat and abrasion durability, adhesion,
agglomeration kinetics, amorphous metal layers, and any property of a metastable
sputtered alloy that a 0 K ordered-crystal database cannot supply.

---

## 9. Conclusion

**What this work established.** A better composition — 5–15 at.% Ag rather than
70%, supported on three independent grounds. A better material class — silicon
nitride, outside the brief's search framing, with the hybrid AZO/metal/Si₃N₄
arrangement beating both pure stacks and matching what industry does. A better
architecture — two metal layers reaching LSG 1.76 against a single-metal ceiling
of 1.37. And a specified climate dependency: the two profiles share one candidate
out of ten.

**What it corrected.** Six defects in the proposed weighting, one of which let
the optimiser return 29% more silver than the incumbent at a perfect score. Two
citations that cannot be traced. One measurement inconsistent with a
model-independent limit, with six explanations eliminated. And five of its own
conclusions, overturned by finer resolution or better sources and recorded rather
than hidden.

**What it cannot claim.** Nothing has been deposited. The candidate rankings are
hypotheses ordered by physics, suitable for directing experimental effort. Their
principal weakness is known, quantified, and addressed by a specified experiment.

**The recommendation.** One XRD scan, one film, an afternoon — measuring the
grain size that §5.7 identifies as the common cause of two separate limitations,
testing the templating mechanism directly, and discriminating the microstructure
hypotheses by a second independent route.

And two questions to Saint-Gobain: **which stack is the right baseline**, and
**which transmittance target is real.**

> A model that identifies the measurement capable of falsifying it is more
> useful to an experimental programme than one that does not. That is what this
> framework is for, and it is what it delivered.
