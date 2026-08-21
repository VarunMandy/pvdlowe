# Work log — 20 August 2026

**Project:** `pvdlowe`, computational screening of sustainable low-emissivity
PVD coatings.
**Theme of the day:** attempting to find a physical mechanism for an empirical
model parameter, by computation and then by literature.

**Outcome in one line:** two surrogate calculations failed and one succeeded;
the mechanism was then found by reading, and it turned out to unify two
previously separate limitations of the framework.

---

## 1. What was attempted and what happened

| # | Task | Outcome |
|---|---|---|
| 1 | Provision compute for ML interatomic potentials | 11 failed attempts; succeeded on `e2-standard-8` |
| 2 | Ag–Cu mixing energies (MACE-MP-0) | **Succeeded** — new result, §3 below |
| 3 | Metal/dielectric bulk adhesion energy | **Failed** — lattice mismatch, §4 |
| 4 | Adatom wetting energy | **Failed** — termination sensitivity, §5 |
| 5 | Find the mechanism in the literature | **Succeeded** — §6, the day's main result |
| 6 | Verify the supporting patent in full text | **Succeeded** — §7, produced an unexpected validation |
| 7 | Re-audit all 14 of the brief's citations | **Succeeded** — §8 |

Tests went 97 → 102. Six documents written or rewritten; one conclusion
retracted.

---

## 2. Infrastructure

Eleven failed instance creations before one succeeded. The failures were
informative enough to record: NVIDIA T4 stockouts across six zones,
`n2` family unavailable in `us-central1-a`, a 150 GB minimum boot disk for the
GPU image that my first command undershot, and a `CPUS_ALL_REGIONS` quota
reading that turned out to be a red herring.

`e2-standard-8` succeeded immediately — the `e2` family is the abundant one.
Recorded in `docs/VERTEX_AI.md` §6 so the next person does not repeat it.

**Cost:** roughly two hours of provisioning effort for about an hour of useful
compute. Noted as a planning lesson rather than a technical one.

---

## 3. Ag–Cu mixing energies — succeeded

MACE-MP-0 on 32-site fcc supercells, three random decorations per composition,
cell and positions relaxed.

**Gated first.** The surrogate was required to reproduce two Materials Project
DFT results before any prediction was accepted:

| | MP (DFT) | MACE | error |
|---|---|---|---|
| Cu₃Ag | 0.0904 | 0.0719 | 0.0185 |
| CuAg₃ | 0.0857 | 0.0517 | 0.0340 |

Passed, with a 20–40% systematic under-prediction that is carried through every
figure below as a lower bound.

**Result.** Positive across the whole range, fitting a regular-solution form to
±6 meV/atom:

    ΔE_mix = 0.287 · x · (1 − x)   eV/atom

Configurational spread across decorations was 1–4 meV/atom, an order of
magnitude below the signal.

**Two things this establishes.**

*It extends the convex-hull result.* The Materials Project says Ag–Cu has no
stable **ordered** compound. This extends the instability to the **disordered
solid solution** a sputtered film might actually be. It also self-checks: at
Ag 25 at.% the surrogate puts the disordered state 13 meV/atom *below* ordered
Cu₃Ag, so there is no ordering tendency — precisely what an empty hull implies,
reached independently.

*It explains an earlier observation.* In the dilute-silver corner the driving
force to separate falls **below thermal energy at deposition** — 0.29–0.77 kT
at 550 K for Ag 5–15 at.%, against 1.27 at the brief's Ag₇₀Cu₃₀. FINDINGS §3.1
had found the two microstructure hypotheses converge there and treated it as
robustness; the thermodynamics now supply the reason.

The dilute-silver optimum is consequently supported on three independent
grounds: least silver, best score, weakest tendency to phase-separate.

Written up in `docs/MLIP_MIXING_ENERGY.md` and folded into report §5.6.

---

## 4. Bulk adhesion energy — failed

Intended to give a mechanism for `metal_growth_factor`.

