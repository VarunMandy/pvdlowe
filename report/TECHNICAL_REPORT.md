# Computational screening of sustainable low-emissivity PVD coatings on soda-lime float glass

**Technical report**
Saint-Gobain Research India
Author: Varun Mandy, Research Intern
Framework: `pvdlowe` v0.1.0 — https://github.com/VarunMandy/pvdlowe

---

## Abstract

A computational framework was developed to execute the screening workflow set
out in the project brief *PVD_Usecase.docx*: element screening, thermodynamic
stability, optical multilayer modelling, design of experiments and
multi-objective ranking, for cost-effective low-emissivity coatings deposited by
argon magnetron sputtering.

Applying the framework to the brief produced three classes of result. First, the
proposed multi-objective weighting was found to contain four defects, one of
which allowed a thickness optimiser to return a design consuming 29% *more*
silver than the incumbent while scoring 100/100. Second, two of the brief's
literature citations could not be matched to any locatable source, and one
pivotal measurement was found inconsistent with a model-independent
electrodynamic limit. Thermodynamic screening of all fifteen nominated chemical systems confirmed that
Ag–Cu possesses no stable ordered compound, supporting the brief's suspicion of
phase separation with first-principles evidence. Third, the design-space search
identified a material class
and a stack architecture outside the brief's framing, both of which outperform
the proposed candidates: silicon nitride dielectrics improve visible
transmittance by up to nine percentage points over AZO, and the composition
optimum lies at 5–15 at.% Ag rather than the proposed 70%.

**No films were deposited.** All performance figures are model outputs. The
framework's own validation identifies its largest error — an approximately
eightfold under-prediction of sputtered copper sheet resistance — in the
material on which most leading candidates depend. A specified experiment
resolving this, with pre-registered decision rules and an automated analysis
path, is delivered with the framework.

---

## 1. Scope and deliverables

### 1.1 What was asked

The brief proposed a materials-by-design programme for transparent
low-emissivity coatings on float glass, centred on a dielectric/metal/dielectric
architecture (AZO/metal/AZO) and asking how much silver could be removed while
retaining visible transmittance, sheet resistance and far-infrared reflectance.

### 1.2 What was delivered

| Deliverable | Status |
|---|---|
| Computational framework implementing the brief's §21 workflow | Complete — 12,000 lines, 86 tests |
| Element and compound screening | Complete |
| Optical multilayer model (transfer matrix, EN 410 / 673 / 12898) | Complete, validated |
| Thin-film transport model coupled to optics | Complete, **uncalibrated — requires §6 experiment** |
| Multi-objective scoring with provenance grading | Complete |
| Design of experiments generator | Complete |
| DFT input generation (VASP) | Complete, **not executed — requires VASP licence and HPC allocation** |
| Materials Project integration | **Complete and executed** — 15/15 systems retrieved |
| Candidate ranking, 36 architectures | Complete, **model outputs only** |
| Experimental protocol with pre-registered analysis | Complete, **not executed — requires tool access** |
| Illuminant sensitivity quantified | Complete (§7.3) |
| Manufacturability constraints | Complete |
| Triple-metal architecture search | Complete — negative result (§5.4) |

Repository, documentation, results and protocols are version-controlled and
archived to `gs://sg-llamole-pvdlowe/pvdlowe/source/`.

### 1.3 What was not done, and why

No depositions were performed. The author did not have sputter tool access
during the internship period. The experimental work is therefore specified
rather than executed, and the protocol in §6 is written as a handover document
that a colleague with tool access can run without further input.

---

## 2. The framework

### 2.1 Physical model

**Optics.** A vectorised transfer-matrix solver handles arbitrary layer counts,
complex refractive indices, both polarisations and oblique incidence. Thick
glass is treated incoherently. Verified against exact Fresnel reflectance for a
bare interface, exact null for a quarter-wave antireflection layer, and energy
conservation to 10⁻¹⁰ on absorbing stacks.

**Optical constants.** Metals use the Lorentz–Drude parameterisation of Rakić et
al. (1998), with one deliberate departure: the free-electron damping is
re-anchored to DC resistivity rather than taken from the published optical fit.
Rakić's fitted Γ₀ for silver implies ρ ≈ 4.4 µΩ·cm against a true 1.587, because
in the visible the Drude term trades off against interband oscillators. Using
the published value and then applying a thin-film size-effect multiplier
double-counts the same scattering, and inflated modelled emissivity roughly
threefold in an early build.

**Transport.** Full Fuchs–Sondheimer integral for surface scattering,
Mayadas–Shatzkes for grain boundaries, and a percolation model below a critical
thickness. Critically, the resulting resistivity ratio **feeds back into the
Drude damping**: a film too thin to conduct is automatically a film that
reflects poorly. Without this coupling, optimising for transmittance drives the
metal thickness to zero and reports an excellent coating.

