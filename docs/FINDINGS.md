# Findings

Organised by conclusion, not by the order things were discovered.

**Framework:** `pvdlowe` v0.1.0 · 9,586 lines · 136 tests · 38 candidate
architectures. Everything here is reproducible from the repository.

---

## The one caveat that governs everything below

**No films were deposited.** Every performance figure is a model output. The
framework's own validation puts its median error at **30.6%** against traceable
literature, and its largest known error — an approximately eightfold
under-prediction of sputtered copper sheet resistance — sits in the material
most leading candidates use.

Candidate rankings are therefore **hypotheses for prioritising experiments**,
not results. The findings in Parts 2 and 3 do not depend on any measurement and
stand on their own.

---

# PART 1 — WHAT THE DESIGN SPACE SAYS

## 1.1 The answer depends on a question the brief did not ask

The brief specifies no climate, and the weighting derived from it does not
constrain solar heat gain. That silently encodes a heating-dominated
assumption — in a project run at Saint-Gobain Research **India**.

Adding the EN 410 / ISO 9050 solar-gain metrics and re-scoring produces two
rankings that **share one candidate out of ten**.

| | Heating-dominated | Cooling-dominated (India) |
|---|---|---|
| Lead candidate | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ (E10e) | AZO/Cu/AZO (M6) |
| T_vis | 0.877 | 0.738 |
| Emissivity ε_h | 0.051 | 0.046 |
| Sheet resistance | 3.13 Ω/sq | 2.87 Ω/sq |
| Solar heat gain g | 0.758 | 0.558 |
| Silver | 0.015 g/m² (**−86%**) | **zero** |
| Meets spec | **yes** | no — T_vis 0.738 < 0.80 |

Benchmark for comparison — AZO/Ag/AZO at 10 nm: T_vis 0.876, ε_h 0.060,
R_s 4.18 Ω/sq, g 0.646, LSG 1.35, 0.105 g/m² Ag.

**The mechanism is physical, not a scoring artifact.** AZO is a *transparent
conductive oxide*: free carriers put a screened plasma edge at 1.25 µm, inside
the solar band, so it rejects solar near-infrared. Si₃N₄ is a passive insulator,
transparent throughout.

| λ (nm) | 1200 | 1600 | 2000 | 2400 |
|---|---|---|---|---|
| AZO stack | 0.240 | 0.115 | 0.068 | 0.046 |
| Si₃N₄ stack | 0.509 | 0.259 | 0.151 | 0.099 |

Same 11 nm copper layer in both.

**Conclusion.** A results table is meaningless without its weighting file. The
climate must be specified before any recommendation is made. For a heating
climate the nitride stack at 5–10 at.% Ag beats the benchmark on transmittance,
emissivity and sheet resistance simultaneously at a seventh of the silver. For
India, no single-metal architecture in the set meets the specification.

## 1.2 The composition optimum is 5–15 at.% Ag, not 70%

The brief nominates Ag₇₀Cu₃₀. Eight composition curves were run — Ag 0–100% in
5% steps, geometry re-optimised at every point, across two microstructure
models, two dielectrics and two climates.

**Every one of the eight peaks between 0 and 10 at.% Ag.**

| Profile | Microstructure | Dielectric | Optimum | Plateau |
|---|---|---|---|---|
| Heating | Segregated | Si₃N₄ | 0.05 | 0.00–0.20 |
| Heating | Segregated | AZO | 0.10 | **0.05–0.40** |
| Cooling | Either | Either | 0.00 | 0.00–0.15 |

**This is a sustainability result, not a performance one.** Emissivity and sheet
resistance keep improving up to 50 at.% Ag — 0.0386 and 2.59 Ω/sq, the best in
the series. The score falls anyway because silver mass carries weight. The trade
is about 0.005 in emissivity for an 87% cut in silver, and it is only the right
trade because silver was decided to matter.

**Plateau width matters more than peak position for a production process.** The
segregated/AZO curve is flat from 5 to 40 at.% Ag.

**The brief's own basis for 70/30 does not transfer.** It traces to a 2022 paper
that does support 70% Ag at 10 nm — but on **polycarbonate**, for first-surface
coatings. §3.2 establishes that the underlayer determines metal grain structure,
so an optimum found on plastic does not carry to a glass line unchecked.

