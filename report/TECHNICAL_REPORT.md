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
phase separation with first-principles evidence; a machine-learning
interatomic potential extended this to the disordered solid solution and showed
that in the dilute-silver range the driving force to separate falls below
thermal energy at deposition, supplying a third independent argument for that
composition range. A literature search subsequently identified the mechanism
behind the dielectric effect — underlayer templating of metal grain structure,
measured by transmission electron microscopy in the patent literature — and
established that it is the same physical effect as the framework's largest
known error, its under-prediction of sputtered copper sheet resistance. Third, the design-space search
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
path, is delivered with the framework. A subsequent literature review narrowed
the cause without deposition: no published surface- or grain-boundary-scattering
parameters account for the discrepancy, whereas a nanocrystalline grain
structure does — reducing the decisive measurement from an eight-film series to
a single X-ray diffraction scan.

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
| Computational framework implementing the brief's §21 workflow | Complete — 12,000 lines, 92 tests |
| Element and compound screening | Complete |
| Optical multilayer model (transfer matrix, EN 410 / 673 / 12898) | Complete, validated |
| Thin-film transport model coupled to optics | Complete, **uncalibrated — requires §6 experiment** |
| Multi-objective scoring with provenance grading | Complete |
| Design of experiments generator | Complete |
| DFT input generation (VASP) | Complete, **not executed — requires VASP licence and HPC allocation** |
| Materials Project integration | **Complete and executed** — 15/15 systems retrieved |
| Candidate ranking, 38 architectures | Complete, **model outputs only** |
| Experimental protocol with pre-registered analysis | Complete, **not executed — requires tool access** |
| Illuminant sensitivity quantified | Complete (§7.3) |
| Manufacturability constraints | Complete |
| Triple-metal architecture search | Complete — negative result (§5.4) |
| ML surrogate: Ag–Cu mixing energies | **Complete and executed** (§5.6) |
| ML surrogate: interface adhesion | Attempted, **failed** — lattice mismatch (§5.6) |

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

Eight literature benchmarks were transcribed from the brief. **All eight
sources have been located. One has been read in full text**; the remainder are
paywalled and confirmed only against their published abstracts.

| State | Count |
|---|---|
| **Fully verified** (full text read, measurement basis confirmed) | **1** |
| Partial (source identified, figures confirmed against abstract) | 5 |
| **Disputed** (located sources do not contain the quoted figures) | **2** |
| Not located | 0 |

Two further sources outside the brief's citation list have also been read in
full: Cueva & Carretero (*Coatings* **13**, 1709, 2023), which corrected the
dielectric model in §5.2, and the four Cu scattering-parameter studies
underpinning §6.1. Both are open access.

Run `pvdlowe provenance` for the live state; the counts above are generated
from `data/benchmarks.yaml` and will change as verification proceeds.

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
| The framework's own convention | **An industrial formula in use since 2000 gives the same answer** |

The band-emissometer hypothesis was the most plausible and was tested by
implementing band-limited emissivity in the framework. For a Drude metal,
reflectance is nearly flat across 5–14 µm and the 283 K Planck weighting already
peaks near 10 µm, so restricting the band removes the 5–8 µm region where these
stacks reflect slightly less well. Correcting for measurement basis therefore
*worsens* the discrepancy, from 0.58 to 0.53 of the limit.

The same group reports ε = 0.045 at 8.10 Ω/sq and ε = 0.050 at comparable sheet
resistance. Three measurements at a consistent 0.57–0.63 of the electrodynamic
limit indicates a systematic effect rather than an isolated error.

**Independent corroboration.** Cueva & Carretero compute emissivity from sheet
resistance as ε_n = 0.0106·R□, citing Gläser, *Large Area Glass Coating* (Von
Ardenne, 2000) — a reference in industrial use for two decades. That relation
and the impedance limit derived here agree within 10% across 2–17 Ω/sq. At
9.96 Ω/sq the industrial formula gives **0.106**, against this framework's
0.096 and the reported 0.055 — a ratio of **0.52**. The objection that the
discrepancy might be an artifact of the framework's convention is therefore
answered: two independent methods, one derived from first principles and one in
commercial use, agree.

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
- ~~The AZO visible transmittance is 81.4%, not 82.4%.~~ **Retracted — see
  §4.5.** The paper reports both figures in different sections; the brief
  quoted the Results value and was right to.
