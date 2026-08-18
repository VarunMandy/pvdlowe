# Methodology

The physics implemented, the approximations made, and where each one breaks.

---

## 1. Optical multilayer

**Transfer matrix method**, coherent, complex refractive indices, both
polarisations, arbitrary angle. Characteristic matrix per layer:

```
M_j = [[cos d_j,  -i sin d_j / eta_j],
       [-i eta_j sin d_j,  cos d_j]],     d_j = 2 pi n_j t_j cos(theta_j) / lambda
```

with `eta = n cos(theta)` for s-polarisation and `n / cos(theta)` for p.
Complex angles are handled by carrying `cos(theta)` as a complex number
throughout and selecting the branch with non-negative imaginary part, which
is the condition for a decaying rather than growing evanescent field.

Verified against: exact Fresnel for a bare interface, exact null for a
quarter-wave antireflection layer, R + T + A = 1 to 1e-10 on an absorbing
stack, and s/p agreement at normal incidence.

**Thick glass is incoherent.** A 4 mm pane is millions of wavelengths thick;
treating it coherently produces interference fringes that no real glazing
shows. `incoherent_sandwich()` combines the coated front surface with the
back surface by summing intensities rather than amplitudes.

*Breaks when:* layers approach or exceed the coherence length of the source,
or when interface roughness is comparable to the wavelength. The model has no
roughness — a real sputtered stack with 1–2 nm RMS roughness will transmit
slightly less and scatter slightly more than predicted.

## 2. Optical constants

**Metals** use the Lorentz–Drude form of Rakić et al. (1998): one free-electron
term plus bound-electron oscillators, with the convention exp(−iωt), ε₂ ≥ 0.

One important departure from the published parameters. Rakić's fitted Γ₀ for
silver is 0.048 eV, which implies a DC resistivity near 4.4 µΩ·cm against
silver's true 1.587. This is normal for optical fits — in the visible the
Drude damping trades off against the interband oscillators, so the fit
recovers the spectrum without recovering the transport. Using it directly and
then multiplying by a thin-film size-effect ratio **double-counts the same
scattering**, which inflated modelled emissivity roughly threefold in the
first build of this framework.

The fix: anchor free-electron damping to DC resistivity,

```
Gamma = eps_0 * E_p^2 * e * rho / hbar
```

giving 0.0146 eV for Ag and 0.0152 eV for Cu. Interband oscillators are
retained from Rakić unchanged, since they are independent of the Drude term.
This makes the far-infrared response exactly consistent with the resistivity
model, which is what emissivity depends on.

*Breaks when:* you need visible-range accuracy better than a few per cent.
Use `TabulatedIndex` with your own ellipsometry.

**TCOs** are parameterised by carrier density N, mobility µ and effective
mass m*, from which the plasma frequency, the Burstein–Moss gap shift, and
the DC resistivity all follow. One parameter set, three consistent
predictions — so a TCO fitted to one Hall measurement behaves correctly
everywhere it appears, and an inconsistent literature entry shows up as a
contradiction rather than sitting quietly in a table. The band-edge
oscillator strength is calibrated so n(550 nm) matches a measurable value.

**Float glass** uses a two-term Sellmeier fit in the visible and NIR, and
Lorentz oscillators for the Si–O reststrahlen bands in the far infrared. The
far-IR oscillator strengths are **calibrated**, not derived: the scale factor
1.3566 is chosen so bare-glass normal emissivity comes out at the accepted
0.837. `substrate_sensitivity()` demonstrates that this calibration does not
propagate into coated results — once the metal exceeds about 5 nm, the
substrate contributes almost nothing to the far-IR response.

## 3. Thin-film transport

At 8–15 nm, bulk resistivity is wrong by a factor of two to five.

**Fuchs–Sondheimer** (surface scattering) is solved as the full integral
rather than the large-κ series, because at d/λ ≈ 0.2 the series is not valid:

