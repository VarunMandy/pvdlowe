# References and verification status

Every claim the brief supplies, and what became of it. Regenerated after the
verification work; an earlier version of this file listed all fourteen as
"unverified" and predates all of it.

**Why this mattered.** The brief's citation URLs all carried
`?utm_source=chatgpt.com`, meaning they were surfaced by a language model
rather than read from a publisher. That does not make them wrong — several are
reproduced well by the model, which is weak evidence they are right. It does
mean none had been checked, and checking changed the status of eight of them.

---

## Status summary

| Status | Count | Meaning |
|---|---|---|
| **Verified** | 4 | full text read, figures confirmed |
| **Partial** | 6 | source located, figures confirmed against abstract only |
| **Disputed** | 2 | located sources do not contain the quoted figures — **do not cite** |
| Supported | 3 | not the original source, but independently corroborated |
| Not located | 1 | searched without success |

---

## The fourteen claims

| # | Claim | Brief § | Status | What was established |
|---|---|---|---|---|
| 1 | AZO/Ag/AZO: 78.7% T_vis, 2.7 Ω/sq | 1 | **DISPUTED** | Appears in neither located AZO/Ag/AZO study. A companion PET-substrate paper reports 78.5% — close, different substrate, different figure |
| 2 | AZO: 82.4% T_vis, 2.6e-3 Ω·cm, 68 Ω/sq, Eg 3.12 eV | 2 | **VERIFIED** | *Materials* **17**(1), 81 (2024), open access, full text read. All four confirmed. **The brief was right about 82.4%** — see the retraction note below |
| 3 | AZO(30)/Ag(10)/AZO(30): 80.5% T_vis; Ag(13): 4.36 Ω/sq, 96% FIR | 3 | partial | *Ceramics International* (2014), PII S0272884214006944. Numbers confirmed. **RF** sputtering, not DC as §3 implies. FTIR + four-point probe, so the measurement basis matches this framework's |
| 4 | AZO/Ag/AZO: 85.4% T_vis, 3.21 Ω/sq, 97% FIR | 3 | **DISPUTED** | Appears in neither located study. **Do not cite** |
| 5 | Ag–Cu Low-E, ~30 at.% Cu, neutral colour, good adhesion | 5 | **partial** | *Environmentally robust Ag–Cu based low-e coatings*, Sol. Energy Mater. Sol. Cells (2022), PII S0927024822004500. Abstract confirms it exactly: a range of Ag–Cu compositions tested for colour neutrality, transmittance, IR reflectance and adhesion, with **the best performing alloy identified as a 10 nm film of 70% Ag and 30% Cu**. Note the substrate is **polycarbonate**, not float glass — see below |
| 6 | Ag–Cu ~13% lattice mismatch, segregation tendency | 5 | **SUPPORTED** | Not the original source, but independently confirmed: the Materials Project convex hull has no stable ordered Ag–Cu compound (Cu₃Ag 0.0904, CuAg₃ 0.0857 eV/atom above hull), and MACE gives ΔE_mix > 0 across the whole composition range. FINDINGS §3.7, §3.8 |
| 7 | GGA underestimates Cu-alloy formation energies; +U improves | 6 | **partial**, with a magnitude | *Central role of d-band energy level in Cu-based intermetallic alloys*, npj Comput. Mater. (2024), DOI 10.1038/s41524-024-01257-y. Confirms the claim and quantifies it: GGA formation energies for Cu–Au are **nearly 40% smaller than experiment**, an error the authors state is common across Cu–transition-metal intermetallics, caused by GGA placing Cu-3d bands too shallow and so mis-describing d–d hybridisation. The Hubbard U correction eliminates it. **This has a consequence for §5.6 — see below** |
| 8 | ~10 nm films: Ag 1.59, Ag–Cu 2.97, Cu 20.5 µΩ·cm | 7 | **VERIFIED — brief is faithful** | The journal (*Appl. Mater. Today* 2025) states 1.59; the group's own patent states 1.29. **Two sources, same films, different numbers**, one of them below bulk and impossible. The brief quoted the journal correctly. Both figures are anomalous — see below |
| 9 | AZO/Cu/AZO: 16.6 Ω/sq, 67% FIR at 15 nm, continuity ~11 nm | 8 | **partial — every figure confirmed** | *J. Mater. Sci.: Mater. Electron.* **25** (2014) 5248–5254, DOI 10.1007/s10854-014-2297-0. Miao et al., Hong Kong PolyU. Glass, RF sputtering, four-point probe + FTIR. **Passes the impedance check** — and is the source of the framework's 7.7× copper error. See below |
| 10 | AZO(40)/Cu/AZO(40): 87.7% T_vis, 9.96 Ω/sq, ε = 0.055 | 16 | partial, **fails consistency — all explanations now eliminated** | *Applied Surface Science* **578** (2022) 152051, DC sputtering. Numbers confirmed, all three from one sample. **Six explanations tested, including the measurement basis, which was the last one standing.** §16's conclusion rests on this and should not be used. See below |
| 11 | Al:ZnO negative formation energies, 6.25–18.75% Al | 2 | **SUPPORTED** | Materials Project Al–Zn–O screening returns 4 entries with 2 near the hull (Al₂ZnO₄ spinel, Al₁₀ZnO₁₆), consistent with negative formation energies for Al in ZnO. Not the original source |
| 12 | Cu/Al co-doped ZnO, gap down to 1.13 eV at high Cu | 9 | **mechanism supported, value not located** | Multiple first-principles studies confirm Cu doping *narrows* the ZnO gap through Cu-3d states in the gap and a downward conduction-band shift (e.g. *Materials* **12**, 196, 2019). The specific figure of 1.13 eV for Cu/Al co-doping was not found in any located source. Direction confirmed, magnitude not |
| 13 | Ga:ZnO, formation energy rises with Ga content | 11 | **not located** | Searched. Al/Ga-doped and co-doped ZnO first-principles studies are plentiful and consistent on optical gaps — AZO 4.61 eV against GZO 4.52 eV in one — but no located source states formation energy rising with Ga content. Remains unverified |
| 14 | ZnO = mp-2133, Cu = mp-30 | 12 | **VERIFIED** | Both IDs used directly against the live Materials Project API. mp-2133 returns wurtzite ZnO and mp-30 returns fcc Cu, as used in `pvdlowe/ml/surrogate.py` and the adatom calculations |