**Failure:** lattice mismatches of 5–21% between the metal film and the oxide
cell. The code strained the film to fit, so the calculation measured elastic
energy rather than binding. Outputs of 9.639 J/m² for Ag/Si₃N₄ and −0.163 for
Ag/TiO₂ are respectively three times any physical metal/oxide adhesion and
impossible.

**Diagnosis:** strain energy at 21% mismatch is ~1.8 J/m² for silver, against a
real work of adhesion of 0.5–3 J/m². The signal was swamped.

**Action:** `MAX_LATTICE_MISMATCH` now raises above 4% rather than returning a
number. This was code-review finding **N1** — "the metal-film tiling uses a
nearest-integer repeat that could leave lattice mismatch unreported as an
error" — landing exactly where predicted.

---

## 5. Adatom wetting — failed, informatively

A better-posed question: whether an arriving atom prefers the oxide or its own
metal, which needs no lattice matching.

    ΔE_wet = E(slab + adatom) − E(slab) − E_bulk

**First result looked usable** and appeared to reproduce the measured ordering
among the oxides. **A termination sweep then disqualified it.** ZnO(0001) is
polar:

| termination | ΔE_wet | regime |
|---|---|---|
| Zn face | +0.696 eV | islanding |
| O face | −1.399 eV | wetting |

**2.095 eV across two faces of one material, against 0.457 eV separating six
different materials.** A factor of 4.6. The dielectric ranking was resolving
which slab the generator returned first.

**A conclusion was retracted.** An earlier write-up that day claimed the model
reproduced the measured ordering. It did not; that claim is withdrawn in
FINDINGS §3.9 and the MLIP document, explicitly rather than by quiet rewriting.

**What survives:** every oxide gives islanding, +0.70 to +1.31 eV. Silver and
copper islanding on oxides is independently known — it is why percolation
thresholds exist at 10–11 nm — so the surrogate reproduces the growth regime
unprompted. A modest but real validation.

**Also fixed:** `wetting_comparison` now excludes any surface whose site spread
exceeds 25% of its binding energy. Two surfaces failed that test, and the
diagnostic had been present in the data all along without being read.

---

## 6. The mechanism, found by reading — the day's main result

After two failed calculations, a literature search resolved the question in
under an hour.

**US 7,632,572 B2 / US 8,512,883 B2** (AFG Industries → AGC Flat Glass North
America → Cardinal CG) deposited 16 nm Ag on amorphous TiOx and on a 5 nm ZnO
seed over the same TiOx, in one study, and examined both by TEM:

- **25 nm grains on ZnO against 15 nm on a-TiOx**
- **{111}-oriented grains two to three times larger** on ZnO
- the film on bare amorphous titania **clearly discontinuous** where the
  ZnO-seeded film was continuous across the whole specimen

And the inventors name the mechanism:

> The zinc oxide grows with the {0001} orientation, which orients the Ag to
> preferentially grow with a {111} orientation. The **epitaxial lattice match**
> between Ag{111} and ZnO{0001} leads to lower sheet resistance and improved
> adhesion of the Ag.

**The nitride case is settled by industrial practice.** Silicon nitride Low-E
stacks use thin NiCr barrier layers specifically to improve nitride/silver
adhesion — a nucleation layer is required because silver adheres poorly to
nitride directly. That is the opposite of what the surrogate predicted from a
crystalline β-Si₃N₄ proxy, and explains why that proxy misled.

### The consequence, which was not anticipated

`metal_growth_factor` and the framework's largest known error — its eightfold
under-prediction of sputtered copper sheet resistance — **are the same physical
effect.** Both are underlayer-dependent metal grain structure.

The framework's default `grain_size_ratio` of 3.0 corresponds to 30 nm grains
in a 10 nm film, within 20% of the 25 nm measured on ZnO. The assumption was
correct, but only for the underlayer it happened to be tuned against.

This is now stated as **the principal structural weakness** in report §7.3: the
framework models each metal layer as though the layer beneath it did not shape
its microstructure. A successor should carry a measured `grain_size_ratio` per
underlayer instead of an opaque multiplier.

**And it simplifies the experimental ask.** One XRD scan now answers both
questions on one film: Scherrer width gives grain size, Cu(111) intensity and
texture test templating.

