# Findings

What the framework found when it was pointed at the brief's own numbers.
These are the results worth discussing in a review; everything else in the
package is machinery to produce them.

> **Scores in this document are from the corrected weighting in
> `data/targets.yaml`, not the brief's section 14 as written.** Four defects in
> the literal encoding of section 14 had to be fixed before the scores meant
> anything; section 3 below documents them. Absolute scores are only
> comparable *within* one weighting — always read a results table with its
> `targets.yaml` attached. Rankings are stable; the numbers are not portable.

---

## 0. Alloying with copper saves far less silver than the composition suggests

The brief's central question is how much silver can be removed. Running it
properly — for each composition, the thinnest metal layer that still meets
T_vis ≥ 0.80, R_s ≤ 5 Ω/sq and ε ≤ 0.10, with the oxides re-optimised at
every thickness — gives this:

| Composition | t_metal (nm) | T_vis | R_s | ε_h | Ag (g/m²) | **Ag saved** |
|---|---|---|---|---|---|---|
| Ag | 10.05 | 0.880 | 4.20 | 0.060 | 0.1054 | — |
| Ag₉₀Cu₁₀ | 10.30 | 0.862 | 5.00 | 0.068 | 0.1004 | **4.7%** |
| Ag₈₀Cu₂₀ | 11.27 | 0.839 | 4.99 | 0.068 | 0.1008 | **4.4%** |
| Ag₇₀Cu₃₀ | 11.98 | 0.818 | 4.99 | 0.067 | 0.0970 | **8.0%** |
| Ag₅₀Cu₅₀ | 12.48 | 0.789 | 4.99 | 0.067 | 0.0775 | fails T_vis |
| Ag₂₅Cu₇₅ | 11.21 | 0.783 | 4.99 | 0.070 | 0.0383 | fails T_vis |
| Cu | 11.01 | 0.769 | 3.19 | 0.054 | 0 | fails T_vis |

**Ag₇₀Cu₃₀ removes 30% of the silver from the composition but only 8% from
the coating.** The reason is that copper's higher resistivity forces a
thicker layer to reach the same sheet resistance — 11.98 nm against 10.05 —
and a thicker layer of a 70% silver alloy contains almost as much silver as a
thin layer of pure silver. The nominal saving is largely eaten by the
thickness compensation.

This is not visible from a fixed-thickness comparison, which is how the
brief's candidate matrix is set up. At a fixed 10 nm, Ag₇₀Cu₃₀ appears to
save 23% of the silver — but that film does not meet the sheet-resistance
target, so the comparison is not like-for-like.

Everything at or below 50% silver fails the visible-transmittance target once
it is made thick enough to conduct. Notably, **pure Cu conducts and reflects
well** (3.19 Ω/sq, ε 0.054 at 11 nm) — it fails only on transmittance
(0.769 against 0.80). That is consistent with the brief's own instinct that
copper deserves attention, and it localises the problem precisely: the Cu
route needs better antireflection or a thinner continuous film, not better
conductivity.

**Implication for the programme.** If the objective is genuinely to reduce
silver consumption, dilute Ag–Cu alloying is a weak lever. The stronger
levers are (a) lowering the percolation threshold so a thinner continuous
film is possible — seed layers, wetting layers, deposition temperature —
and (b) improving the antireflection design so a Cu-rich or Cu-only stack
can clear 0.80. Both are process questions rather than composition
questions.

Caveat: these are model outputs on uncalibrated percolation and size-effect
parameters, and the ranking of compositions is more trustworthy than the
absolute thicknesses. Phase 1 of the roadmap fixes that.

## 1. The AZO/Cu/AZO result: source located, and the discrepancy survives

**Source found.** *Preparation of AZO/Cu/AZO films with low infrared
emissivity, high conductivity and high transmittance by adjusting the AZO
layer*, Applied Surface Science **578** (2022) 152051, from Xi'an University of
Architecture and Technology. The brief's transcription is accurate.

The abstract also settles the question I could not settle before: **all three
values come from the same sample** — the variant with 40 nm AZO layers, which
the authors identify as simultaneously lowest in sheet resistance, lowest in
emissivity and high in transmittance. That eliminates the "measured on
different films" explanation.

So the physical objection stands. For a conducting sheet thin compared with the
wavelength, far-infrared reflectance is fixed by sheet resistance alone:

```
r = (n₁ − n₂ − Z₀/R_s) / (n₁ + n₂ + Z₀/R_s),    ε = 1 − r²
```

At 9.96 Ω/sq this gives **ε ≥ 0.096**. The reported 0.055 is 0.58× that limit
and would require about 5.5 Ω/sq. The result is robust to the far-IR glass
index, which is the only free parameter in it:

| n_glass | 1.5 | 2.0 | 2.5 | 3.0 | 4.0 |
|---|---|---|---|---|---|
| limit at 9.96 Ω/sq | 0.097 | 0.096 | 0.095 | 0.093 | 0.091 |

