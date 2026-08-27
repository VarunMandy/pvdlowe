# AZO/Cu/AZO in the literature

Six studies located beyond the two the brief cites. They matter for three
reasons: one challenges the experiment this project recommends, one contradicts
an assumption in the model, and one shows a route to performance neither of the
brief's sources reaches.

**Grade:** `LITERATURE_UNVERIFIED` throughout — abstracts read, full texts not.

---

## 1. The one that threatens the XRD plan

**Effect of Cu layer thickness on the structural, optical and electrical
properties of AZO/Cu/AZO tri-layer films**, *Vacuum* (2010), PII
S0042207X10001284. Glass, RF-sputtered AZO with ion-beam-sputtered Cu, 3–13 nm.

> **No diffraction peaks related to Cu are observed through X-ray diffraction
> analysis.**

That is a direct problem for `experiments/PROTOCOL_cu_series.md`, which proposes
discriminating the microstructure hypotheses by Cu peak count and measuring
grain size from Cu peak width. **If there is no Cu peak, neither works.**

**But it is not settled.** The ApSS 2022 study (benchmark
`azo_cu_azo_optimised`) reports the opposite for a comparable film:

> a weaker (1 1 1) peak near 43.8° proves that Cu exists the structure of
> face-centred cubic

The framework predicts Cu(111) at **43.32°**, so that observation agrees to
0.5°. Same architecture, same thickness range, opposite outcome — the
difference is presumably deposition method and count statistics.

**Consequence for the protocol.** A copper peak in this stack is *marginal, not
guaranteed*. Three changes follow:

- **Use grazing-incidence geometry.** At a fixed shallow incidence the beam
  path through the film is far longer than in Bragg–Brentano, and substrate
  scattering is suppressed. This is the standard answer for a buried 12 nm
  layer and the protocol should specify it.
- **Deposit a thicker calibration film.** A 30 nm Cu layer on AZO, with no
  capping oxide, gives an unambiguous peak and a grain size. It will not have
  the same microstructure as a 12 nm buried layer, but it establishes that the
  measurement works before it is applied to the marginal case.
- **Expect long counts.** A 12 nm layer under 40 nm of AZO is very little
  scattering material, and the AZO(002) reflection near 34° is far stronger.

Without those, a null result would be ambiguous between "no Cu peak because
amorphous or nanocrystalline" and "no Cu peak because insufficient signal" —
and those have opposite implications.

---

## 2. One that appears to contradict the model, and does not

**Tuning microstructure and optoelectronic performance in AZO/Ag/AZO and
AZO/Cu/AZO: a comparative investigation**, Mendil, Chelouche, Challali et al.,
*Opt. Mater.* (2025), PII S0925346725005142. AZO 25–65 nm, Ag 10 nm against
Cu 13 nm.

**A ScienceDirect highlight on this paper reads "Cu interlayer yields higher
visible transmittance across all AZO thicknesses."** That would contradict the
interband absorption §5.4 depends on, and it was recorded here as a threat to
one of the project's headline findings.

**It is not what the paper says.** The abstract, via ADS
(2025OptMa.16517154M), reads:

> Transmittance spectra showed that thicker AZO layers reduced visible
> transmittance, with AZO/Cu/AZO exhibiting better **NIR** performance.

Near-infrared, not visible. A companion paper by an overlapping group —
Camez-Cota et al., *Opt. Mater.* **165** (2025) 117089, on AZO/Cu/Ag/AZO —
states the same thing without ambiguity:

> **Ag-rich layers improved visible transmittance, while Cu-rich layers
> favoured near-infrared transparency.**

**And the framework reproduces it.** Running the paper's own comparison:

| AZO nm | Ag 10 T_vis | Cu 13 T_vis | Ag T_sol | Cu T_sol |
|---|---|---|---|---|
| 25 | 0.859 | 0.687 | 0.598 | 0.447 |
| 35 | **0.876** | 0.722 | 0.606 | 0.467 |
| 45 | 0.873 | 0.741 | 0.599 | 0.472 |
| 65 | 0.782 | 0.678 | 0.550 | 0.442 |

Silver wins the visible at every AZO thickness by 12–17 points, and the
peak-then-decline with AZO thickness is reproduced as well.

Note also that "better NIR performance" for a Low-E coating means better NIR
*rejection*, not transmission. Copper passing less near-infrared is copper
performing better, and the framework agrees — T_sol 0.467 against silver's
0.606.

**§5.4 stands. No action needed.**

> **A note on method.** This entry was first written as a threat to a headline
> finding on the strength of an aggregator highlight, without checking it
> against the paper's own abstract. That is the third time in this project that
> reading one rendering of a source and not another produced a false alarm —
> the others being the 1.59 µΩ·cm resistivity and the 82.4% AZO transmittance.
> In all three the error was the same shape: hold a fragment, treat it as the
> source, and conclude someone else was careless.

## 3. The one that shows what a seed layer buys

**Improved performance of transparent-conducting AZO/Cu/AZO multilayer thin
films by inserting a metal Ti layer**, *Opt. Lett.* **42** (2017) 3020.
Polycarbonate substrate, argon–oxygen mixture.

| | R_s | T_vis |
|---|---|---|
| AZO/**Ti**/Cu/AZO | **4.31 Ω/sq** | >0.82 |
| ApSS 2022, no seed | 9.96 | 0.877 |
| Miao 2014, no seed | 16.6 | 0.60–0.80 |

**A 1–2 nm titanium seed under the copper gives sheet resistance nearly four
times better than one of the brief's benchmarks and twice the other.**

This is the same mechanism as `docs/NUCLEATION_MECHANISM.md`: the layer beneath
the metal determines the metal's microstructure. It is also what the SVC review
records industry doing with NiCr under silver on nitride.

**It matters for the copper discrepancy.** The framework predicts 2.16 Ω/sq for
15 nm Cu. The unseeded measurements are 9.96 and 16.6; the seeded one is 4.31.
The model is not eightfold wrong about *copper* — it is eightfold wrong about
*unseeded, poorly nucleated* copper, and only twofold wrong about copper grown
on a seed. **That narrows the discrepancy substantially and points at the same
cause.**

Caveat: polycarbonate substrate, not glass.

---

## 4–6. Bimetallic and comparative work

- **Cu/Ag bimetallic layers on AZO**, *J. Mater. Sci.: Mater. Electron.* (2023),
  DOI 10.1007/s10854-023-10206-2. Best figure of merit 1.92 × 10⁻² Ω⁻¹ at
  Cu 4 nm / Ag 2 nm — a six-nanometre metal total, which is below any
  percolation threshold this framework models, so how it conducts at all is a
  question worth understanding.
- **AZO/Cu/Ag/AZO competing thicknesses**, *Opt. Mater.* (2025), PII
  S092534672500802X. Notes that only two prior studies address this
  architecture.
- **AZO/metal/AZO for CIS solar cells**, *Vacuum* (2018), PII S004060901830155X.
  Figure of merit by interlayer: Mo 2.98 × 10⁻⁶, **Cu 1.06 × 10⁻³**,
  **Ag 3.91 × 10⁻²**. Silver is roughly **37× better than copper** on this
  measure — a useful independent scale for how much the copper substitution
  costs, from a source with no stake in the answer.

---

## What to do with this

**Amend the protocol** (§1) before the scan is run. The grazing-incidence
requirement and the thicker calibration film are cheap insurance against an
ambiguous null.

**Add a seeded copper arm to the thickness series** (§3). If a 1–2 nm Ti seed
recovers most of the eightfold gap, that is both an explanation and a process
route, and it costs one extra target in an existing run.
