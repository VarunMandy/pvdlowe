"""HTTP interface to the framework.

**One source of truth.** Every endpoint calls the same functions the CLI and
the test suite call. Nothing is recomputed here and nothing is reimplemented in
the browser — the front end is a form and a table, and every number in it comes
from a round trip to Python.

That constraint is deliberate. This project has already been bitten twice by
the same defect: two places building a scoreable record and drifting apart
(code review M1), and an emitted frame renaming a criterion so that re-scoring
it silently dropped a quarter of the weight. A JavaScript transfer-matrix
solver would be a third instance of it, and a worse one, because nothing would
compare the two.

Run it with::

    pip install flask
    python -m pvdlowe.api            # http://127.0.0.1:5000

Or point a browser at ``/`` for the interactive form, ``/docs`` for the
endpoint list.
"""

from __future__ import annotations

import json

from flask import Flask, jsonify, request

from ..materials.alloys import Alloy
from ..materials.tco import TCOS, tco
from ..optics.integrate import performance_summary
from ..optimize.thickness import build
from ..screening.candidates import evaluate_all, record_for
from ..screening.scoring import ScoringScheme, weight_sweep

app = Flask(__name__)

#: Values a caller may reasonably supply. Anything outside these is refused
#: rather than silently clamped, because a clamped input returns a number for
#: a coating the caller did not ask about.
LIMITS = {
    "metal_nm": (1.0, 60.0),
    "dielectric_nm": (0.0, 400.0),
    "ag_fraction": (0.0, 1.0),
}

SPEC = {"T_vis": 0.80, "R_sheet": 5.0, "emissivity_hemispherical": 0.10}


def _bounded(name: str, value, lo: float, hi: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: expected a number, got {value!r}")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: {v} is outside {lo}-{hi}")
    return v


def _coating_from(payload: dict):
    """Build a coating from a request body, refusing anything out of range."""
    metal = str(payload.get("metal", "Ag"))
    x = payload.get("ag_fraction")
    if x is not None:
        x = _bounded("ag_fraction", x, *LIMITS["ag_fraction"])
        mixing = str(payload.get("mixing_model", "solid_solution"))
        if mixing not in ("solid_solution", "ema"):
            raise ValueError("mixing_model must be solid_solution or ema")
        comp = ({"Ag": 1.0} if x >= 1.0 else
                {"Cu": 1.0} if x <= 0.0 else {"Ag": x, "Cu": 1.0 - x})
        metal = Alloy(comp, mixing_model=mixing)

    dielectric = str(payload.get("dielectric", "AZO"))
    if dielectric not in TCOS:
        raise ValueError(f"dielectric must be one of {sorted(TCOS)}")

    return build(
        metal,
        _bounded("metal_nm", payload.get("metal_nm", 10.0), *LIMITS["metal_nm"]),
        _bounded("bottom_nm", payload.get("bottom_nm", 35.0), *LIMITS["dielectric_nm"]),
        _bounded("top_nm", payload.get("top_nm", 35.0), *LIMITS["dielectric_nm"]),
        tco(dielectric))


def _spec_check(record: dict) -> dict:
    """Which of the three specified properties this coating fails, and why.

    Reported alongside continuity, because a discontinuous film fails for a
    reason none of the three names: it has stopped being a film.
    """
    failures = []
    if record["T_vis"] < SPEC["T_vis"]:
        failures.append("T_vis")
    if record["R_sheet"] > SPEC["R_sheet"]:
        failures.append("R_sheet")
    if record["emissivity_hemispherical"] > SPEC["emissivity_hemispherical"]:
        failures.append("emissivity")
    return {
        "meets_spec": not failures and bool(record["continuous"]),
        "failures": failures,
        "continuous": bool(record["continuous"]),
        "note": ("below percolation -- the layer is islands, not a film"
                 if not record["continuous"] else ""),
        "specification": SPEC,
    }


@app.get("/health")
def health():
    from .. import __version__
    return jsonify({"status": "ok", "version": __version__,
                    "dielectrics": sorted(TCOS)})


