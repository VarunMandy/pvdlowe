"""Validation, DoE and DFT planning."""

import numpy as np

from pvdlowe.dft.plans import (fcc_supercell_poscar, mixing_energy,
                               smallest_supercell)
from pvdlowe.doe.design import (alias_structure, box_behnken,
                                central_composite, fractional_factorial,
                                full_factorial, latin_hypercube,
                                recommended_screening)
from pvdlowe.doe.sputter import SputterModel, rate_ratios
from pvdlowe.validate import (check_consistency, emissivity_to_sheet_resistance,
                              sheet_resistance_to_emissivity, validate_model,
                              verification_status)


def test_impedance_relation_round_trips():
    for rs in (2.0, 5.0, 10.0, 30.0):
        eps = sheet_resistance_to_emissivity(rs)
        back = emissivity_to_sheet_resistance(eps)
        assert abs(back - rs) / rs < 1e-6, (rs, back)


def test_lower_sheet_resistance_gives_lower_emissivity():
    values = [sheet_resistance_to_emissivity(r) for r in (2, 5, 10, 20)]
    assert all(a < b for a, b in zip(values, values[1:])), values


def test_consistency_check_flags_the_cu_emissivity_claim():
    """The pivotal AZO/Cu/AZO number must be flagged as below the limit."""
    findings = check_consistency()
    high = findings[findings["severity"] == "high"]
    assert len(high) >= 1
    assert any("azo_cu_azo_optimised" == i for i in high["id"])


def test_consistency_check_flags_bulk_resistivity_at_10nm():
    findings = check_consistency()
    assert any("agcu_thin_film" in i for i in findings["id"])


def test_model_validation_runs_and_is_not_absurd():
    mv = validate_model().dropna(subset=["modelled"])
    assert len(mv) >= 6
    assert mv["rel_error_pct"].median() < 60


def test_verification_flags_require_a_citation():
    """A benchmark may only claim verification if it records a source.

    Replaces an earlier test that asserted nothing was verified. Two entries
    are now 'partial' -- located, numbers confirmed against the published
    abstract, full text unread. The guard that matters is not "nothing is
    verified" but "nothing claims verification without a citation and a note
    saying what was and was not checked".
    """
    from pvdlowe.validate import load_benchmarks
    for bm in load_benchmarks():
        state = bm.get("verified", False)
        if state is False:
            continue
        assert state in (True, "partial", "disputed"), (bm["id"], state)
        assert bm.get("citation", "").strip(), f"{bm['id']} claims verification with no citation"
        assert bm.get("verified_note", "").strip(), f"{bm['id']} must record what was NOT checked"


def test_verification_states_partition_the_benchmarks():
    """Every benchmark sits in exactly one state.

    Replaces an earlier test asserting nothing was fully verified. One entry
    (azo_standalone, Materials 17(1) 81) is now `true`: its full text was read
    via the open-access version and the measurement basis confirmed. The guard
    that remains useful is the partition, not a zero count.
    """
    status = verification_status()
    assert (status["verified"] + status["partial"] + status["disputed"]
            + status["unverified"]) == status["total"]
    assert status["verified"] >= 1, "expected at least one fully verified entry"


def test_full_verification_requires_more_than_an_abstract():
    """A `true` flag must record what was read, not merely that it was found."""
    from pvdlowe.validate import load_benchmarks
    for bm in load_benchmarks():
        if bm.get("verified") is not True:
            continue
        note = bm.get("verified_note", "")
        assert "full text" in note.lower(), (
            f"{bm['id']} claims full verification without recording that the "
            "full text was read")


def test_full_factorial_size():
    d = full_factorial(["metal_thickness_nm", "metal_power_w"], levels=2)
    assert d.n_runs == 4


def test_fractional_factorial_resolution_iv_has_clean_main_effects():
    d = fractional_factorial(
        ["metal_thickness_nm", "metal_power_w", "metal_pressure_mtorr",
         "substrate_temperature_c", "azo_thickness_nm", "azo_al_percent",
         "oxygen_fraction_pct"], n_base=4)
    assert d.n_runs == 16 and d.resolution == "IV"
    aliases = alias_structure(d, max_order=2)
    # no main effect may appear as a primary aliased effect
    mains = set(d.names)
    assert not (mains & set(aliases["effect"]))


def test_design_columns_are_orthogonal():
    d = recommended_screening()
    X = d.coded
    gram = X.T @ X / len(X)
    assert np.allclose(gram, np.eye(X.shape[1]), atol=1e-12)


