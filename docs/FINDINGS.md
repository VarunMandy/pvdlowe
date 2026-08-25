# Findings

Results from `pvdlowe`, a computational screening framework built from the
project brief `PVD_Usecase.docx`. Organised by conclusion rather than by order
of discovery. Every number is reproducible from the commands in Appendix B.

**Read the scope note first.** Every performance figure here is a *model*
output. No films have been deposited. The framework's own validation shows it
under-predicting sputtered copper sheet resistance by roughly 8x against
literature, and copper is central to most of the leading candidates. These are
hypotheses ranked by physics, not results.

---

# Summary

**The brief asks how much silver can be removed from an AZO/Ag/AZO Low-E stack.
The answer depends on a question the brief does not ask: which climate.**

| | heating-dominated | cooling-dominated (India) |
|---|---|---|
| Lead candidate | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ | AZO/Cu/AZO |
| T_vis | 0.878 | 0.738 |
| ε_h | 0.0456 | 0.0463 |
| R_s (Ω/sq) | 3.13 | 2.87 |
| g (SHGC) | 0.760 | 0.558 |
| Ag (g/m²) | 0.015 (**86% less**) | **0** |
| Meets full spec | yes | no — T_vis |

Six substantive conclusions, in descending order of confidence:

1. **The composition optimum is 5–15% Ag, not the brief's 70%** — and it is a
   sustainability result, not a performance one (§3.1).
2. **Silicon nitride outperforms AZO on transmittance by up to 9 points**, a
   material class the brief's framing structurally excluded (§3.2).
3. **Climate reverses the ranking**, because AZO's free carriers do
   solar-control work a passive nitride cannot (§3.3).
4. **No single-metal stack can reach solar-control performance**; two metal
   layers can (§3.4).
5. **The brief's section 14 weighting has four defects**, one of which let the
   optimiser return *more* silver than the benchmark at a perfect score (§2).
6. **Two of the brief's citations cannot be matched to any source, and one
   pivotal measurement is physically inconsistent** (§1).

---

# 1. Evidence audit

Eight literature benchmarks were transcribed from the brief. All eight sources
have now been located. None has been read in full.

| State | Count | Meaning |
|---|---|---|
| fully verified | 0 | full text read, measurement basis confirmed |
| partial | 6 | source identified, numbers confirmed against the abstract |
| **disputed** | **2** | **located sources do not contain the quoted figures** |
| not located | 0 | — |

Run `pvdlowe provenance` and `pvdlowe validate` for the current state.

## 1.1 Two citations cannot be supported

The brief's figures of **85.4% T_vis / 3.21 Ω/sq / 97% FIR** and **78.7% T_vis
/ 2.7 Ω/sq** appear in neither located AZO/Ag/AZO paper. A companion
PET-substrate study reports 78.5% with 91% FIR at 10 nm Ag — close to one of
them, but a different substrate and a different number.

**Do not cite either.** Both are flagged `disputed` in `data/benchmarks.yaml`.

There is an uncomfortable corollary. **These two entries are the model's three
best agreements** (0.3%, 1.0%, 1.2% relative error). Excluding them, the
median validation error rises from **14.7% to 30.6%**. The framework's apparent
accuracy was resting partly on figures that cannot be traced to a source.

## 1.2 The pivotal Cu emissivity is physically inconsistent

*Applied Surface Science* **578** (2022) 152051 reports AZO(40)/Cu/AZO(40) with
T_vis 87.7%, R_s 9.96 Ω/sq and ε 0.055 — and the brief's section 16 concludes
from it that an Ag-free stack may already meet a Low-E target. The
transcription is accurate and the abstract attributes all three values to the
same sample.

For a conducting sheet much thinner than the wavelength between media of index
n₁ and n₂:

    r = (n₁ − n₂ − Z₀/R_s) / (n₁ + n₂ + Z₀/R_s),    ε = 1 − r²

with Z₀ = 376.73 Ω. No fitted parameter enters. At 9.96 Ω/sq this gives
**ε ≥ 0.096**; the reported 0.055 would require about **5.5 Ω/sq**.

Every benign explanation has been tested and eliminated:

| Explanation | Status |
|---|---|
| Different samples | ruled out — abstract attributes all three to one sample |
| Transcription error | ruled out — confirmed against the abstract |
| Far-IR glass index assumption | ruled out — limit is 0.091–0.097 for n = 1.5–4.0 |
| Band-limited emissometer | **ruled out — moves it the wrong way** (§5.3) |
| Framework's own convention | **ruled out — an industrial formula agrees** (below) |
| Single outlier | ruled out — three reports at 0.57–0.63 of the limit |

**Independent corroboration.** Cueva & Carretero compute emissivity from sheet
resistance as ε_n = 0.0106·R□, citing Gläser, *Large Area Glass Coating* (2000)
— in industrial use for two decades. That formula and this framework's
impedance limit agree within 10% across 2–17 Ω/sq. At 9.96 Ω/sq the industrial
formula gives **0.106** against the framework's 0.096 and the reported 0.055.
Reported/industry = **0.52**. The discrepancy is not an artifact of the
framework's convention.

The same group reports ε = 0.045 at 8.10 Ω/sq and ε = 0.050 at similar sheet
resistance. A *consistent* factor of ~0.6 across three measurements indicates a
systematic effect, not an error.

Untested: hemispherical vs normal basis (which would also *raise* the reading),
instrument calibration, or the two quantities coming from different areas of
one nominal sample.

**Action:** this is the single highest-value verification remaining. Section 16's
conclusion should not be used until it is settled.