**Standards integration.** EN 410 / ISO 9050 for visible and solar
transmittance; EN 12898 for normal emissivity, weighted by a 283 K Planck
radiance; EN 673 for the hemispherical correction and centre-pane U-value,
cross-checked against direct angular integration.

### 2.2 Provenance grading

Every physical quantity carries an evidence grade — MEASURED, LITERATURE,
LITERATURE_UNVERIFIED, MP_API, DFT_OWN, MODEL, CALIBRATED, ESTIMATE, HYPOTHESIS
— and a guard function refuses to admit HYPOTHESIS-grade values into headline
tables without explicit opt-in.

This implements the brief's own caution ("I would not yet put numerical DFT
values for Ag₇₀Cu₂₉Ti₁ into a thesis as if they were established facts") as a
type constraint rather than a footnote, so the distinction survives contact
with a spreadsheet.

---

## 3. Method audit: the multi-objective weighting

The brief's §14 specifies criteria and weights for ranking candidates. Encoding
that table literally produced a scoring function that did not measure the
project's stated objective. Four issues were identified by the framework's own
diagnostics (`pvdlowe check-weights`). All are documented decisions in
`data/targets.yaml`; none is a silent change.

### 3.1 Silver consumption carried zero weight

The §14 table contains no line for silver consumption, although §17 and §20 both
name minimising it as an objective. In the literal encoding, silver mass was
computed, displayed, and reported as the limiting criterion, but contributed
nothing to the score.

The thickness optimiser exploited this immediately, returning a 12.84 nm design
using **0.135 g/m² of silver — 29% more than the incumbent benchmark — at a
score of 100/100.**

*Correction applied:* weight 0.15.

### 3.2 Emissivity and sheet resistance double-count one property

Across the candidate set these correlate at **r = 0.996**, because both are the
free-carrier response of the same metal layer. The §14 weights of 0.25 and 0.15
therefore place 0.40 of the total on a single physical quantity.

*Correction applied:* sheet resistance weighted 0.0 and reported as a
constraint. This should be reversed (with emissivity reduced to 0.15) if the
coating is also required to function as a transparent electrode, where sheet
resistance is an independent objective.

The same diagnostic flags cost against supply risk (r = 0.993) and silver mass
against cost (r = 1.000 — silver dominates metal cost so completely that they
are the same quantity in different units).

### 3.3 Targets set at the specification minimum, causing saturation

Derringer–Suich desirability saturates at 1.0 once a target is reached. Setting
the visible-transmittance target to 0.80 — the brief's *floor of acceptability*
— made the criterion flat exactly where candidates differ.

The consequence was measurable: across 181 oxide-thickness combinations clearing
T_vis = 0.80, transmittance spanned 0.800 to 0.881 while the **score decreased**
from 74.99 to 73.30. The optimiser satisficed at the specification floor and
drove the top oxide to 15 nm, a thickness that would not survive handling.

*Correction applied:* targets set as aspirations (T_vis 0.90, ε_h 0.02).
Re-optimising then returned AZO 25 / Ag 10 / AZO 35 nm at T_vis 0.880 — eight
points better on identical silver.

*General principle:* a desirability target should be an aspiration, not a
specification minimum.

### 3.4 The supply-risk band could not discriminate

With floor 8.0 against candidate values of 4.5–7.5, all silver-bearing
compositions scored 0.1–0.28 and supply risk was reported as limiting for 12 of
14 candidates.

*Correction applied:* floor 9.5, target 4.0 — still zeroing indium-bearing ITO,
which is the criterion's purpose.

### 3.5 Aggregation

The brief states its weighting should prevent a candidate "winning simply
because it has excellent conductivity while being unacceptable optically". A
weighted arithmetic sum does not achieve this — a candidate scoring zero on one
criterion forfeits only that criterion's weight. A geometric mean does.

Under the corrected weighting the pure-silver benchmark ranks 4th under
arithmetic aggregation and 7th under geometric; pure copper ranks 1st and 2nd
respectively. These are precisely the two candidates the brief is concerned with
comparing. The framework defaults to geometric and reports both.

### 3.6 Note on interpreting the diagnostics

The `limiting_criterion` field is `argmin(desirability)` — where a candidate is
weakest, not what drives the ordering. Under geometric aggregation, whichever
criterion sits nearest its floor is reported as limiting for every candidate.
The appropriate test of whether weights are doing work is the weight-sensitivity
analysis: before these corrections, one candidate won 97.5% of randomised
weightings with a rank standard deviation of 0.16, which indicates the weights
had no effect rather than that the result was robust.

---

## 4. Evidence audit

Eight literature benchmarks were transcribed from the brief. All eight sources
have now been located; none has been read in full text.

| State | Count |
|---|---|
| Fully verified (full text read, measurement basis confirmed) | 0 |
| Partial (source identified, figures confirmed against abstract) | 6 |
| **Disputed (located sources do not contain the quoted figures)** | **2** |
| Not located | 0 |

