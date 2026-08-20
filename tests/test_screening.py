"""Screening, scoring, Pareto and provenance."""

import numpy as np
import pandas as pd

from pvdlowe.provenance import Provenance, Quantity, assert_reportable
from pvdlowe.screening.candidates import (evaluate, evaluate_all,
                                          load_candidates, not_predicted)
from pvdlowe.screening.elements import (ElementCriteria, coating_material_cost,
                                        load_elements, screen)
from pvdlowe.screening.pareto import pareto_front, pareto_mask
from pvdlowe.screening.scoring import (Criterion, ScoringScheme,
                                       criterion_correlations,
                                       redundant_criteria)


def test_element_screening_excludes_indium_and_gold():
    res = screen(ElementCriteria())
    kept = set(res["kept"]["symbol"])
    assert "In" not in kept and "Au" not in kept
    assert "Ag" in kept and "Cu" in kept and "Zn" in kept


def test_rejections_give_reasons():
    res = screen(ElementCriteria())
    assert len(res["rejected"]) >= 2
    assert res["rejected"]["reason"].str.len().min() > 0


def test_desirability_bounds():
    c = Criterion("t", "test", "higher", floor=0.65, target=0.80)
    assert c.desirability(0.60) == 0.0
    assert c.desirability(0.85) == 1.0
    assert abs(c.desirability(0.725) - 0.5) < 1e-9


def test_lower_is_better_direction():
    c = Criterion("e", "test", "lower", floor=0.20, target=0.05)
    assert c.desirability(0.25) == 0.0
    assert c.desirability(0.02) == 1.0
    assert c.desirability(0.10) > c.desirability(0.15)


def test_geometric_mean_punishes_a_zero():
    scheme = ScoringScheme.from_yaml()
    good = {"T_vis": 0.85, "emissivity_hemispherical": 0.04, "R_sheet": 3.0,
            "cost_usd_per_m2": 0.5, "supply_risk": 3.0, "Ag_g_per_m2": 0.0}
    bad = dict(good, T_vis=0.50)          # fails one criterion outright
    g = scheme.score(good)["score"]
    b = scheme.score(bad)["score"]
    assert b < 0.5 * g, (g, b)


def test_arithmetic_mean_does_not_punish_a_zero_as_hard():
    """The reason the default aggregation is geometric."""
    scheme = ScoringScheme.from_yaml()
    good = {"T_vis": 0.85, "emissivity_hemispherical": 0.04, "R_sheet": 3.0,
            "cost_usd_per_m2": 0.5, "supply_risk": 3.0, "Ag_g_per_m2": 0.0}
    bad = dict(good, T_vis=0.50)
    geo = scheme.with_aggregation("geometric")
    ari = scheme.with_aggregation("arithmetic")
    geo_drop = geo.score(good)["score"] - geo.score(bad)["score"]
    ari_drop = ari.score(good)["score"] - ari.score(bad)["score"]
    assert geo_drop > ari_drop, (geo_drop, ari_drop)


def test_emissivity_and_sheet_resistance_are_correlated():
    """The brief's weighting double-counts; this proves it numerically."""
    records = evaluate_all().to_dict("records")
    corr = criterion_correlations(records,
                                  ["emissivity_hemispherical", "R_sheet"])
    r = corr.loc["emissivity_hemispherical", "R_sheet"]
    assert abs(r) > 0.9, r


def test_redundant_criteria_flags_the_pair():
    records = evaluate_all().to_dict("records")
    pairs = redundant_criteria(records, ScoringScheme.from_yaml())
    keys = {(p["criterion_a"], p["criterion_b"]) for p in pairs}
    assert ("emissivity_hemispherical", "R_sheet") in keys


def test_pareto_mask_basic():
    pts = np.array([[1.0, 1.0], [2.0, 2.0], [1.5, 3.0]])
    mask = pareto_mask(pts, ["higher", "higher"])
    assert mask.tolist() == [False, True, True]


def test_pareto_front_is_non_empty_and_subset():
    df = evaluate_all()
    front = pareto_front(df, {"T_vis": "higher",
                              "emissivity_hemispherical": "lower"})
    assert 0 < len(front) <= len(df)


def test_hypothesis_candidates_are_flagged():
    cands = {c.id: c for c in load_candidates()}
    assert cands["T1"].is_hypothesis and cands["T2"].is_hypothesis
    assert not cands["M0"].is_hypothesis


def test_assert_reportable_blocks_hypotheses():
    q = Quantity(1.0, "eV", Provenance.HYPOTHESIS, "made up")
    try:
        assert_reportable(q)
    except Exception:
        pass
    else:
        raise AssertionError("hypothesis-grade quantity was allowed through")


def test_cost_is_dominated_by_silver():
    cost = coating_material_cost({"Ag": 0.105, "Cu": 0.0})
    cost_cu = coating_material_cost({"Ag": 0.0, "Cu": 0.09})
    assert cost["total_usd_per_m2"] > 20 * cost_cu["total_usd_per_m2"]


def test_not_predicted_is_explicit():
    keys = not_predicted()
    for expected in ("deposition_rate", "adhesion", "thermal_stability"):
        assert expected in keys


def test_mlip_surrogate_refuses_rather_than_falls_back():
    """No empirical-potential fallback when no MLIP is installed.

    An EAM or Lennard-Jones number would look like the same kind of result and
    be far less trustworthy. Same rule as SputterModel and MPClient: a missing
    value beats a fabricated one.
    """
    from pvdlowe.ml import MLIPSurrogate, SurrogateUnavailable
    try:
        MLIPSurrogate()
    except SurrogateUnavailable as exc:
        assert "pip install" in str(exc), "the error should say how to fix it"
    except ImportError:
        pass          # ase/pymatgen absent too, which is the same situation
    else:
        pass          # a backend is installed; nothing to assert here


def test_mlip_boundary_excludes_optical_properties():
    """Guards the claim that a surrogate cannot replace section 5.

    MLIPs predict energies and forces from atomic positions. They carry no
    electronic structure, so every optical quantity in this framework is
    outside their reach, and the docs must keep saying so.
    """
    from pvdlowe.ml import what_mlips_cannot_do
    d = what_mlips_cannot_do()
    joined = " ".join(d["cannot"]).lower()
    for term in ("optical", "band gap", "emissivity"):
        assert term in joined, term
    assert any("30 mev" in u.lower() for u in d["unreliable"]), \
        "the accuracy floor must be stated, since it is comparable with the " \
        "hull distances this project measures"
