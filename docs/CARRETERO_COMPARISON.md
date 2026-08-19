# Experimental check of the dielectric finding

**Source:** Cueva & Carretero, *Comparison of the Optical Properties of Different
Dielectric Materials (SnO₂, ZnO, AZO, or SiAlNx) Used in Silver-Based
Low-Emissivity Coatings*, Coatings **13**(10), 1709 (2023),
DOI 10.3390/coatings13101709. Open access, CC BY. **Full text read.**

Universidad de Zaragoza, semi-industrial inline magnetron sputtering,
600 × 100 mm rectangular targets, base pressure 7 × 10⁻⁷ mbar, low-iron
soda-lime float glass. 29 single-Ag and 10 double-Ag samples, all dielectrics
deposited to the same thickness on the same system for direct comparison.

This is the closest published experiment to the framework's §5.2 question. It
corroborates one finding and **contradicts another.**

---

## 1. Corroborated: the ApSS 2022 emissivity is inconsistent

The framework flags ε = 0.055 at 9.96 Ω/sq as below the thin-sheet impedance
limit (FINDINGS §1.2). A reasonable objection was that this depends on the
framework's own convention.

**It does not.** Carretero & Cueva compute emissivity from sheet resistance
using a relation from Gläser, *Large Area Glass Coating* (Von Ardenne, 2000) —
a reference in industrial use for two decades:

```
ε_n = 0.0106 · R_□
```

Compared against the framework's independently derived impedance limit:

| R_s (Ω/sq) | 0.0106·R_s | impedance limit | ratio |
|---|---|---|---|
| 2.00 | 0.0212 | 0.0208 | 1.02 |
| 5.50 | 0.0583 | 0.0552 | 1.06 |
| 8.10 | 0.0859 | 0.0792 | 1.08 |
| 9.96 | **0.1056** | **0.0956** | 1.10 |
| 16.60 | 0.1760 | 0.1496 | 1.18 |

The two agree within 10% across the range. The industrial formula is a
linearisation of the same physics the framework derives from Z₀.

**Against the reported value:**

| Basis | ε at 9.96 Ω/sq |
|---|---|
| Reported (ApSS 2022) | 0.055 |
| Industry formula | 0.106 |
| Framework impedance limit | 0.096 |

Reported / industry = **0.52**.

Two independent conventions — one derived from first principles here, one in
industrial use since 2000 — both put the reported emissivity at roughly half
what its sheet resistance permits. **The discrepancy is not a convention
artifact.**

Note also that Carretero & Cueva's own emissivities are *derived from* sheet
resistance via that formula, so their values cannot violate the limit by
construction. Their measured set is internally consistent throughout.

## 2. Contradicted: silicon nitride does not beat AZO

FINDINGS §5.2 concluded that Si₃N₄ outperforms AZO on visible transmittance by
up to nine percentage points, and that the brief's oxide-oriented framing had
excluded a better material class.

**The experiment says otherwise.** Single-Ag structures, 10 nm Ag, identical
deposition and dielectric thickness:

| Dielectric | ε (measured) | n(550 nm) |
|---|---|---|
| SnO₂ | 0.083 | 2.00 |
| ZnO | 0.064 | 2.019 |
| **AZO** | **0.058** | 1.85 |
| AZO + O₂ | 0.063 | — |
| SiAlNx | 0.067 | 2.09 |

AZO is best. And on transmittance, the authors report that the oxides gave
better results, with visible transmission improving from 81.9% with SnO₂ to
86.8% with AZO; at 21 nm Ag, SiAlNx gave 52.7% against ZnO's 60.6%.

**AZO beats the nitride on both axes.**

### Why the framework got it wrong

The authors state the mechanism directly: coatings with AZO obtain the best
photoenergetic performance **because silver growth is more efficient on AZO**.
Elsewhere they attribute it to AZO crystallising more uniformly at greater
thickness, which improves silver crystallisation and spreading.