### 4.1 Two citations could not be supported

The figures **85.4% T_vis / 3.21 Ω/sq / 97% FIR** and **78.7% T_vis / 2.7 Ω/sq**
appear in neither located AZO/Ag/AZO study. A companion PET-substrate paper
reports 78.5% with 91% FIR at 10 nm Ag — close to one, but a different substrate
and a different figure.

**Recommendation: these two entries should not be cited** pending
identification of their source. Both are flagged `disputed` in the framework.

A corollary worth recording: these two entries are the model's three closest
agreements (0.3%, 1.0%, 1.2% relative error). Excluding them, the median
validation error rises from 14.7% to 30.6%. The framework's apparent accuracy
rested partly on figures that cannot be traced.

### 4.2 A pivotal measurement is physically inconsistent

*Applied Surface Science* **578** (2022) 152051 reports AZO(40)/Cu/AZO(40) with
T_vis 87.7%, R_s 9.96 Ω/sq and ε 0.055. The brief's §16 concludes from this that
a silver-free stack may already meet a low-emissivity target — a conclusion that
reframes the entire programme.

The transcription is accurate and the abstract attributes all three values to
one sample. However, for a conducting sheet thin compared with the wavelength,
far-infrared reflectance is fixed by sheet resistance alone:

```
r = (n₁ − n₂ − Z₀/R_s) / (n₁ + n₂ + Z₀/R_s),    ε = 1 − r²
```

with Z₀ = 376.73 Ω. No fitted parameter enters. At 9.96 Ω/sq this gives
**ε ≥ 0.096**; the reported 0.055 would require approximately 5.5 Ω/sq.

Four candidate explanations were tested and eliminated:

| Explanation | Outcome |
|---|---|
| Values from different samples | Abstract attributes all three to one sample |
| Transcription error | Confirmed against published abstract |
| Far-IR glass index assumption | Limit is 0.091–0.097 across n = 1.5 to 4.0 |
| Band-limited emissometer (8–14 µm) | **Reads 5–8% higher, not lower — moves it the wrong way** |

The band-emissometer hypothesis was the most plausible and was tested by
implementing band-limited emissivity in the framework. For a Drude metal,
reflectance is nearly flat across 5–14 µm and the 283 K Planck weighting already
peaks near 10 µm, so restricting the band removes the 5–8 µm region where these
stacks reflect slightly less well. Correcting for measurement basis therefore
*worsens* the discrepancy, from 0.58 to 0.53 of the limit.

The same group reports ε = 0.045 at 8.10 Ω/sq and ε = 0.050 at comparable sheet
resistance. Three measurements at a consistent 0.57–0.63 of the electrodynamic
limit indicates a systematic effect rather than an isolated error.

**Untested:** hemispherical versus normal basis (which would also raise the
reading), instrument calibration, or the two quantities being measured on
different areas of one nominal sample.

**Recommendation:** obtain the full text and establish the measurement basis
before §16's conclusion is used. This is the single highest-value literature
action outstanding.

### 4.3 A reported thin-film resistivity that cannot be correct

A 2025 study reports ~10 nm films of Ag at 1.59 µΩ·cm, Ag–Cu at 2.97 and Cu at
20.5, deposited under identical conditions.

| Film | Reported | × bulk | Framework model |
|---|---|---|---|
| Ag, 10 nm | 1.59 µΩ·cm | 1.00× | 4.44 µΩ·cm (2.79×) |
| Cu, 10 nm | 20.5 µΩ·cm | 12.2× | 7.11 µΩ·cm (4.23×) |

Silver's electron mean free path is 53 nm; a 10 nm film cannot reach bulk
resistivity, and Fuchs–Sondheimer alone forces a ratio above approximately 2.
The stated thickness uncertainty (±2.5 nm) does not resolve this: the upper
bound is still 1.25× bulk. Under identical deposition, the copper film shows a
strong size effect and the silver film shows none.

**Consequence for the brief.** §7 argues that amorphous Ag–Cu retains unusually
good conductivity by comparing 2.97 against 1.59. If the silver baseline is not
like-for-like, the comparison should be made against the copper value (20.5),
against which the alloy appears sevenfold better — the argument survives in
stronger form.

### 4.4 Three factual corrections

- **Deposition methods differ across the benchmark set.** The AZO/Ag/AZO
  trilayers used RF magnetron sputtering (§3 implies DC); the AZO single-layer
  study used medium-frequency sputtering. Film density and resistivity do not
  transfer between techniques and these sources should not be pooled.
- **The AZO visible transmittance is 81.4%, not 82.4%.** Resistivity
  2.6 × 10⁻³ Ω·cm, hardness 11.4 GPa and reduced modulus 98 GPa are confirmed.
- **§7's resistivity table mixes measurement conventions**, per §4.3 above.

### 4.5 What verification confirmed