## 1.3 Two metal layers break a ceiling one cannot

The best light-to-solar-gain ratio across all 38 single-metal candidates is
**1.37**, against roughly 2.0 for commercial solar-control glazing. Under the
cooling profile no single-metal stack met the transmittance target at all.

| Architecture | Metal | Dielectric | Geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| Single | Cu | AZO | 35/12/35 | 0.738 | 0.558 | 1.32 | 0.046 | 2.87 |
| **Double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.025 | 1.67 |
| Double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.024 | **1.33** |

**LSG 1.76 against a ceiling of 1.37 — 28% better.**

**Why one layer cannot.** A single film trades transmittance against infrared
reflectance along one curve; thickness moves along it but never off it. The
dielectric *between* two metals adds an interference degree of freedom, so the
two reflections can cancel in the visible while adding in the infrared.

Note the optimum geometry: **thin outer dielectrics, thick middle**. A symmetric
guess misses it.

**A third layer is not worth adding.** LSG goes 1.33 → 1.76 → 1.81 for
n = 1, 2, 3. The third buys 0.05 for a 25% silver increase, and for copper it is
actively harmful — transmittance collapses to 0.437.

**Conclusion.** The architecture argument stops at two layers. Silver
consumption doubles, since each layer must independently clear percolation near
10 nm, so double-silver scores badly on sustainability despite being the best
solar-control design found.

## 1.4 On the brief's own terms, almost no silver can be removed

Asked literally — thin the silver in AZO/Ag/AZO, hold everything else — the
answer is **about half a nanometre**.

| Ag nm | T_vis | ε_h | R_s | Status |
|---|---|---|---|---|
| 10.5 | 0.872 | 0.057 | 3.88 | OK |
| **10.0** | 0.876 | 0.060 | **4.18** | **OK — the limit** |
| 9.5 | 0.876 | 0.080 | 5.90 | **discontinuous** |

**Percolation is the binding constraint, not any of the three specified
properties.** A 5% thickness reduction costs 41% in sheet resistance.
Re-optimising both oxides at every thickness does not move it — the wall is in
the metal.

The 82–86% reduction reported above comes from changing the **composition**, not
the thickness. That distinction should be stated plainly wherever the figure
appears.

## 1.5 No candidate meets the Indian code's solar-gain requirement

Two criteria the brief left unspecified, anchored to ECBC 2017 rather than
invented:

| Criterion | Anchor | Value |
|---|---|---|
| `g_value` | ECBC prescriptive SHGC, composite climate | ≤ 0.27 |
| `U_g` | ECBC assembly U-factor | ≤ 3.0 W/m²K |

**Basis warning, and it matters.** ECBC specifies *assembly* values — frame and
glass, area-weighted. The framework computes centre-of-glass, and its g-value is
single-pane with the standard N = 0.36 inward fraction. The conversion must be
stated rather than assumed.

Chaining a clear second pane (T_sol 0.83) gives an approximate DGU SHGC:

| | g single | g DGU | vs 0.27 |
|---|---|---|---|
| M6, the best | 0.558 | **0.463** | fails by +0.19 |
| N35e, the worst | 0.793 | 0.658 | fails by +0.39 |

**Not one of the 38 meets it, and the best misses by seventy per cent.** That is
external regulatory confirmation of §1.3: these are thermal Low-E coatings, not
solar-control coatings. For Indian commercial glazing the single-metal
architecture is not merely suboptimal — it is non-compliant, and the
double-metal stack becomes a requirement rather than a refinement.

**U-value is not binding.** Every candidate lands at 1.12–1.29 W/m²K
centre-pane; even after a frame adds 0.5–1.5 there is room.

**And the two targets are mutually incompatible.** Searching 990 double-metal
designs, ECBC's 0.27 is reachable — at T_vis 0.644. The brief asks for 0.80.
Since ECBC's own visible-light minimum is 0.27, the conflict is not with the
regulation but with the brief's self-imposed transmittance target, which was
written for a heating climate.

---

# PART 2 — WHAT THE AUDIT FOUND

## 2.1 Six defects in the proposed weighting

