#!/usr/bin/env python3
"""Batch entrypoint for Vertex AI Custom Jobs.

Runs the framework's expensive analyses in parallel across vCPUs and writes
results straight to GCS. This is the only part of pvdlowe that benefits from
Vertex at all: the sweeps are embarrassingly parallel over composition, and
a 16-vCPU machine turns a four-minute serial run into well under a minute.

Usage inside the container:

    python vertex/job.py --output gs://bucket/runs/2026-08-17 --task all

Tasks:
    silver          the silver-reduction trade-off curve (the expensive one)
    microstructure  solid-solution vs segregated predictions
    sweeps          thickness and oxide-thickness sweeps
    candidates      full candidate evaluation, scoring and report
    validate        model-vs-literature and consistency checks
    all             every task above
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

# Resolve the package relative to this file so the script runs identically
# in the container (/app), on a Workbench instance, and on a laptop.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

DEFAULT_FRACTIONS = (1.0, 0.9, 0.8, 0.7, 0.5, 0.25, 0.0)


def _one_composition(payload):
    """Silver curve for a single composition -- the unit of parallel work.

    Module-level and picklable, which is why it takes a tuple rather than
    keyword arguments.
    """
    fraction, mixing_model, spec = payload
    from pvdlowe.optimize.thickness import silver_reduction_curve
    return silver_reduction_curve(targets=spec, fractions=(fraction,),
                                  mixing_model=mixing_model)


def silver_curve(n_workers: int, mixing_model: str = "solid_solution",
                 spec: dict | None = None) -> pd.DataFrame:
    """Parallel silver-reduction curve.

    Each composition is independent -- the oxide re-optimisation and
    thickness bisection for Ag70Cu30 knows nothing about Ag90Cu10 -- so this
    scales linearly to the number of compositions and then stops. Seven
    compositions means seven useful cores; asking for 32 wastes money.
    """
    payloads = [(x, mixing_model, spec) for x in DEFAULT_FRACTIONS]
    workers = min(n_workers, len(payloads))
    with mp.Pool(processes=workers) as pool:
        frames = pool.map(_one_composition, payloads)
    df = pd.concat(frames, ignore_index=True)

    # ag_saving_pct is relative to pure Ag, which each worker could not see
    base = df.loc[df["ag_fraction"] == 1.0, "Ag_g_per_m2"]
    if len(base) and pd.notna(base.iloc[0]) and base.iloc[0]:
        df["ag_saving_pct"] = (100 * (1 - df["Ag_g_per_m2"]
                                      / base.iloc[0])).round(1)
    return df.sort_values("ag_fraction", ascending=False)


def write(df_or_text, destination: str) -> None:
    """Write a DataFrame or string to GCS or a local path.

    pandas handles gs:// natively through gcsfs; plain text needs the path
    opened explicitly, so route through fsspec when the target is remote.
    """
    if not destination.startswith("gs://"):
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
    if isinstance(df_or_text, pd.DataFrame):
        df_or_text.to_csv(destination, index=False)
    elif destination.startswith("gs://"):
        import fsspec
        with fsspec.open(destination, "w") as fh:
            fh.write(df_or_text)
    else:
        Path(destination).write_text(df_or_text)
    print(f"  wrote {destination}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True,
                        help="gs://bucket/prefix or a local directory")
    parser.add_argument("--task", default="all",
                        choices=["all", "silver", "microstructure", "sweeps",
                                 "candidates", "validate"])
    parser.add_argument("--workers", type=int, default=0,
                        help="0 means use every available vCPU")
    parser.add_argument("--mixing-model", default="solid_solution",
                        choices=["solid_solution", "ema"])
    parser.add_argument("--spec", default=None,
                        help='JSON override, e.g. \'{"T_vis": 0.75}\'')
    args = parser.parse_args()

    workers = args.workers or os.cpu_count() or 1
    out = args.output.rstrip("/")
    spec = json.loads(args.spec) if args.spec else None
    started = time.time()
    print(f"pvdlowe batch run | {workers} workers | output {out}", flush=True)

    tasks = ({"silver", "microstructure", "sweeps", "candidates", "validate"}
             if args.task == "all" else {args.task})

    if "validate" in tasks:
        from pvdlowe.validate import check_consistency, report, validate_model
        print("\nvalidation", flush=True)
        write(validate_model(), f"{out}/validation_model.csv")
        write(check_consistency(), f"{out}/validation_consistency.csv")
        write(report(), f"{out}/validation_report.txt")

    if "candidates" in tasks:
        from pvdlowe.report.export import markdown_report
        from pvdlowe.report.tables import (candidate_table,
                                           comparison_to_benchmarks,
                                           pareto_table)
        print("\ncandidates", flush=True)
        write(candidate_table(), f"{out}/candidates.csv")
        write(comparison_to_benchmarks(), f"{out}/vs_benchmark.csv")
        write(pareto_table(), f"{out}/pareto.csv")
        write(markdown_report(), f"{out}/report.md")

    if "microstructure" in tasks:
        from pvdlowe.optimize.sweep import microstructure_comparison
        print("\nmicrostructure", flush=True)
        write(microstructure_comparison(), f"{out}/microstructure.csv")

    if "sweeps" in tasks:
        from pvdlowe.optimize.sweep import (tco_thickness_sweep,
                                            thickness_sweep)
        print("\nsweeps", flush=True)
        for metal in ("Ag", "Cu"):
            write(thickness_sweep(metal), f"{out}/thickness_sweep_{metal}.csv")
        write(tco_thickness_sweep("Ag", 10.0), f"{out}/tco_sweep_Ag.csv")

    if "silver" in tasks:
        print(f"\nsilver-reduction curve ({args.mixing_model})", flush=True)
        t0 = time.time()
        df = silver_curve(workers, args.mixing_model, spec)
        print(df.to_string(index=False), flush=True)
        print(f"  {time.time() - t0:.1f}s", flush=True)
        write(df, f"{out}/silver_reduction_{args.mixing_model}.csv")

    print(f"\ndone in {time.time() - started:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