- **§7's resistivity table mixes measurement conventions**, per §4.3 above.

### 4.5 The one fully verified source, and a retraction

Mazur et al., *Materials* **17**(1), 81 (2024), DOI 10.3390/ma17010081 — the
AZO single-layer benchmark — is open access and has been read in full.

**Confirmed:** resistivity 2.6 × 10⁻³ Ω·cm; optical band gap 3.12 eV by Tauc
for allowed indirect transitions; hardness 11.4 GPa; reduced modulus 98 GPa;
sheet resistance 68 Ω/sq. The band gap had been unchecked until now.

**A correction is retracted.** §4.4 of an earlier version of this report
recorded that the brief's 82.4% visible transmittance was a transcription error
for 81.4%. **That was wrong.** The paper reports both: §3.1 gives the average
transparency over 360–760 nm as 82.4%, while the abstract and conclusions give
81.4%. The source is internally inconsistent, and the brief quoted the Results
figure — which is defensible. The error was introduced by checking only the
abstract, which is precisely the shortcut the `partial` grade exists to flag.

**Two facts established that are not in the brief.** The film thickness is
380 ± 5 nm by optical profilometry, which independently confirms the
framework's inference from ρ/R_s and means this resistivity is not transferable
to the 30–40 nm layers used inside a multilayer. And the crystallite sizes by
Scherrer are 14.0 nm (ZnO 002), 17.7 nm (Al₂O₃ 023) and 16.2 nm (Al₂ZnO₄ 220) —
roughly 0.04 × the film thickness, with the authors attributing the unusually
high hardness to that nanocrystalline structure via Hall–Petch. **Strongly
nanocrystalline growth is therefore normal for magnetron-sputtered oxide
films**, which supports the grain-size hypothesis in §6.1.

Deposition was medium-frequency pulsed magnetron sputtering, on fused silica
and Corning glass — not soda-lime float glass.

### 4.6 What verification confirmed elsewhere

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

Thirty-eight candidate architectures were evaluated; 58 metal systems screened; a
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

### 5.2 The dielectric choice matters, through metal nucleation rather than optics

**This section was revised after experimental comparison.** An earlier version
concluded that silicon nitride outperforms AZO on optical grounds. That
conclusion is contradicted by measurement, the model has been corrected, and
the correction is recorded here rather than applied silently.

**The measurement.** Cueva & Carretero (*Coatings* **13**, 1709, 2023, open
access, full text read) deposited five dielectrics under identical conditions
on a semi-industrial inline sputtering system with 10 nm Ag:

| Dielectric | Measured ε | n(550 nm) |
|---|---|---|
| SnO₂ | 0.083 | 2.00 |
| ZnO | 0.064 | 2.019 |
| **AZO** | **0.058** | 1.85 |
| SiAlNx | 0.067 | 2.09 |

AZO gives the lowest emissivity *and* the better visible transmission (86.8%
against 81.9% for SnO₂), despite having the **lowest** refractive index of the
set. The authors attribute this to silver growth being more efficient on AZO.

**The framework's error.** It modelled the dielectric purely as an interference
layer — index and thickness — and therefore preferred the higher-index nitride.
The optical inputs were sound; their measured indices match the framework's
closely. What was missing is that the underlayer determines the *quality of the
metal grown on it*.

**The correction.** A `metal_growth_factor` per dielectric now applies a
resistivity penalty, calibrated to that series and normalised to AZO = 1.00:
ZnO 1.10, SiAlNx 1.16, ITO 1.20, TiO₂ 1.25, SnO₂ 1.43. The model now reproduces
the measured ordering and the magnitudes to within 4–8%.

**What this implies more broadly.** This is the same class of omission as the
copper sheet-resistance discrepancy in §6: the framework models ideal metal
layers, while the dominant effect in practice is underlayer-dependent metal
microstructure. Two independent findings now converge on that gap, and any
successor should treat nucleation quality as a first-class parameter.

**The productive outcome: a hybrid stack.** AZO beneath for nucleation, nitride
above for durability through tempering — which is what industry does, and which
the same authors measured as giving *better* emissivity than two AZO layers,
because nitride deposited over the Ti barrier converts part of it to TiNx. Two
candidates were added on this basis:

