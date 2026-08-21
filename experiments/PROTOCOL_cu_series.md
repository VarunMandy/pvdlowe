# Experiment 1 — Copper thickness series

**Purpose.** The framework under-predicts sputtered Cu sheet resistance by
roughly 8× against literature (`docs/FINDINGS.md` §3.6). Most leading
candidates in both climate profiles are copper-based, so this one measurement
either confirms or invalidates them. Nothing else available is as decisive.

**Cost.** Eight films, one four-point probe session. Half a day.

**Run sheet.** `experiments/cu_series_runsheet.csv`, or regenerate with
`pvdlowe calibrate --runsheet out.csv`.

---

## Matrix

Cu at 8, 10, 12, 14, 16, 18, 20 nm, plus **one Ag film at 10 nm as a control**.
Deposition order randomised.

## Protocol

**Randomise the order.** Target erosion drifts across a campaign; in standard
order that drift aliases directly onto thickness and you cannot tell a size
effect from a tool trend. The run sheet is pre-randomised.

**Deposit on the underlayer the real stack will use** — AZO or Si₃N₄, not bare
glass. Percolation depends on what the metal wets, and d_c is the parameter
this experiment recovers most reliably.

**Measure thickness independently.** Profilometry, XRR or a calibrated quartz
monitor. ρ = R_s · t, so a 20% thickness error is a 20% resistivity error and
will be misread as a scattering parameter. Record it in
`measured_thickness_nm`.

**Four-point probe at five points per film**, and record the spread rather than
the mean alone. Non-uniformity is itself diagnostic: a thin film near
percolation is patchy, and a large spread at 10–12 nm is evidence about d_c.

**The Ag control is not optional.** It anchors the tool against a film whose
behaviour is well characterised — 10 nm Ag on AZO should give roughly
4–5 Ω/sq. If the control comes out wrong, the Cu series cannot be interpreted,
and you have learned something more urgent.

**Record an open circuit as blank, not zero.** A sub-percolation film reads
open. That is evidence about d_c and the fitter uses it as a bound; a zero
would be fitted as data.

## Analysis

```bash
pvdlowe calibrate -i experiments/cu_series_runsheet.csv
```

Fits specularity, grain-boundary reflection, percolation threshold and a
thickness-independent excess resistivity, then diagnoses which of three causes
is operating.

---

## Amendment, before any data was taken

A literature review of published Fuchs-Sondheimer and Mayadas-Shatzkes
parameters for copper (`docs/LITERATURE_CALIBRATION.md`) was carried out after
these rules were written and before any deposition. It changes two things, and
both are recorded here rather than in the interpretation afterwards.

**Rule A is eliminated.** Four independent published fits give p between 0.48
and 0.80 and R between 0.16 and 0.43; the framework's assumed p = 0.50,
R = 0.25 sits inside that range. All of them predict 2.2-2.7 ohm/sq for
AZO/Cu(15)/AZO against a literature value of 16.6, and an exhaustive scan over
p in [0,1] and R in [0,0.6] reaches only 4.42. No scattering parameters explain
the discrepancy.

**A fifth mechanism is added: nanocrystalline grain structure.** The models take
grain size as an input, and the framework assumes lateral grains three times the
film thickness. Grains at roughly half the thickness give 14.1 ohm/sq, which
does reproduce the literature. That is now the leading hypothesis, displacing
oxygen contamination.

**Consequence for this experiment.** Grain size becomes a measured quantity, not
an assumption, and `grain_size_ratio` joins p, R and d_c as a calibration
target. Measure it by XRD on at least three films, using Scherrer broadening of
the Cu(111) reflection. If XRD access is easier to obtain than sputter time,
**one scan on a single 12-15 nm film is now the cheapest decisive measurement**
and should be done first.

---

## Pre-registered decision rules

Written before the data exists, so the interpretation is not chosen to suit the
result. Rule A was subsequently eliminated by literature review, as recorded
above; it is retained here unaltered so the amendment is auditable.

### A. Classical size effect — fitted excess < 1 µΩ·cm, ρ(100 nm)/ρ_bulk < 1.5
**[ELIMINATED by literature review — see amendment above]**

The model form was right and only its parameters were wrong.

**Then:** adopt the fitted parameters, re-run `pvdlowe evaluate`, and report the
updated ranking. The Cu-based recommendations stand with revised numbers.

### B. Thickness-independent excess — fitted excess > 50% of bulk, and adding it improves the relative RMS by more than 20%

Not a size effect. Impurity scattering, most likely oxygen incorporated during
deposition.