**And it is a pattern, not a single point.** The same group's later work reports
ε = 0.045 at 8.10 Ω/sq for AZO/Ti/Cu/AZO (*Ceramics International*, 2023), and
ε = 0.050 at similar sheet resistance for an aged film. Against the limit:

| Report | R_s (Ω/sq) | ε reported | limit | ratio | R_s implied by ε |
|---|---|---|---|---|---|
| AZO/Cu/AZO, ApSS 2022 | 9.96 | 0.055 | 0.096 | 0.58 | 5.5 |
| AZO/Ti/Cu/AZO, Ceram. Int. 2023 | 8.10 | 0.045 | 0.079 | 0.57 | 4.4 |
| aged film, follow-up | 8.10 | 0.050 | 0.079 | 0.63 | 5.0 |

Three independent measurements, all landing at 0.57–0.63 of the limit. A
consistent factor is the signature of a systematic effect, not of error.

**What remains unresolved, and it is now the only candidate explanation:** the
measurement basis. Emissometers of the type common in this literature report a
band-limited quantity — often 8–14 µm — rather than the full 283 K
Planck-weighted normal emissivity that EN 12898 defines and that this framework
computes. A metal's reflectance rises with wavelength, so a value averaged over
8–14 µm will read lower than one weighted across the full thermal band. That
could plausibly account for a consistent factor near 0.6.

**This does not invalidate the papers.** It means their ε and this framework's ε
may be different quantities, and comparing them directly — as the brief does
when it concludes an Ag-free stack meets a Low-E target — may be comparing
unlike things. **Before section 16's conclusion is used, establish which
emissivity the target refers to.** That needs the full text, specifically the
instrument and band. Institutional access required; I could not read it.

## 2. Section 7's silver resistivity: my proposed explanation was wrong, and the problem is worse

**Source found.** *Ag–Cu amorphous alloy thin-films with unusually high
electrical conductivity* (2025), from a University of North Texas group, with
related patents US 10,822,692 and US 11,840,756. The brief's transcription is
accurate.

An earlier version of this document proposed that the 1.59 µΩ·cm silver value
was a **bulk reference tabulated alongside measured values**, and recommended
checking that. **That hypothesis is wrong.** The abstract states the pure Ag and
Cu films were *deposited under identical conditions for comparison* at the same
nominal thickness. 1.59 µΩ·cm is claimed as a measurement of a 10 nm film.

That makes the objection stronger, not weaker:

| Film | Reported | × bulk | FS–MS model predicts |
|---|---|---|---|
| Ag, 10 nm | 1.59 µΩ·cm | **1.00×** | 4.44 µΩ·cm (2.79×) |
| Cu, 10 nm | 20.5 µΩ·cm | 12.2× | 7.11 µΩ·cm (4.23×) |

Under *identical* deposition, their copper shows a strong size effect and their
silver shows none at all. Silver's electron mean free path is 53 nm, so a 10 nm
film is deep in the Fuchs–Sondheimer regime; reaching bulk resistivity would
require essentially specular surfaces and no grain boundaries.

Nor does thickness uncertainty rescue it. The paper states 10 ± 2.5 nm, and
since ρ = R_s·t that propagates directly: ρ_Ag lies between 1.19 and
1.99 µΩ·cm across the stated range. **Even the upper bound is 1.25× bulk,
against a model floor near 3×.**

Two readings are possible and the paper cannot distinguish them from the
abstract alone. Either the silver film genuinely is extraordinary — which would
itself be the headline result, and is not what the paper claims to be about —
or the silver row is not a like-for-like measurement.

**Why this matters for the brief.** Section 7 uses this table to argue that
amorphous Ag–Cu "retains unusually good conductivity", by comparing 2.97
against 1.59. If the silver baseline is not comparable, that comparison does
not support the claim, and the Ag–Cu figure should be read against the
copper value (20.5) instead — where the alloy looks genuinely impressive,
seven times better, and the argument survives in a different form.

Note also that the associated patent transcribes the same value as
"2.97×10⁶ Ohm-cm", twelve orders of magnitude off. The number has been carried
inconsistently across documents, which is its own reason to go to the source.

## 3. The section 14 weighting has four defects, and all four changed the answer

Encoding the brief's section 14 table literally produced a scoring scheme that
did not measure what the project is for. Each of these was found by running the
framework against its own diagnostics, and each is now a documented decision in
`data/targets.yaml` rather than an accident.

**(a) Silver consumption carried zero weight.** Section 14's table has no
silver line, although sections 17 and 20 both name minimising Ag as an
objective. So `Ag_g_per_m2` was computed, displayed, reported as the limiting
criterion — and contributed nothing to the score. The thickness optimiser
exploited this immediately, returning a 12.84 nm design using **0.135 g/m² of
silver, 29% more than the benchmark, at a perfect 100/100.** Corrected to
weight 0.15.