| ID | Stack | T_vis | ε_h | R_s | Heating score |
|---|---|---|---|---|---|
| **H1** | AZO/Ag/Si₃N₄ | **0.918** | 0.057 | 4.30 | 67.4 |
| M0 | AZO/Ag/AZO (benchmark) | 0.876 | 0.060 | 4.18 | 65.0 |
| **H2** | AZO/Cu/Si₃N₄ (silver-free) | 0.788 | **0.042** | 2.93 | 79.9 |
| M6 | AZO/Cu/AZO | 0.738 | 0.046 | 2.87 | 69.6 |

H1 beats the benchmark on transmittance and emissivity simultaneously. H2 gains
five points of transmittance over the pure-AZO copper stack at lower
emissivity, and remains silver-free.

### 5.2b Superseded analysis: index matching

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

The best light-to-solar-gain ratio across all 38 candidates is **1.37**, against
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

**This adds a mechanism to the dilute-stabiliser finding in §5.9.** Both Cu–Ti
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

### 5.6 Mixing energies: the dilute corner is thermodynamically favoured

§5.5 established from the Materials Project convex hull that Ag–Cu has no
stable *ordered* compound. That is an equilibrium statement about ordered
phases, and a sputtered film is neither ordered nor at equilibrium. The
question left open was whether the *disordered solid solution* the film might
actually be is also unstable.

**Method.** MACE-MP-0, a machine-learning interatomic potential trained on
Materials Project DFT data, on 32-site fcc supercells with three random
decorations per composition, cell and positions relaxed. Not DFT — a surrogate
for it, and its error is quantified rather than assumed. Full account in
`docs/MLIP_MIXING_ENERGY.md`.

**Validation gate.** Before any prediction the surrogate was required to
reproduce two Materials Project results computed at DFT level:

| | MP (DFT) | MACE | error |
|---|---|---|---|
| Cu₃Ag | 0.0904 | 0.0719 | 0.0185 |
| CuAg₃ | 0.0857 | 0.0517 | 0.0340 |

Passed, but the margin should be read: MACE under-predicts both by 20–40%, and
both errors point the same way, so this is a systematic bias. Every figure
below is a lower bound.

**Result.** The mixing energy is positive across the whole composition range
and fits a regular-solution form to within ±6 meV/atom:

    ΔE_mix = 0.287 · x · (1 − x)   eV/atom

The spread across three random decorations is 1–4 meV/atom, an order of
magnitude below the signal, so the configurational sampling is converged. End
members return exactly zero.

**A useful internal check.** At Ag 25 at.% the surrogate puts the *disordered*
solution at 0.0591 eV/atom and the *ordered* Cu₃Ag compound at 0.0719 — the
disordered state is 13 meV/atom **lower**. There is no ordering tendency at
all, which is precisely what an empty convex hull implies, reached by an
independent route.

**The finding that bears on the design.** Comparing the driving force against
thermal energy at deposition:

| Ag at.% | ΔE_mix | × kT (300 K) | × kT (550 K) |
|---|---|---|---|
| 70 — the brief's priority | 0.0602 | 2.33 | 1.27 |
| 50 | 0.0717 | 2.77 | 1.51 |
| **15** | 0.0366 | 1.41 | **0.77** |
| **10** | 0.0258 | 1.00 | **0.54** |
| **5** | 0.0136 | 0.53 | **0.29** |

**In the dilute-silver corner the driving force to separate falls below thermal
energy at deposition.**

§5.1 found that the two microstructure hypotheses converge there — 2.5 score
points apart at Ag₅Cu₉₅ against 9–14 at Ag₇₀Cu₃₀ — and treated that as a
robustness argument for designing in that range. **The thermodynamics now
supply the mechanism:** at 5–15 at.% Ag there is barely any driving force to
segregate, so the film is far more likely to remain as deposited and it matters
much less which hypothesis is correct.

The dilute-silver optimum is therefore supported on three independent grounds:
lowest silver consumption, highest score under the corrected weighting, and the
weakest thermodynamic tendency to phase-separate.