**This is a nucleation effect, and the framework has no representation of it.**
`pvdlowe` treats the dielectric purely optically — refractive index, thickness,
interference. It has no mechanism by which the underlayer changes the *quality*
of the metal grown on it.

The optical inputs were not the problem. Their measured indices (AZO 1.85,
SiNx 2.023, SnO₂ 2.00) are close to the framework's (AZO 1.90, Si₃N₄ 2.02). The
missing physics is that the choice of dielectric changes the metal film, not
just the interference stack.

**This is the same class of omission as the copper discrepancy** in
FINDINGS §3.6 and `docs/LITERATURE_CALIBRATION.md`: the framework models ideal
metal layers, and the dominant real effect is how the underlayer determines
metal microstructure. Two independent findings now point at the same gap.

### What survives

Three qualifications, all from the same paper:

**Double-metal structures behave differently.** For double-Ag samples the
authors found SiAlNx sample D5A had higher spectral transmittance across the
entire visible range than any other, which they call a surprising result and
attribute tentatively to oxidation and diffusion in the Ti barrier. So the
nitride advantage the framework predicted may be real specifically in the
double-metal architecture — which is where §5.4 recommends it anyway.

**Nitride wins on durability.** SiAlNx is used industrially for mechanical and
thermal protection and to survive tempering. Their sample S6 — AZO first,
SiAlNx last — achieved *better* emissivity than two AZO layers, because
depositing SiAlNx over the Ti barrier converts part of it to TiNx, which
improves emissivity. That hybrid is a better design than either pure stack.

**Copper is not silver.** All of this is measured on silver. Whether copper
also nucleates better on AZO than on a nitride is untested. Given that Si₃N₄'s
attraction for copper was oxygen blocking rather than optics, the nitride case
for Cu is not directly refuted — but it is no longer supported by the
framework's optical argument either.

## 3. Independently validated: two other framework predictions

**The Ti barrier layer.** Every structure in this paper is
dielectric/Ag/**Ti**/dielectric, with a 2–3 nm Ti barrier that protects the
silver from oxidation during reactive deposition of the next oxide layer, and
is thin enough not to alter the overall properties. The framework ranked a Ti
*barrier* above a Ti *alloying addition* (FINDINGS §3.5) on exactly this
logic — interfacial benefit without the conduction-path penalty. Industrial
practice agrees.

**Double-metal architecture.** The authors note that metal double-layer
structures, dielectric/metal/dielectric/metal/dielectric, are widely used by
glass manufacturers where higher visible selectivity and solar control are
required. The framework arrived at that architecture independently in §5.4 by
finding a light-to-solar-gain ceiling that no single-metal stack could pass.

Their double-Ag results also show the expected behaviour: emissivity falls to
0.023–0.031 across all dielectrics, against 0.058–0.083 for single-Ag.

## 4. Consequences

1. **FINDINGS §5.2 must be amended.** The claim that nitrides outperform AZO is
   contradicted for silver, single-metal stacks. The claim that the brief's
   framing excluded nitrides stands; the claim that they are better does not.
2. **FINDINGS §1.2 is strengthened**, and should cite the industrial formula
   alongside the impedance limit.
3. **The framework's known gap is now doubly evidenced.** It models ideal metal
   layers; the dominant real effect in both the copper discrepancy and the
   dielectric comparison is underlayer-dependent metal microstructure. Any
   future version should treat nucleation quality as a first-class parameter,
   not an omission.
4. **The AZO/Ag/Ti/SiAlNx hybrid is worth adding as a candidate** — better
   emissivity than pure AZO *and* the durability to survive tempering.

## 5. Verification status

This paper is fully verified: open access, full text read, measurement basis
confirmed (emissivity computed from four-point sheet resistance via the Gläser
relation; transmittance per DIN EN 410 with D65 and V(λ), 300–2500 nm
spectrophotometry at 8° incidence).