**Then:** this is the **good** outcome. It means the copper route's obstacle is
film quality, not physics — an engineering problem with known levers. Follow
with: base pressure before deposition, a getter step, substrate temperature,
and an XPS depth profile for oxygen. The candidate rankings become achievable
targets rather than predictions.

### C. Shifted percolation — fitted d_c differs from 11 nm by more than 1.5 nm

The film dewets more or less than assumed on this underlayer.

**Then:** every silver-consumption number changes, because minimum usable
thickness changes. Try a 0.5 nm seed layer or a lower substrate temperature and
repeat. Update `PERCOLATION["Cu"]` and re-run the composition series.

### D. The literature point is simply right — R_s at 15 nm near 16.6 Ω/sq

**Then:** the framework's copper optics are optimistic by roughly 8×, and
**N6, E5e, E10e and the double-Cu stack all fall.** The project reverts to
silver reduction, and §3.1's dilute-silver optimum becomes the recommendation
in its own right rather than a copper-adjacent one.

This is the outcome that would invalidate the most, and it must be reported if
it occurs.

---

### E. Nanocrystalline grain structure — XRD grain size ≲ 0.6 × film thickness

Added by the amendment above and now the leading hypothesis.

**Then:** the model's grain-size assumption is wrong rather than its scattering
parameters. Set `grain_size_ratio` from the measured value and re-run
`pvdlowe evaluate`. The fix is thermal or morphological — a seed layer, an
elevated substrate temperature, or a brief post-deposition anneal to promote
grain growth — rather than the vacuum-hygiene measures implied by rule B.

Distinguishing E from B is the reason grain size must be measured rather than
inferred: both produce an elevated resistivity that a thickness series alone
cannot separate, because a small-grain film and a contaminated film give
similar R_s(d) curves.

---

## What this experiment cannot settle

**Specularity and grain-boundary reflection are not separately identifiable**
from R_s(d) alone — over an 8–20 nm window they produce nearly the same 1/d
dependence. In a recovery test on synthetic data, a film generated with p = 0.35
was fitted at p = 1.00 with a 1.5% relative residual: an excellent fit to the
data and a wrong value for the parameter.

The fitted model therefore **predicts sheet resistance reliably** in the fitted
range, which is what the framework needs. The individual parameters must not be
quoted as measurements. Separating them requires varying grain size
independently — anneal at fixed thickness and re-measure.

**d_c is the identifiable parameter** and is recovered to better than 1 nm in
testing. It is also the one that matters most, since it sets the minimum usable
thickness.

## The same scan answers the microstructure question too

`pvdlowe.characterise.xrd` predicts what each hypothesis looks like, so the
scan can be planned rather than interpreted afterwards.

**Peak positions, Cu K-alpha1:**

| Case | (111) 2-theta | Signature |
|---|---|---|
| Segregated Ag-Cu | 38.12 and 43.32 | **two** peak sets, at the pure-element angles |
| Solid solution, Ag70Cu30 | 39.54 | **one** peak set, between them |
| Pure Ag | 38.12 | — |
| Pure Cu | 43.32 | — |

The solid-solution peak sits 1.42 degrees from silver, against a peak width of
0.59 degrees at 15 nm grains. The two cases cannot be confused.

**This is a second, independent discriminator.** The sheet-resistance test
separates the hypotheses by a number, 6.4 against 2.6 ohm/sq. Diffraction
separates them by peak count. Two unrelated observables agreeing is far
stronger evidence than either, and both come from the same film.

**Grain size from the same peak:**

| Underlayer | Grain size | FWHM(111) |
|---|---|---|
| Crystalline ZnO / AZO (TEM, patent) | 25 nm | 0.351 deg |
| Framework default | 30 nm | 0.293 deg |
| Amorphous TiOx (TEM, patent) | 15 nm | 0.585 deg |
| Nanocrystalline, the Cu hypothesis | 6 nm | 1.463 deg |

Measure instrumental broadening on a LaB6 or silicon standard and subtract in
quadrature before inverting. Strain also broadens peaks; separating size from
strain needs several reflections and a Williamson-Hall plot.

**And the texture answers the templating question.** Compare the observed
(111)/(200) intensity ratio against the powder value of about 2.2. A much
larger ratio means {111} texture, which is the epitaxial templating the AGC
patent attributes to ZnO. That is the third thing this one scan settles.

## Follow-on, if Experiment 1 is clean

**Experiment 2 (§6.3):** R_s across Ag 0, 25, 50, 75% at fixed 10 nm. The
*curve shape* discriminates the microstructure hypotheses — segregated predicts
flat ~3 Ω/sq, a metastable solid solution predicts a Nordheim hump peaking
above 7 Ω/sq.