**A second observation, bearing on §8.3.** Even at the 50:50 peak the driving
force is only about 1.5 kT at 550 K. That is modest enough that a magnetron-
sputtered film quenched from the vapour could plausibly trap a metastable solid
solution — so **both microstructure hypotheses remain physically viable**,
which retrospectively justifies the framework modelling both rather than
selecting one. It also sharpens the annealing prediction: precipitation should
be observable but may require elevated temperature or extended time rather than
appearing immediately.

**Limitations.** The 20–40% systematic under-prediction above; random
decorations rather than proper special quasi-random structures; and 0 K
energies with no entropy term. That last point works in the conclusion's
favour — configurational entropy at 550 K contributes roughly 33 meV/atom at
50:50, comparable with ΔE_mix itself, so including it would push the mixing
free energy further toward zero across the range.

**What the same tooling could not do.** An attempt at metal/dielectric adhesion
energies with the same surrogate **failed and produced no usable result**:
lattice mismatches of 5–21% meant the calculation measured elastic strain
rather than binding, returning 9.6 J/m² for Ag/Si₃N₄ and −0.16 J/m² for
Ag/TiO₂, neither of which is physical. The module now refuses interfaces above
4% mismatch. Mixing energies sit in the regime these models handle best — bulk
metals, no surfaces; interfaces do not, and the empirical
`metal_growth_factor` of §5.2 therefore remains without a computed mechanism.

### 5.7 The nucleation mechanism, and a structural weakness it exposes

§5.2 established that the choice of dielectric changes the metal's growth, and
encoded it as an empirical `metal_growth_factor` calibrated to measurement.
The mechanism was left open. Two machine-learning surrogate calculations were
run to find it, and both failed:

| Attempt | Failure mode |
|---|---|
| Bulk interface adhesion | 5–21% lattice mismatch — the calculation measured elastic strain, not binding |
| Adatom wetting energy | ZnO(0001) termination changed the result by 2.1 eV, against 0.46 eV separating all six materials |

A literature search then resolved it in under an hour, with direct
experimental evidence.

**The measurement.** Guardian Industries (US 7,632,572 B2) compared silver
deposited on **crystalline ZnO** with silver on **amorphous TiOx** by
transmission electron microscopy. Silver on the amorphous layer shows an
abnormal microstructure with irregular grains averaging about 15 nm; on ZnO it
shows regular grains averaging about 25 nm. In dark field on the Ag{220}
reflections, {111}-oriented grains are two to three times larger on ZnO. On
the amorphous underlayer the film is **clearly discontinuous**.

That is templating, measured directly: a crystalline oxide templates Ag(111)
growth, an amorphous underlayer does not, and the film islands instead of
coalescing.

**The nitride case is settled by industrial practice.** Silicon nitride Low-E
stacks use thin NiCr barrier layers specifically to increase adhesion between
the nitride and the silver. A metallic nucleation layer is required precisely
because silver adheres poorly to nitride directly — the opposite of what the
surrogate predicted from a crystalline β-Si₃N₄ proxy, and an explanation of
why that proxy misled.

**A structural weakness in the framework follows.** The default
`grain_size_ratio` of 3.0 corresponds to 30 nm grains in a 10 nm film, within
20% of the 25 nm the patent measured on ZnO — the assumption was correct, but
only for the oxide underlayer it happened to be tuned against:

| Underlayer | Grain size | Ratio | ρ(10 nm Ag) |
|---|---|---|---|
| Crystalline ZnO / AZO | 25 nm | 2.5 | 4.69 µΩ·cm |
| **Framework default** | 30 nm | **3.0** | **4.44** |
| Amorphous TiOx | 15 nm | 1.5 | 5.70 |
| Amorphous nitride (inferred) | ~12 nm | 1.2 | 6.33 |

**And this is the same physics as the copper discrepancy of §6.**
`docs/LITERATURE_CALIBRATION.md` concluded that no published scattering
parameters explain the eightfold under-prediction of sputtered copper sheet
resistance, and that a nanocrystalline grain structure does. The patent shows
that the underlayer *determines* metal grain size.

So `metal_growth_factor` and the copper grain-size hypothesis are not two
separate limitations. **They are one effect appearing in two places** — the
framework models the metal layer as though the layer beneath it did not shape
its microstructure. That is the single most consequential structural weakness
identified in this work, and a successor should replace the empirical
multiplier with a per-underlayer grain size, which is physically meaningful,
directly measurable, and feeds both the optical and electrical paths through
the existing Mayadas–Shatzkes term.

