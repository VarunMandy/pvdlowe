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
| **Partial** | 4 | source located, figures confirmed against abstract only |
| **Disputed** | 2 | located sources do not contain the quoted figures — **do not cite** |
| Supported | 2 | not the original source, but independently corroborated |
| Unverified | 4 | not pursued |

---

## The fourteen claims

| # | Claim | Brief § | Status | What was established |
|---|---|---|---|---|
| 1 | AZO/Ag/AZO: 78.7% T_vis, 2.7 Ω/sq | 1 | **DISPUTED** | Appears in neither located AZO/Ag/AZO study. A companion PET-substrate paper reports 78.5% — close, different substrate, different figure |
| 2 | AZO: 82.4% T_vis, 2.6e-3 Ω·cm, 68 Ω/sq, Eg 3.12 eV | 2 | **VERIFIED** | *Materials* **17**(1), 81 (2024), open access, full text read. All four confirmed. **The brief was right about 82.4%** — see the retraction note below |
| 3 | AZO(30)/Ag(10)/AZO(30): 80.5% T_vis; Ag(13): 4.36 Ω/sq, 96% FIR | 3 | partial | *Ceramics International* (2014), PII S0272884214006944. Numbers confirmed. **RF** sputtering, not DC as §3 implies. FTIR + four-point probe, so the measurement basis matches this framework's |
| 4 | AZO/Ag/AZO: 85.4% T_vis, 3.21 Ω/sq, 97% FIR | 3 | **DISPUTED** | Appears in neither located study. **Do not cite** |
| 5 | Ag–Cu Low-E, ~30 at.% Cu, neutral colour, good adhesion | 5 | unverified | Not pursued |
| 6 | Ag–Cu ~13% lattice mismatch, segregation tendency | 5 | **SUPPORTED** | Not the original source, but independently confirmed: the Materials Project convex hull has no stable ordered Ag–Cu compound (Cu₃Ag 0.0904, CuAg₃ 0.0857 eV/atom above hull), and MACE gives ΔE_mix > 0 across the whole composition range. FINDINGS §3.7, §3.8 |
| 7 | GGA underestimates Cu-alloy formation energies; +U improves | 6 | unverified | Not pursued. The framework acts on it anyway — `dft/plans.py` requests a PBE/PBE+U comparison rather than a single functional |
| 8 | ~10 nm films: Ag 1.59, Ag–Cu 2.97, Cu 20.5 µΩ·cm | 7 | **VERIFIED**, and **mistranscribed** | US 10,822,692 B2 (Das & Mukherjee, UNT), full text read. **The patent says Ag = 1.29, not 1.59.** Ag–Cu 2.97 and Cu 20.5 confirmed. The correction makes it worse: 1.29 is **0.81× bulk silver**, below bulk, impossible at any thickness. See below |
| 9 | AZO/Cu/AZO: 16.6 Ω/sq, 67% FIR at 15 nm, continuity ~11 nm | 8 | partial | Located by title; abstract not retrieved. RF sputtering — a different study from #10, and the two should not be pooled |
| 10 | AZO(40)/Cu/AZO(40): 87.7% T_vis, 9.96 Ω/sq, ε = 0.055 | 16 | partial, **fails consistency** | *Applied Surface Science* **578** (2022) 152051. Numbers confirmed, all three from the same sample. ε = 0.055 at 9.96 Ω/sq is below the thin-sheet impedance limit of 0.096, and below the 0.106 an industrial formula in use since 2000 gives. Four explanations tested and eliminated. **§16's conclusion rests on this.** FINDINGS §1.2 |
| 11 | Al:ZnO negative formation energies, 6.25–18.75% Al | 2 | **SUPPORTED** | Materials Project Al–Zn–O screening returns 4 entries with 2 near the hull (Al₂ZnO₄ spinel, Al₁₀ZnO₁₆), consistent with negative formation energies for Al in ZnO. Not the original source |
| 12 | Cu/Al co-doped ZnO, gap down to 1.13 eV at high Cu | 9 | unverified | Not pursued |
| 13 | Ga:ZnO, formation energy rises with Ga content | 11 | unverified | Not pursued |
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

## A second mistranscription, and it matters

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
