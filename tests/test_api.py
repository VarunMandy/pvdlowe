"""Tests for the HTTP interface.

The interface exists to make the framework usable without the CLI. The risk it
introduces is a second implementation of the physics -- a JavaScript solver in
the browser, or recomputation in a route handler -- which is the defect class
this project has already been bitten by twice (code review M1, and the emitted
frame that renamed a criterion). These tests pin the constraint that every
number comes from the same functions the CLI and suite use.

Skipped cleanly if flask is absent; nothing else in the package needs it.
"""

try:
    from pvdlowe.api import app
    HAVE_FLASK = True
except ImportError:                                          # pragma: no cover
    HAVE_FLASK = False


def _client():
    return app.test_client()


def test_evaluate_agrees_with_the_framework_exactly():
    """The endpoint must not recompute anything.

    Any divergence here means a second code path has appeared, which is the
    whole hazard of adding an interface.
    """
    if not HAVE_FLASK:
        return
    from pvdlowe.materials.tco import tco
    from pvdlowe.optimize.thickness import build
    from pvdlowe.screening.candidates import record_for

    direct = record_for(build("Ag", 10.0, 35.0, 35.0, tco("AZO")))
    served = _client().post("/evaluate", json={
        "metal": "Ag", "metal_nm": 10.0, "bottom_nm": 35.0,
        "top_nm": 35.0, "dielectric": "AZO"}).get_json()["performance"]

    for key in ("T_vis", "emissivity_hemispherical", "R_sheet", "Ag_g_per_m2"):
        assert abs(served[key] - direct[key]) < 1e-5, (
            f"{key} differs between the API and record_for: "
            f"{served[key]} vs {direct[key]} -- a second code path has appeared")


def test_out_of_range_input_is_refused_not_clamped():
    """A clamped input returns a number for a coating nobody asked about."""
    if not HAVE_FLASK:
        return
    r = _client().post("/evaluate", json={"metal_nm": 999.0})
    assert r.status_code == 400
    assert "outside" in r.get_json()["error"]

    bad = _client().post("/evaluate", json={"dielectric": "unobtainium"})
    assert bad.status_code == 400


def test_sub_percolation_films_report_why_they_fail():
    """"Fails R_sheet" is true but misleading below percolation.

    A 9 nm silver layer is islands, not a film. Reporting only the three
    specified properties would suggest a thickness problem when the layer has
    stopped existing as a conductor.
    """
    if not HAVE_FLASK:
        return
    spec = _client().post("/evaluate", json={
        "metal_nm": 9.0, "dielectric": "AZO"}).get_json()["spec"]
    assert spec["meets_spec"] is False
    assert spec["continuous"] is False
    assert "percolation" in spec["note"]


def test_every_response_carries_the_copper_caveat():
    """The framework's largest known error must travel with its output.

    An eightfold under-prediction of sputtered copper sheet resistance is not
    something a caller should have to go looking for.
    """
    if not HAVE_FLASK:
        return
    d = _client().post("/evaluate", json={"metal": "Cu", "metal_nm": 12.0}).get_json()
    assert "eightfold" in d["caveat"] or "copper" in d["caveat"]


def test_candidate_listing_warns_about_the_weighting_file():
    """A ranking without its weighting file is the easiest way to misuse this."""
    if not HAVE_FLASK:
        return
    d = _client().get("/candidates?n=5").get_json()
    assert len(d["candidates"]) == 5
    assert "weighting file" in d["warning"]
    assert d["targets"]


def test_weight_sweep_is_exposed_because_the_weight_decides_the_answer():
    """The silver weight is a judgement, and the interface must show that."""
    if not HAVE_FLASK:
        return
    d = _client().get("/weight-sweep").get_json()
    assert d["transitions"], "expected the winner to change across the range"
    assert len(d["sweep"]) >= 5
