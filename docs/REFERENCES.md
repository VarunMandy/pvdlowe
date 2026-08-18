# References

## Verification status

**None of the sources cited in the project brief has been verified against
its publisher.** Every citation URL in `PVD_Usecase.docx` carries a
`?utm_source=chatgpt.com` query parameter, which means the reference was
surfaced by a language model. Those references may well be accurate — but a
citation that has not been opened is a lead, not a source.

This matters more than usual here, because two of the transcribed values fail
internal consistency checks (FINDINGS §1, §2), and because the brief's
central recommendation rests on one of them.

| # | Claim used | Brief § | Status |
|---|---|---|---|
| 1 | AZO/Ag/AZO: 78.7% T_vis, 2.7 Ω/sq | 1 | unverified |
| 2 | AZO: 82.4% T_vis, 2.6e-3 Ω·cm, 68 Ω/sq, Eg 3.12 eV | 2 | unverified |
| 3 | AZO(30)/Ag(10)/AZO(30): 80.5% T_vis; Ag(13): 4.36 Ω/sq, 96% FIR | 3 | unverified |
| 4 | AZO/Ag/AZO: 85.4% T_vis, 3.21 Ω/sq, 97% FIR | 3 | unverified |
| 5 | Ag–Cu Low-E, ~30 at.% Cu, neutral colour, good adhesion | 5 | unverified |
| 6 | Ag–Cu ~13% lattice mismatch, segregation tendency | 5 | unverified |
| 7 | GGA underestimates Cu-alloy formation energies; +U improves | 6 | unverified |
| 8 | ~10 nm films: Ag 1.59, Ag–Cu 2.97, Cu 20.5 µΩ·cm | 7 | **fails consistency check** |
| 9 | AZO/Cu/AZO: 16.6 Ω/sq, 67% FIR at 15 nm, continuity ~11 nm | 8 | unverified |
| 10 | AZO(40)/Cu/AZO(40): 87.7% T_vis, 9.96 Ω/sq, ε = 0.055 | 16 | **fails consistency check** |
| 11 | Al:ZnO negative formation energies, 6.25–18.75% Al | 2 | unverified |
| 12 | Cu/Al co-doped ZnO, gap down to 1.13 eV at high Cu | 9 | unverified |
| 13 | Ga:ZnO, formation energy rises with Ga content | 11 | unverified |
| 14 | ZnO = mp-2133, Cu = mp-30 | 12 | checkable via the MP API |

## Sources used by the framework itself

These are not from the brief; they are the physics the code implements.

- **Rakić, Djurišić, Elazar & Majewski (1998)**, *Optical properties of
  metallic films for vertical-cavity optoelectronic devices*, Appl. Opt. 37,
  5271. Lorentz–Drude parameters for Ag, Cu, Al, Au, Ti, Ni, Cr. Used with
  free-electron damping re-anchored to DC resistivity (see METHODOLOGY §2).
- **Fuchs (1938)** and **Sondheimer (1952)** — surface-scattering size effect.
- **Mayadas & Shatzkes (1970)**, Phys. Rev. B 1, 1382 — grain-boundary
  scattering.
- **Bruggeman (1935)** — effective-medium approximation.
- **Nordheim (1931)** — alloy resistivity rule.
- **Derringer & Suich (1980)**, J. Qual. Technol. 12, 214 — desirability
  functions.
- **Wyman, Sloan & Shirley (2013)**, *Simple analytic approximations to the
  CIE XYZ colour matching functions*, JCGT 2, 11 — the V(λ) fit.
- **EN 410** / **ISO 9050** — visible and solar transmittance.
- **EN 12898** — normal emissivity by infrared spectrometry.
- **EN 673** — thermal transmittance, and the hemispherical correction
  polynomial.
- **Box & Behnken (1960)**; **Box & Wilson (1951)** — response-surface designs.

## Sources you will need and do not yet have

- Primary sources for all fourteen brief claims above.
- Tabulated D65 and AM1.5G spectra, if standards-grade T_vis and T_sol are
  needed (the framework currently approximates both and flags them).
- Measured n and k for your own AZO and metal films, which would remove the
  largest single source of visible-range error.
- A measured R_s versus thickness series for each metal, to re-fit the
  specularity and grain-boundary parameters.
