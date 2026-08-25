# Results

Generated output. Everything here is reproducible from the framework and the
data files; nothing here is a source of truth.

## Regenerating

```bash
pvdlowe evaluate > evaluate_default.txt
pvdlowe evaluate --targets ../data/targets_cooling.yaml > evaluate_cooling.txt
pvdlowe validate   > validation.txt
pvdlowe provenance > provenance.txt
pvdlowe report -o report.md
pvdlowe report -o results.xlsx --format excel     # gitignored, not committed
```

## What each file is

| File | Contents | Cost to regenerate |
|---|---|---|
| `evaluate_default.txt` | 38 candidates, heating profile | seconds |
| `evaluate_cooling.txt` | the same, cooling profile | seconds |
| `validation.txt` | model against literature, plus consistency checks | seconds |
| `provenance.txt` | evidence grades and what is not predicted | seconds |
| `report.md` | every table in one document | ~1 minute |
| `metal_dielectric_search.csv` | 5 metals × 8 dielectrics, thickness optimised | ~2 minutes |
| `si3n4_with_phonons.csv` | far-IR phonon penalty check | seconds |
| `double_metal.csv` | n = 1, 2 architectures scored under both profiles | ~10 minutes |
| `multimetal_n_scan.csv` | n = 1, 2, 3 comparison | ~15 minutes |
| `silver_reduction_curve.csv` | silver mass against score | ~1 minute |
| `ag_thickness_sweep.csv` | thickness sweep, physical columns only | ~1 minute |
| `agcu_fine_sweep.csv` | composition sweep, physical columns only | ~5 minutes |
| `microstructure_comparison.csv` | segregated against solid solution, R_s | seconds |
| `broad_metal_search.csv` | 58 metal systems — **scores are stale** | ~30 minutes |
| `composition_series_all.csv` | 168 geometry-optimised points — **scores are stale** | ~13 minutes |

## The two stale files

`broad_metal_search.csv` and `composition_series_all.csv` carry scores computed
before the weighting correction of 2026-08-25, in which metal cost and supply
risk were zeroed as silver proxies (FINDINGS §2, report §5.5).

**Their physical columns — transmittance, emissivity, sheet resistance, silver
mass — are unaffected**, because the correction touched only the scoring. Only
the score column is out of date. Both carry a header comment saying so.

They were not regenerated because they are the two most expensive outputs here
and no conclusion in the documents depends on their score column. Regenerate
them if you need scored versions:

```bash
pvdlowe series --dielectric Si3N4 --mixing ema -o composition_series_all.csv
```