Encoding the brief's §14 table literally produced a scoring function that did
not measure the project's stated objective. Four defects were in the table;
**two more were found by re-auditing the corrections for the first two.**

**(a) Silver consumption carried zero weight.** §14's table has no line for it,
although §17 and §20 both name minimising silver as an objective.

> The thickness optimiser exploited this immediately, returning a design using
> **29% more silver than the benchmark, at a perfect 100/100.**

**(b) Emissivity and sheet resistance double-count.** They correlate at
**r = 0.978** across the candidate set — the same free-carrier response of the
same layer — so weights of 0.25 and 0.15 put 0.40 of the total on one property.

**(c) Targets set at the specification minimum.** Derringer–Suich desirability
saturates at 1.0 once a target is reached. Setting T_vis's target to 0.80 — the
brief's *floor of acceptability* — made the criterion flat exactly where
candidates differ. Across 181 oxide pairs clearing 0.80, transmittance spanned
0.800–0.881 while the **score went down**.

**(d) The supply-risk band could not discriminate.** At floor 8.0 against
candidate values of 4.5–7.5, every silver-bearing composition scored 0.1–0.28.

**(e) A triple-count the fix for (b) left untouched.** Silver mass, metal cost
and supply risk correlate at **r = 1.000** and **0.991** — silver dominates
metal cost so completely that cost is the same quantity in different units, and
supply risk in this candidate set *is* silver's. Together they carried **36% of
the effective weight** on one property.

**(f) Weight reserved for criteria never populated.** Structural stability,
thermal stability and deposition efficiency carried **0.30 of a 0.90 nominal
total while being `None` for every candidate**. The scheme renormalises, so that
third was silently redistributed: a file stating emissivity at 0.25 was applying
0.42. `structural_stability` additionally had **no criterion definition at all**
and could never have scored.

**A seventh issue: aggregation.** The brief asks that its weighting prevent a
candidate "winning simply because it has excellent conductivity while being
unacceptable optically". A weighted arithmetic sum cannot do that — a zero
forfeits only that criterion's weight. A geometric mean sends the whole score to
zero.

**All corrected in `data/targets.yaml`; none applied silently.** Three criteria
now carry the heating ranking: T_vis 0.20, emissivity 0.25, silver mass 0.15.

**General rules extracted:** a desirability target should be an aspiration, not
a specification minimum; and a weight that changes the winner should be reported
as a sweep, not a value.

## 2.2 The ranking depends on a number nobody derived

Silver mass carries a weight of 0.15. That value is a judgement, and it selects
the answer:

| Silver weight | Winner | Ag g/m² | Runner-up | Margin |
|---|---|---|---|---|
| 0.00 | N35e | 0.065 | N3e | 0.52 |
| 0.05 | N35e | 0.065 | E10e | **0.09** |
| 0.10 | E10e | 0.015 | E5e | 0.57 |
| **0.15** | **E10e** | **0.015** | E5e | 0.22 |
| 0.20 | E5e | 0.008 | E10e | **0.09** |
| 0.30 | N6 | **zero** | E5e | 0.17 |

**The winner changes three times**, and **five of eight settings separate first
from second by under half a point** — at those weights the ranking is not
distinguishing candidates, it is resolving noise in a judgement.

**The honest output is the sweep.** The recommendation is E10e at 0.15, E5e at
0.20–0.25, and the silver-free N6 at 0.30 and above. Choosing among them is a
decision about how much silver consumption matters to Saint-Gobain, and it is
not the framework's to make.

## 2.3 Eight of fourteen citations changed on checking

Every citation in the brief carried `utm_source=chatgpt.com`, meaning the
sources were surfaced by a language model rather than read from a publisher.

| Status | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — source located, figures confirmed against abstract | 4 |
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

**Three factual corrections to the brief's characterisations.** Deposition
methods differ across the benchmark set — RF for the AZO/Ag/AZO trilayers where
§3 implies DC, medium-frequency for the AZO single layer — so these sources
cannot be pooled.

## 2.4 A measurement that contradicts a model-independent limit

*Applied Surface Science* **578** (2022) reports AZO/Cu/AZO with T_vis 87.7%,
R_s 9.96 Ω/sq and ε 0.055. **The brief's §16 conclusion — that a silver-free
stack may already meet a Low-E target — rests entirely on it.**