**(b) Emissivity and sheet resistance double-count one property.** They
correlate at **r = 0.996** across the candidate set — both are the free-carrier
response of the same layer — so section 14's 0.25 + 0.15 put 0.40 of the total
weight on one physical quantity. `R_sheet` is now weighted 0.0 and reported as
a constraint to check rather than an independent objective. Restore it (and cut
emissivity to 0.15) if the coating must also serve as a transparent electrode.

The same check flags cost against supply risk (r = 0.993) and silver mass
against cost (r = 1.000 — silver dominates metal cost so completely they are
the same number in different units).

**(c) Targets were set at the specification minimum, so criteria saturated.**
Derringer–Suich desirability clamps at 1.0 once the target is reached. Setting
`T_vis` target to 0.80 — the brief's *floor of acceptability* — meant the
criterion went flat exactly where candidates start to differ. The optimiser
duly satisficed: it returned T_vis = 0.800 and walked the oxides to a 15 nm top
layer, because above 0.80 transmittance was free and thinner oxides marginally
help emissivity. Across 181 oxide pairs clearing 0.80, T_vis spanned
0.800–0.881 while the **score went down**, 74.99 to 73.30.

Targets are now aspirations: `T_vis` 0.90, `emissivity_hemispherical` 0.02,
both slightly beyond what a single silver layer reaches, so the criteria keep
discriminating. Re-optimising gave AZO 25 / Ag 10.0 / AZO 35 nm at T_vis 0.880
— eight points better than the saturated version, on identical silver.

**(d) The supply-risk floor was too tight to discriminate.** At floor 8.0
against candidate values of 4.5–7.5, every silver-bearing composition scored
desirability 0.1–0.28 and `supply_risk` was reported as limiting for 12 of 14
candidates. Widened to floor 9.5 / target 4.0, which still zeroes
indium-bearing ITO — the point of the criterion — while letting Ag-versus-Cu
differences register.

**A caution on reading `limiting_criterion`.** It is `argmin(desirability)`:
where a candidate is *weakest*, not what drives the ordering. Under a geometric
mean whichever criterion sits nearest its floor is reported as limiting for
everyone, which looks alarming and usually is not. The real test of whether the
weights do any work is `sensitivity_to_weights`. Before these fixes one
candidate won 97.5% of randomised weightings with rank_std 0.16 — not
robustness, but weights having no effect. Now the top two genuinely compete at
62% and 38%.

## 4. A weighted sum does not achieve what the brief wants from it

The brief states the purpose of its weighting explicitly:

> This prevents a material from "winning" simply because it has excellent
> conductivity while being unacceptable optically or economically.

A weighted arithmetic sum does not do this. A candidate scoring zero on one
criterion loses only that criterion's weight and can still win overall. A
**geometric** mean of desirabilities does do it — one zero drives the whole
score to zero.

The difference is not academic here. Under the corrected weighting the pure-Ag
benchmark ranks **4th under arithmetic aggregation and 7th under geometric** —
its excellent transmittance partly offsets its silver consumption in a weighted
sum, and cannot in a product. Pure Cu shows the mirror image, 1st arithmetic
and 2nd geometric: its zero silver cannot fully compensate a T_vis of 0.738
once one weak criterion drags the whole product down. Those are the two
candidates where the choice of aggregation matters most, and they are precisely
the two the brief cares about comparing.

The framework defaults to geometric and reports both, with rank shifts, via
`pvdlowe check-weights`.

## 5. The two Ag–Cu microstructure hypotheses are experimentally distinguishable

The brief is right that a sputtered Ag–Cu film may be either a metastable
solid solution or a segregated Ag-rich/Cu-rich nanocomposite, and that this
is unresolved. The framework implements both and finds they predict
measurably different films:

| Composition | R_s solid solution | R_s segregated | ΔR_s |
|---|---|---|---|
| Ag₉₀Cu₁₀ | 5.18 | 3.18 | −2.00 |
| Ag₈₀Cu₂₀ | 5.89 | 2.81 | −3.08 |
| Ag₇₀Cu₃₀ | 6.36 | 2.63 | −3.73 |
| Ag₅₀Cu₅₀ | 6.68 | 2.50 | −4.18 |

A 3–4 Ω/sq difference is far outside four-point-probe resolution. **A single
sheet-resistance measurement on one Ag₇₀Cu₃₀ film distinguishes the two
hypotheses** — no TEM required for the first-order answer. The transmittance
difference is smaller (0.5–0.8 percentage points) but also measurable.

The consequence for the candidate table is large. The same composition at the
same thickness scores **71.5 as segregated (M3ema, 1st place) and 64.4 as a
metastable solid solution (M3, 9th)** — a seven-point spread and eight rank
positions, from an assumption rather than a measurement. The top-ranked
candidate in the whole set sits on the optimistic side of an unresolved
question, which is reason enough to resolve it before anything else.

This converts the brief's section 5 caveat from a discussion point into a
cheap, decisive experiment. It should be run early, because almost every
downstream prediction depends on which answer it gives.