def test_box_behnken_has_no_corner_points():
    d = box_behnken(["metal_thickness_nm", "metal_power_w",
                     "metal_pressure_mtorr"])
    assert not np.any(np.all(np.abs(d.coded) == 1, axis=1))


def test_central_composite_face_centred_stays_in_range():
    d = central_composite(["metal_thickness_nm", "metal_power_w"],
                          face_centred=True)
    assert np.max(np.abs(d.coded)) <= 1.0 + 1e-12


def test_latin_hypercube_is_space_filling():
    d = latin_hypercube(["metal_thickness_nm", "metal_power_w"], n_samples=20,
                        seed=3)
    for i in range(d.coded.shape[1]):
        counts, _ = np.histogram(d.coded[:, i], bins=4, range=(-1, 1))
        assert counts.min() >= 3, counts


def test_run_sheet_includes_centre_points():
    sheet = recommended_screening().with_run_sheet(seed=1,
                                                   replicates_at_centre=3)
    assert sheet["is_centre"].sum() >= 3
    assert list(sheet["run"]) == list(range(1, len(sheet) + 1))


def test_uncalibrated_sputter_model_refuses_absolute_rates():
    m = SputterModel("Ag")
    try:
        m.rate_nm_per_min(150.0)
    except RuntimeError:
        pass
    else:
        raise AssertionError("uncalibrated model returned an absolute rate")


def test_calibrated_sputter_model_reproduces_its_calibration():
    m = SputterModel("Cu").calibrate(9.0, 150.0)
    assert abs(m.rate_nm_per_min(150.0) - 9.0) < 1e-9


def test_rate_ratios_available_without_calibration():
    df = rate_ratios()
    ag = df[df["material"] == "Ag"]["relative_rate_vs_Ag"].iloc[0]
    assert abs(ag - 1.0) < 1e-9
    assert df["relative_rate_vs_Ag"].min() > 0


def test_supercell_selection_is_exact():
    sc = smallest_supercell((1.0, 0.9, 0.75, 0.7, 0.5, 0.25, 0.0))
    n = 4 * sc[0] * sc[1] * sc[2]
    for f in (0.9, 0.75, 0.7, 0.5, 0.25):
        assert abs(f * n - round(f * n)) < 1e-9, (f, n)


def test_poscar_has_correct_atom_count():
    txt = fcc_supercell_poscar({"Ag": 0.75, "Cu": 0.25}, (2, 2, 2))
    lines = txt.strip().split("\n")
    counts = [int(x) for x in lines[6].split()]
    assert sum(counts) == 32
    assert len(lines) == 8 + 32


def test_poscar_is_deterministic():
    a = fcc_supercell_poscar({"Ag": 0.5, "Cu": 0.5}, (2, 2, 2), seed=4)
    b = fcc_supercell_poscar({"Ag": 0.5, "Cu": 0.5}, (2, 2, 2), seed=4)
    assert a == b


def test_mixing_energy_sign_convention():
    q = mixing_energy(-2.5, {"Ag": -2.7, "Cu": -3.5}, {"Ag": 0.5, "Cu": 0.5})
    assert q.value > 0                      # above the weighted average
    q2 = mixing_energy(-3.2, {"Ag": -2.7, "Cu": -3.5}, {"Ag": 0.5, "Cu": 0.5})
    assert q2.value < 0


def test_validation_table_reports_the_true_source_state():
    """A tri-state flag must not be collapsed to a boolean.

    'partial' and 'disputed' are truthy strings; reporting them as verified
    would defeat the point of grading the evidence at all.
    """
    # the audit view, which still contains everything
    df = validate_model(include_disputed=True)
    states = set(df["source_state"])
    assert states <= {True, "partial", "disputed", "not located"}, states
    assert True in states, "expected at least one fully verified source"
    assert "disputed" in states, "the two unmatched entries must show as disputed"

    # and the default view, which must not
    default = validate_model()
    assert "disputed" not in set(default["source_state"]), (
        "disputed entries must be excluded from the default validation table")


def test_surrogate_refuses_cleanly_when_unavailable():
    """A missing potential must raise SurrogateUnavailable with install advice,
    not a bare ImportError. The framework's convention is that a missing
    capability is an error, never an invitation to produce a plausible number.
    """
    from pvdlowe.dft.surrogate import (SurrogateUnavailable, mixing_energy_series,
                                       screen_ternaries, validate_against_hull)
    import importlib
    try:
        importlib.import_module("ase")
    except ImportError:
        pass
    else:
        return                      # a potential may genuinely be installed
    for fn in (mixing_energy_series, screen_ternaries, validate_against_hull):
        try:
            fn()
        except SurrogateUnavailable as exc:
            assert "pip install" in str(exc), str(exc)
        else:
            raise AssertionError(f"{fn.__name__} did not refuse")