**Consequence for the experimental programme.** One X-ray diffraction scan now
answers both open questions on the same film:

| Measurement | Answers |
|---|---|
| Ag(111) or Cu(111) peak intensity and texture | whether the underlayer templates the metal |
| Scherrer peak width → grain size | `grain_size_ratio` for that underlayer, and the copper discrepancy |

§8.2 already calls for this scan. It should now record the metal reflections,
not only the film thickness.

**Consequence for the design.** If templating is the operative mechanism it
favours crystalline oxide underlayers and disfavours amorphous nitrides. That
is consistent with the measurement in §5.2, with industrial practice, and with
the hybrid stack introduced there — AZO beneath for nucleation, nitride above
for durability. That arrangement is not a compromise between two materials but
the physically correct order.

### 5.8 Ranked candidates

All 38 architectures were scored under both climate profiles. **The two
top-ten lists share exactly one candidate.** This is the practical form of
§5.3: the climate is not a refinement to the ranking, it selects a different
design space.

The single exception is instructive. **H2, the AZO/Cu/Si₃N₄ hybrid, appears in
both** — 9th on the heating profile and 2nd on cooling. It is the only
architecture in the set that combines a conductive-oxide underlayer (for
solar-NIR rejection, which the cooling profile rewards) with a nitride
overlayer (for transmittance and durability, which the heating profile
rewards). Before the §5.2 nucleation correction, no candidate did both, and
the lists were fully disjoint. That a hybrid is the only design robust to the
climate question is a result in its own right.

Columns: geometry as bottom/metal/top in nm; g is the EN 410 solar heat gain
coefficient; LSG = T_vis/g; "spec" is T_vis ≥ 0.80, R_s ≤ 5 Ω/sq, ε_h ≤ 0.10.

#### Heating-dominated (Northern Europe) — `data/targets.yaml`

| # | ID | Architecture | Geometry | T_vis | ε_h | R_s | g | LSG | Ag g/m² | $/m² | Score | Spec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | E5e | Si3N4/Ag5Cu95/Si3N4 (segregated) | 59/11/48 | 0.863 | 0.0481 | 2.98 | 0.731 | 1.18 | 0.008 | 0.07 | **88.1** | yes |
| 2 | E10e | Si3N4/Ag10Cu90/Si3N4 (segregated) | 59/10/48 | 0.877 | 0.0511 | 3.13 | 0.758 | 1.16 | 0.015 | 0.12 | **88.1** | yes |
| 3 | N6 | Si3N4/Cu/Si3N4 | 60/11/50 | 0.858 | 0.0538 | 3.41 | 0.729 | 1.18 | 0.000 | 0.01 | **87.5** | yes |
| 4 | E5 | Si3N4/Ag5Cu95/Si3N4 | 59/11/48 | 0.861 | 0.0609 | 3.99 | 0.728 | 1.18 | 0.008 | 0.07 | **85.1** | yes |
| 5 | N7 | Si3N4/Cu90Zn10/Si3N4 | 60/11/50 | 0.850 | 0.0695 | 4.66 | 0.725 | 1.17 | 0.000 | 0.01 | **83.0** | yes |
| 6 | E10 | Si3N4/Ag10Cu90/Si3N4 | 59/11/48 | 0.864 | 0.0670 | 4.50 | 0.729 | 1.19 | 0.016 | 0.14 | **83.0** | yes |
| 7 | N8 | Si3N4/Cu90Ag10/Si3N4 | 60/11/50 | 0.863 | 0.0671 | 4.50 | 0.730 | 1.18 | 0.016 | 0.14 | **82.9** | yes |
| 8 | N35e | Si3N4/Ag60Cu40/Si3N4 (segregated) | 45/9/40 | 0.902 | 0.0498 | 3.04 | 0.793 | 1.14 | 0.065 | 0.53 | **80.7** | yes |
| 9 | H2 | AZO/Cu/Si3N4 (hybrid, silver-free) | 40/12/40 | 0.788 | 0.0425 | 2.93 | 0.631 | 1.25 | 0.000 | 0.01 | **79.9** | **no** |
| 10 | N3e | Si3N4/Ag70Cu30/Si3N4 (segregated) | 25/9/35 | 0.899 | 0.0508 | 3.16 | 0.769 | 1.17 | 0.073 | 0.59 | **78.1** | yes |
| — | M0 | AZO/Ag/AZO (**benchmark**) | 35/10/35 | 0.876 | 0.0603 | 4.18 | 0.646 | 1.35 | 0.105 | 0.85 | 65.0 | yes |