For a conducting sheet much thinner than the wavelength, far-infrared
reflectance is fixed by sheet resistance alone:

```
r = (n₁ − n₂ − Z₀/R_s) / (n₁ + n₂ + Z₀/R_s),   ε = 1 − r²
```

with Z₀ = 376.73 Ω. **No fitted parameter enters.** At 9.96 Ω/sq the floor is
**ε ≥ 0.096**; 0.055 would require about 5.48 Ω/sq.

**Six explanations tested and eliminated:**

| Explanation | Outcome |
|---|---|
| Different samples | Abstract attributes all three to one sample |
| Transcription error | Confirmed against the abstract |
| Far-IR glass index | Limit is 0.091–0.097 for n = 1.5–4.0 |
| Band-limited emissometer | Reads 5–8% **higher** — wrong direction |
| The framework's own convention | An industrial formula in use since 2000 agrees |
| **Measurement basis** | **Hemispherical reading fails by 51% rather than 42%** |

That last one was the final benign explanation. The impedance floor is a
normal-incidence quantity, so the open question was whether 0.055 might be
hemispherical and not comparable. Reading it that way gives a normal equivalent
of 0.0472 — **worse, not better**.

**§16's conclusion should not be used until this is settled.**

## 2.5 The two copper measurements sit in opposite positions

Both copper benchmarks, checked against the same physical bound:

| | Group, technique | R_s | ε | Floor | |
|---|---|---|---|---|---|
| Miao 2014, HK PolyU | **RF** | 16.60 | 0.330 | 0.150 | consistent |
| ApSS 2022, Xi'an | **DC** | 9.96 | 0.055 | 0.096 | **below floor** |

**The measurement that obeys the electrodynamic limit is the one that
contradicts this framework**, by a factor of 7.7 — the model gives 2.16 Ω/sq for
15 nm Cu against 16.6 measured. The measurement that agrees with the model's
optimism is the impossible one.

That contrast is stronger evidence than either entry alone, and it points the
same way as §3.3: the fault is in the model, not the literature.

**They must not be pooled** — different groups, RF against DC, and the 2014
study is from a textiles laboratory that coats polyester fabric with the same
stacks.

---

# PART 3 — WHERE THE MODEL WAS WRONG

## 3.1 The dielectric finding was reversed by measurement

The framework originally concluded that Si₃N₄ outperforms AZO on transmittance
by up to nine points, on index-matching grounds. Cueva & Carretero
(*Coatings* **13**, 1709, 2023, open access, **full text read**) deposited five
dielectrics under identical conditions with 10 nm Ag:

| Dielectric | Measured ε | n(550 nm) |
|---|---|---|
| SnO₂ | 0.083 | 2.00 |
| ZnO | 0.064 | 2.019 |
| **AZO** | **0.058** | **1.85** |
| SiAlNx | 0.067 | 2.09 |

**AZO wins on emissivity *and* transmittance despite the lowest refractive index
of the five.** The authors give the reason: silver grows more efficiently on AZO.

**What the model was missing.** It treated the dielectric purely as an
interference layer. The optical inputs were sound — their measured indices match
the framework's closely. What was absent is that the underlayer determines the
**quality of the metal grown on it**.

**The correction.** `TCOPreset.metal_growth_factor` applies a resistivity
penalty per underlayer, calibrated to that series and normalised to AZO = 1.00:
ZnO 1.10, SiAlNx 1.16, ITO 1.20, TiO₂ 1.25, SnO₂ 1.43. The model reproduces the
measured ordering and magnitudes to 4–8%.

**The productive outcome is a hybrid**, which is what industry already does: AZO
beneath for nucleation, nitride above for durability through tempering.

| ID | Stack | T_vis | ε_h | Heating |
|---|---|---|---|---|
| **H1** | AZO/Ag/Si₃N₄ | **0.918** | 0.057 | 69.6 |
| M0 | AZO/Ag/AZO (benchmark) | 0.876 | 0.060 | 66.6 |
| **H2** | AZO/Cu/Si₃N₄ (silver-free) | 0.788 | **0.042** | 77.6 |

**H2 is the only architecture appearing in both climate top-tens.**