## 6. The dilute-Ti ternary is predicted to underperform — but the barrier variant is not a silver-reduction candidate either

The brief proposes Ag₇₀Cu₂₉Ti₁ as a high-novelty candidate, on the hypothesis that
dilute Ti stabilises the metal layer and suppresses Cu segregation. The
framework scores it **13th of 14**, at 61.5.

The mechanism is Nordheim scattering. Titanium's bulk resistivity is
42 µΩ·cm, roughly 26× silver's, so even at 1 at.% a solute that dissimilar
raises the alloy resistivity enough to cost both sheet resistance (7.55 Ω/sq,
the worst in the set) and emissivity (0.0921, also the worst). The hypothesised
interface benefit may well be real, but it is not free, and the conductivity
penalty is a weighting-independent prediction — T1 sits near the bottom under
every scoring variant tried.

**A correction to an earlier version of this document.** It previously reported
that the Ti *barrier-layer* variant B1 beat the ternary T1 (81.9 against 75.9)
and recommended testing the barrier first as a cheaper route to the same
hypothesis. Under the corrected weighting that reverses: **B1 now ranks last at
59.5, below T1.** The earlier result was an artifact of silver carrying zero
weight, as described in section 3(a). B1 uses a full pure-silver layer
(0.105 g/m²) and buys no transmittance over the benchmark, so once silver mass
is weighted at all it is the worst candidate in the set.

The two claims should be kept apart:

- **As a silver-reduction candidate, B1 is not competitive.** It reduces no
  silver. It should not appear in a table ranked on sustainability.
- **As a test of the interface hypothesis, a barrier layer is still the
  cheaper experiment.** It isolates the interfacial effect without putting Ti
  into the conduction path, which is also what industrial Low-E coatings
  actually do. That argument is about experimental design, not about score.

So: run the barrier variant to test whether the interface hypothesis holds,
and do not present it as a route to using less silver.

## 7. Transmittance and emissivity are controlled by different layers

Sweeping the AZO thickness at fixed 10 nm Ag:

- T_vis varies from **0.738 to 0.877** — a 14-point swing, with a sharp
  optimum near 40 nm.
- Normal emissivity varies from **0.049 to 0.059** — essentially flat.

At 10 µm a 40 nm oxide is λ/250 thick and optically invisible; the metal does
all the infrared work. This is the clearest demonstration in the framework of
the brief's own section 10 point that Low-E performance belongs to the
multilayer rather than to any single material — and it means the two design
problems can be separated: **choose the metal for emissivity and sheet
resistance, then tune the oxides purely for antireflection.**

## 8. Model validation against the transcribed benchmarks

| Benchmark | Metric | Reported | Modelled | Error |
|---|---|---|---|---|
| AZO/Ag(13)/AZO | far-IR R | 0.960 | 0.964 | 0.4% |
| AZO/Ag/AZO (2nd) | R_s | 3.21 | 3.20 | 0.3% |
| AZO/Ag/AZO (2nd) | far-IR R | 0.970 | 0.960 | 1.0% |
| AZO/Ag/AZO (2nd) | T_vis | 0.854 | 0.844 | 1.2% |
| AZO/Ag(10)/AZO | T_vis | 0.805 | 0.870 | 8.1% |
| AZO/Cu(15)/AZO | R_s | 16.6 | 2.10 | 87% |

Median relative error 14.7%. The silver stacks are reproduced well,
especially in the infrared, which is what the model is built to get right.

**The copper failures are the interesting ones.** The model under-predicts
copper sheet resistance by nearly an order of magnitude. The classical size
effect cannot account for that gap, which points to something the model does
not contain: oxygen incorporation during deposition, a native oxide at the
interfaces, or much poorer grain structure than silver on the same oxide.

If that reading is right it is a substantive result for the project's
direction. **The obstacle to the copper route may be film quality rather
than intrinsic physics** — which is an engineering problem (better base
vacuum, barrier layers, getter, deposition temperature) rather than a
fundamental limit. That is a far more tractable target than replacing
silver's electronic structure, and it deserves to be tested directly.

## 9. Current ranking

Under the corrected weighting. Regenerate with `pvdlowe evaluate`; the
companion `targets.yaml` is what makes these numbers interpretable.