**Nine of ten use silicon nitride**; the exception is the AZO/Cu/Si₃N₄ hybrid
(H2) introduced by the §5.2 correction. 9 of ten meet the
full specification, and 8 of ten use less
than 0.05 g/m² of silver against the benchmark's 0.105. The leading candidate
uses **one thirteenth of the benchmark's silver** while beating it on
emissivity and sheet resistance.

Note these figures moved when the nucleation correction of §5.2 was applied:
emissivities rose by roughly 5–12% for the nitride stacks, since Si₃N₄ carries
a growth-factor penalty of 1.16 against AZO's 1.00. The ordering within the
nitride family was not disturbed, but the margin over AZO narrowed.

#### Cooling-dominated (India) — `data/targets_cooling.yaml`

| # | ID | Architecture | Geometry | T_vis | ε_h | R_s | g | LSG | Ag g/m² | $/m² | Score | Spec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M6 | AZO/Cu/AZO (low-cost control) | 35/12/35 | 0.738 | 0.0463 | 2.87 | 0.558 | 1.32 | 0.000 | 0.01 | **65.4** | **no** |
| 2 | H2 | AZO/Cu/Si3N4 (hybrid, silver-free) | 40/12/40 | 0.788 | 0.0425 | 2.93 | 0.631 | 1.25 | 0.000 | 0.01 | **63.4** | **no** |
| 3 | D10e | AZO/Ag10Cu90/AZO (segregated) | 15/9/37 | 0.789 | 0.0585 | 3.52 | 0.641 | 1.23 | 0.013 | 0.11 | **59.3** | **no** |
| 4 | D15e | AZO/Ag15Cu85/AZO (segregated) | 15/9/37 | 0.794 | 0.0564 | 3.31 | 0.643 | 1.23 | 0.019 | 0.16 | **59.3** | **no** |
| 5 | M5 | AZO/Ag25Cu75/AZO | 35/10/35 | 0.784 | 0.0780 | 5.92 | 0.612 | 1.28 | 0.034 | 0.28 | **58.2** | **no** |
| 6 | M3ema | AZO/Ag70Cu30/AZO (segregated) | 35/10/35 | 0.840 | 0.0462 | 2.63 | 0.635 | 1.32 | 0.081 | 0.66 | **57.9** | yes |
| 7 | M35e | AZO/Ag60Cu40/AZO (segregated) | 15/9/35 | 0.843 | 0.0514 | 2.95 | 0.659 | 1.28 | 0.065 | 0.53 | **57.4** | yes |
| 8 | S10 | ITO/Ag70Cu30/ITO | 35/10/35 | 0.848 | 0.0764 | 5.48 | 0.619 | 1.37 | 0.081 | 0.66 | **57.3** | **no** |
| 9 | D10 | AZO/Ag10Cu90/AZO | 15/9/37 | 0.786 | 0.0784 | 5.66 | 0.638 | 1.23 | 0.013 | 0.11 | **57.1** | **no** |
| 10 | D15 | AZO/Ag15Cu85/AZO | 15/9/37 | 0.790 | 0.0828 | 6.15 | 0.639 | 1.24 | 0.019 | 0.16 | **56.3** | **no** |
| — | M0 | AZO/Ag/AZO (**benchmark**) | 35/10/35 | 0.876 | 0.0603 | 4.18 | 0.646 | 1.35 | 0.105 | 0.85 | 53.0 | yes |

**Every entry uses a conductive oxide as the underlayer** (AZO or ITO), for the
reason in §5.3 — the free carriers reject solar near-infrared, which a passive
nitride cannot. Only **2 of ten meet the full
specification**, and those use substantial silver. The rest fail on visible
transmittance.