## 1.3 A silver resistivity that cannot be right

A 2025 study reports ~10 nm films of Ag at 1.59 µΩ·cm, Ag–Cu at 2.97, Cu at
20.5, *deposited under identical conditions*.

| Film | Reported | × bulk | Framework model |
|---|---|---|---|
| Ag, 10 nm | 1.59 µΩ·cm | **1.00×** | 4.44 µΩ·cm (2.79×) |
| Cu, 10 nm | 20.5 µΩ·cm | 12.2× | 7.11 µΩ·cm (4.23×) |

Silver's electron mean free path is 53 nm, so a 10 nm film cannot reach bulk
resistivity — Fuchs–Sondheimer alone forces a ratio above ~2. Thickness
uncertainty (10 ± 2.5 nm) does not rescue it: even the upper bound is 1.25× bulk.
Under identical deposition their copper shows a strong size effect and their
silver shows none.

**Consequence for the brief.** Section 7 argues Ag–Cu "retains unusually good
conductivity" by comparing 2.97 against 1.59. If the silver baseline is not
like-for-like, compare against their copper (20.5) instead — the alloy then
looks *seven times better* and the argument survives in stronger form.

## 1.4 Three factual corrections

- **Deposition methods differ across the benchmark set.** The AZO/Ag/AZO
  trilayers used **RF** sputtering (the brief's §3 implies DC); the AZO single
  layer used **medium-frequency**. Film density and resistivity do not transfer
  between techniques, so these should not be pooled.
- **The AZO transmittance is 81.4%, not 82.4%.** Resistivity 2.6 × 10⁻³ Ω·cm,
  hardness 11.4 GPa and modulus 98 GPa are all confirmed.
- **The §7 resistivity table mixes conventions**, as above.

## 1.5 What verification confirmed

Not everything failed. The *Ceramics International* abstract states far-IR
reflectance was measured by **FTIR spectroscopy** and sheet resistance by
**four-point probe** — a spectroscopic reflectance directly comparable with the
framework, no emissometer ambiguity. Consistent with the model reproducing that
benchmark to **0.4%**, its best agreement against a traceable source.

It also independently confirms the percolation anchor: **Ag continuity at 10 nm
supported by XRD 200 and 220 peaks**, structural evidence rather than a
resistivity kink.

---

# 2. Method audit: six defects in the section 14 weighting

Encoding the brief's weighting table literally produced a scorer that did not
measure what the project is for. Each defect was found by the framework's own
diagnostics (`pvdlowe check-weights`) and each is now a documented decision in
`data/targets.yaml`.

## 2.1 Silver consumption carried zero weight

Section 14's table has no silver line, though §17 and §20 both name minimising
it as an objective. `Ag_g_per_m2` was computed, displayed, reported as the
limiting criterion — and contributed nothing to the score.

The thickness optimiser exploited this immediately, returning a 12.84 nm design
using **0.135 g/m² of silver, 29% more than the benchmark, at a perfect
100/100.** Corrected to weight 0.15.

## 2.2 Emissivity and sheet resistance double-count

They correlate at **r = 0.996** across the candidate set — both are the
free-carrier response of the same layer — so 0.25 + 0.15 put 0.40 of the total
weight on one physical quantity. `R_sheet` is now weighted 0.0 and reported as
a constraint. Restore it (cutting emissivity to 0.15) if the coating must also
serve as a transparent electrode.

The same diagnostic flags cost vs supply risk (r = 0.993) and silver mass vs
cost (r = 1.000 — silver dominates metal cost so completely they are the same
number in different units).

## 2.3 Targets set at the specification minimum, so criteria saturated

Derringer–Suich desirability clamps at 1.0 once the target is reached. Setting
`T_vis` target to 0.80 — the brief's *floor of acceptability* — made the
criterion flat exactly where candidates differ. The optimiser satisficed: it
returned T_vis = 0.800 and walked the oxides to a 15 nm top layer, because above
0.80 transmittance was free and thinner oxides marginally help emissivity.
Across 181 oxide pairs clearing 0.80, T_vis spanned 0.800–0.881 while the
**score went down**, 74.99 to 73.30.

Targets are now aspirations: `T_vis` 0.90, `emissivity_hemispherical` 0.02.
Re-optimising gave AZO 25 / Ag 10.0 / AZO 35 nm at T_vis 0.880 — eight points
better on identical silver.

**General rule: a desirability target should be an aspiration, not a
specification minimum.**

## 2.4 The supply-risk floor could not discriminate

At floor 8.0 against candidate values of 4.5–7.5, every silver-bearing
composition scored 0.1–0.28 and `supply_risk` was reported as limiting for 12 of
14 candidates. Widened to 9.5 / 4.0, which still zeroes indium-bearing ITO.

## 2.4b Weight reserved for criteria that were never populated

**A sixth defect, found by asking what the framework does not predict.** Three
criteria — structural stability, thermal stability and deposition efficiency —
carried **0.30 of the 0.90 nominal weight while being `None` for every
candidate**. The scheme renormalises over available criteria, so that third was
silently redistributed onto the three that do have values: a file stating
emissivity at 0.25 was in fact applying 0.42.

Worse, `structural_stability` carried 0.15 **with no criterion definition at
all** — no entry under `criteria:`, so it could never have scored even had a
value been supplied.

*Correction applied:* all three weighted 0.0, and the missing definition
written. The ranking is unchanged, which is the point — they were renormalising
away already.

**One of them is now partly populatable, and deliberately left unpopulated.**
When `structural_stability` was written the value was unavailable. It is not
any more: the Materials Project screening supplies hull distances for ordered
phases and the surrogate mixing energies extend that to the disordered solid
solution, both in eV/atom, which is exactly what the criterion asks for.

It is left at weight 0.0 on purpose. Populating it would change every ranking,
the values carry a 20–40% systematic under-prediction inherited from GGA, and
0.15 is another weight nobody derived — the same problem the sweep exposes for
silver. **Populating a criterion and choosing its weight are one decision, not
two**, and that decision belongs to whoever continues the work. The criterion
block records the data source and the caveat.

## 2.5 A weighted sum does not do what the brief wants

The brief states its weighting should prevent a candidate "winning simply
because it has excellent conductivity while being unacceptable optically". A
weighted arithmetic sum does not do this — a candidate scoring zero on one
criterion loses only that weight. A **geometric** mean does.

Under the corrected weighting the pure-Ag benchmark ranks 4th arithmetic and
7th geometric; pure Cu is 1st arithmetic and 2nd geometric. Those are exactly
the two candidates the brief cares about comparing. The framework defaults to
geometric and reports both.

## 2.6 How to read `limiting_criterion`

It is `argmin(desirability)`: where a candidate is *weakest*, not what drives
the ordering. Under a geometric mean, whichever criterion sits nearest its floor
is reported as limiting for everyone. The real test of whether weights do any
work is `sensitivity_to_weights`. Before these fixes one candidate won 97.5% of
randomised weightings with rank_std 0.16 — not robustness, but weights having
no effect.

---

# 3. Design-space results

38 candidates, 58 metal systems screened, 168-point composition series across
two microstructure models, two dielectrics and two climate profiles.

## 3.1 The composition optimum is 5–15% Ag

`pvdlowe series` re-optimises geometry at every composition. Eight curves,
Ag 0–100% in 5% steps:

| profile | model | dielectric | optimum Ag | score | plateau |
|---|---|---|---|---|---|
| heating | segregated | Si₃N₄ | **0.05** | **89.3** | 0.00–0.20 |
| heating | solid solution | Si₃N₄ | 0.00 | 88.9 | 0.00 |
| heating | segregated | AZO | **0.10** | 76.5 | **0.05–0.40** |
| heating | solid solution | AZO | 0.00 | 74.4 | 0.00–0.05 |
| cooling | either | AZO | 0.00 | 68.2 | 0.00–0.15 |
| cooling | either | Si₃N₄ | 0.00 | 67.6 | 0.00–0.10 |

**Every curve peaks between 0 and 10% Ag.** Under the cooling profile all four
peak at exactly zero, monotonically. The brief's Ag₇₀Cu₃₀ priority is beaten in
all eight cases.

**This is a sustainability result, not a performance one.** Emissivity and sheet
resistance keep *improving* to Ag 50% (0.0386 and 2.59 Ω/sq, the best in the
series). The score falls anyway because silver mass is weighted 0.15. The trade
is ~0.005 in emissivity for an 87% cut in silver, and it is only the right trade
because you decided silver matters.

**Plateau width matters more than peak position** for a sputtering process. The
segregated/AZO curve is flat from **5% to 40% Ag** — a forgiving window.
Solid-solution curves are sharp (0–5%).

**The microstructure question stops mattering in the dilute corner.** At
Ag₇₀Cu₃₀ the two hypotheses differ by 9–14 points; at Ag₅Cu₉₅ by 2.5. Designing
at 5–15% Ag makes the project *robust* to an unresolved question rather than
hostage to it — worth more than the two points of score.

## 3.2 The dielectric matters — but not for the reason first concluded

> **AMENDED.** The original conclusion of this section — that silicon nitride
> outperforms AZO — is **contradicted by measurement** and has been corrected.
> The model has been changed as a result. See `docs/CARRETERO_COMPARISON.md`.

**What was wrong.** The framework treated the dielectric as purely an
interference layer: index, thickness, nothing else. On that basis Si₃N₄
(n = 2.02) beat AZO (n = 1.90) by up to nine points of transmittance.

**What the measurement says.** Cueva & Carretero (*Coatings* 13, 1709, 2023)
deposited five dielectrics under identical conditions with 10 nm Ag. Measured
emissivity: **AZO 0.058 < ZnO 0.064 < SiAlNx 0.067 < SnO₂ 0.083.** AZO also
gave the better visible transmission. AZO wins on both axes, and the reason
they give is that silver growth is more efficient on AZO.

**That is a nucleation effect the model did not contain.** The underlayer
changes the *quality of the metal grown on it*, not just the interference
stack. The optical inputs were fine — their measured indices (AZO 1.85,
SiNx 2.023) match the framework's closely.

**The model now contains it.** `TCOPreset.metal_growth_factor` applies a
resistivity penalty per underlayer, calibrated to that series and normalised to
AZO = 1.00: ZnO 1.10, SiAlNx 1.16, ITO 1.20, TiO₂ 1.25, SnO₂ 1.43. With it, the
model reproduces both the measured ordering and the magnitudes to 4–8%:

| Dielectric | measured ε | model ε_h |
|---|---|---|
| AZO | 0.058 | 0.060 |
| ZnO | 0.064 | 0.061 |
| Si₃N₄ | 0.067 | 0.065 |
| SnO₂ | 0.083 | 0.077 |

**What survives.** The brief's framing did exclude nitrides, and that
observation stands. Two qualifications from the same paper keep them relevant:
in double-metal structures their SiAlNx sample had the highest spectral
transmittance of any across the whole visible range; and nitride is the
industrial choice for durability through tempering.

**The best answer is a hybrid**, and it is what industry already does: AZO
underneath for silver nucleation, nitride on top for protection. Their sample
S6 measured *better* emissivity than two AZO layers. Added here as candidate
**H1 — AZO/Ag/Si₃N₄, which now outscores both pure stacks** (T_vis 0.918,
ε_h 0.057 against the AZO benchmark's 0.876 / 0.060), and **H2 — AZO/Cu/Si₃N₄**,
the silver-free version, which gains five points of transmittance over
AZO/Cu/AZO at lower emissivity.

## 3.2b Original analysis: silicon nitride and index matching

*Retained for the record; superseded above.*

58 metal systems were screened at fixed AZO 35/35 — every pure metal with
available optical constants plus ten binary families at five compositions,
thickness optimised per system. **Exactly one met the full specification: pure
silver.** Copper failed only on transmittance, 0.752 against 0.80.

Then the dielectric was allowed to vary:

| Metal | AZO | SnO₂ | TiO₂ | **Si₃N₄** |
|---|---|---|---|---|
| Cu | 0.755 | 0.795 | 0.786 | **0.845** |
| Cu₉₀Zn₁₀ | 0.772 | 0.808 | 0.780 | **0.836** |
| Ag₇₀Cu₃₀ | 0.837 | 0.869 | 0.835 | **0.912** |
| Ag | 0.880 | 0.902 | 0.868 | **0.923** |

Si₃N₄ buys **nine points of T_vis on copper** — the gap that was disqualifying
it. Every metal improves, so this is a dielectric property.

**Highest index does not win.** TiO₂ (n = 2.45) underperforms SnO₂ (n = 2.00).
Antireflection around a metal is index-*matching*, not index-*maximisation*.

**Why the brief missed it.** The brief began from the RSC periodic table and the
Materials Project, both of which surface oxides. **Nitrides fall outside that
framing, and the framing was the constraint.** Si₃N₄ is also what industrial
Low-E actually uses — dense, an excellent diffusion barrier, durable enough to
survive tempering — and it blocks the oxygen ingress that is copper's dominant
failure mode, which is why the Cu/Si₃N₄ pairing is attractive and why it does
not appear in the AZO literature.

**Lattice absorption checked and negligible.** Si₃N₄ absorbs near 11.7 µm,
inside the thermal band, so far-IR phonon oscillators were added. The penalty on
the Cu stack is **+0.0007 in emissivity (1.7% relative)** — because at 10 µm the
copper reflects ~96% of the field, so little reaches the nitride. Lattice
absorption only matters when the metal is poor, which is when you have no Low-E
coating anyway.

## 3.3 Climate reverses the ranking

`data/targets.yaml` follows the brief and does not constrain solar heat gain.
That omission encodes a climate. The metrics now computed:

    g = T_sol + N·A_sol       (EN 410 / ISO 9050, N = 0.36 for surface 2)
    LSG = T_vis / g

| Candidate | heating | rank | cooling | rank | g | LSG |
|---|---|---|---|---|---|---|
| Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ (E10e) | **89.3** | 1 | 50.4 | 20 | 0.760 | 1.16 |
| Si₃N₄/Cu/Si₃N₄ (N6) | 88.9 | 3 | 55.5 | 12 | 0.731 | 1.18 |
| **AZO/Cu/AZO (M6)** | 69.6 | 15 | **65.4** | **1** | 0.558 | 1.32 |
| AZO/Ag/AZO (M0) | 65.0 | 22 | 53.0 | 17 | 0.646 | 1.35 |

**The mechanism is real.** AZO is a *transparent conductive oxide*: its free
carriers give a screened plasma wavelength at **1.25 µm, inside the solar
band**. Si₃N₄ is a passive insulator, transparent throughout.

| λ (nm) | 1200 | 1600 | 2000 | 2400 |
|---|---|---|---|---|
| k(AZO) | 0.155 | 0.729 | 1.587 | 2.240 |
| k(Si₃N₄) | 0.0004 | 0.0005 | 0.0008 | 0.0012 |
| T, AZO stack | 0.240 | 0.115 | 0.068 | 0.046 |
| T, Si₃N₄ stack | 0.509 | 0.259 | 0.151 | 0.099 |

**The conductive oxide is doing solar-control work the nitride cannot.** Section
3.2 read AZO's near-infrared absorption purely as a transmittance penalty; half
of it is a solar-control benefit the default weighting could not see.

**Choose the profile before quoting a ranking.** The two disagree on the winner
and on most positions.

## 3.4 No single-metal stack can do solar control; two can

Best LSG across all 38 candidates is **1.37**, against ~2.0 for commercial
solar-control glazing. Under the cooling profile no single-metal stack met the
transmittance target at all.

`MultiMetalCoating` generalises to n metal layers separated by n+1 dielectrics:

| Architecture | metal | dielectric | geometry (nm) | T_vis | g | **LSG** | ε_h | R_s |
|---|---|---|---|---|---|---|---|---|
| single | Cu | AZO | 45/12/45 | 0.738 | 0.558 | 1.32 | 0.0463 | 2.87 |
| **double** | **Ag** | **Si₃N₄** | **15/12/60/12/15** | **0.819** | 0.464 | **1.76** | 0.0248 | 1.67 |
| double | Cu | Si₃N₄ | 59/13/105/13/59 | 0.716 | 0.516 | 1.39 | 0.0244 | **1.33** |
| double | Cu | AZO | 15/15/75/15/15 | 0.423 | 0.274 | 1.54 | 0.0204 | 1.05 |

**LSG 1.76 against a ceiling of 1.37 — 28% better, and the first architecture
here to approach the commercial range.**

**Why one layer cannot.** A single film trades transmittance against IR
reflectance along one curve; thickness moves you along it, never off it. The
dielectric *between* two metals adds an interference degree of freedom — the two
reflections can cancel in the visible while adding in the infrared. Sections
3.1–3.3 searched compositions exhaustively and could never have found this.

Note the optimum: **thin outer dielectrics (15 nm), thick middle (60 nm)**. The
middle layer does the interference work; a symmetric guess misses it.

**The costs are real.** Silver doubles, because each layer must independently
clear percolation near 10 nm — so double-Ag uses 0.252 g/m² and scores *badly*
on the sustainability profiles (21.9 cooling). Splitting a film also raises
resistance: two 12 nm layers are not one 24 nm layer, each carries its own
surface scattering.

**The interesting row is Cu/Si₃N₄ double**: LSG 1.39, R_s 1.33 Ω/sq,
ε_h 0.0244, **zero silver**, cooling score **68.9 — the highest of any candidate
in the project.** Its sheet resistance and emissivity are the best numbers the
framework has produced. T_vis 0.716 still misses 0.80, but the deficit narrowed
from 12 points to 8, and the dielectric search was coarse (11–15 nm steps).

**Triple-metal is now expressible and untested.**

## 3.5 The dilute-Ti ternary is predicted to underperform

The brief proposes Ag₇₀Cu₂₉Ti₁ on the hypothesis that dilute Ti stabilises the
layer. It scores **13th of 14** in the original set.

Titanium's bulk resistivity is 42 µΩ·cm, ~26× silver's, so even 1 at.% raises
alloy resistivity enough to cost sheet resistance (7.55 Ω/sq, worst in the set)
and emissivity (0.0921, also worst). The interface benefit may be real but is
not free, and the penalty is weighting-independent.

**A Ti barrier layer is still the better experiment** — it isolates the
interfacial effect without putting Ti in the conduction path, which is what
industrial coatings do. But it is **not a silver-reduction candidate**: it uses
a full pure-silver layer and ranks last once silver is weighted. Keep the two
claims apart.

## 3.6 Where the model disagrees with literature

| Benchmark | Metric | Reported | Modelled | Error | Source |
|---|---|---|---|---|---|
| AZO/Ag(13)/AZO | far-IR R | 0.960 | 0.964 | **0.4%** | partial |
| AZO/Ag(10)/AZO | T_vis | 0.805 | 0.870 | 8.1% | partial |
| AZO/Ag(13)/AZO | R_s | 4.36 | 2.84 | 34.8% | partial |
| AZO/Cu/AZO (2022) | ε | 0.055 | 0.0405 | 26.4% | partial |
| AZO/Cu/AZO (2022) | R_s | 9.96 | 2.86 | **71.3%** | partial |
| AZO/Cu(15)/AZO | R_s | 16.6 | 2.10 | **87.3%** | partial |

Median 30.6% excluding disputed entries. The silver stacks are reproduced well
in the infrared, which is what the model is built to get right.

**The copper failures are the substantive result.** The model under-predicts Cu
sheet resistance by ~8×, and the classical size effect cannot account for that.
It points to something the model does not contain: oxygen incorporation during
deposition, native oxide at the interfaces, or much poorer grain structure than
silver on the same oxide.

If that reading is right, **the obstacle to the copper route is film quality,
not intrinsic physics** — an engineering problem (base vacuum, seed layers,
getter, substrate temperature) rather than a fundamental limit. That is far more
tractable than replacing silver's electronic structure, and it now gates most of
the leading candidates.

---

# 3.7 Thermodynamic screening: Ag-Cu has no stable ordered compound

All 15 chemical systems from the brief's section 9 retrieved from the Materials
Project. Screened at 50 meV/atom of the convex hull.

**Ag-Cu is the only nominated binary with no stable intermediate phase.** Cu3Ag
sits 0.0904 eV/atom above the hull and CuAg3 0.0857 -- both well above k_BT at
deposition (26 meV at 300 K, 48 meV at 550 K). The system wants to separate, and
the driving force is substantial.

This is an equilibrium statement. A sputtered film is quenched from the vapour
and can trap a metastable solution, so it does not predict the as-deposited
state -- it predicts the direction of change on annealing. Resistivity should
*fall* as Cu precipitates. That is the signature to look for in section 6.3's
experiment, and it gives thermodynamic support to the segregated model under
which section 3.1's dilute-Ag optimum is strongest.

**A second finding, bearing on the Ti hypothesis.** Cu-Ti has 8 near-hull
phases and Al-Cu has 10. A dilute Ti or Al addition to a Cu-bearing film has
stable intermetallics available to form, so on annealing it is more likely to
precipitate than to remain in solution acting as a stabiliser. That is a
mechanism for the ternary underperforming beyond the Nordheim conductivity
penalty in section 3.5.

**Ag-Cu-O has 4 near-hull phases** including CuAgO2 -- relevant to durability,
since an oxidising Ag-Cu film has stable ternary oxides available rather than
just a mixture of Ag2O and CuO.

---

# 3.8 Mixing energies confirm the dilute corner is thermodynamically favoured

MACE-MP-0 on 32-site fcc supercells, gated against two Materials Project DFT
results (errors 19-34 meV/atom, both under-predicting). Full account in
`docs/MLIP_MIXING_ENERGY.md`.

The Ag-Cu mixing energy is positive across the whole range and fits a
regular-solution form to +/-6 meV/atom:

    dE_mix = 0.287 * x * (1 - x)   eV/atom

**A compounded correction, from verifying the brief's own citation.** The
brief's claim 7 -- that GGA underestimates Cu-alloy formation energies -- is now
supported with a magnitude: npj Comput. Mater. (2024) puts GGA's error on
Cu-transition-metal intermetallics at nearly 40% too small, caused by Cu-3d
bands sitting too shallow. The Materials Project hull is GGA/GGA+U, and both
MLIPs are trained on it, so there are two errors in series and both in the same
direction. The upward correction to dE_mix is therefore larger than the MLIP
gate alone implies. That **strengthens** the conclusion below at 5-10 at.% Ag
and makes it **marginal at 15%**, where a compounded correction approaching 2x
would bring the driving force above kT.

**Cross-checked against CHGNet.** Both models under-predict the known hull
distances (MACE by 0.026 eV/atom, CHGNet by 0.047), so the bias is inherited
from the shared Materials Project training data rather than specific to one
architecture -- which means dE_mix should be corrected upward, not read as a
lower bound. The between-model spread is 0.0112 eV/atom against a margin of
0.0216 at Ag 10%, so the conclusion below holds under both models and under
the correction. Caveat: CHGNet and MACE-MP-0 share training trajectories, so
agreement shows the bias is consistent, not absent.

**This extends section 3.7 from ordered compounds to the disordered solid
solution** a sputtered film might actually be. It also self-checks: at Ag 25%
the surrogate puts the disordered solution 13 meV/atom BELOW the ordered Cu3Ag
compound, so there is no ordering tendency -- which is what an empty convex
hull implies, reached independently.

**The finding that matters:** in the dilute-silver corner the driving force to
separate falls below thermal energy at deposition.

| Ag at.% | dE_mix | x kT (550 K) |
|---|---|---|
| 70 (brief's priority) | 0.0602 | 1.27 |
| 50 | 0.0717 | 1.51 |
| 15 | 0.0366 | 0.77 |
| 10 | 0.0258 | 0.54 |
| 5 | 0.0136 | 0.29 |

Section 3.1 found the two microstructure hypotheses converge at 5-15% Ag --
2.5 score points apart against 9-14 at Ag70Cu30 -- and treated that as
robustness. **The thermodynamics now supply the reason:** there is barely any
driving force to segregate there, so the film is far more likely to stay as
deposited.

The dilute-silver optimum is therefore favoured on three independent grounds:
lowest silver consumption, best score under the corrected weighting, and the
weakest tendency to phase-separate.

Note also that even at the 50:50 peak the driving force is only ~1.5 kT at
550 K. That is modest enough that a quenched sputtered film could plausibly
trap a metastable solution, so **both microstructure hypotheses remain
viable** -- which retrospectively justifies modelling both.

## 3.9 Adatom wetting cannot resolve the dielectric question

> **This section replaces an earlier version that claimed the opposite.** That
> version reported the model reproducing the measured ordering among the
> oxides. A subsequent termination sweep showed the claim was an artifact.

`dE_wet = E(slab + adatom) - E(slab) - E_bulk` decides whether an arriving atom
prefers the oxide or its own metal. Six placements per surface.

**The disqualifying result.** ZnO(0001) is polar and has two terminations. For
a silver adatom they give:

| termination | dE_wet | regime |
|---|---|---|
| Zn face | **+0.696** | islanding |
| O face | **-1.399** | wetting |

**A range of 2.095 eV, against 0.457 eV separating all six dielectrics tested.**
The choice of which face to model dominates the material comparison by a factor
of 4.6, and the first run silently took whichever slab the generator returned.

The earlier claim that AZO ranked best among oxides was therefore resolving
slab index, not material. It is withdrawn.

**Why this cannot be fixed by picking the right face.** Which termination a
real sputtered film presents depends on deposition conditions -- oxygen partial
pressure, substrate temperature, growth rate -- and is itself an experimental
question. There is no principled way to choose one without the measurement the
calculation was meant to substitute for.

**What survives.** One thing, and it is worth keeping: every oxide on its
Zn-equivalent termination gives islanding, +0.70 to +1.31 eV. Silver and copper
islanding on oxides is independently known -- it is why percolation thresholds
exist at 10-11 nm and why section 2 needs a percolation model at all. The
surrogate reproduces that regime without being told, which is a real if modest
validation of the method.

**What it means for `metal_growth_factor`.** The parameter stays empirical,
calibrated against Cueva & Carretero's measured series and reproducing it to
4-8%. Two computational attempts at a mechanism have now failed for different
reasons -- bulk adhesion on lattice mismatch, adatom wetting on termination
sensitivity -- and both failures are documented with the diagnostic that caught
them. That is the honest state.

**The mechanism the authors themselves propose is untestable this way.**
Carretero attribute the AZO advantage to it crystallising uniformly and
templating silver growth. Templating is lattice registry between layers; a
single adatom has no registry, and a strained interface measures elastic energy.
Neither method used here could have found it.

## 3.10 The nucleation mechanism, resolved from literature

Two surrogate calculations failed to find the mechanism behind
`metal_growth_factor`. A literature search found it, with direct experimental
evidence. Full account in `docs/NUCLEATION_MECHANISM.md`.

**US 7,632,572 / 8,512,883** (AFG Industries / AGC Flat Glass North America,
now Cardinal CG; full text read, `verified: true`) deposited 16 nm Ag on
a-TiOx and on a 5 nm ZnO seed over a-TiOx in the same study. Grains of 25 nm on
ZnO against 15 nm on a-TiOx, {111}-oriented grains two to three times larger on
ZnO, and the film on the bare amorphous underlayer **clearly discontinuous**
where the ZnO-seeded film was continuous everywhere.

*(An earlier version of this section attributed the patent to Guardian
Industries. Wrong assignee -- Guardian appears in the citation list, not on
the patent.)*

**The inventors state the mechanism themselves:** ZnO grows {0001}, which
orients Ag to grow {111}, and the epitaxial lattice match between Ag{111} and
ZnO{0001} lowers sheet resistance and improves adhesion. Templating, named by
the people who measured it.

**And the full text validates the framework quantitatively.** The patent
reports four-point sheet resistance on the two underlayers: **5.68 ohm/sq with
the ZnO seed against 7.56 without**, a ratio of **1.331**.
`metal_growth_factor` was calibrated independently -- Carretero's emissivity
series, different group, different decade, different measured quantity -- and
gives a TiO2:AZO ratio of **1.250**. The two agree to **6%**. That is the
first independent validation of a parameter fitted to one dataset reproducing
another it never saw.

Caveat: the patent contrasts ZnO-on-a-TiOx against a-TiOx alone, so 1.331 is
the effect of adding a 5 nm seed rather than of ZnO versus TiO2 as bulk
dielectrics. Close agreement, partly fortuitous.

**A percolation datum too.** The patent claims continuous, strongly adherent Ag
**down to 8 nm** on a ZnO seed, against the framework's assumed 10 nm critical
thickness -- a 20% difference affecting every silver-consumption figure, and
one more thing the section 6.2 XRD session could settle.

**Industrial practice answers the nitride case.** Silicon nitride Low-E stacks
use thin NiCr barrier layers specifically to increase adhesion between nitride
and silver -- a nucleation layer is required because silver adheres poorly to
nitride directly. The opposite of what the surrogate predicted from a
crystalline proxy.

**The framework's grain assumption was accidentally right, for AZO.**
`grain_size_ratio` defaults to 3.0, i.e. 30 nm grains in a 10 nm film, against
the 25 nm measured on ZnO. Within 20%.

**And this is the same physics as the copper discrepancy.** Section 3.6 and
`docs/LITERATURE_CALIBRATION.md` concluded that nanocrystalline grain structure
explains the 8x under-prediction of sputtered Cu sheet resistance. The patent
shows the underlayer determines metal grain size. So `metal_growth_factor` and
the copper grain-size hypothesis are **one effect appearing twice** --
underlayer-dependent metal microstructure -- and the framework's structural
weakness is modelling the metal as though the layer beneath it did not shape
its grains.

**Consequence for the experiment.** One XRD scan measures both: Ag(111) or
Cu(111) texture answers the templating question, Scherrer width gives the
grain size for that underlayer. Section 6.2's scan should record the metal
reflections, not only the film thickness.

---

# 4. Limitations

## 4.1 What the framework does not predict

`not_predicted()` is the machine-readable list. Deposition rate without
calibration, adhesion, roughness, interdiffusion, agglomeration kinetics,
damp-heat and abrasion durability, and any property of a metastable sputtered
alloy that a 0 K ordered-crystal database cannot supply.

## 4.2 What is calibrated, and to what

| Parameter | Calibrated to |
|---|---|
| Glass far-IR oscillator scale | bare-glass ε_n = 0.837 |
| TCO band-edge strength | n(550 nm) = preset value |
| Ag percolation d_c = 10 nm | literature, XRD-confirmed |
| Cu percolation d_c = 11 nm | literature, unconfirmed |
| Drude damping | metal DC resistivity |
| Specularity, grain-boundary reflection | **fitted, not measured** |

## 4.3 Known weak points

- **Si₃N₄ and TiO₂ are `ESTIMATE` grade** — indices from typical sputtered
  values, phonon parameters order-of-magnitude.
- **D65 and AM1.5 are Planckian approximations**, flagged `MODEL`. Supply
  tabulated spectra via `Weighting.from_csv()` for standards-grade work.
- **Visible-range metal optics are good to a few per cent at best.** Far-IR is
  reliable (pure Drude, pinned to resistivity); the visible is not.
- **No roughness, no interdiffusion, no barrier absorption.** A real stack will
  transmit slightly less than predicted.
- **Reactive Si₃N₄ sputtering is harder than AZO** — target poisoning, slow
  deposition. The brief's §15 deposition-efficiency criterion would penalise it
  and the framework cannot score that without a calibrated rate model.

## 4.4 Scores are not portable

Absolute scores moved by ~25 points as the §2 defects were fixed. **A score is
not a property of a material** — 89.3 is a fact about Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ under
one weighting of eight criteria, three of which the framework cannot populate.
Quote the ordering, attach `targets.yaml`, and say what is unverified.

---

# 5. Corrections

Conclusions stated earlier in this project that later work overturned. Kept
because the pattern is instructive.

## 5.1 There is no optimum at Ag₆₀Cu₄₀

Reported as a local optimum on the evidence that it scored above both Ag₇₀Cu₃₀
and Ag₅₀Cu₅₀. A three-point artifact. At 5% resolution the curve rises
monotonically as silver falls, with no feature at 60%.

## 5.2 The Ti barrier variant does not beat the ternary

Reported as B1 (81.9) beating T1 (75.9), with a recommendation to test the
barrier first as a silver-reduction route. That ranking was an artifact of
silver carrying zero weight (§2.1). Corrected, B1 ranks **last**. The barrier is
still the better *interface* experiment; it is not a silver-reduction candidate.

## 5.3 The band-emissometer explanation is wrong

Proposed that the Xi'an group's low emissivities might be 8–14 µm
band-emissometer values, which would read lower than full-band EN 12898 because
metal reflectance rises with wavelength. `band_emissivity()` was added to test
it. **The band value reads 5–8% *higher*:**

| Stack | full-band (283 K) | 8–14 µm | ratio |
|---|---|---|---|
| AZO/Cu(12)/AZO | 0.0405 | 0.0437 | 1.079 |
| AZO/Ag(10)/AZO | 0.0518 | 0.0545 | 1.052 |

A Drude metal's reflectance is nearly flat across 5–14 µm and the 283 K Planck
weight already peaks near 10 µm, so the restricted band merely drops the 5–8 µm
tail where these stacks reflect slightly worse. Correcting for basis makes the
discrepancy **worse** (0.58 → 0.53).

## 5.4 An earlier cooling-profile series was an artifact

A composition series showed cooling scores jumping erratically (50.4, 38.2,
37.8, 40.5, 25.6, 43.6 across adjacent compositions). Those geometries had been
optimised against the *heating* objective and then scored under cooling; the
g-value swings hard with oxide thickness, so adjacent compositions landed on
geometries with very different solar gain. Re-run properly, the series is
smooth (50.5 → 67.6 monotonically).

`composition_series` now records which scheme it optimised against.
**Rule: optimise against the objective you intend to report.**

## 5.5 The common cause

Three of these four are the same error: **reading structure into too few
points** — three compositions in one case, one geometry per composition in
another, one instrument hypothesis untested in a third. The framework's value
came largely from re-running things at finer resolution and finding earlier
conclusions dissolve.

---

# 6. Recommended next steps

## 6.1 Highest value: one measurement

**A copper thickness series, 8–20 nm, four-point-probe R_s.** The model
under-predicts sputtered Cu sheet resistance by ~8×. Most leading candidates in
both climate profiles depend on that being model error rather than film quality.
Until it is measured, §3.4's 1.33 Ω/sq is the most optimistic claim in this
document.

## 6.2 Highest value on paper: one line of full text

The **hemispherical-vs-normal basis** in the *Applied Surface Science* 2022
paper. If their ε is not the quantity EN 12898 defines, the brief's §16
conclusion needs restating rather than discarding — and that restatement would
apply to much of the Low-E emissivity literature.

## 6.3 The experiment that settles the most

**One AZO/Ag₇₀Cu₃₀/AZO film at 10 nm, R_s measured.** The two microstructure
hypotheses predict 6.4 vs 2.6 Ω/sq — far outside probe resolution. Confirm with
XRD (one fcc peak set vs two) and anneal at 200/300/400 °C: a metastable solid
solution should show resistivity *falling* as Cu precipitates.

Better still, measure R_s across Ag 0, 25, 50, 75% — the *curve shape* is
diagnostic. Segregated predicts flat ~3 Ω/sq; mixed predicts a Nordheim hump
peaking above 7.

## 6.4 Design work still available

- **Finer optimisation of the double-Cu stack** — asymmetric outers, mixed-metal
  pairing, finer dielectric steps. The transmittance gap is 8 points.
- **Triple-metal search**, now expressible.
- **Measured n and k** for your own AZO, Si₃N₄ and metal films — the largest
  single source of visible-range error.

## 6.5 First deposition run

**Si₃N₄/Cu/Si₃N₄ at 60/12/50 nm against an AZO/Ag/AZO control**, measured for
T_vis, four-point-probe R_s and FTIR emissivity. One comparison tests the
dielectric hypothesis, the copper film-quality question and the silver-free
premise together.

For a cooling-dominated application, add **AZO/Cu/AZO at 45/12/45** — the lead
candidate under that profile.

---

# Appendix A — What changed relative to the brief

| Brief's position | Finding |
|---|---|
| Ag₇₀Cu₃₀ is the priority composition | beaten under all eight weighting/model/dielectric combinations; optimum is 5–15% Ag (§3.1) |
| AZO is the dielectric | Si₃N₄ better for transmittance; AZO better for solar control (§3.2, §3.3) |
| Dilute Ti may stabilise the layer | predicted to cost conductivity; ranks near last (§3.5) |
| §14 weighting as tabulated | four defects, all changing the ranking (§2) |
| §16: Ag-free may already suffice | rests on a physically inconsistent measurement (§1.2) |
| §7: Ag–Cu retains good conductivity | comparison baseline is not like-for-like (§1.3) |
| Single DMD architecture | cannot reach solar-control performance at any composition (§3.4) |
| Climate not specified | reverses the ranking (§3.3) |

# Appendix B — Reproducing every number

```bash
pvdlowe validate                                    # §1, §3.6
pvdlowe provenance                                  # §1, §4.1
pvdlowe check-weights                               # §2
pvdlowe evaluate                                    # §3, heating
pvdlowe evaluate --targets data/targets_cooling.yaml  # §3.3, cooling
pvdlowe series --dielectric Si3N4 --mixing ema      # §3.1
pvdlowe optimise --metal Ag                         # §2.3
pvdlowe report -o report.md                         # full tables
python tests/run_tests.py                           # 82 tests
```

Results archived in `results/`. Weighting profiles in `data/targets.yaml` and
`data/targets_cooling.yaml` — **a results table without its weighting file is
uninterpretable.**