```
rho_0/rho = 1 - (3/2k)(1-p) INT_1^inf (1/t^3 - 1/t^5)(1 - e^-kt)/(1 - p e^-kt) dt
```

**Mayadas–Shatzkes** (grain boundaries) uses the standard closed form with
α = (λ/D)·R/(1−R). Grain size is taken as 3× the film thickness, reflecting
the lateral grain structure of a coalesced sputtered film rather than a
columnar one.

**Percolation** below a critical thickness. Volmer–Weber growth on an oxide
gives islands that coalesce only above some d_c; the multiplier is
constructed to equal exactly 1.0 at d_c and diverge as d approaches the
percolation threshold d_p = 0.75·d_c. Calibrated to the brief's own anchors:
Ag continuous near 10 nm, Cu near 11 nm.

**The coupling that matters:** the same resistivity ratio feeds back into the
Drude damping. A film too thin to conduct is automatically a film that
reflects poorly. Without this, optimising for visible transmittance drives
the silver thickness to zero and reports an excellent coating.

*Breaks when:* specularity and grain-boundary reflection are treated as
physical constants. They are fitting parameters. Re-fit them to a measured
R_s(d) series before quoting an absolute sheet resistance.

## 4. Alloys

Two microstructures, deliberately both implemented:

- **Solid solution** — one Drude term with fraction-weighted f₀ω_p², damping
  raised by Nordheim alloy scattering (ρ = Σxᵢρᵢ + ΣC_ij x_i x_j), plus
  composition-weighted interband structure.
- **Effective medium** — Ag-rich and Cu-rich domains combined by Bruggeman.

Which one a real sputtered film matches is an experimental question, and
`discriminating_wavelengths()` reports where the two predictions diverge
enough to be told apart. See FINDINGS §5.

*Breaks when:* domains approach the wavelength in size, where Bruggeman's
quasi-static assumption fails and Mie scattering takes over. Also, linear
mixing of dielectric functions is a first-order approximation for a
disordered alloy — a real calculation of the alloy band structure is the DFT
work the brief proposes.

## 5. Standards integration

- **T_vis, T_sol** — EN 410 / ISO 9050 weighting. The CIE V(λ) photopic curve
  uses the Wyman et al. (2013) multi-lobe analytic fit. D65 and AM1.5 are
  approximated by Planckians and **flagged as MODEL** — supply the tabulated
  spectra via `Weighting.from_csv()` for standards-grade work.
- **Normal emissivity** — EN 12898, 1 − R(λ) weighted by the 283 K Planck
  radiance. This weighting is exact and needs no external data, which is why
  the headline metric is the most trustworthy number the framework produces.
- **Hemispherical emissivity** — the EN 673 polynomial
  ε_h = 1.1887ε − 0.4967ε² + 0.2452ε³, cross-checked against direct angular
  integration (`hemispherical_emissivity_direct`). The two agree to 0.003 for
  a typical Low-E stack.
- **U-value** — EN 673 centre-pane, with gas conductance for air, argon,
  krypton and xenon.

## 6. Scoring

Derringer–Suich desirability per criterion, aggregated by **geometric** mean
by default. Each criterion maps its value onto [0, 1] between a floor (
unacceptable) and a target (fully satisfied), with an adjustable exponent.

Geometric rather than arithmetic because the brief's stated intent — stopping
a candidate winning on one axis while failing on another — is a property of
the geometric mean and not of a weighted sum. See FINDINGS §4.

Weights renormalise over whichever criteria are actually available, so a
candidate missing a measured thermal-stability number is scored on the rest
rather than silently penalised for the gap.

## 7. What is not modelled

Deposition rate without calibration, adhesion, roughness, interdiffusion,
agglomeration kinetics, damp-heat and abrasion durability, and any property
of a metastable sputtered alloy that a 0 K ordered-crystal database cannot
supply. `not_predicted()` is the machine-readable list.
