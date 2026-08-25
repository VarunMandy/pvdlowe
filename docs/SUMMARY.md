# Executive summary

**Project:** cost-effective, sustainable low-emissivity coatings on soda-lime
float glass by Ar magnetron sputtering.
**Deliverable:** `pvdlowe`, a computational screening framework, plus the
findings from applying it to the project brief.
**Status:** framework complete and validated against itself; **no films
deposited.** Every performance figure below is a model output.

---

## The question and the answer

The brief asks how much silver can be removed from an AZO/Ag/AZO Low-E stack.
The framework's answer depends on something the brief does not specify — the
climate the glazing serves.

| | heating-dominated | cooling-dominated (India) |
|---|---|---|
| Recommended | Si₃N₄ / Ag₁₀Cu₉₀ / Si₃N₄ | AZO / Cu / AZO |
| Geometry (nm) | 59 / 10 / 48 | 45 / 12 / 45 |
| T_vis | 0.878 | 0.738 |
| Emissivity ε_h | 0.0456 | 0.0463 |
| Sheet resistance | 3.13 Ω/sq | 2.87 Ω/sq |
| Solar heat gain g | 0.760 | 0.558 |
| Silver | 0.015 g/m² (**−86%**) | **zero** |
| Metal cost | $0.12/m² | $0.01/m² |
| Meets full spec | **yes** | no — T_vis 0.738 < 0.80 |

**The lead candidate is a judgement, not a result.** Silver mass carries a
weight of 0.15, and that number selects the answer: at weight 0 the winner
carries 0.065 g/m², at 0.30 it carries none, and the winner changes three times
in between. Five of eight settings separate first from second by under half a
point. The honest statement is **E10e at weight 0.15, E5e at 0.20–0.25, and the
silver-free N6 at 0.30 and above** — choosing among them is a decision about
how much silver consumption matters to Saint-Gobain, not one the framework can
make. Run `pvdlowe check-weights`.

Benchmark for comparison: AZO/Ag/AZO at 10 nm — T_vis 0.876, ε_h 0.0603,
R_s 4.18 Ω/sq, 0.105 g/m² Ag, $0.85/m².

The heating-climate recommendation **beats the silver benchmark on every
performance axis simultaneously** while using an eighth of the silver.

---

## Six findings

**1. The composition optimum is 5–15% Ag, not 70%.** Every one of eight
composition curves peaks between 0 and 10% Ag. The brief's Ag₇₀Cu₃₀ priority is
beaten in all eight. It is a sustainability result, not a performance one:
emissivity keeps improving to 50% Ag, but silver mass is weighted.

**2. Silicon nitride outperforms AZO on transmittance by up to nine points.**
A material class the brief's framing structurally excluded — it began from the
periodic table and the Materials Project, both of which surface oxides.

**3. Climate reverses the ranking.** AZO's free carriers put a plasma edge at
1.25 µm, inside the solar band, so the conductive oxide does solar-control work
a passive nitride cannot. The two profiles disagree on the winner.

**4. No single-metal architecture can reach solar-control performance.** Best
light-to-solar-gain ratio across 38 candidates is 1.37 against ~2.0 commercial.
Two metal layers reach 1.76 — an architectural limit, not a compositional one.

**5. The brief's section 14 weighting has six defects.** The most serious: it
omits silver consumption, so the optimiser returned a design using **29% more
silver than the benchmark at a perfect 100/100 score.** Two more were found by re-auditing the
first fixes: silver mass, metal cost and supply risk correlate at r = 1.000 and
0.991 and together carried 36% of the effective weight on one property; and
three further criteria carried 30% of the nominal weight while being `None` for
every candidate, one of them with no definition at all.

**6. Two of the brief's citations cannot be matched to any source, and one
pivotal measurement is physically inconsistent** with a model-independent
electrodynamic limit. Section 16's Ag-free conclusion rests on it.

---

## What must happen before any of this is a result

**One measurement.** A copper thickness series, 8–20 nm, four-point-probe sheet
resistance. The model under-predicts sputtered Cu R_s by ~8× against literature,
and copper is central to most leading candidates in both climates.

**One line of full text.** Whether the *Applied Surface Science* 2022 emissivity
is normal or hemispherical. If it is not the EN 12898 quantity, the brief's
section 16 needs restating rather than discarding.

**One film.** AZO/Ag₇₀Cu₃₀/AZO at 10 nm, R_s measured. The two microstructure
hypotheses predict 6.4 vs 2.6 Ω/sq — one probe reading settles a question most
downstream predictions depend on.

---

## Methodological contribution

Independent of any candidate ranking, and not contingent on pending
measurements:

- Four defects in a proposed multi-objective weighting, found by the framework
  auditing its own inputs, each of which changed the ranking.
- Two literature values that fail model-independent physical consistency checks,
  and two citations that cannot be traced.
- A material class and an architecture that the project's framing excluded, both
  of which outperform what was proposed.
- Four of the project's own intermediate conclusions overturned by re-running at
  finer resolution — documented rather than quietly corrected.

The framework's most useful output was the checks that caught its own inputs,
not the rankings it produced.

---

Full detail in `docs/FINDINGS.md`. Physics and approximations in
`docs/METHODOLOGY.md`. Evidence grading in `docs/PROVENANCE.md`. Experimental
programme in `docs/ROADMAP.md`.