def test_surrogate_results_are_graded_below_dft():
    """A surrogate value must never be reportable as a calculation."""
    from pvdlowe.provenance import Provenance
    assert Provenance.ML_SURROGATE.rank < Provenance.DFT_OWN.rank
    assert Provenance.ML_SURROGATE.rank < Provenance.MP_API.rank
    assert Provenance.ML_SURROGATE.needs_verification


def test_surrogate_carries_mp_reference_values():
    """Validation targets must match what stage 2 actually retrieved."""
    from pvdlowe.dft.surrogate import MP_REFERENCE
    assert abs(MP_REFERENCE["Cu3Ag"] - 0.0904) < 1e-4
    assert abs(MP_REFERENCE["CuAg3"] - 0.0857) < 1e-4


def test_source_actual_records_conflicts_between_sources():
    """Where two publications of the same work disagree, record both figures.

    The brief quotes 1.59 uohm.cm for a 10 nm Ag film. The journal article says
    1.59 -- so the brief is FAITHFUL -- while the group's own patent says 1.29,
    which is below bulk silver and therefore impossible.

    An earlier version of this test encoded the opposite conclusion, that the
    brief had mistranscribed the value. That was reached by reading one source,
    finding a different number, and assuming the other party was careless. It
    is the same error made over the AZO transmittance, and the guard now
    asserts the corrected shape so it cannot quietly revert.
    """
    from pvdlowe.validate import load_benchmarks
    for bm in load_benchmarks():
        actual = bm.get("source_actual")
        if not actual:
            continue
        assert bm.get("verified") is True, (
            f"{bm['id']} records source_actual without full verification")
        assert "note" in actual, "source_actual must explain the discrepancy"
        figures = {k: v for k, v in actual.items() if k != "note"}
        assert len(figures) >= 2, (
            f"{bm['id']}: source_actual should carry the conflicting figures "
            "from each source, not a single 'true' value")


def test_disputed_benchmarks_are_excluded_from_validation_by_default():
    """The flattering number must not be the default.

    The two benchmarks whose figures match no locatable source are also the
    model's closest agreements. Including them halves the reported median
    error, from 30.6% to 14.7%. Defaulting to the lower figure would let an
    untraceable value flatter the model, which is the opposite of what this
    validation exists to do.
    """
    from pvdlowe.validate import validate_model
    default = validate_model()
    audit = validate_model(include_disputed=True)

    assert default.attrs["excluded"], "expected disputed entries to be excluded"
    assert len(default) < len(audit), "the audit view should have more rows"
    assert default.attrs["median_rel_error_pct"] > audit.attrs["median_rel_error_pct"], (
        "excluding disputed entries must RAISE the reported error; if it "
        "lowers it, the exclusion is flattering the model rather than "
        "protecting against it")
    assert "note" in default.attrs and "cannot be quoted" not in default.attrs["note"]
    assert not audit.attrs["excluded"], "audit view must include everything"


def test_validation_report_names_which_figure_it_quotes():
    """A median error printed without saying what it excludes is a trap."""
    from pvdlowe.validate import report
    text = report()
    assert "disputed benchmark" in text
    assert "do not quote" in text.lower()


def test_resolved_checks_do_not_suggest_work_already_done():
    """A consistency check must not send the reader to redo an eliminated test.

    The Ag thin-film resistivity check originally advised checking whether the
    bulk value had been tabulated alongside the measured ones. That was a
    reasonable first hypothesis and it was tested: the source patent states
    1.29 uohm.cm against the 1.59 the brief transcribed, and 1.29 is BELOW
    bulk, so the correction makes the anomaly worse. Where `source_actual`
    records a mistranscription, the action must say so.
    """
    from pvdlowe.validate import check_consistency
    rows = check_consistency()
    resistivity = rows[rows["check"].str.contains("resistivity", case=False)]
    assert len(resistivity), "the Ag resistivity check should still fire"
    action = " ".join(resistivity["action"])
    assert "tabulated alongside" not in action, (
        "the superseded action is still being suggested")
    assert "faithful" in action.lower(), (
        "the action must say the brief is faithful to its source -- the "
        "conflict is between two publications, not a transcription error")