---

## A retraction

An earlier version of this project recorded that the brief's **82.4%** AZO
transmittance (claim 2) was a transcription error for 81.4%. **That was wrong.**

The paper reports both: §3.1 gives the average transparency over 360–760 nm as
82.4%, while the abstract and conclusions give 81.4%. The source is internally
inconsistent, and the brief quoted the Results figure — which is the defensible
choice. The error came from checking only the abstract, which is precisely the
shortcut the `partial` grade exists to flag.

## Claim 8: not a mistranscription — two sources that disagree

> **This section replaces one asserting that the brief had mistranscribed the
> silver value. That assertion was wrong**, and wrong in the same way as the
> AZO transmittance error recorded above: one source was read, a different
> number was found, and the other party was assumed careless.

The journal article reports **1.59 µΩ·cm** for the pure-silver control. The
group's own patent, describing the same films, reports **1.29**. The brief
quoted the journal, and quoted it correctly.

| | Ag | Ag–Cu | Cu |
|---|---|---|---|
| Brief | 1.59 | 2.97 | 20.5 |
| Journal | **1.59** ✓ | 2.97 ✓ | 20.5 ✓ |
| Patent | **1.29** | 2.97 | 20.5 |

**Both silver figures are anomalous, independently of which is taken.** Silver's
electron mean free path is 53 nm, so a 10 nm film is deep in the size-effect
regime. Fuchs–Sondheimer with diffuse scattering, ρ/ρ₀ ≈ 1 + (3/8)(λ/d), gives
**2.99× bulk = 4.74 µΩ·cm** before any grain-boundary term. This framework's
full FS + Mayadas–Shatzkes model gives 4.44, and reproduces an independent
12 nm measurement of 4.8 µΩ·cm to within 17%.