The *Ceramics International* study states that far-infrared reflectance was
measured by FTIR spectroscopy and sheet resistance by four-point probe — a
spectroscopic reflectance directly comparable with the framework's convention,
with no emissometer ambiguity. This is consistent with the model reproducing
that benchmark to 0.4%, its closest agreement against a traceable source.

It also independently supports the percolation anchor: silver continuity at
10 nm is confirmed by XRD (200 and 220 reflections), which is structural
evidence rather than an inference from a resistivity discontinuity.

---

## 5. Design-space results

Thirty-six candidate architectures were evaluated; 58 metal systems screened; a
168-point composition series run across two microstructure models, two
dielectrics and two climate profiles.

### 5.1 The composition optimum lies at 5–15 at.% Ag

Eight composition curves were generated with stack geometry re-optimised at
every composition (Ag 0–100% in 5% steps).

| Profile | Microstructure | Dielectric | Optimum Ag | Score | Plateau |
|---|---|---|---|---|---|
| Heating | Segregated | Si₃N₄ | **0.05** | **89.3** | 0.00–0.20 |
| Heating | Solid solution | Si₃N₄ | 0.00 | 88.9 | 0.00 |
| Heating | Segregated | AZO | **0.10** | 76.5 | **0.05–0.40** |
| Heating | Solid solution | AZO | 0.00 | 74.4 | 0.00–0.05 |
| Cooling | Either | AZO | 0.00 | 68.2 | 0.00–0.15 |
| Cooling | Either | Si₃N₄ | 0.00 | 67.6 | 0.00–0.10 |

Every curve peaks between 0 and 10 at.% Ag. The brief's Ag₇₀Cu₃₀ priority
composition is outperformed in all eight combinations.

**This is a sustainability result, not a performance one.** Emissivity and sheet
resistance continue improving to 50 at.% Ag (0.0386 and 2.59 Ω/sq, the best in
the series). The score declines because silver mass carries weight. The trade is
approximately 0.005 in emissivity for an 87% reduction in silver, and it is the
correct trade only under the premise that silver consumption matters.

**Plateau width is more relevant to process capability than peak position.** The
segregated/AZO curve is flat from 5 to 40 at.% Ag — a wide composition tolerance.
Solid-solution curves are sharp (0–5%).

**The unresolved microstructure question loses importance in the dilute regime.**
At Ag₇₀Cu₃₀ the two hypotheses differ by 9–14 points; at Ag₅Cu₉₅ by 2.5. Designing
at 5–15 at.% Ag makes the programme robust to a question that is currently
unsettled, rather than dependent on it.

### 5.2 Silicon nitride outperforms AZO on visible transmittance

An initial screen of 58 metal systems at fixed AZO thickness found that **only
pure silver met the full specification**; copper failed on transmittance alone
(0.752 against 0.80). Allowing the dielectric to vary changed this:

| Metal | AZO | SnO₂ | TiO₂ | **Si₃N₄** |
|---|---|---|---|---|
| Cu | 0.755 | 0.795 | 0.786 | **0.845** |
| Cu₉₀Zn₁₀ | 0.772 | 0.808 | 0.780 | **0.836** |
| Ag₇₀Cu₃₀ | 0.837 | 0.869 | 0.835 | **0.912** |
| Ag | 0.880 | 0.902 | 0.868 | **0.923** |

Silicon nitride gains **nine percentage points of visible transmittance on
copper** — the margin that was disqualifying it. All metals improve, indicating
a dielectric property rather than a copper-specific effect.

Notably, **the highest-index material does not win**: TiO₂ (n = 2.45)
underperforms SnO₂ (n = 2.00). Antireflection around a metal layer is an
index-*matching* problem, not an index-*maximisation* problem.

**Why this was outside the brief's framing.** The brief's screening began from
the periodic table and the Materials Project, both of which surface oxides.
Nitrides fall outside that search structure. Silicon nitride is nonetheless the
industry-standard Low-E dielectric — dense, an effective diffusion barrier, and
durable through tempering — and it blocks the oxygen ingress that is copper's
dominant degradation pathway, which is precisely why the Cu/Si₃N₄ pairing is
attractive and why it does not appear in the AZO literature.

**Lattice absorption was checked and found negligible.** Si₃N₄ absorbs near
11.7 µm, within the thermal band, so far-infrared phonon oscillators were added
to the model. The penalty on the copper stack is +0.0007 in emissivity (1.7%
relative), because at 10 µm the copper layer reflects approximately 96% of the
incident field and little reaches the nitride.

### 5.3 Climate reverses the ranking

The brief does not specify a climate, and `targets.yaml` as derived from it does
not constrain solar heat gain. That omission encodes a heating-dominated
assumption. Adding the EN 410 / ISO 9050 metrics:

```
g = T_sol + N·A_sol      (N = 0.36 for a coating on surface 2)
LSG = T_vis / g
```