| # | ID | Architecture | t (nm) | T_vis | ε_h | R_s | Ag (g/m²) | Score | Weakest at | Grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M3ema | AZO/Ag70Cu30/AZO (segregated) | 10.0 | 0.840 | 0.0462 | 2.63 | 0.081 | **71.5** | Ag_g_per_m2 | model |
| 2 | M6 | AZO/Cu/AZO (low-cost control) | 12.0 | 0.738 | 0.0463 | 2.87 | 0.000 | **69.6** | T_vis | lit. unverif. |
| 3 | S10 | ITO/Ag70Cu30/ITO | 10.0 | 0.852 | 0.0688 | 5.48 | 0.081 | **68.7** | Ag_g_per_m2 | model |
| 4 | M5 | AZO/Ag25Cu75/AZO | 10.0 | 0.784 | 0.0780 | 5.92 | 0.034 | **68.0** | T_vis | model |
| 5 | S9 | FTO/Ag70Cu30/FTO | 10.0 | 0.859 | 0.0814 | 6.48 | 0.081 | **67.0** | Ag_g_per_m2 | model |
| 6 | M4 | AZO/Ag50Cu50/AZO | 10.0 | 0.809 | 0.0844 | 6.68 | 0.062 | **65.3** | Ag_g_per_m2 | model |
| 7 | M0 | AZO/Ag/AZO (benchmark) | 10.0 | 0.876 | 0.0603 | 4.18 | 0.105 | **65.0** | Ag_g_per_m2 | lit. unverif. |
| 8 | M1 | AZO/Ag90Cu10/AZO | 10.0 | 0.860 | 0.0698 | 5.18 | 0.097 | **64.5** | Ag_g_per_m2 | model |
| 9 | M3 | AZO/Ag70Cu30/AZO | 10.0 | 0.832 | 0.0811 | 6.36 | 0.081 | **64.4** | Ag_g_per_m2 | model |
| 10 | M2 | AZO/Ag80Cu20/AZO | 10.0 | 0.846 | 0.0766 | 5.89 | 0.089 | **64.3** | Ag_g_per_m2 | model |
| 11 | S8 | GZO/Ag70Cu30/GZO | 10.0 | 0.827 | 0.0820 | 6.33 | 0.081 | **63.7** | Ag_g_per_m2 | model |
| 12 | T2 | AZO/Ag70Cu29Al1/AZO | 10.0 | 0.826 | 0.0821 | 6.47 | 0.081 | **63.7** | Ag_g_per_m2 | **hypothesis** |
| 13 | T1 | AZO/Ag70Cu29Ti1/AZO | 10.0 | 0.825 | 0.0921 | 7.55 | 0.081 | **61.5** | Ag_g_per_m2 | **hypothesis** |
| 14 | B1 | AZO/Ti(0.5)/Ag/Ti(0.5)/AZO | 10.0 | 0.816 | 0.0599 | 4.18 | 0.105 | **59.5** | Ag_g_per_m2 | model |

**What is stable across every weighting tried.** Absolute scores moved by about
25 points as the four defects in section 3 were fixed, but three conclusions did
not move at all:

- **M3ema and M6 are always in the top two.** Cu-rich and segregated-alloy
  stacks win under any weighting that takes silver consumption seriously.
- **T1 (Ti ternary) is always near the bottom.** The Nordheim conductivity
  penalty is real and weighting-independent.
- **The benchmark M0 never wins.** Which is the correct answer to the brief's
  question: pure silver is the thing to beat, and on a sustainability-weighted
  objective it does not win.

**What the top of the table depends on.** The leading three are separated by
3.5 points and every one of them rests on something unmeasured:

| Candidate | Depends on |
|---|---|
| M3ema | the microstructure question (section 5), unresolved |
| M6 | the Cu sheet-resistance discrepancy (section 8), 8× against literature |
| S10 | ITO, which the brief rules out on indium supply risk regardless of score |

So the defensible statement to a supervisor is: *Cu-rich stacks lead on this
weighting, and the two measurements that would confirm it — a Cu thickness
series and one Ag₇₀Cu₃₀ sheet-resistance reading — have not been made.* Those
are Roadmap Phases 1 and 2, about a week of tool time between them.

**Do not quote a score as a property of a material.** 71.5 is not a fact about
Ag₇₀Cu₃₀; it is a fact about Ag₇₀Cu₃₀ under one weighting of eight criteria,
three of which the framework cannot populate. Quote the ordering, attach the
weighting, and say what is unverified.

---

## 10. The dielectric was the binding constraint, not the metal

**This section supersedes the framing of sections 0 and 8.** Everything before it
held the dielectric fixed at AZO, which turns out to have been the limiting
choice all along.

### The search

58 metal systems — every pure metal with available optical constants (Ag, Cu,
Al, Au, Zn, Ni, Cr, Ti) plus ten binary families at five compositions each,
thickness optimised per system, AZO 35/35 fixed. **Exactly one met the full
specification: pure silver.** Copper came closest and failed only on visible
transmittance, 0.752 against 0.80.

That negative result is worth stating on its own: *no metal substitution alone
reaches the target, so the sustainability route is not a different metal.*

### Then the dielectric was allowed to vary

Adding Si₃N₄, TiO₂ and SnO₂ alongside AZO, with oxide thicknesses optimised per
combination, changes the conclusion completely:

| Metal | AZO | SnO₂ | TiO₂ | **Si₃N₄** |
|---|---|---|---|---|
| Cu | 0.755 | 0.795 | 0.786 | **0.845** |
| Cu₉₀Zn₁₀ | 0.772 | 0.808 | 0.780 | **0.836** |
| Cu₉₀Ag₁₀ | 0.786 | 0.821 | 0.782 | **0.852** |
| Ag₇₀Cu₃₀ | 0.837 | 0.869 | 0.835 | **0.912** |
| Ag | 0.880 | 0.902 | 0.868 | **0.923** |