## 3.2 The mechanism, and the framework's principal structural weakness

Two ML surrogate calculations were run to find the mechanism behind
`metal_growth_factor`. **Both failed**, and are documented with the diagnostic
that caught them:

| Attempt | Failed on | Diagnostic |
|---|---|---|
| Bulk interface adhesion | 5–21% lattice mismatch — measured elastic strain | unphysical 9.6 and −0.16 J/m² |
| Adatom wetting | ZnO(0001) termination changed the answer by 2.1 eV against 0.46 eV between materials | explicit termination sweep |

**A literature search then resolved it in under an hour.** US 7,632,572 B2 /
US 8,512,883 B2 (AFG Industries → AGC → Cardinal CG; **full text read**)
deposited 16 nm Ag on amorphous TiOx and on a 5 nm ZnO seed over the same TiOx:

- **25 nm grains on ZnO against 15 nm on a-TiOx**
- {111}-oriented grains **two to three times larger** on ZnO
- the film on bare amorphous titania **clearly discontinuous** where the
  ZnO-seeded film was continuous across the whole specimen

And the inventors name the mechanism: zinc oxide grows {0001}, which orients the
silver to grow {111}, and the **epitaxial lattice match between Ag{111} and
ZnO{0001}** lowers sheet resistance and improves adhesion.

**An unexpected validation.** The patent also reports four-point sheet
resistance: **5.68 Ω/□ with the ZnO seed against 7.56 without**, a ratio of
**1.331**. `metal_growth_factor` — calibrated independently from a different
group's *emissivity* series — gives **1.250**. **Agreement to 6%**: a parameter
fitted to one dataset reproducing another it never saw.

> **The most consequential statement in this work.** The framework models each
> metal layer as though the layer beneath it did not shape its microstructure.
> That single omission accounts for **both** `metal_growth_factor` **and** the
> eightfold copper under-prediction. They are one effect appearing twice, not
> two separate caveats.

The default `grain_size_ratio` of 3.0 corresponds to 30 nm grains in a 10 nm
film — within 20% of the 25 nm measured on ZnO. The assumption was correct, but
only for the underlayer it happened to be tuned against.

## 3.3 A seed layer may account for most of the copper discrepancy

Six further AZO/Cu/AZO studies were located beyond the two the brief cites.

| Film | Seed | R_s |
|---|---|---|
| AZO/**Ti**/Cu/AZO, *Opt. Lett.* 2017 | 1–2 nm Ti | **4.31 Ω/sq** |
| AZO/Cu/AZO, ApSS 2022 | none | 9.96 |
| AZO/Cu/AZO, Miao 2014 | none | 16.6 |
| **this framework, 15 nm Cu** | — | **2.16** |

The framework is eightfold optimistic against unseeded measurements and roughly
**twofold** against the seeded one. **So the model is not wrong about copper as
a material — it is wrong about *poorly nucleated* copper**, and a seed recovers
most of the gap.

That is the same mechanism as §3.2, now visible in three independent places:
silver on ZnO versus amorphous titania, silver on nitride requiring NiCr in
industrial practice, and copper on AZO with and without a Ti seed.

**Consequence.** The copper thickness series should include a seeded arm. One
extra target in an existing run converts the framework's largest error from an
anomaly into a process variable.

## 3.4 Corrections to the project's own conclusions

Five conclusions stated during this work were later overturned **by the work
itself**. They are recorded rather than quietly fixed.

| Claim | Overturned by |
|---|---|
| An optimum exists at Ag₆₀Cu₄₀ | A three-point artifact; at 5% resolution the curve is monotonic |
| The Ti barrier variant beats the ternary | An artifact of silver carrying zero weight; corrected, it ranks last |
| A band-limited emissometer explains the ApSS emissivity | Implemented and tested: it reads 5–8% *higher* |
| Adatom wetting reproduces the measured ordering | A termination sweep showed it was resolving slab index |
| The brief mistranscribed a 1.59 µΩ·cm resistivity | The journal says 1.59; the brief is faithful. Two publications by the same group disagree |

**Three of five are the same error: reading structure into too few points.**
Three compositions in one case, one geometry per composition in another, one
untested hypothesis in a third.