| Candidate | Heating | Rank | Cooling | Rank | g | LSG |
|---|---|---|---|---|---|---|
| Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ | **89.3** | 1 | 50.4 | 20 | 0.760 | 1.16 |
| Si₃N₄/Cu/Si₃N₄ | 88.9 | 3 | 55.5 | 12 | 0.731 | 1.18 |
| **AZO/Cu/AZO** | 69.6 | 15 | **65.4** | **1** | 0.558 | 1.32 |
| AZO/Ag/AZO (benchmark) | 65.0 | 22 | 53.0 | 17 | 0.646 | 1.35 |

The mechanism is physical, not a scoring artifact. **AZO is a transparent
conductive oxide**: its free carriers give a screened plasma wavelength at
1.25 µm, inside the solar band. Si₃N₄ is a passive insulator, transparent
throughout.

| λ (nm) | 1200 | 1600 | 2000 | 2400 |
|---|---|---|---|---|
| Transmittance, AZO stack | 0.240 | 0.115 | 0.068 | 0.046 |
| Transmittance, Si₃N₄ stack | 0.509 | 0.259 | 0.151 | 0.099 |

Same 11 nm copper layer in both. **The conductive oxide performs solar-control
work that a passive nitride cannot.** §5.2 read AZO's near-infrared absorption
purely as a transmittance penalty; a substantial part of it is a solar-control
benefit that the heating-weighted objective could not see.

**For Indian architectural glazing this is decisive**, and the recommended
material differs from the heating-climate case. A results table should not be
circulated without its weighting profile attached.

### 5.4 Single-metal architectures cannot achieve solar control

The best light-to-solar-gain ratio across all 36 candidates is **1.37**, against
approximately 2.0 for commercial solar-control glazing. Under the cooling
profile, no single-metal stack met the transmittance target.

Generalising the framework to n metal layers separated by n+1 dielectrics:

| Architecture | Metal | Dielectric | Geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| Single | Cu | AZO | 45/12/45 | 0.738 | 0.558 | 1.32 | 0.0463 | 2.87 |
| **Double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.0248 | 1.67 |
| Double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.0244 | **1.33** |

**LSG 1.76 against a single-metal ceiling of 1.37 — a 28% improvement.**

A single metal film trades transmittance against infrared reflectance along one
curve; thickness moves along that curve but not off it. The dielectric *between*
two metal layers introduces an interference degree of freedom, allowing the two
metal reflections to cancel in the visible while adding in the infrared. This
degree of freedom does not exist with one metal layer at any thickness or
composition — the limitation is architectural, and no compositional search could
have revealed it.

**A third metal layer was tested and is not worth adding.** Scanning n = 1, 2, 3
against the cooling profile, the second layer buys a large gain and the third
almost none:

| n | Ag/Si₃N₄ LSG | Ag (g/m²) | Cu/Si₃N₄ cooling score |
|---|---|---|---|
| 1 | 1.33 | 0.115 | 67.3 |
| 2 | **1.76** | 0.252 | **68.9** |
| 3 | 1.81 | 0.315 | 37.2 |

The third layer adds 0.05 in LSG for a 25% increase in silver, and for copper it
is actively harmful — transmittance collapses to 0.437 and the cooling score
halves. **The architecture argument stops at two layers for this
specification.** Commercial triple-silver products reach LSG ≈ 2.0 using
asymmetric layer thicknesses and tuned interlayer spacing that this coarse scan
did not explore; that remains open, but it is a fine-optimisation question
rather than an architectural one.

**Costs are real.** Silver consumption doubles, since each layer must
independently exceed percolation near 10 nm. Splitting a film also raises
resistance: two 12 nm layers are not equivalent to one 24 nm layer, each
carrying its own surface scattering. Process complexity rises to five layers.

**Of most interest for the Indian application:** the double-copper Si₃N₄ stack
achieves LSG 1.39 at R_s 1.33 Ω/sq and ε_h 0.0244 with **zero silver**, scoring
68.9 on the cooling profile — the highest of any candidate evaluated. Its sheet
resistance and emissivity are the best figures the framework has produced.
Transmittance at 0.716 remains short of 0.80, but the deficit has narrowed from
12 points to 8 and the dielectric search was coarse.

### 5.5 Thermodynamic screening (Materials Project)

All fifteen chemical systems nominated in the brief's §9 were retrieved and
screened for phases within 50 meV/atom of the convex hull.

**The central result: Ag–Cu has no stable ordered compound.** Two intermediate
phases exist and neither lies on the hull:

| Phase | E above hull | Stable |
|---|---|---|
| Cu₃Ag | 0.0904 eV/atom | No |
| CuAg₃ | 0.0857 eV/atom | No |

Ag–Cu is thermodynamically a **phase-separating system** — which the brief's §5
suspected from the 13% lattice mismatch, and which is now supported by
first-principles data rather than inferred. The magnitude matters: 86–90 meV/atom
is well above k_BT at deposition (26 meV at 300 K, 48 meV at 550 K), so the
driving force to separate is substantial rather than marginal.

