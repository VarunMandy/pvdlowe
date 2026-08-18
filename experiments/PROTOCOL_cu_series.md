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

## Pre-registered decision rules

Written before the data exists, so the interpretation is not chosen to suit the
result.

### A. Classical size effect — fitted excess < 1 µΩ·cm, ρ(100 nm)/ρ_bulk < 1.5

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

## Follow-on, if Experiment 1 is clean

**Experiment 2 (§6.3):** R_s across Ag 0, 25, 50, 75% at fixed 10 nm. The
*curve shape* discriminates the microstructure hypotheses — segregated predicts
flat ~3 Ω/sq, a metastable solid solution predicts a Nordheim hump peaking
above 7 Ω/sq.