The AZO/Cu/Si₃N₄ hybrid (H2) now ranks **second** on this profile, which was
not the case before the §5.2 correction: it keeps AZO's solar-NIR rejection
underneath while gaining five points of transmittance from the nitride
overlayer, and remains silver-free.

**This is the honest state of the cooling-climate answer: the framework is
ranking near-misses.** No single-metal architecture in the set clears
T_vis ≥ 0.80 at acceptable solar gain, which is the finding that motivated the
multi-layer work in §5.4. The double-copper Si₃N₄ stack scores 68.9 on this
profile — higher than anything in the table above — but at T_vis 0.716 it too
falls short.

#### How to read these tables

1. **They share one candidate out of ten.** A recommendation is only meaningful
   with its climate profile named. Circulating one table without the other
   would be misleading — except for H2, which is defensible under either.
2. **The benchmark appears in neither top ten**, which is the correct answer to
   the brief's question: pure silver is the incumbent to beat, and on a
   sustainability-weighted objective it is beaten.
3. **Four of ten in each list are "segregated" variants** — the same
   composition under the alternative microstructure hypothesis. Until the
   Phase 2 measurement (§8.3) is made, those four entries are conditional. §5.5
   provides thermodynamic support for segregation but not proof of the
   as-deposited state.
4. **All copper-bearing entries are contingent on §6.** The framework
   under-predicts sputtered copper sheet resistance by roughly eightfold; if
   that gap is real film quality rather than model error, most of both tables is
   affected.
5. **Scores are not comparable between the two tables**, being computed under
   different weightings. Compare within a column only.

### 5.9 The dilute-titanium ternary is predicted to underperform

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

**A literature review has since narrowed the cause without any deposition.**
Fuchs–Sondheimer specularity and Mayadas–Shatzkes grain-boundary reflection are
well characterised for copper because interconnect scaling depends on them. Four
independent published fits give p between 0.48 and 0.80 and R between 0.16 and
0.43; the framework's assumed p = 0.50, R = 0.25 sits inside that range.

| p | R | Source | Predicted R_s, AZO/Cu(15)/AZO |
|---|---|---|---|
| 0.52 | 0.43 | Chawla & Gall, *Phys. Rev. B* **81**, 155454 (2010) | 2.69 |
| 0.48 | 0.27 | twin-boundary study, nanocrystalline Cu | 2.23 |
| 0.80 | 0.38 | *Thin Solid Films* (2006) | 2.17 |
| ≈0 | 0.17 | *AIP Advances* **9**, 025015 (2019) | 2.71 |
| 0.50 | 0.25 | framework default | 2.16 |

All cluster near 2.2–2.7 Ω/sq against the 16.6 to be explained. An exhaustive
scan over the entire admissible range — p ∈ [0, 1], R ∈ [0, 0.6] — reaches only
**4.42 Ω/sq**, short by a factor of 3.8.

**No scattering parameters anywhere in the literature range explain the
discrepancy.** Decision rule A below is eliminated on that basis.

**What does explain it is grain size.** Both models take grain size as an input,
and the framework assumes lateral grains three times the film thickness,
appropriate to a coalesced film. Grains at roughly *half* the thickness give
14.1 Ω/sq:

| Grain size | R_s(15 nm) |
|---|---|
| 3.0 × thickness (assumed) | 4.42 |
| 1.0 × thickness | 8.31 |
| **0.5 × thickness** | **14.13** |
| 0.25 × thickness | 25.77 |

That is a nanocrystalline structure — grains of order 5–8 nm in a 15 nm film —
which is plausible for copper sputtered at room temperature onto an oxide it
wets poorly. It is now the leading hypothesis, displacing oxygen contamination.

**Caveat on transferability.** The published values are for copper on Ta or SiO₂
at 25–158 nm, deposited for interconnects. This work concerns copper on AZO at
10–15 nm, where nucleation differs and the thickness lies below anything in the
cited studies. The transferable conclusion is therefore the *negative* one — that
p and R cannot account for the gap — rather than a positive calibration. Grain
size for copper on AZO at these thicknesses was not found in the literature
searched, and is the missing number. Full analysis in
`docs/LITERATURE_CALIBRATION.md`.

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