1.59 is exactly handbook bulk silver at 300 K. 1.29 is *below* it, which is not
possible at room temperature. A 10 nm polycrystalline silver film reaching bulk
resistivity would be a headline result on its own, and the paper does not treat
it as one — it is a control.

**What is defensible to cite.** The comparative claim: amorphous Ag–Cu at
2.97 µΩ·cm beats polycrystalline Cu of the same thickness at 20.5 by about
sevenfold, and the absence of grain boundaries is the paper's real
contribution. **Do not cite 1.59 as a validated pure-Ag thin-film benchmark** —
a reader who knows FS/MS scaling will stop there.

**And a limit on its relevance to this project.** This is an interconnect
paper. A conductivity figure says nothing about infrared reflectance, and
amorphous metals do not share crystalline silver's optical constants. The
low-loss Drude response that makes silver the Low-E workhorse depends on its
being crystalline, so a conductivity gain from amorphisation does not transfer
to emissivity or to light-to-solar-gain. See FINDINGS §3.13.

## The AZO retraction, for comparison

Claim **8** was verified through the associated patent, US 10,822,692 B2 — the
journal article is paywalled but the patent carries the same measurements and
is free. The patent states verbatim that 99.999% Ag and Cu films measured
**1.29 × 10⁻⁶** and 2.05 × 10⁻⁵ Ω·cm.

**The brief says 1.59. The source says 1.29.**

| | brief | patent |
|---|---|---|
| Ag | 1.59 | **1.29** |
| Ag–Cu | 2.97 | 2.97 ✓ |
| Cu | 20.5 | 20.5 ✓ |

The correction makes the anomaly worse. Bulk silver is 1.587 µΩ·cm, so the
brief's figure was exactly 1.00× bulk — already impossible for a 10 nm film.
The patent's actual 1.29 is **0.81× bulk**, which is impossible at *any*
thickness: surface and grain-boundary scattering can only ever add resistivity
to a polycrystalline film.

The patent also prints the alloy value as "2.97 × 10⁶ Ω·cm", twelve orders of
magnitude out. The numeric care in this source is not high.

**Consequence.** The brief's §7 argues that amorphous Ag–Cu "retains unusually
good conductivity" by comparing 2.97 against the silver baseline. That baseline
is both mistranscribed and unphysical. Compare against the copper value instead
— 20.5, against which the alloy is genuinely seven times better — and the
argument survives in stronger form.

## Claim 5: the source exists, but on the wrong substrate

The 2022 paper confirms the brief's claim precisely — Ag–Cu compositions
screened for colour neutrality, transmittance, IR reflectance and adhesion,
with 70% Ag / 30% Cu at 10 nm identified as best.

**But the substrate is polycarbonate, not float glass.** The paper concerns
first-surface coatings on plastic. Thermal budget, surface energy, nucleation
behaviour and durability requirements all differ from a glass line, and the
nucleation finding of `docs/NUCLEATION_MECHANISM.md` says the underlayer
determines metal grain structure. A composition optimum established on
polycarbonate does not transfer to glass without checking.

This weakens the brief's §5 justification for Ag₇₀Cu₃₀ as the priority
composition — independently of FINDINGS §3.1, which finds the optimum at
5–15 at.% Ag on modelling grounds.

## Claim 7 has a consequence for the mixing energies

The npj paper quantifies GGA's error on Cu–transition-metal intermetallics at
**nearly 40% too small**, and attributes it to Cu-3d bands sitting too shallow.