**Two are a different error, and it recurred: holding a fragment of a source and
treating it as the source.** The 1.59 case above, and an aggregator highlight
that appeared to contradict §1.3 and did not — the paper's own abstract said the
opposite of the highlight. The project's own `LITERATURE` versus
`LITERATURE_UNVERIFIED` grading exists precisely to prevent this and was not
being applied to reasoning, only to data.

---

# PART 4 — WHAT WAS COMPUTED

## 4.1 Ag–Cu has no stable ordered compound

All fifteen chemical systems from the brief's §9 were retrieved from the
Materials Project and screened within 50 meV/atom of the convex hull.

Two intermediate Ag–Cu phases exist and **neither is stable**: Cu₃Ag at
**0.0904 eV/atom** above the hull, CuAg₃ at **0.0857**. Ag–Cu is the only
nominated binary with no stable intermediate phase, and 86–90 meV/atom is well
above k_BT at deposition (26 meV at 300 K, 48 meV at 550 K).

**A second finding.** Cu–Ti has 8 near-hull phases and Al–Cu has 10. A dilute Ti
or Al addition therefore has stable intermetallics available to precipitate
rather than remaining in solution — a second, independent mechanism for the
ternary underperforming, alongside the Nordheim conductivity penalty.

## 4.2 The dilute corner is thermodynamically favoured

MACE-MP-0 and CHGNet on 32-site fcc supercells, gated against the two known hull
distances before any prediction was accepted.

Positive across the whole range, fitting a regular-solution form to ±6 meV/atom:
**ΔE_mix = 0.287·x·(1−x)**.

**A self-check that matters more than the gate.** At Ag 25 at.% the surrogate
puts the *disordered* solution 13 meV/atom **below** the ordered Cu₃Ag compound.
No ordering tendency at all — precisely what an empty hull implies, reached
independently.

| Ag at.% | ΔE_mix | ×kT (550 K) |
|---|---|---|
| 70 — the brief's priority | 0.0602 | 1.27 |
| 15 | 0.0366 | 0.77 |
| 10 | 0.0258 | 0.54 |
| 5 | 0.0136 | 0.29 |

**In the dilute corner the driving force to separate falls below thermal energy
at deposition.** §1.2 found the two microstructure hypotheses converge there and
treated it as robustness; the thermodynamics supply the reason.

**The dilute-silver optimum is therefore supported three independent ways:**
lowest silver consumption, highest score under the corrected weighting, and the
weakest tendency to phase-separate.

**Cross-checked, with a caveat.** Both models under-predict — MACE by 0.026,
CHGNet by 0.047 eV/atom — so the bias is inherited from shared Materials Project
training data rather than architecture-specific, meaning ΔE_mix should be
corrected *upward*. **They are not independent**: both train on the same
relaxation trajectories, so agreement shows the bias is consistent, not absent.

**And a compounded correction.** Verifying the brief's own claim 7 established
that GGA underestimates Cu–transition-metal formation energies by nearly 40%
(npj Comput. Mater. 2024), because it places Cu-3d bands too shallow. The MP
hull is GGA/GGA+U and both surrogates train on it, so two errors act in series.
The conclusion **holds at 5–10 at.% Ag and becomes marginal at 15%**.

## 4.3 What a surrogate cannot do

**Cannot, at all:** optical constants, dielectric functions, band gaps,
emissivity. These models predict energies and forces from atomic positions and
carry no electronic structure. **Every optical number must come from the
transfer-matrix model or from measurement.**

**And a conductivity result does not transfer to an optical one.** Sheet
resistance and emissivity correlate at r = 0.978 here, but that link assumes a
low-damping Drude metal — a property of *crystalline* silver. An amorphous film
has different optical constants entirely, so a conductivity gain from
amorphisation cannot be assumed to give the corresponding emissivity gain.

---

# PART 5 — WHAT REMAINS

## 5.1 The critical unknown

The framework validates well against silver in the infrared — within 0.4% on the
benchmark it reproduces best — and **fails on copper**, under-predicting
sputtered sheet resistance by roughly eightfold. Six of the leading candidates
in both climate profiles are copper-based.

