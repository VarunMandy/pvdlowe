"""Command-line interface.

    python -m pvdlowe <command> [options]

The commands mirror the brief's workflow stages, plus three diagnostics that
exist because they are the checks most likely to be skipped: `validate`
tests the model against the transcribed literature, `check-weights` tests
whether the scoring criteria are actually independent, and `provenance`
reports how much of the evidence base has been verified.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _print(df, max_rows: int = 60, index: bool = False) -> None:
    import pandas as pd
    if df is None or (hasattr(df, "empty") and df.empty):
        print("  (no rows)")
        return
    with pd.option_context("display.max_rows", max_rows,
                           "display.max_columns", None,
                           "display.width", 220):
        print(df.to_string(index=index))


def cmd_screen(args):
    from .screening.elements import ElementCriteria, screen
    res = screen(ElementCriteria(max_supply_risk=args.max_supply_risk,
                                 max_price_usd_per_kg=args.max_price))
    print("STAGE 1 -- ELEMENT SCREENING\n")
    _print(res["kept"][["symbol", "name", "role", "crustal_abundance_ppm",
                        "price_usd_per_kg", "supply_risk_score",
                        "sustainability"]])
    if len(res["rejected"]):
        print("\nExcluded:")
        _print(res["rejected"])
    print(f"\n{res['note']}")


def cmd_evaluate(args):
    from .report.tables import candidate_table
    from .screening.scoring import ScoringScheme
    scheme = ScoringScheme.from_yaml(args.targets) if args.targets else None
    if args.targets:
        print(f"CANDIDATE EVALUATION  (weighting: {args.targets})\n")
    else:
        print("CANDIDATE EVALUATION\n")
    _print(candidate_table(scheme=scheme,
                           include_hypotheses=not args.no_hypotheses))
    print("\nScores are model outputs. Rows graded 'hypothesis' have no "
          "measured or calculated properties for that composition.")


def cmd_validate(args):
    from .validate import report
    print(report())


def cmd_check_weights(args):
    import pandas as pd
    from .screening.candidates import evaluate_all
    from .screening.scoring import (ScoringScheme, compare_aggregations,
                                    criterion_correlations, redundant_criteria,
                                    sensitivity_to_weights)
    scheme = ScoringScheme.from_yaml()
    records = evaluate_all().to_dict("records")

    print("CRITERION CORRELATIONS\n")
    _print(criterion_correlations(records, list(scheme.criteria)).round(3),
           index=True)
    redundant = redundant_criteria(records, scheme)
    if redundant:
        print("\nStrongly correlated criterion pairs -- these are not "
              "independent objectives, and weighting them separately "
              "double-counts one physical property:\n")
        _print(pd.DataFrame(redundant))

    print("\n\nAGGREGATION COMPARISON\n")
    _print(compare_aggregations(scheme, records).round(2), index=True)
    print("\nA large rank shift between geometric and arithmetic means the "
          "arithmetic winner is unbalanced. The brief's stated aim -- stopping "
          "a candidate winning on conductivity while failing optically -- "
          "requires the geometric mean, not a weighted sum.")

    print("\n\nWEIGHT SENSITIVITY\n")
    _print(sensitivity_to_weights(scheme, records))


def cmd_optimise(args):
    from .optimize.thickness import optimise_thicknesses
    print(f"OPTIMISING {args.metal}\n")
    res = optimise_thicknesses(args.metal, symmetric=args.symmetric)
    print(f"  metal          {res['metal_thickness_nm']:6.2f} nm")
    print(f"  bottom oxide   {res['bottom_thickness_nm']:6.2f} nm")
    print(f"  top oxide      {res['top_thickness_nm']:6.2f} nm")
    print(f"  score          {res['score']:6.2f} / 100")
    print(f"  limited by     {res['limiting_criterion']}")
    p = res["performance"]
    print(f"\n  T_vis {p['T_vis']:.3f}   eps_h {p['emissivity_hemispherical']:.4f}"
          f"   R_s {p['R_sheet']:.2f} ohm/sq   U_g {p['U_g']:.2f} W/m2K"
          f"   Ag {p['Ag_g_per_m2']:.3f} g/m2")


def cmd_silver(args):
    from .optimize.thickness import silver_reduction_curve
    print("HOW MUCH SILVER CAN BE REMOVED?\n")
    df = silver_reduction_curve()
    _print(df)
    print(f"\nSpecification: {df.attrs.get('specification')}")
    print("Each row is the thinnest metal layer of that composition, with the "
          "oxides re-optimised, that still meets the specification.")


def cmd_sweep(args):
    from .optimize.sweep import microstructure_comparison, thickness_sweep
    if args.what == "thickness":
        _print(thickness_sweep(args.metal))
    else:
        df = microstructure_comparison()
        print("SOLID SOLUTION versus SEGREGATED -- the brief's section 5 "
              "question, as a measurable prediction\n")
        _print(df)
        print(f"\n{df.attrs.get('note', '')}")


def cmd_series(args):
    from .optimize.sweep import composition_series, series_optimum
    from .screening.scoring import ScoringScheme
    scheme = ScoringScheme.from_yaml(args.targets) if args.targets else None
    label = args.targets or "data/targets.yaml"
    print(f"COMPOSITION SERIES  {args.elements}  |  {args.dielectric}  |  "
          f"{args.mixing}  |  weighting {label}\n")
    df = composition_series(mixing_model=args.mixing, dielectric=args.dielectric,
                            scheme=scheme, elements=tuple(args.elements.split("-")))
    _print(df)
    opt = series_optimum(df, f"{args.elements.split('-')[0]}_fraction")
    print(f"\n  optimum at {opt['optimum_fraction']:.2f} "
          f"({opt['optimum_score']:.1f}), plateau "
          f"{opt['plateau_low']:.2f}-{opt['plateau_high']:.2f}, "
          f"Ag {opt['Ag_at_optimum_g_per_m2']:.4f} g/m2")
    print(f"  {df.attrs['note']}")
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\n  written to {args.output}")


def cmd_calibrate(args):
    """Fit the transport model to a measured thickness series."""
    import pandas as pd
    from .electrical.calibrate import diagnose, load_series

    if args.runsheet:
        from .electrical.calibrate import PERCOLATION  # noqa: F401
        print(f"CALIBRATION RUN SHEET -> {args.runsheet}\n")
        rows = []
        for sym, thicknesses in (("Cu", [8, 10, 12, 14, 16, 18, 20]),
                                 ("Ag", [10])):
            for t_nm in thicknesses:
                rows.append({"metal": sym, "thickness_nm": t_nm,
                             "target_power_W": "", "pressure_mTorr": "",
                             "R_sheet_ohm_sq": "", "measured_thickness_nm": "",
                             "notes": ""})
        df = pd.DataFrame(rows)
        # randomise deposition order so tool drift does not alias onto thickness
        df = df.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
        df.insert(0, "run", range(1, len(df) + 1))
        df.to_csv(args.runsheet, index=False)
        _print(df)
        print("\nProtocol:")
        print("  - Randomised order: target erosion drifts over a campaign, and")
        print("    in standard order that drift aliases directly onto thickness.")
        print("  - Measure film thickness independently (profilometry or XRR);")
        print("    rho = R_s * t, so a 20% thickness error is a 20% rho error.")
        print("  - Four-point probe at 5 points per film; record the spread,")
        print("    not just the mean.")
        print("  - The Ag control at 10 nm anchors the tool against a film")
        print("    whose behaviour is already well characterised. If Ag comes")
        print("    out wrong, the Cu series cannot be interpreted.")
        print("  - Deposit on the same underlayer the real stack will use.")
        print("    Percolation depends on what the metal wets.")
        print("\nFill in R_sheet_ohm_sq and re-run:")
        print(f"  pvdlowe calibrate -i {args.runsheet}")
        return

    if not args.input:
        print("error: pass -i RUNSHEET.csv with measurements, or "
              "--runsheet OUT.csv to generate a blank one", file=sys.stderr)
        raise SystemExit(2)

    series = load_series(args.input)
    for sym, g in series.items():
        if len(g) < 4:
            print(f"{sym}: only {len(g)} measured film(s); the fit needs at "
                  f"least 4. Skipping.\n")
            continue
        print("=" * 66)
        rs = g["R_sheet_ohm_sq"].to_numpy(dtype=float)
        if args.capped:
            from .electrical.calibrate import deembed_series
            rs = deembed_series(rs, args.dielectric, args.cap_nm, args.cap_nm)
            print(f"de-embedded {args.dielectric} shunt "
                  f"({args.cap_nm:g} nm each side) from the measured "
                  f"trilayer sheet resistance\n")
        d = diagnose(g["thickness_nm"], rs, sym)
        fit = d["fit_with_excess"]
        print(fit.summary())
        print()
        _print(fit.data)
        print("\nDIAGNOSIS\n")
        for f in d["findings"]:
            print(f"  [{f['verdict']}]")
            print(f"    evidence : {f['evidence']}")
            print(f"    means    : {f['means']}")
            print(f"    next     : {f['next']}")
            print(f"    project  : {f['for_the_project']}\n")


def cmd_surrogate(args):
    """Mixing energies from an ML interatomic potential."""
    from .surrogate import (BACKENDS, Surrogate, available_backends,
                            cross_check, interpret, mixing_energy_series,
                            what_a_surrogate_cannot_answer)
    avail = available_backends()
    if not avail:
        print("No ML interatomic potential installed. Install one:\n")
        for _, label, cmd in BACKENDS:
            print(f"  {cmd:28s}  # {label}")
        print("\nThese are graph neural networks trained on Materials Project")
        print("DFT data -- not language models. They predict energy and forces")
        print("in milliseconds against the core-hours of the DFT they mimic.")
        raise SystemExit(2)
    print("available:", ", ".join(l for _, l, _ in avail), "\n")

    if args.cross_check:
        res = cross_check(n_configs=args.configs)
        for k, v in res.items():
            if k == "frames":
                continue
            print(f"=== {k} ===")
            for kk, vv in v.items():
                print(f"  {kk}: {vv}")
            print()
        for label, df in res.get("frames", {}).items():
            print(f"--- {label} ---")
            _print(df)
        return

    s = Surrogate.load(prefer=args.model)
    print(f"model: {s.label}\n")
    df = mixing_energy_series(s, n_configs=args.configs, relax=not args.no_relax)
    _print(df)
    print(f"\n{df.attrs['note']}\n")
    for k, v in interpret(df, args.temperature).items():
        print(f"  {k}: {v}")
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nwritten to {args.output}")
    if args.limits:
        print()
        for k, v in what_a_surrogate_cannot_answer().items():
            print(f"{k}:")
            if isinstance(v, list):
                for item in v:
                    print(f"  - {item}")
            else:
                print(f"  {v}")


def cmd_doe(args):
    from .doe.design import alias_structure, recommended_screening
    design = recommended_screening()
    print(f"{design.kind}, resolution {design.resolution}, "
          f"{design.n_runs} base runs\n")
    sheet = design.with_run_sheet(seed=args.seed)
    _print(sheet)
    print(f"\n{len(sheet)} runs including centre points.")
    print("\nALIAS STRUCTURE (read before interpreting results)\n")
    _print(alias_structure(design))
    for note in design.notes:
        print(f"\n  note: {note}")
    if args.output:
        sheet.to_csv(args.output, index=False)
        print(f"\nrun sheet written to {args.output}")


def cmd_dft(args):
    from .dft.plans import ag_cu_series_plan, stabiliser_plan
    plan = ag_cu_series_plan()
    plan2 = stabiliser_plan()
    print(f"{plan.title}\n  {len(plan.calculations)} calculations, "
          f"~{plan.total_core_hours:.0f} core-hours")
    print(f"{plan2.title}\n  {len(plan2.calculations)} calculations, "
          f"~{plan2.total_core_hours:.0f} core-hours")
    if args.output:
        root = Path(args.output)
        plan.write(root / "stageA")
        plan2.write(root / "stageA2")
        print(f"\nVASP inputs written to {root}")
        print("POTCAR files are not generated -- assemble them from your own "
              "licensed VASP distribution in the POSCAR element order.")


def cmd_provenance(args):
    from .report.tables import limitations_table, provenance_table
    from .validate import verification_status
    print("EVIDENCE GRADE BY CANDIDATE\n")
    _print(provenance_table())
    print("\n\nNOT PREDICTED BY THIS FRAMEWORK\n")
    _print(limitations_table())
    print(f"\n\n{verification_status()['message']}")


def cmd_report(args):
    from .report.export import markdown_report, to_csv_directory, to_excel
    out = Path(args.output)
    if args.format == "markdown":
        out.parent.mkdir(parents=True, exist_ok=True)
        markdown_report(out)
    elif args.format == "excel":
        to_excel(out, include_sweeps=True)
    else:
        to_csv_directory(out)
    print(f"written to {out}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pvdlowe",
        description="Screening and optimisation for sustainable Low-E PVD "
                    "coatings on float glass.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("screen", help="stage 1: element screening")
    s.add_argument("--max-supply-risk", type=float, default=8.0)
    s.add_argument("--max-price", type=float, default=5000.0)
    s.set_defaults(func=cmd_screen)

    s = sub.add_parser("evaluate", help="evaluate and score all candidates")
    s.add_argument("--no-hypotheses", action="store_true",
                   help="exclude compositions with no measured properties")
    s.add_argument("--targets", help="alternative weighting file, e.g. "
                                     "data/targets_cooling.yaml")
    s.set_defaults(func=cmd_evaluate)

    s = sub.add_parser("validate", help="model vs literature, and consistency")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("check-weights", help="are the criteria independent?")
    s.set_defaults(func=cmd_check_weights)

    s = sub.add_parser("optimise", help="optimise layer thicknesses")
    s.add_argument("--metal", default="Ag")
    s.add_argument("--symmetric", action="store_true")
    s.set_defaults(func=cmd_optimise)

    s = sub.add_parser("silver", help="silver reduction trade-off curve")
    s.set_defaults(func=cmd_silver)

    s = sub.add_parser("sweep", help="parameter sweeps")
    s.add_argument("what", choices=["thickness", "microstructure"])
    s.add_argument("--metal", default="Ag")
    s.set_defaults(func=cmd_sweep)

    s = sub.add_parser("series", help="binary composition series, geometry "
                                     "optimised at every point")
    s.add_argument("--elements", default="Ag-Cu")
    s.add_argument("--dielectric", default="AZO")
    s.add_argument("--mixing", default="solid_solution",
                   choices=["solid_solution", "ema"])
    s.add_argument("--targets", help="weighting file to optimise against")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_series)

    s = sub.add_parser("calibrate",
                       help="fit transport parameters to a measured R_s series")
    s.add_argument("-i", "--input", help="run sheet with R_sheet_ohm_sq filled in")
    s.add_argument("--runsheet", help="generate a blank run sheet at this path")
    s.add_argument("--capped", action="store_true",
                   help="measurements are of a capped trilayer; subtract the "
                        "dielectric shunt before fitting")
    s.add_argument("--dielectric", default="AZO")
    s.add_argument("--cap-nm", type=float, default=40.0)
    s.add_argument("--seed", type=int, default=0)
    s.set_defaults(func=cmd_calibrate)

    s = sub.add_parser("surrogate",
                       help="ML interatomic potential as a DFT surrogate")
    s.add_argument("--model", default="auto",
                   choices=["auto", "mace", "chgnet", "m3gnet", "sevennet"])
    s.add_argument("--validate", action="store_true",
                   help="check the model against known Materials Project values")
    s.add_argument("--ternaries", action="store_true",
                   help="screen the brief's dilute Ti and Al additions")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_surrogate)

    s = sub.add_parser("surrogate",
                       help="mixing energies from an ML interatomic potential")
    s.add_argument("--model", help="chgnet | mace | matgl")
    s.add_argument("--configs", type=int, default=4,
                   help="random decorations averaged per composition")
    s.add_argument("--temperature", type=float, default=300.0)
    s.add_argument("--no-relax", action="store_true",
                   help="skip geometry relaxation (faster, and wrong for Ag-Cu)")
    s.add_argument("--cross-check", action="store_true",
                   help="run two potentials and compare")
    s.add_argument("--limits", action="store_true",
                   help="print what a surrogate cannot answer")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_surrogate)

    s = sub.add_parser("doe", help="generate a sputter run sheet")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_doe)

    s = sub.add_parser("dft", help="generate VASP inputs")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_dft)

    s = sub.add_parser("provenance", help="evidence grades and limitations")
    s.set_defaults(func=cmd_provenance)

    s = sub.add_parser("report", help="write a full report")
    s.add_argument("-o", "--output", default="report.md")
    s.add_argument("--format", choices=["markdown", "excel", "csv"],
                   default="markdown")
    s.set_defaults(func=cmd_report)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:               # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