---

## 7. Patent verified in full — an unexpected validation

The above initially rested on search snippets. Reading the full text confirmed
every quoted figure, corrected the assignee (I had attributed it to Guardian,
who appear in the citation list rather than on the patent), and produced
something the snippets did not contain:

> The sheet resistance of the Ag films … was found to be **5.68 Ω/□** with the
> ZnO/a-TiOx under(bi)layer and **7.56 Ω/□** with the a-TiOx underlayer.

Ratio **1.331**.

`metal_growth_factor` was calibrated independently — from Cueva & Carretero's
*emissivity* series, a different group, a different decade, a different measured
quantity — and gives a TiO₂:AZO ratio of **1.250**.

**Agreement: 93.9%.** The first independent quantitative validation of anything
in this framework: a parameter fitted to one dataset reproducing another it
never saw.

Stated as corroboration rather than confirmation, since the patent compares a
ZnO seed *over* titania against titania alone rather than the two as bulk
dielectrics.

**A second datum:** the patent claims continuous, strongly adherent Ag down to
**8 nm** on a ZnO seed, against the framework's assumed 10 nm critical
thickness. A 20% difference affecting every silver-consumption figure.

---

## 8. Citation audit completed

`docs/REFERENCES.md` was regenerated. It had listed all fourteen of the brief's
claims as "unverified" and predated all verification work.

| Status | Count |
|---|---|
| Verified — full text read | 3 |
| Partial — source located, abstract confirmed | 5 |
| **Disputed — appear in no locatable source** | **2** |
| Supported — corroborated independently | 2 |
| Not pursued | 4 |

Also added a second table for the six sources found *outside* the brief that
changed the model. Three of them corrected it.

**A retraction recorded.** An earlier claim that the brief's 82.4% AZO
transmittance was a transcription error is withdrawn. The paper reports 82.4%
in §3.1 and 81.4% in the abstract; the brief quoted Results and was right. The
error came from checking only the abstract — the exact shortcut the `partial`
grade exists to flag.

---

## 9. Documents produced or rewritten

| File | Status |
|---|---|
| `docs/NUCLEATION_MECHANISM.md` | new, 218 lines |
| `docs/MLIP_MIXING_ENERGY.md` | new, 205 lines |
| `docs/REFERENCES.md` | rewritten, 130 lines |
| `docs/FINDINGS.md` | §3.8, §3.9, §3.10 added; §3.9 retracted and replaced |
| `report/TECHNICAL_REPORT.md` | §5.6, §5.7 added; §7.3 promoted; now 17 pages |
| `README.md` | corrected — had said 68 tests and "all benchmarks unverified" |
| `pvdlowe/ml/` | mixing energies, adhesion, wetting, termination sweep |
| `examples/10_`, `11_` | wetting and termination scripts |

---

## 10. What the day actually demonstrated

**Three of four questions were resolved by reading, not computing.** After the
Cu scattering parameters and the Carretero dielectric comparison earlier in the
project, this was the third and fourth time literature outperformed
calculation — and on this occasion it followed two failed calculations directly.

The framework's contribution was not the answer. It was **identifying which
question to ask**: the surrogate work established that binding energy in any
formulation was not the operative mechanism, which is what made the
templating literature the right thing to search for.

That is worth stating plainly in the write-up. For a mature field, the marginal
value of a literature search exceeds that of a new calculation, and a screening
framework's role is to narrow the search rather than to replace it.

**Both failures were caught by diagnostics rather than by inspection** —
unphysical magnitudes in the first case, an explicit termination sweep in the
second. Neither would have been obvious from a plausible-looking number.

---

## 11. Open at end of day

- **One XRD scan** — grain size and metal texture, one film, an afternoon.
  Resolves the framework's principal structural weakness.
- **One Cu thickness series** — half a day, calibrates the transport model.
- **One paywalled paper** — normal versus hemispherical basis in
  *Applied Surface Science* 578 (2022), on which the brief's §16 conclusion
  rests.

None are computational. All three are specified and handed over.
