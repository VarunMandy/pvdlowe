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
        assert state in (True, "partial"), (bm["id"], state)
        assert bm.get("citation", "").strip(), f"{bm['id']} claims verification with no citation"
        assert bm.get("verified_note", "").strip(), f"{bm['id']} must record what was NOT checked"


def test_full_verification_is_not_claimed_without_reading_the_paper():
    """No entry should be `verified: true` while the basis is unchecked."""
    status = verification_status()
    assert status["verified"] + status["partial"] + status["unverified"] == status["total"]
    assert status["verified"] == 0, (
        "an entry claims full verification -- confirm the full text was read, "
        "including the measurement basis, before allowing this")


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