The Materials Project convex hull is computed with GGA/GGA+U. MACE-MP-0 and
CHGNet are trained on Materials Project data. So there are **two errors in
series**, both in the same direction:

| Step | Error | Direction |
|---|---|---|
| Experiment → GGA | up to ~40% | GGA too small |
| GGA → MLIP | 20–40% (measured, §5.6) | MLIP too small |

FINDINGS §3.8 already concluded that ΔE_mix should be corrected *upward* rather
than read as a lower bound, on the evidence that both MLIPs under-predict the
MP values. This suggests the correction is larger than that analysis assumed,
because the MP reference is itself low against experiment.

**It strengthens the conclusion rather than threatening it.** §5.6 finds the
driving force to separate falls *below* thermal energy in the dilute corner;
a larger correction pushes ΔE_mix up, which narrows that margin. The margin
survived a 1.42× correction with room to spare — 0.74 kT at Ag 10% — but a
compounded correction approaching 2× would bring Ag 15% above kT. **The
conclusion holds at 5–10 at.% Ag and becomes marginal at 15%.**

That is worth stating rather than leaving implicit, and it is a caveat that
only emerged from verifying a citation the brief made in passing.

## The two copper claims sit in opposite positions

This is the strongest single result of the citation audit, and it only emerged
once both entries were checked against the same physical bound.

| | Group, technique | R_s | ε | Impedance floor | |
|---|---|---|---|---|---|
| **#9** | Miao 2014, Hong Kong PolyU, **RF** | 16.60 | 0.330 | 0.150 | **passes**, +0.18 margin |
| **#10** | ApSS 2022, Xi'an, **DC** | 9.96 | 0.055 | 0.096 | **below floor by 42%** |

**The entry that obeys the electrodynamic limit is the one that disagrees with
this framework.** The model predicts 2.16 Ω/sq for a 15 nm copper layer against
#9's measured 16.6 — a factor of **7.7**. That is the copper discrepancy, and
it comes from the physically consistent source.

Meanwhile #10 agrees with the model's optimism and is impossible. A model that
matched both would have to be wrong about one of them; matching the impossible
one would be worse.

**And they must not be pooled.** Different groups, different technique (RF
against DC), different decade, and #9 is from a textiles laboratory that also
coats polyester fabric with the same stacks — not a glazing group.

## Claim 10: every explanation is now eliminated

The measurement basis was the last benign explanation standing. The impedance
floor is a normal-incidence quantity, so the open question was whether 0.055
might be hemispherical and therefore not comparable.

| Reading | Normal-basis value | vs floor 0.0956 |
|---|---|---|
| 0.055 is **normal** | 0.0550 | fails by **42%** |
| 0.055 is **hemispherical** | 0.0472 | fails by **51%** |

**Reading it as hemispherical makes the discrepancy worse**, because the normal
equivalent is lower still. Neither basis rescues it.

Six explanations tested and eliminated: different samples, transcription, far-IR
glass index, band-limited emissometer, this framework's own convention (an
industrial formula in use since 2000 gives the same answer), and now measurement
basis. ε = 0.055 would require about **5.48 Ω/sq** against the 9.96 reported.

The full text remains paywalled, but the arithmetic above does not depend on it
— what the method section would add is the instrument model, not a resolution.

## Two entries that should be withdrawn

Claims **1** and **4** cannot be matched to any locatable source. They should
not appear in any document derived from the brief until someone establishes
where they came from.

An uncomfortable corollary: **these two are the model's three closest
agreements** (0.3%, 1.0%, 1.2% relative error). Excluding them, the median
validation error rises from 14.7% to 30.6%. The framework's apparent accuracy
rested partly on figures that cannot be traced.

## Three corrections to the brief's characterisations

- **Deposition methods differ across the benchmark set.** The AZO/Ag/AZO
  trilayers used **RF** sputtering (§3 implies DC); the AZO single layer used
  **medium-frequency**. Film density and resistivity do not transfer between
  techniques, so these sources should not be pooled.
