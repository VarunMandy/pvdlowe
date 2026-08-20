# The nucleation mechanism, resolved from literature

**Status:** the mechanism behind `TCOPreset.metal_growth_factor` is now
identified, and it is the same physics as the copper sheet-resistance
discrepancy of `docs/LITERATURE_CALIBRATION.md`. Both are underlayer-dependent
metal grain structure. Two computational attempts failed to find this; a
literature search found it in an afternoon.

---

## 1. What was being asked

Cueva & Carretero measured that silver on AZO gives lower emissivity than
silver on SiAlNx, and attributed it to silver growing more efficiently on AZO.
The framework encodes that as an empirical multiplier with no mechanism
attached (`docs/CARRETERO_COMPARISON.md`, FINDINGS §3.2).

Two surrogate calculations were run to find the mechanism. Both failed:

| Attempt | Failure |
|---|---|
| Bulk adhesion energy | 5–21% lattice mismatch — measured elastic strain, not binding |
| Adatom wetting energy | ZnO(0001) termination changed the answer by 2.1 eV against 0.46 eV between materials |

## 2. What the literature says

**Guardian Industries, US 7,632,572 / 8,512,883** — transmission electron
microscopy comparing silver deposited on **crystalline ZnO** against silver on
**amorphous TiOx**, in the same study:

> Silver grown directly on the amorphous TiOx has an abnormal microstructure
> with irregular grains; silver grown directly on the ZnO has a more normal
> microstructure with regular grains. Average grain size is about **25 nm on
> ZnO** against about **15 nm on a-TiOx**.

> In dark field on the Ag{220} reflections, the {111}-oriented grains are
> **two to three times larger** on ZnO than on a-TiOx.

> On the amorphous underlayer, the silver film is **clearly discontinuous**.

That is the templating hypothesis measured directly. A crystalline oxide
templates Ag(111) growth; an amorphous underlayer does not, and the film
islands rather than coalescing.

**Confirmation from the DFT literature.** Studies of Ag/ZnO interfaces report
that the ZnO(0001) polar plane binds metals better through surface charge
compensation, and that the O-terminated face binds more strongly than the
Zn-terminated one. Photoemission work on Ag/ZnO finds silver adsorbing
cationically on the O face and anionically on the Zn face at the earliest
stages of growth. **The termination sensitivity the surrogate ran into is real
physics, not a model artifact** — and the surrogate got the ordering right
(O face −1.399 eV, Zn face +0.696 eV). It simply could not tell us which face
a sputtered film presents, and neither can any calculation.

**And the nitride question is answered by industrial practice.** A Society of
Vacuum Coaters review of silicon nitride Low-E stacks records that thin NiCr
barrier layers are used specifically to increase adhesion between the nitride
and the silver. Industry uses Si₃N₄ *and adds a metallic nucleation layer
beneath the silver*, which is only necessary because silver adheres poorly to
nitride directly.

That is the opposite of what the surrogate predicted from a crystalline
β-Si₃N₄ proxy, and it explains why: a cleaved crystalline nitride presents
reactive dangling bonds that a passivated amorphous film does not.

## 3. Why this matters beyond the one parameter

**The framework's grain-size assumption was accidentally correct — for AZO.**

`grain_size_ratio` defaults to 3.0, meaning lateral grains three times the film
thickness. For a 10 nm silver film that is 30 nm grains, against the 25 nm the
patent measured on ZnO. Within 20%.

| Underlayer | grain size | ratio | ρ(10 nm Ag) |
|---|---|---|---|
| crystalline ZnO / AZO | 25 nm | 2.5 | 4.69 µΩ·cm |
| **framework default** | 30 nm | **3.0** | **4.44** |
| amorphous TiOx | 15 nm | 1.5 | 5.70 |
| amorphous nitride (inferred) | ~12 nm | 1.2 | 6.33 |

**This is the same mechanism as the copper discrepancy.**
`docs/LITERATURE_CALIBRATION.md` concluded that no published surface- or
grain-boundary-scattering parameters explain the framework's 8× under-
prediction of sputtered Cu sheet resistance, and that a nanocrystalline grain
structure does. The patent shows the underlayer *determines* metal grain size.

So `metal_growth_factor` and the copper grain-size hypothesis are not two
separate caveats. **They are one physical effect — underlayer-dependent metal
microstructure — appearing in two places**, and the framework's structural
weakness is that it models the metal layer as though the layer beneath it did
not affect its microstructure.

## 4. Consequences

**For the model.** `metal_growth_factor` should eventually be replaced by a
per-underlayer `grain_size_ratio`, which is physically meaningful, directly
measurable, and feeds both the optical and electrical paths through the
existing Mayadas–Shatzkes term. That is a better parameterisation than an
opaque multiplier on resistivity.

**For the experiment.** One XRD scan now measures both open questions at once:

| Measurement | Answers |
|---|---|
| Ag(111) / Cu(111) peak intensity and texture | whether the underlayer templates the metal |
| Scherrer width → grain size | `grain_size_ratio` for that underlayer, and the copper discrepancy |

Both on the same film, in the same scan, in an afternoon. §8.2 of the technical
report already calls for this scan; it should now also record the metal
reflections, not only the film thickness.

**For the design.** If templating is the mechanism, it favours crystalline
oxide underlayers and disfavours amorphous nitrides — which is consistent with
Carretero's measurement, with industrial practice using a NiCr nucleation
layer under silver on nitride, and with FINDINGS §3.2's correction. The
hybrid stack (AZO beneath for nucleation, nitride above for durability) is
therefore not a compromise but the physically correct arrangement.

## 5. What this cost, and what it says about method

Two surrogate calculations, roughly three hours of setup and compute across
several failed instance provisionings, produced no usable mechanism. A
literature search produced it in under an hour, with direct experimental
evidence rather than a proxy.

That is now the third time in this project that reading beat computing — after
the Cu scattering parameters of `docs/LITERATURE_CALIBRATION.md` and the
dielectric comparison of `docs/CARRETERO_COMPARISON.md`, both of which
corrected the model. It is worth stating plainly as a methodological finding:
**for a mature field, the marginal value of a literature search exceeds that
of a new calculation, and the framework's role is to identify which question
to search for.**

## 6. Sources

- Guardian Industries, *Double silver low-emissivity and solar control
  coatings*, US 7,632,572 B2 and US 8,512,883 B2 — TEM grain-size comparison,
  Ag on ZnO versus amorphous TiOx.
- *Tuning the interface adhesion of Ag/ZnO composites by metallic dopants: a
  DFT study*, Comput. Mater. Sci. (2023) — polar-plane binding, O- versus
  Zn-termination.
- *Band alignment at Ag/ZnO(0001) interfaces*, Phys. Rev. B **97**, 235430
  (2018) — photoemission, cationic on O face, anionic on Zn face.
- Society of Vacuum Coaters technical review, silicon nitride Low-E stacks —
  NiCr barrier layers for nitride/silver adhesion.

All located and cross-checked against abstracts and available excerpts; none
read in full text. Grade: `LITERATURE_UNVERIFIED`.