@app.post("/evaluate")
def evaluate_one():
    """Evaluate one coating. The single most useful endpoint."""
    payload = request.get_json(silent=True) or {}
    try:
        coating = _coating_from(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    record = record_for(coating)
    scheme = ScoringScheme.from_yaml(payload.get("targets"))
    scored = scheme.score(record)

    numeric = {k: (round(v, 5) if isinstance(v, float) else v)
               for k, v in record.items()
               if isinstance(v, (int, float, bool, str)) or v is None}
    return jsonify({
        "coating": coating.label,
        "performance": numeric,
        "score": round(scored["score"], 2),
        "limiting_criterion": scored["limiting_criterion"],
        "missing_criteria": scored["missing"],
        "spec": _spec_check(record),
        "caveat": ("model output. The framework under-predicts sputtered copper "
                   "sheet resistance by roughly eightfold; see docs/FINDINGS.md "
                   "section 3.6 before using a copper-bearing result."),
    })


@app.get("/candidates")
def candidates():
    """The scored candidate table, under either climate profile."""
    targets = request.args.get("targets")
    scheme = ScoringScheme.from_yaml(targets)
    frame = evaluate_all()
    records = frame.to_dict("records")
    frame["score"] = [scheme.score(r)["score"] for r in records]
    cols = ["id", "label", "T_vis", "emissivity_hemispherical", "R_sheet",
            "g_value", "LSG", "Ag_g_per_m2", "score"]
    top = frame.nlargest(int(request.args.get("n", 10)), "score")[cols]
    return jsonify({
        "targets": targets or "data/targets.yaml",
        "candidates": json.loads(top.round(4).to_json(orient="records")),
        "warning": ("a ranking is meaningless without its weighting file. The "
                    "two climate profiles disagree on the winner and on nine of "
                    "ten top-ten positions."),
    })


@app.get("/weight-sweep")
def sweep():
    """How the winner moves with one criterion's weight.

    Exposed because the silver weight of 0.15 is a judgement, not a
    measurement, and it selects the answer.
    """
    key = request.args.get("key", "Ag_g_per_m2")
    frame = weight_sweep(evaluate_all().to_dict("records"), key=key)
    return jsonify({
        "criterion": key,
        "sweep": json.loads(frame.to_json(orient="records")),
        "transitions": frame.attrs.get("transitions", []),
        "note": frame.attrs.get("note", ""),
    })


@app.get("/validate")
def validate():
    """Model against literature, and the internal consistency checks."""
    from ..validate import check_consistency, validate_model, verification_status
    frame = validate_model().dropna(subset=["modelled"])
    return jsonify({
        "median_rel_error_pct": frame.attrs.get("median_rel_error_pct"),
        "excluded": frame.attrs.get("excluded", []),
        "note": frame.attrs.get("note", ""),
        "verification": {k: v for k, v in verification_status().items()
                         if k != "provenance"},
        "consistency": json.loads(
            check_consistency()[["id", "severity", "check", "detail"]]
            .to_json(orient="records")),
    })


@app.get("/docs")
def docs():
    return jsonify({
        "GET  /health": "version and available dielectrics",
        "POST /evaluate": {
            "body": {"metal": "Ag | Cu | ...", "ag_fraction": "0-1, optional, "
                     "makes an Ag-Cu alloy and overrides `metal`",
                     "mixing_model": "solid_solution | ema",
                     "metal_nm": 10.0, "bottom_nm": 35.0, "top_nm": 35.0,
                     "dielectric": "AZO | Si3N4 | SnO2 | TiO2 | ITO | GZO | FTO",
                     "targets": "optional path to a weighting file"},
        },
        "GET  /candidates?n=10&targets=...": "the scored candidate table",
        "GET  /weight-sweep?key=Ag_g_per_m2": "how the winner moves with a weight",
        "GET  /validate": "model against literature, plus consistency checks",
        "note": ("every endpoint calls the same functions as the CLI and the "
                 "test suite. Nothing is recomputed here."),
    })


@app.get("/")
def index():
    from .ui import PAGE
    return PAGE


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="pvdlowe HTTP interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    print(f"pvdlowe API on http://{args.host}:{args.port}  (/ for the form, "
          f"/docs for endpoints)")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


__all__ = ["app", "main", "SPEC", "LIMITS"]