- **Claims 9 and 10 are different studies from different groups**, one RF and
  one DC, and should not be treated as a series.
- **Claim 8's table mixes conventions**, per FINDINGS §1.3.

---

# Sources found outside the brief that changed the model

These were not cited by the brief. Three of them corrected it.

| Source | Status | Effect |
|---|---|---|
| Cueva & Carretero, *Coatings* **13**, 1709 (2023) | **VERIFIED**, open access, full text read | Measured five dielectrics under identical conditions. **Reversed FINDINGS §3.2** — AZO beats SiAlNx on both emissivity and transmittance. Added `metal_growth_factor` to the model |
| Glenn et al., US 7,632,572 B2 / US 8,512,883 B2 (AFG / AGC, now Cardinal CG) | **VERIFIED**, full text read | TEM grain sizes 25 nm on ZnO vs 15 nm on a-TiOx; epitaxial Ag{111}/ZnO{0001} mechanism named by the inventors; **four-point sheet resistance 5.68 vs 7.56 Ω/sq, validating `metal_growth_factor` to 6%** |
| Chawla & Gall, *Phys. Rev. B* **81**, 155454 (2010), and three further Cu scattering studies | partial | Eliminated decision rule A in the copper protocol: **no published p or R value explains the 8× discrepancy**, which redirected the hypothesis to grain structure |
| Gläser, *Large Area Glass Coating* (2000), via Carretero | partial | ε = 0.0106·R□, an industrial relation agreeing with this framework's impedance limit within 10% — independent corroboration that claim 10 is inconsistent |
| Society of Vacuum Coaters review, silicon nitride Low-E | partial | NiCr barrier layers are used to improve nitride/silver adhesion — industry adds a nucleation layer because silver adheres poorly to nitride directly |
| Materials Project, 15 chemical systems | **executed** | Ag–Cu has no stable ordered compound; Cu–Ti has 8 near-hull phases and Al–Cu 10, giving a second mechanism for the Ti ternary underperforming |

---

## Sources still needed

- **Primary sources for claims 5, 7, 12 and 13**, none pursued.
- **The measurement basis for claim 10** — normal versus hemispherical, and the
  instrument band. This is the highest-value item outstanding: §16's conclusion
  depends on it and it is one line of a paywalled full text.
- **Tabulated D65 and AM1.5G spectra**, if standards-grade T_vis and T_sol are
  needed. The illuminant sensitivity is quantified in §7.4: T_vis moves 0.1%,
  T_sol 8.3%.
- **Measured n and k** for in-house AZO, Si₃N₄ and metal films — the largest
  single source of visible-range error.
- **A measured R_s versus thickness series** for each metal, to re-fit
  specularity and grain-boundary reflection.

---

## Physics implemented by this framework

Not from the brief; these are the models the code contains.

- **Rakić, Djurišić, Elazar & Majewski (1998)**, Appl. Opt. **37**, 5271 —
  Lorentz–Drude parameters, used with free-electron damping re-anchored to DC
  resistivity (METHODOLOGY §2).
- **Fuchs (1938)** and **Sondheimer (1952)** — surface-scattering size effect.
- **Mayadas & Shatzkes (1970)**, Phys. Rev. B **1**, 1382 — grain-boundary
  scattering.
- **Bruggeman (1935)** — effective-medium approximation.
- **Nordheim (1931)** — alloy resistivity rule.
- **Derringer & Suich (1980)**, J. Qual. Technol. **12**, 214 — desirability.
- **Wyman, Sloan & Shirley (2013)**, JCGT **2**, 11 — the V(λ) analytic fit.
- **EN 410 / ISO 9050**, **EN 12898**, **EN 673** — transmittance, emissivity,
  thermal transmittance.
- **Box & Behnken (1960)**; **Box & Wilson (1951)** — response-surface designs.