Si₃N₄ buys **nine points of visible transmittance on copper** — precisely the gap
that was disqualifying it. Every metal improves, so this is a property of the
dielectric, not a copper-specific effect.

### The result

**Si₃N₄ (60 nm) / Cu (12 nm) / Si₃N₄ (50 nm) on soda-lime float glass**

| | modelled | target |
|---|---|---|
| T_vis | 0.847 | ≥ 0.80 |
| ε_h | 0.0422 | ≤ 0.10, stretch ≤ 0.05 |
| R_s | 3.00 Ω/sq | ≤ 5 |
| Ag | **0** | minimise |
| metal cost | ~$0.01/m² | vs $0.85 for the Ag benchmark |

Score 88.5 against the silver benchmark's 67.5. Its emissivity is *better* than
silver's 0.0567 — copper is the better far-infrared mirror at these
thicknesses, and was only ever losing on transmittance.

Two further silver-free or silver-lean options also clear the specification:

| Stack | T_vis | ε_h | R_s | Ag (g/m²) | score |
|---|---|---|---|---|---|
| Si₃N₄/Cu₉₀Zn₁₀/Si₃N₄ | 0.838 | 0.0548 | 4.11 | 0 | 84.8 |
| Si₃N₄/Cu₉₀Ag₁₀/Si₃N₄ | 0.852 | 0.0530 | 3.98 | 0.017 | 84.5 |

The last is a **6× silver reduction against the benchmark while exceeding it on
transmittance** — which is a far better answer to the brief's central question
than anything the Ag–Cu series produced (section 0 found only 8%).

### Why highest index does not win

