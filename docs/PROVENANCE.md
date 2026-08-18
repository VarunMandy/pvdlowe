# Provenance

Every physical quantity in this framework carries an evidence grade. This
exists because the brief itself insists on it:

> I would **not yet put numerical DFT values for Ag₇₀Cu₂₉Ti₁, Ag₇₀Cu₂₉Al₁,
> etc. into a thesis as if they were established facts**.

Implementing that as a type rather than a footnote means the distinction
survives contact with a spreadsheet.

## Grades

| Grade | Meaning | Reportable |
|---|---|---|
| `MEASURED` | measured on your own sample | yes |
| `LITERATURE` | published and verified against the primary source | yes |
| `LITERATURE_UNVERIFIED` | published, cited, **not yet read from the publisher** | with caveat |
| `MP_API` | retrieved from the Materials Project, with material ID | yes |
| `DFT_OWN` | computed by you, with method recorded | yes |
| `DFT_LITERATURE` | published first-principles result for that family | with caveat |
| `MODEL` | output of a physical model in this framework | yes, as a model |
| `CALIBRATED` | model parameter fitted to reproduce a known value | yes, disclose the fit |
| `ESTIMATE` | plausible value, no specific source | no |
| `HYPOTHESIS` | proposed composition with no measured or calculated properties | **no** |

`assert_reportable(quantity)` raises on `HYPOTHESIS` and `ESTIMATE` grades
unless explicitly overridden.

## Current state of the evidence base

**All eight literature benchmarks are `LITERATURE_UNVERIFIED`.** The brief's
citation URLs all carry `?utm_source=chatgpt.com`, meaning they were surfaced
by a language model rather than read from the publisher. That does not make
them wrong — several are reproduced well by the model, which is weak
evidence that they are right. It does mean none has been checked, and two of
them fail internal consistency checks (see FINDINGS §1 and §2).

`python -m pvdlowe provenance` prints the current status.

## Verifying a benchmark

1. Find the primary source. The `source_hint` and `citation` fields in
   `data/benchmarks.yaml` are starting points, not DOIs.
2. Confirm the numbers, the layer thicknesses, **and the measurement basis** —
   normal versus hemispherical emissivity, average versus weighted visible
   transmittance, and whether all quoted values come from the same sample.
3. Set `verified: true` and record the DOI.
4. Re-run `python -m pvdlowe validate`.

Do not set `verified: true` from a search result or an abstract. The whole
point of the flag is that someone has read the paper.

## Things that are calibrated, and to what

| Parameter | Calibrated to | Where |
|---|---|---|
| Glass far-IR oscillator scale (1.3566) | bare-glass ε_n = 0.837 | `materials/glass.py` |
| TCO band-edge strength | n(550 nm) = preset value | `materials/tco.py` |
| Ag percolation d_c = 10 nm | brief §3, unverified | `electrical/thinfilm.py` |
| Cu percolation d_c = 11 nm | brief §8, unverified | `electrical/thinfilm.py` |
| Drude damping | metal DC resistivity | `materials/metals.py` |
| Nordheim coefficients | dilute-limit dρ/dc | `materials/alloys.py` |

A calibrated parameter is honest as long as the calibration is disclosed and
the model is not then used to "predict" the thing it was calibrated to.
