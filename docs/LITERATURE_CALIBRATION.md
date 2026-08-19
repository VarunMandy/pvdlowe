# Can literature substitute for the copper thickness series?

**Partly — and the part it settles changes the diagnosis.**

The framework under-predicts sputtered Cu sheet resistance by roughly eightfold
(`docs/FINDINGS.md` §3.6). §6 of the technical report proposes a thickness
series to resolve it. Before running that, the question is whether published
values for the three uncalibrated parameters already answer it.

---

## 1. What the literature supplies

Fuchs–Sondheimer specularity `p` and Mayadas–Shatzkes grain-boundary
reflection `R` are heavily studied for copper, because interconnect scaling
depends on them.

| p | R | Source | Conditions |
|---|---|---|---|
| 0.52 | 0.43 | Chawla & Gall, *Phys. Rev. B* **81**, 155454 (2010) | Cu on SiO₂, 27–158 nm, grain size 35–425 nm |
| 0.48 | 0.27 | twin-boundary study, nanocrystalline Cu | grain size by precession electron diffraction |
| 0.80 | 0.38 | *Thin Solid Films* (2006) | Cu at 50 and 90 nm |
| ≈0 (−0.2 reported) | 0.16–0.17 | *AIP Advances* **9**, 025015 (2019) | sub-14 nm interconnect lines; negative p attributed to roughness |
| **0.50** | **0.25** | **pvdlowe defaults** | assumed, not measured |

**The framework's assumed values sit squarely inside the published range.** The
mean free path used (39 nm) also matches the literature value quoted at 21 °C.

## 2. What that rules out

Predicted sheet resistance for AZO/Cu(15)/AZO under each pair:

| p | R | R_s (Ω/sq) |
|---|---|---|
| 0.52 | 0.43 | 2.69 |
| 0.48 | 0.27 | 2.23 |
| 0.80 | 0.38 | 2.17 |
| 0.00 | 0.17 | 2.71 |
| 0.50 | 0.25 | 2.16 |

All cluster near 2.2–2.7 Ω/sq. The literature value to reproduce is **16.6**.

An exhaustive scan over the *entire* physically admissible range —
p ∈ [0, 1], R ∈ [0, 0.6] — reaches a maximum of **4.42 Ω/sq**, still short by a
factor of 3.8.

> **No combination of surface and grain-boundary scattering parameters, anywhere
> in the literature range, explains the discrepancy.** Decision rule A
> ("classical size effect, model form right, parameters wrong") is therefore
> ruled out by literature alone, without depositing anything.

## 3. What it points to instead — and this is a different answer

Both scattering models take *grain size* as an input. The framework assumes
lateral grains three times the film thickness, appropriate to a well-coalesced
sputtered film. Relaxing that assumption:

| Grain size | R_s(15 nm) |
|---|---|
| 3.0 × thickness (assumed) | 4.42 |
| 1.0 × thickness | 8.31 |
| **0.5 × thickness** | **14.13** |
| 0.25 × thickness | 25.77 |
| 0.1 × thickness | 60.67 |

**Grains at roughly half the film thickness reproduce the literature value.**

That is a nanocrystalline structure — grains of order 5–8 nm in a 15 nm film —
rather than the coalesced columnar structure the model assumes. It is entirely
plausible for copper sputtered at room temperature onto an oxide, which it
wets poorly.

## 4. Why this matters for the diagnosis

The report's decision rules distinguished three mechanisms. This analysis
reweights them before any deposition:

| Rule | Mechanism | Status after literature review |
|---|---|---|
| A | Classical size effect, wrong p/R | **Ruled out** — no literature parameters reach the value |
| B | Impurity scattering (oxygen) | Still possible, but no longer the leading hypothesis |
| C | Shifted percolation threshold | Untouched by this analysis |
| **—** | **Nanocrystalline grain structure** | **New leading hypothesis** |

The previous leading candidate was oxygen contamination. Grain structure now
looks more likely, because it explains the magnitude with a single plausible
parameter change, whereas an impurity term of 12–18 µΩ·cm is a large
contamination level to invoke.

Both are still "film quality rather than physics", so the strategic conclusion
in the report is unchanged — copper's obstacle remains an engineering problem.
But the *fix* differs, and that matters for what to try next:

- **If grain structure:** seed layers, elevated substrate temperature, or a
  brief anneal to promote grain growth.
- **If oxygen:** base pressure, getter, target condition.

## 5. What the literature does *not* settle

**The published p and R values are for the wrong system.** They come from
copper on Ta or SiO₂ barriers at 25–158 nm, deposited for interconnect
applications. Our case is copper on AZO at 10–15 nm. Copper nucleates
differently on a transparent conducting oxide than on a diffusion barrier, and
the thickness regime is below anything in the cited studies.

So the transferable conclusion is the *negative* one — that p and R cannot
explain the gap — and not a positive calibration.

**Grain size on AZO at these thicknesses was not found in the literature
searched.** That is the missing number.

## 6. Revised recommendation

The full thickness series is still the better experiment, but it is no longer
the *cheapest* decisive one.

**A single XRD scan on one 12–15 nm Cu film on AZO** gives the grain size by
Scherrer broadening. That one measurement discriminates between the new leading
hypothesis and the alternatives:

- Grain size ≈ half the film thickness → nanocrystalline structure confirmed,
  the model's grain assumption is wrong, and the fix is thermal or a seed layer.
- Grain size ≳ film thickness → grain structure is not the cause, and attention
  returns to oxygen contamination and decision rule B.

XRD is far more widely available than a dedicated sputter session, and the
sample requirement is one film rather than eight.

**If both are available, run both.** The thickness series still calibrates the
model; the XRD tells you what to fix. But if only one is possible, XRD now has
the better information-per-hour.

## 7. Effect on the reported results

None of §5's rankings change — this analysis does not alter any parameter, it
constrains which explanations remain open. The copper-based candidates remain
contingent exactly as stated. What has changed is that one of the four
pre-registered outcomes is now much less likely, and a fifth mechanism has been
identified that the original protocol did not name.

`experiments/PROTOCOL_cu_series.md` should be amended to add grain size as a
measured quantity, and `grain_size_ratio` should be treated as a calibration
target alongside p, R and d_c.

---

## Sources

- Chawla & Gall, *Surface and grain-boundary scattering in nanometric Cu films*,
  Phys. Rev. B **81**, 155454 (2010). DOI 10.1103/PhysRevB.81.155454
- *An evaluation of Fuchs-Sondheimer and Mayadas-Shatzkes models below 14nm node
  wide lines*, AIP Advances **9**, 025015 (2019)
- *The contribution of grain boundary scattering versus surface scattering to
  the resistivity of thin polycrystalline films*, Thin Solid Films (2006),
  PII S0040609005024831
- *Thickness dependence of resistivity for Cu films deposited by ion beam
  deposition* (2003)

All located and cross-checked against abstracts; none read in full text. Grade:
`LITERATURE_UNVERIFIED`, per `docs/PROVENANCE.md`.