**The classical size effect is eliminated.** Four independent published fits give
specularity 0.48–0.80 and grain-boundary reflection 0.16–0.43. The framework's
assumed 0.50 and 0.25 sit inside that range, and an exhaustive scan over the
entire admissible range reaches only **4.42 Ω/sq against the 16.6 to be
explained** — short by a factor of 3.8.

Grain structure is the leading hypothesis: grains at roughly half the film
thickness give 14.1 Ω/sq. §3.3 adds that a seed layer recovers most of the gap.

**If that reading is right, copper's obstacle is film quality, not physics** — an
engineering problem with known levers rather than a fundamental limit.

## 5.2 The experiment that resolves it

**One XRD scan, one film, an afternoon — and it answers three questions.**

| Measurement | Question answered |
|---|---|
| Peak count and position | **Microstructure.** Segregated gives two fcc sets at 38.12° and 43.32°; a solid solution gives one at 39.54° for Ag₇₀Cu₃₀ |
| Scherrer peak width | **Grain size**, and therefore `grain_size_ratio` |
| (111)/(200) ratio vs the powder value of 2.2 | **Templating**, the mechanism of §3.2 |

**Scan to 2θ = 100°, not 60.** Separation grows faster than width with angle:
the (222) reflection separates at 4.8× its width against (111)'s 2.4×.

**A second, independent discriminator.** Sheet resistance separates the
microstructure hypotheses by a number — 6.4 against 2.6 Ω/sq. Diffraction
separates them by *peak count*. Two unrelated observables agreeing is far
stronger than either, and both come from one film.

**Three amendments from the literature survey**, all cheap:

1. **Grazing incidence, not Bragg–Brentano.** A 2010 study of this exact
   architecture reports *no detectable Cu peaks* for 3–13 nm layers, while ApSS
   2022 sees a weak (111) at 43.8° — matching the framework's predicted 43.32°.
   A copper peak here is **marginal, not guaranteed**, and a null would
   otherwise be ambiguous between "nanocrystalline" and "insufficient signal".
2. **A 30 nm uncapped calibration film**, to prove the measurement works before
   applying it to the marginal case.
3. **A seeded arm** — one extra target, per §3.3.

**Pre-registered decision rules** are in `experiments/PROTOCOL_cu_series.md` —
four outcomes, each with what it means and what to do, **including the one where
the literature is right and six candidates fall**.

## 5.3 The question only SGRI can answer

The report benchmarks against a 10 nm AZO/Ag/AZO at ε_h 0.060, taken from the
brief — whose citations for that stack are the two **disputed** entries.

Saint-Gobain's own patents (US 7,745,009) claim silver at **12.5–16 nm targeting
ε ≤ 0.038**. The model says that needs 14–16 nm.

| Ag nm | ε_h | Ag g/m² |
|---|---|---|
| **10.0** (current benchmark) | 0.060 | 0.105 |
| 14.0 | 0.039 | 0.147 |
| 16.0 | 0.033 | 0.168 |

**If production runs at 12.5–16 nm, the reported silver reductions are measured
against a stack that would not meet SGRI's own emissivity specification.** The
baseline needs confirming before the percentages are quoted. This is the single
highest-value question outstanding.

---

# PART 6 — LIMITATIONS

**No experimental validation.** Every performance figure is a model output.

**Fitted parameters.** Specularity and grain-boundary reflection are fitted, not
measured. Si₃N₄ and TiO₂ optical constants are `ESTIMATE` grade.

**Illuminant approximation, quantified.** Varying colour temperature over
5000–7500 K moves **T_vis by 0.1%** and **T_sol by 8.3%**. T_vis is reportable as
computed; T_sol, g and LSG carry a 5–10% systematic until tabulated AM1.5G
spectra are supplied.

**Scores are not portable.** Absolute scores moved by ~25 points as the §2.1
defects were fixed. A score is not a property of a material.

**Not modelled at all:** roughness, interdiffusion, damp-heat and abrasion
durability, adhesion, agglomeration kinetics, amorphous metal layers, and any
property of a metastable sputtered alloy that a 0 K ordered-crystal database
cannot supply.

**The principal structural weakness**, restated because it governs the rest: the
framework models each metal layer as though the layer beneath it did not shape
its microstructure. §5.2 measures it.