**What this does and does not establish.** It is an equilibrium statement. A
magnetron-sputtered film is quenched from the vapour at effective rates that
routinely trap metastable solid solutions, so it does not predict the
as-deposited microstructure. It predicts what the film will do on annealing —
which is precisely the discriminating experiment of §8.3, and it indicates the
direction to expect: resistivity should *fall* as copper precipitates from a
trapped solution.

It also lends thermodynamic support to the segregated microstructure model, under
which §5.1's dilute-silver optimum is strongest.

**Ag–Cu is the only nominated binary with no stable intermediate phase:**

| System | Entries | Near-hull | Representative phases |
|---|---|---|---|
| **Ag–Cu** | 2 | **0** | — (phase-separating) |
| Ag–Ti | 4 | 2 | Ti₂Ag, TiAg |
| Al–Cu | 15 | 10 | Al₂Cu, AlCu, AlCu₃ |
| Cu–Ti | 12 | 8 | TiCu, TiCu₂, Ti₂Cu |
| Al–Zn–O | 4 | 2 | Al₂ZnO₄, Al₁₀ZnO₁₆ |
| Cu–O | 37 | 9 | Cu₂O, CuO, Cu₄O₃ |
| Ag–O | 18 | 11 | Ag₂O, AgO, Ag₃O |
| Ag–Cu–O | 7 | 4 | CuAgO₂, Cu₂Ag₂O₃ |

**This adds a mechanism to the dilute-stabiliser finding in §5.6.** Both Cu–Ti
and Al–Cu are richly intermetallic — eight and ten near-hull phases
respectively. A dilute Ti or Al addition to a Cu-bearing film therefore has
stable compounds available to form, so on annealing it is more likely to
precipitate an intermetallic than to remain in solution acting as a stabiliser.
That is a second reason for the ternary underperforming, independent of the
conductivity penalty.

**Ag–Cu–O is also populated** (four near-hull phases including CuAgO₂), which
bears on durability: an Ag–Cu film that oxidises has stable ternary oxides
available, not merely a mixture of Ag₂O and CuO.

**Limitation.** The Materials Project holds DFT results for ordered crystalline
phases at 0 K. It cannot describe a disordered sputtered solid solution,
thin-film optical constants at 10 nm, or interface energies against an amorphous
oxide. The framework records this limitation per query rather than leaving it
implicit.

### 5.6 The dilute-titanium ternary is predicted to underperform

Ag₇₀Cu₂₉Ti₁, proposed in the brief on the hypothesis that dilute Ti stabilises
the metal layer, ranks 13th of 14 in the original candidate set. Titanium's bulk
resistivity is 42 µΩ·cm, approximately 26× silver's; even at 1 at.% this raises
alloy resistivity enough to give the worst sheet resistance (7.55 Ω/sq) and
worst emissivity (0.0921) in the set. The interfacial benefit may be real, but
the conductivity penalty is weighting-independent.

A titanium *barrier layer* remains the better test of the interface hypothesis,
isolating the interfacial effect without placing Ti in the conduction path — as
industrial coatings do. It is not, however, a silver-reduction candidate: it
uses a full pure-silver layer and ranks last once silver consumption is
weighted. The two claims should be kept separate.

---

## 6. The critical unknown, and the experiment that resolves it

### 6.1 The discrepancy

Validation against literature shows the model reproducing silver stacks well in
the infrared — its intended strength — and failing on copper:

| Benchmark | Metric | Reported | Modelled | Error |
|---|---|---|---|---|
| AZO/Ag(13)/AZO | Far-IR reflectance | 0.960 | 0.964 | 0.4% |
| AZO/Cu/AZO (2022) | Sheet resistance | 9.96 | 2.86 | 71% |
| AZO/Cu(15)/AZO | Sheet resistance | 16.6 | 2.10 | 87% |

The model under-predicts sputtered copper sheet resistance by approximately
eightfold. The classical size effect cannot account for a gap of this magnitude,
which points to a mechanism the model does not contain: oxygen incorporation
during deposition, native oxide at the interfaces, or substantially poorer grain
structure than silver on the same underlayer.

**If this reading is correct, the obstacle to the copper route is film quality
rather than intrinsic physics** — an engineering problem with known levers (base
pressure, seed layers, getter, substrate temperature) rather than a fundamental
limit. That is a considerably more tractable target than replacing silver's
electronic structure.

**It also gates six of the leading candidates** in both climate profiles.

### 6.2 The experiment

Specified in `experiments/BENCH_cu_series.md` with pre-registered decision rules
in `experiments/PROTOCOL_cu_series.md`.

**Matrix.** Cu at 8, 10, 12, 14, 16, 18, 20 nm plus a 10 nm Ag control, all as
AZO(40)/metal/AZO(40) capped trilayers, deposition order randomised. Plus one
uncapped Cu film at 12 nm as an oxidation control.