TiO₂ has the highest index of the four (2.45 against Si₃N₄'s 2.02) and performs
*worse* than SnO₂. Antireflection around a metal is an index-*matching* problem,
not an index-*maximisation* problem, and 2.0 sits nearer the optimum for a metal
between air and glass. Worth recording because the intuitive choice is wrong.

### Lattice absorption checked, and it is negligible

Si₃N₄ absorbs near 11.7 µm (the Si–N stretch) and TiO₂ has strong phonons
throughout the thermal band, so both were modelled with far-infrared
oscillators. The penalty on the Cu stack is **+0.0007 in emissivity, 1.7%
relative**.

That is not luck. At 10 µm the copper layer reflects about 96% of the incident
field, so very little reaches the nitride to be absorbed. Lattice absorption in
the dielectric only matters when the metal is poor — which is when you have no
Low-E coating regardless. `test_phonon_penalty_is_small_behind_a_good_mirror`
holds this in place.

### Why this is plausible rather than a model artifact

Si₃N₄ is what industrial Low-E actually uses: dense, an excellent diffusion
barrier, and durable enough to survive tempering — which is the real reason AZO
struggles in production, quite apart from optics. The brief never considered it
because it began from the RSC periodic table and the Materials Project, both of
which point at oxides. **Nitrides fall outside that framing, and the framing was
the constraint.**

The pairing is also independently sensible: Si₃N₄ blocks the oxygen and moisture
ingress that is copper's dominant failure mode. That is precisely why the
combination is attractive, and why it does not appear in the AZO literature.

### Caveats, in order of seriousness

1. **The Cu sheet-resistance discrepancy still stands.** Validation shows the
   model under-predicting sputtered Cu R_s by roughly 8× against the one
   available literature point. If that gap is real film quality rather than
   model error, the 3.00 Ω/sq above is optimistic and this result weakens
   considerably. **This is now the highest-value experiment in the project.**
2. **Si₃N₄ and TiO₂ are `ESTIMATE` grade.** Indices set from typical sputtered
   values; phonon parameters are order-of-magnitude. Measured n and k would
   settle it.
3. **Reactive Si₃N₄ sputtering is harder than AZO.** A Si target in N₂/Ar needs
   process control against target poisoning, and deposits slowly. The brief's
   section 15 deposition-efficiency criterion would penalise it, and the
   framework cannot score that without a calibrated rate model.

### Revised first experiment

**Si₃N₄/Cu/Si₃N₄ at 60/12/50 nm, against an AZO/Ag/AZO control**, measured for
T_vis, four-point-probe R_s and FTIR emissivity. That single comparison tests
the dielectric hypothesis, the copper film-quality question and the silver-free
premise at once. It supersedes the Ag–Cu composition series as the priority.

---

## 11. Climate reverses the answer: the nitride result is Northern-European, not Indian

Sections 0-10 scored against `data/targets.yaml`, which follows the brief and
constrains transmittance, emissivity, sheet resistance, silver and cost. It says
nothing about **solar heat gain** — and that omission encodes a climate.

### The metric that was missing

    g = T_sol + N * A_sol          (EN 410 / ISO 9050, N = 0.36 for surface 2)
    LSG = T_vis / g

`g` is the solar heat gain coefficient: what gets transmitted plus the share of
what is absorbed that flows inward. `LSG` is daylight admitted per unit of solar
heat. In a heating-dominated climate a high `g` is an **asset** — admitted solar
energy offsets heating. In a cooling-dominated one it is a **liability**, since
every unit admitted is a unit the air conditioning must remove.

Both are now in `performance_summary`, and `data/targets_cooling.yaml` is a
second weighting profile that scores them.

### The ranking inverts

| Candidate | default score | rank | cooling score | rank | g | LSG |
|---|---|---|---|---|---|---|
| Si₃N₄/Cu/Si₃N₄ (N6) | **88.9** | 1 | 55.5 | **6** | 0.731 | 1.18 |
| Si₃N₄/Cu₉₀Zn₁₀/Si₃N₄ (N7) | 85.0 | 2 | 54.1 | 10 | 0.727 | 1.17 |
| Si₃N₄/Ag₇₀Cu₃₀ segregated (N3e) | 79.2 | 5 | 43.8 | **24 (last)** | 0.770 | 1.17 |
| **AZO/Cu/AZO (M6)** | 69.6 | 9 | **65.4** | **1** | 0.558 | 1.32 |
| AZO/Ag/AZO (M0) | 65.0 | 17 | 53.0 | 14 | 0.646 | 1.35 |

**The entire Si₃N₄ family collapses and AZO/Cu/AZO takes first place.** Section
10's recommendation is correct for Stockholm and wrong for Mumbai.

### Why — and it is a real physical mechanism, not a scoring artifact

AZO is not merely a dielectric. It is a *transparent conductive oxide*, and its
free carriers give it a screened plasma wavelength at **1.25 µm — inside the
solar band**. Si₃N₄ is a passive insulator, transparent throughout.

Absorption index k, and stack transmittance with the same 11 nm Cu layer:

| λ (nm) | 550 | 1200 | 1600 | 2000 | 2400 |
|---|---|---|---|---|---|
| k(AZO) | 0.031 | 0.155 | 0.729 | 1.587 | 2.240 |
| k(Si₃N₄) | 0.0008 | 0.0004 | 0.0005 | 0.0008 | 0.0012 |
| T, AZO stack | 0.771 | 0.240 | 0.115 | 0.068 | 0.046 |
| T, Si₃N₄ stack | 0.864 | 0.509 | 0.259 | 0.151 | 0.099 |

**The conductive oxide is doing solar-control work the nitride cannot.** Section
10 read AZO's near-infrared absorption purely as a transmittance penalty. Half
of it is a solar-control benefit that the default weighting had no way to see.

### What no candidate achieves

Best LSG in the whole 24-candidate set is **1.37** (ITO/Ag₇₀Cu₃₀/ITO). The
`targets_cooling.yaml` target of 1.80 is met by nothing, and that is deliberate:
commercial triple-silver solar-control glazings reach roughly 2.0, and **no
single-metal stack can.** Reaching genuine solar control needs two or three
metal layers with tuned interference between them, which is an architecture this
framework does not currently model.

That is the honest answer to "what is the best candidate for Indian
architectural glazing": *none of these, and the reason is architectural rather
than compositional.*

### What to do with this

- **Choose the profile before quoting a ranking.** `pvdlowe evaluate` for
  heating-dominated, `pvdlowe evaluate --targets data/targets_cooling.yaml` for
  cooling-dominated. A ranking without its profile is meaningless — the two
  disagree on the winner and on 23 of 24 positions.
- **For a Mumbai application, AZO/Cu/AZO is the lead candidate**, and it is
  silver-free and essentially free in materials. Its weakness is unchanged:
  T_vis 0.738, below the 0.80 target.
- **The real opportunity is a double-metal stack**, AZO/Cu/AZO/Cu/AZO, which
  could plausibly hold the NIR rejection while recovering visible
  transmittance. Supporting it needs `LowECoating` generalised beyond a single
  metal layer — a bounded piece of work and, on this evidence, the highest-value
  extension to the framework.

### A note on how this was found

The solar-gain gap was not in the brief, not in the framework, and not in the
first ten findings. It surfaced only because the `T_sol` and `selectivity`
columns were being computed and displayed even though nothing scored them —
someone reading the table noticed the nitride stacks had visibly worse
selectivity. **Compute and display more than you score.** An unscored column
costs almost nothing and is the only way a missing objective becomes visible.

---

## 12. The optimum is at 5-15% silver, not 70% — and two corrections

`pvdlowe series` now runs a full binary composition series with the geometry
re-optimised at every point, against a chosen weighting profile. Eight curves:
Ag 0-100% in 5% steps, both microstructure models, both dielectrics, both
climate profiles. 168 points.

### The optima

| profile | model | dielectric | optimum Ag | score | plateau | Ag (g/m²) |
|---|---|---|---|---|---|---|
| heating | segregated | Si₃N₄ | **0.05** | **89.3** | 0.00-0.20 | 0.0082 |
| heating | solid solution | Si₃N₄ | 0.00 | 88.9 | 0.00 | 0 |
| heating | segregated | AZO | **0.10** | 76.5 | 0.05-0.40 | 0.0131 |
| heating | solid solution | AZO | 0.00 | 74.4 | 0.00-0.05 | 0 |
| cooling | either | AZO | 0.00 | 68.2 | 0.00-0.15 | 0 |
| cooling | either | Si₃N₄ | 0.00 | 67.6 | 0.00-0.10 | 0 |

**Every curve peaks between 0 and 10% silver.** Under the cooling profile all
four peak at exactly zero, monotonically. The brief's Ag₇₀Cu₃₀ priority is
beaten in all eight cases.

### The plateaus matter more than the peaks

`series_optimum` reports the width of the within-one-point plateau, because for
a sputtering process that is the number that governs feasibility. The
segregated/AZO curve is flat from **5% to 40% Ag** — a 35-point-wide window, so
composition control at the target is easy. The solid-solution curves are much
sharper (0-5%), meaning if the film mixes you have little tolerance.

So the answer to "what composition" is properly stated as a *range*: **5-15% Ag
is safe under either microstructure hypothesis and either architecture.**

### The microstructure question stops mattering in the dilute corner

This is the most useful consequence. At Ag₇₀Cu₃₀ the two hypotheses differ by
about 14 points (79.2 against 65.0 on AZO), so the design is hostage to an
unresolved question. At 5% Ag they differ by 2.5 points:

| Composition | segregated | solid solution | gap |
|---|---|---|---|
| Ag₇₀Cu₃₀, Si₃N₄ | 79.2 | 70.0 | 9.2 |
| Ag₅Cu₉₅, Si₃N₄ | 89.3 | 86.8 | **2.5** |

**Designing in the dilute-silver corner makes the project robust to the
microstructure question rather than dependent on it.** That is worth more than
the two points of score.

### New candidates

Eight added to `data/candidates.yaml`: D10, D10e, D15, D15e (AZO) and E5, E5e,
E10, E10e (Si₃N₄), each at the geometry the series selected. The table is now 36
candidates and the dilute family holds the top four places under the heating
profile.

| ID | Stack | T_vis | ε_h | R_s | Ag (g/m²) | score |
|---|---|---|---|---|---|---|
| E10e | Si₃N₄/Ag₁₀Cu₉₀/Si₃N₄ segregated | 0.878 | 0.0456 | 3.13 | 0.015 | 89.3 |
| E5e | Si₃N₄/Ag₅Cu₉₅/Si₃N₄ segregated | 0.864 | 0.0428 | 2.98 | 0.008 | 89.3 |
| N6 | Si₃N₄/Cu/Si₃N₄ | 0.859 | 0.0478 | 3.41 | 0 | 88.9 |
| E5 | Si₃N₄/Ag₅Cu₉₅/Si₃N₄ mixed | 0.862 | 0.0540 | 3.99 | 0.008 | 86.8 |

**E10e is an 86% silver reduction against the benchmark while beating it
simultaneously on transmittance (0.878 vs 0.876), emissivity (0.0456 vs 0.0603)
and sheet resistance (3.13 vs 4.18).** Against section 0's finding that Ag₇₀Cu₃₀
saves only 8% of the silver, this is a different order of answer.

### Correction 1: there is no optimum at Ag₆₀Cu₄₀

An earlier turn reported Ag₆₀Cu₄₀ as a local optimum, on the evidence that it
scored above both Ag₇₀Cu₃₀ and Ag₅₀Cu₅₀. That was a three-point artifact. At 5%
resolution the curve rises monotonically as silver falls, with no feature at
60%. The apparent peak was geometry-search noise between separately optimised
candidates.

### Correction 2: the earlier cooling column was not a curve

Section 11 showed cooling scores that jumped erratically (50.4, 38.2, 37.8,
40.5, 25.6, 43.6 across adjacent compositions). That was not physics. Those
geometries had been optimised against the *heating* objective and then scored
under the cooling one, and the g-value swings hard with oxide thickness, so
adjacent compositions landed on geometries with very different solar gain.

Re-run with the geometry optimised against the cooling scheme, the same series
is perfectly smooth:

    Si3N4, segregated:  50.5 52.0 53.1 54.0 55.1 ... 66.8 67.3 67.6

`composition_series` now records which scheme it optimised against, and its
docstring states the rule: **optimise against the objective you intend to
report.** Cross-scoring a geometry-optimised frame under a different objective
produces an artifact that looks like structure.

### Both corrections have the same cause

Reading structure into too few points, twice — three compositions in one case,
one geometry per composition in the other. Worth stating in any write-up: the
framework's value came from re-running things at finer resolution and finding
that earlier conclusions dissolved.
