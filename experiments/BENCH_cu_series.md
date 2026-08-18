# Bench procedure — copper thickness series

Print this. One session, eight films, plus a rate calibration.

**What it decides:** the framework under-predicts sputtered Cu sheet resistance
by roughly 8x against literature. Six of the top candidates in `docs/SUMMARY.md`
are copper-based. This session confirms or kills them.

---

## Before the session

**Substrates.** 8 pieces, plus 2 spare. Soda-lime float glass, cleaned
(ultrasonic in detergent, DI rinse, IPA, N₂ blow). **Coat all of them with the
same AZO underlayer in one run** — 40 nm. Percolation depends on what the metal
wets, so a bare-glass series answers a different question than the one you have.

**Target.** Cu, 99.99%+. Check for oxide discolouration; if present, pre-sputter
longer.

**Base pressure.** Pump to **< 5 × 10⁻⁶ Torr, and record the actual value.**
This is not routine hygiene — oxygen contamination is decision rule B, one of
the four outcomes under test. If you cannot reach 5e-6, record what you did
reach and note it; a poor base pressure with elevated resistivity is itself
the result.

**Rate calibration first.** Deposit one thick Cu film (~100 nm nominal) on a
spare, measure by profilometry or XRR, compute nm/min. Every thickness in the
series is a timed deposition against this rate. **Do not trust a quartz monitor
tooling factor you have not checked this session.**

---

## Deposition

Order is pre-randomised in `experiments/cu_series_runsheet.csv`. **Follow it.**
Target erosion drifts across a campaign; in ascending-thickness order that drift
aliases directly onto thickness and you cannot separate a size effect from a
tool trend.

| Setting | Value |
|---|---|
| Gas | Ar, 99.999% |
| Working pressure | 3–5 mTorr, held constant |
| Power | DC, constant across the series (50–100 W typical) |
| Substrate | room temperature, no intentional heating |
| Pre-sputter | 5 min with shutter closed, before the first film and after any vent |

**Cap every film.** Deposit **AZO 40 nm on top without breaking vacuum.**

This is not optional and it is the most important instruction here. A 10 nm bare
Cu film oxidises in air within minutes. The hypothesis under test is that oxygen
degrades these films — so a bare film measured after venting reports *air*
oxidation and tells you nothing about deposition quality. Every stack is
AZO(40)/Cu(t)/AZO(40).

**One deliberate exception:** deposit a **9th film, bare Cu at 12 nm, no cap.**
Measure it immediately on venting, then again at +1 h and +24 h. That quantifies
the air-oxidation rate and tells you how much of any literature discrepancy is a
handling artifact rather than a deposition one.

**Record for every film:** actual deposition time, power, pressure, base
pressure before the run, and anything unusual (arcing, pressure excursion).

---

## Measurement

**Four-point probe, 5 points per film** — centre and four positions ~10 mm out.
**Record all five, not the mean.** Spread is diagnostic: a film near percolation
is patchy, and a large spread at 10–12 nm is evidence about d_c independent of
the fit.

**An open circuit is a result.** Leave `R_sheet_ohm_sq` **blank**, not zero. The
fitter uses open-circuit films as a lower bound on the percolation threshold; a
zero would be fitted as data.

**Measure thickness independently** on at least 3 films — profilometry on a
masked step, or XRR. ρ = R_s · t, so a 20% thickness error becomes a 20%
resistivity error and the fitter will misread it as a scattering parameter.
Enter it in `measured_thickness_nm`.

**The Ag control at 10 nm is the tool check.** Expect roughly 4–5 Ω/sq for
AZO/Ag(10)/AZO. If it comes out far from that, **stop and diagnose the tool**
— the Cu series cannot be interpreted against an uncalibrated baseline, and you
have found something more urgent than the copper question.

---

## Data entry

Fill `R_sheet_ohm_sq` in the run sheet with the **mean of the five points**, and
put the five individual readings in `notes`.

```bash
cd ~/lowe
python -m pvdlowe calibrate -i experiments/cu_series_runsheet.csv \
    --capped --dielectric AZO --cap-nm 40
```

`--capped` subtracts the AZO shunt to recover the metal layer alone. The
correction is large where it matters — a measured 16.6 Ω/sq trilayer is
22.6 Ω/sq in the metal, a 36% difference — and skipping it biases the fit toward
"the copper is fine".

---

## At the bench: what to do if

**Ag control is far off.** Stop. Check probe calibration on a known standard,
then target condition and rate calibration. Do not proceed.

**Everything reads open below 14 nm.** Copper is dewetting badly on this
underlayer. Still useful — that *is* decision rule C. Finish the series, then
repeat with a 0.5 nm Ti or ZnO seed layer.

**Readings drift between the first and last film.** Deposit a repeat of run 1 at
the end. If it differs by more than ~10%, the tool drifted and the series needs
splitting into blocks.

**A pressure excursion or arc during a run.** Note it and re-deposit that
thickness on a spare. Do not silently keep a compromised film.

**Numbers look "too good"** — Cu at 10 nm near 2 Ω/sq. Check the probe is not
reading the AZO, and confirm the metal thickness by profilometry. That result
would contradict the literature strongly and needs to be solid before it is
claimed.

---

## Decision rules

Pre-registered in `experiments/PROTOCOL_cu_series.md`, written before any data
exists. Read them **before** the session, not after — the point is that the
interpretation is fixed in advance.

Briefly: **A** classical size effect → re-parameterise, recommendations stand.
**B** thickness-independent excess → oxygen, an engineering problem, the *good*
outcome. **C** shifted percolation → dewetting, every silver number changes.
**D** literature is right → six top candidates fall and the project reverts to
silver reduction.

---

## After

```bash
python -m pvdlowe evaluate                                    # updated ranking
python -m pvdlowe evaluate --targets data/targets_cooling.yaml
git add -A && git commit -m "Cu thickness series: measured R_s(d)" && git push
```

Commit the filled run sheet. It is the project's first measured data and the
only thing here that is not a model output.