**A cheaper measurement now comes first.** Because the leading hypothesis is
grain structure, a **single XRD scan on one 12–15 nm copper film on AZO** gives
the grain size directly by Scherrer broadening of the Cu(111) reflection, and
discriminates between the remaining hypotheses:

- Grain size ≲ 0.6 × film thickness → nanocrystalline structure confirmed; the
  model's grain assumption is wrong and the remedy is thermal or morphological
  (seed layer, elevated substrate temperature, brief anneal).
- Grain size ≳ film thickness → grain structure is not the cause, and attention
  returns to impurity scattering.

One sample rather than eight, and XRD is more widely available than a dedicated
sputter session. **If only one measurement can be obtained, this is now the one
to take.** The thickness series remains the better experiment where both are
possible, since it also calibrates the model.

**Analysis.** One command:

```bash
pvdlowe calibrate -i experiments/cu_series_runsheet.csv --capped
```

This fits specularity, grain-boundary reflection, percolation threshold and a
thickness-independent excess resistivity, then diagnoses which of three
mechanisms is operating.

### 6.3 Pre-registered decision rules

Written before any data exists, so that interpretation is not selected to suit
the outcome. Rule A was subsequently eliminated and rule E added by the
literature review in §6.1, which was also completed before any deposition; both
changes are recorded rather than applied silently.

**Distinguishing E from B requires measuring grain size**, not inferring it: a
small-grain film and a contaminated film produce similar R_s(d) curves, so a
thickness series alone cannot separate them.

| Rule | Criterion | Interpretation | Consequence |
|---|---|---|---|
| **A** | Excess < 1 µΩ·cm, ρ(100 nm)/ρ_bulk < 1.5 | Classical size effect; model form correct, parameters wrong | **Eliminated by literature review** (§6.1). Retained here unaltered so the amendment is auditable |
| **E** | XRD grain size ≲ 0.6 × film thickness | **Nanocrystalline grain structure — now the leading hypothesis** | Set `grain_size_ratio` from the measured value and re-run the ranking. Remedy is thermal or morphological, not vacuum hygiene |
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

### 7.3 The principal structural weakness

**The framework models each metal layer as though the layer beneath it did not
shape its microstructure.** §5.7 establishes that this single omission accounts
for both the empirical `metal_growth_factor` and the eightfold under-prediction
of sputtered copper sheet resistance in §6. Grain size in a sputtered metal
film is set substantially by the underlayer — 25 nm on crystalline ZnO against
15 nm on an amorphous oxide, measured by TEM — and grain size feeds directly
into the Mayadas–Shatzkes term that the framework already contains.

A successor should carry a measured `grain_size_ratio` per underlayer rather
than an opaque multiplier on resistivity. The XRD scan of §8.2 supplies it.

### 7.4 Other known weaknesses

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

### 7.5 Scores are not portable between weightings

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

**One XRD scan on a single 12–15 nm copper film on AZO, recording the metal
reflections as well as the film thickness.** An afternoon, one sample, and it
now answers two questions rather than one: Scherrer width gives the grain size
that §5.7 identifies as the common cause of both the copper discrepancy and the
dielectric effect, while the Cu(111) intensity and texture test whether the
underlayer templates the metal. Following the literature review in §6.1, grain structure is the leading
explanation for the model's largest error, and Scherrer broadening measures it
directly. This is now the highest information-per-hour measurement available.

**Then the copper thickness series** (§6.2). Half a day of tool time. It
confirms or refutes six leading candidates and calibrates the transport model.
The protocol is written for handover and requires no further specification.

If both can be obtained, run both — the XRD identifies the mechanism, the series
calibrates the model. If only one, take the XRD.

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
- **Coherent-interface adhesion energies**, if the mechanism behind
  `metal_growth_factor` is wanted. This requires lattice-matched supercells of
  200–500 atoms (`pymatgen.analysis.interfaces.ZSLGenerator`) and several
  surface terminations per dielectric — roughly two days of work and compute,
  with an outcome still limited by the surrogate's accuracy on systems far from
  its training distribution. Not recommended ahead of the measurements in §8.2
  and §8.3.

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

Installation is `pip install -e .`; the test suite (92 tests, no external
dependencies beyond numpy/scipy/pandas/pyyaml) runs with
`python tests/run_tests.py` (92 tests) and should be run after any environment change, as
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