**Key design decisions.**

*Films must be capped.* Bare 10 nm copper oxidises in air within minutes, and the
hypothesis under test is that oxygen degrades these films. A bare film measured
after venting reports air oxidation rather than deposition quality. The
framework de-embeds the AZO shunt to recover the metal layer; the correction is
non-linear and largest where it matters — a measured 16.6 Ω/sq trilayer is
22.6 Ω/sq in the metal alone, a 36% difference. Omitting it would bias the
result toward "the copper is acceptable".

*Order randomised.* Target erosion drifts across a campaign; in ascending
thickness order that drift aliases directly onto thickness and cannot be
separated from a size effect.

*Thickness measured independently.* ρ = R_s · t, so a 20% thickness error becomes
a 20% resistivity error and would be misattributed to a scattering parameter.

*Silver control is a stop condition.* AZO/Ag(10)/AZO should give approximately
4–5 Ω/sq. If it does not, the tool requires diagnosis before the copper series
can be interpreted.

**Analysis.** One command:

```bash
pvdlowe calibrate -i experiments/cu_series_runsheet.csv --capped
```

This fits specularity, grain-boundary reflection, percolation threshold and a
thickness-independent excess resistivity, then diagnoses which of three
mechanisms is operating.

### 6.3 Pre-registered decision rules

Written before any data exists, so that interpretation is not selected to suit
the outcome.

| Rule | Criterion | Interpretation | Consequence |
|---|---|---|---|
| **A** | Excess < 1 µΩ·cm, ρ(100 nm)/ρ_bulk < 1.5 | Classical size effect; model form correct, parameters wrong | Adopt fitted parameters; copper recommendations stand with revised figures |
| **B** | Excess > 50% of bulk, improving fit by > 20% | Impurity scattering, most likely oxygen | **Favourable**: film quality, not physics. Follow with base-pressure study and XPS depth profile |
| **C** | Fitted d_c differs from 11 nm by > 1.5 nm | Dewetting on this underlayer | Minimum usable thickness changes, and with it every silver-consumption figure. Trial a seed layer |
| **D** | R_s at 15 nm near 16.6 Ω/sq | Literature is correct; model optics optimistic by ~8× | **Six leading candidates fall.** Programme reverts to silver reduction, with §5.1's dilute-silver optimum as the recommendation in its own right |

### 6.4 Validation of the analysis path

The fitter was tested against synthetic data generated with known parameters.
All four cases were diagnosed correctly at 0.5–2.4% relative residual, and the
percolation threshold was recovered to better than 1 nm in every case.

**A limitation identified by that testing and stated in the protocol:**
specularity and grain-boundary reflection are **not separately identifiable**
from R_s(d) alone — across an 8–20 nm window they produce nearly the same 1/d
dependence. A synthetic film generated with p = 0.35 was fitted at p = 1.00 with
a 1.5% residual: an excellent fit to the data and an incorrect value for the
parameter.

The fitted model therefore predicts sheet resistance reliably within the fitted
range, which is what the framework requires, but the individual parameters must
not be reported as measurements. Separating them requires varying grain size
independently, for instance by annealing at fixed thickness. The percolation
threshold **is** identifiable, and is the parameter of greatest consequence
since it sets minimum usable thickness.

---

## 7. Limitations

### 7.1 No experimental validation

No films were deposited. Every performance figure in this report is a model
output. The candidate rankings are hypotheses ordered by physics, suitable for
directing experimental effort, and are not results.

### 7.2 Calibrated and fitted parameters

| Parameter | Basis |
|---|---|
| Glass far-IR oscillator scale | Calibrated to bare-glass ε_n = 0.837 |
| TCO band-edge strength | Calibrated to n(550 nm) |
| Ag percolation d_c = 10 nm | Literature, XRD-confirmed |
| Cu percolation d_c = 11 nm | Literature, unconfirmed |
| Drude damping | Anchored to DC resistivity |
| Specularity, grain-boundary reflection | **Fitted, not measured** |

### 7.3 Known weaknesses

- **Si₃N₄ and TiO₂ optical constants are ESTIMATE grade** — indices from typical
  sputtered values, phonon parameters order-of-magnitude.
- **D65 and AM1.5 spectra are Planckian approximations**, flagged as MODEL.
  The cost of this has now been quantified rather than left open
  (`illuminant_sensitivity`): varying the assumed colour temperature over
  5000–7500 K moves **T_vis by 0.1%** and **T_sol by 8.3%**. The asymmetry is
  structural — the photopic response V(λ) is narrow and dominates the visible
  weighting, whereas in the solar band the spectrum *is* the weighting.

  *Consequence:* T_vis is reportable as computed. **T_sol, and the g-value and
  LSG derived from it, carry a systematic uncertainty of order 5–10%** until a
  tabulated AM1.5G spectrum is supplied. Rankings within a climate profile are
  unaffected, the bias being common to all candidates, but absolute solar-gain
  figures quoted against a building code are.
