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

**US 7,632,572 B2 / US 8,512,883 B2**, AFG Industries → AGC Flat Glass North
America → now assigned to Cardinal CG. Inventors Glenn, Johnson, Dannenberg,
Sieck and Countrywood; priority 2001. **Full text read.**

*(An earlier version of this document attributed the patent to Guardian
Industries. That was wrong — Guardian appears throughout the citation list,
not as the assignee.)*

Example 1 of the patent deposits 16 nm Ag by planar DC magnetron onto two
underlayers in the same study: **a-TiOx (25 nm)** alone, and **ZnO (5 nm) on
a-TiOx (25 nm)**. Electron diffraction confirmed the TiOx was amorphous —
broad diffuse rings only. TEM used silicon-nitride membrane grids; sheet
resistance was measured separately on bulk glass.

**Confirmed, verbatim from the full text:**

> The average normal grain size of the Ag directly on the ZnO is about **25 nm**,
> while that of the Ag directly on the a-TiOx is about **15 nm**.

> {111} oriented Ag grains giving rise to the strong 220 reflections have a
> significantly larger average grain size (**two to three times larger**) when
> deposited directly on the 5 nm thick ZnO than when deposited directly on
> a-TiOx.

> The Ag film near the center of the TEM grid is **clearly discontinuous**
> [on a-TiOx]. … Remarkably, the Ag deposited directly on 5 nm thick ZnO was
> continuous over the entire TEM grid, even in places where Ag deposited
> directly on a-TiOx was discontinuous.

**And the mechanism is stated explicitly by the inventors — more strongly than
this document previously claimed:**

> The zinc oxide grows with the {0001} orientation, which orients the Ag to
> preferentially grow with a {111} orientation. **The epitaxial lattice match
> between Ag {111} and ZnO {0001} leads to lower sheet resistance and improved
> adhesion of the Ag.**

That is templating, named as such, by the people who measured it.

## 2a. The measurement that validates the framework

The full text contains a quantity the search snippets did not: **direct
four-point sheet resistance on the two underlayers**, same silver thickness,
same run.

> The sheet resistance of the Ag films, measured when deposited on substrates
> of bulk glass, was found to be **5.68 Ω/□** with the ZnO/a-TiOx under
> (bi)layer and **7.56 Ω/□** with the a-TiOx underlayer.

That ratio is **1.331**.

`TCOPreset.metal_growth_factor` was calibrated independently — from Cueva &
Carretero's *emissivity* series, a different group, a different decade, a
different measured quantity — and gives AZO 1.00, TiO₂ 1.25, a ratio of
**1.250**.

**The two agree to 6%.**

| | ratio, TiO₂-like : ZnO-like |
|---|---|
| Patent, four-point sheet resistance, 16 nm Ag | 1.331 |
| Framework, calibrated to emissivity, 10 nm Ag | 1.250 |
| Agreement | **93.9%** |

This is the first independent quantitative validation of `metal_growth_factor`.
It was fitted to one dataset and reproduces another that it never saw.

**A caveat on what is being compared.** The patent's comparison is
ZnO-on-a-TiOx against a-TiOx alone — both stacks contain amorphous titania, and
the ZnO is only a 5 nm interlayer. So the measured 1.331 is the effect of
*adding a ZnO seed*, not of ZnO versus TiO₂ as bulk underlayers. The framework's
1.250 compares the two as full dielectric layers. That the two agree so closely
is encouraging but partly fortuitous, and the comparison should not be
presented as exact.

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

**A percolation datum, also from the full text.** The patent states that zinc
oxide "provides a means for forming a high conductivity, strongly adherent Ag
layer with a thickness as low as **8 nm**". The framework uses a critical
thickness of 10 nm for silver, taken from an unverified literature value in the
brief. The patent suggests 8 nm is achievable on a ZnO seed — a 20% difference
that would matter for every silver-consumption figure, and one more thing the
§8.2 XRD session could settle.

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

- Glenn, Johnson, Dannenberg, Sieck & Countrywood, *Double silver
  low-emissivity and solar control coatings*, US 7,632,572 B2 / US 8,512,883 B2,
  AFG Industries / AGC Flat Glass North America (now Cardinal CG), priority
  2001-09-04. Example 1: TEM grain sizes, epitaxial mechanism, and four-point
  sheet resistance on the two underlayers. **Full text read.**
- *Tuning the interface adhesion of Ag/ZnO composites by metallic dopants: a
  DFT study*, Comput. Mater. Sci. (2023) — polar-plane binding, O- versus
  Zn-termination.
- *Band alignment at Ag/ZnO(0001) interfaces*, Phys. Rev. B **97**, 235430
  (2018) — photoemission, cationic on O face, anionic on Zn face.
- Society of Vacuum Coaters technical review, silicon nitride Low-E stacks —
  NiCr barrier layers for nitride/silver adhesion.

The patent is **fully verified**: full text read via Google Patents, all quoted
figures confirmed in the Description, Example 1. The remaining three sources are
cross-checked against abstracts only. Grade: `LITERATURE` for the patent,
`LITERATURE_UNVERIFIED` for the rest.