- **Visible-range metal optics are accurate to a few per cent at best.** The
  far-infrared response is reliable, being pure Drude and anchored to
  resistivity; the visible is not.
- **Roughness, interdiffusion and barrier absorption are not modelled.** A real
  stack will transmit somewhat less than predicted.
- **Reactive Si₃N₄ deposition is more demanding than AZO** — target poisoning,
  lower rate. The brief's §15 deposition-efficiency criterion would penalise it,
  and the framework cannot score this without a calibrated rate model.

### 7.4 Scores are not portable between weightings

Absolute scores moved by approximately 25 points as the §3 corrections were
applied. **A score is not a property of a material.** A figure of 89.3 is a
statement about one architecture under one weighting of eight criteria, three of
which the framework cannot populate. Rankings should be quoted with the
weighting file attached and the unverified elements identified.

---

## 8. Recommendations

### 8.1 Immediate — literature

1. **Obtain the full text of *Applied Surface Science* 578 (2022) 152051** and
   establish whether the reported emissivity is normal or hemispherical, and the
   instrument's spectral band. §16's conclusion depends on this.
2. **Withdraw the two disputed citations** (§4.1) from any document derived from
   the brief pending identification of their source.
3. **Apply the three factual corrections** in §4.4.

### 8.2 First experimental priority

**Execute the copper thickness series** (§6). Half a day of tool time. It
confirms or refutes six leading candidates and is the single highest-leverage
measurement available. The protocol is written for handover and requires no
further specification.

### 8.3 Second experimental priority

**One AZO/Ag₇₀Cu₃₀/AZO film at 10 nm, sheet resistance measured.** The two
microstructure hypotheses predict 6.4 versus 2.6 Ω/sq — far outside probe
resolution. Better still, measure across Ag 0, 25, 50, 75 at.%: the *curve shape*
is diagnostic, with the segregated model predicting a flat ~3 Ω/sq and a
metastable solid solution predicting a Nordheim maximum above 7 Ω/sq.

### 8.4 First deposition run for the target application

For a cooling-dominated application (Indian architectural glazing):
**AZO/Cu/AZO at 45/12/45 nm**, measured for T_vis, sheet resistance and FTIR
emissivity, against an AZO/Ag/AZO control.

For a heating-dominated application: **Si₃N₄/Cu/Si₃N₄ at 60/12/50 nm** against
the same control.

Either comparison tests the dielectric hypothesis, the copper film-quality
question and the silver-free premise simultaneously.

### 8.5 Framework extensions worth the effort

- **Finer optimisation of the double-copper stack** — asymmetric outer layers,
  mixed-metal pairing, finer dielectric steps. The transmittance deficit is 8
  points and the scan performed was coarse. This is the most likely route to
  closing it, now that the triple-layer route has been ruled out (§5.4).
- **A tabulated AM1.5G spectrum**, to remove the 5–10% systematic on T_sol,
  g and LSG.
- **Measured n and k** for in-house AZO, Si₃N₄ and metal films — the largest
  single source of visible-range error.

---

## 9. Handover

| Item | Location |
|---|---|
| Source, documentation, results | `github.com/VarunMandy/pvdlowe` |
| Archive | `gs://sg-llamole-pvdlowe/pvdlowe/source/` |
| Executive summary | `docs/SUMMARY.md` |
| Full findings | `docs/FINDINGS.md` |
| Physics and approximations | `docs/METHODOLOGY.md` |
| Evidence grading | `docs/PROVENANCE.md` |
| Experimental programme | `docs/ROADMAP.md` |
| Bench procedure | `experiments/BENCH_cu_series.md` |
| Pre-registered decision rules | `experiments/PROTOCOL_cu_series.md` |
| Blank run sheet | `experiments/cu_series_runsheet.csv` |
| Worked example output | `experiments/EXAMPLE_filled_runsheet.csv` |

Installation is `pip install -e .`; the test suite (86 tests, no external
dependencies beyond numpy/scipy/pandas/pyyaml) runs with
`python tests/run_tests.py` and should be run after any environment change, as
it validates the physics rather than only the interfaces.

---

## 10. Conclusion

The framework delivered implements the brief's proposed workflow and, in doing
so, identified several respects in which the brief's own assumptions do not
survive quantitative examination: a weighting scheme that omitted the
programme's primary objective, two citations that could not be traced, a
measurement inconsistent with a model-independent physical limit, and a
material class and stack architecture excluded by the search framing but
outperforming the proposed candidates.

The candidate rankings produced should be treated as hypotheses for
experimental prioritisation. Their principal weakness is known, quantified, and
addressed by a specified experiment with pre-registered decision rules — which
is offered as the more useful deliverable. A model that identifies the
measurement capable of falsifying it is more valuable to an experimental
programme than one that does not.

The recommended next action is half a day of sputter tool time.
