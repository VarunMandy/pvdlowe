"""Numerical-path tests for the ML surrogate, without an MLIP installed.

This addresses code-review finding N1: the `ml/` subpackage shipped with no
coverage of its numerical paths, because MACE, CHGNet and their weights cannot
be installed in the environment the rest of the suite runs in.

The parts that actually had defects are not the energy evaluations -- those are
the model's job -- but the **judgement applied to them**. That logic went wrong
twice: once by letting an unreliable surface set a verdict, and once by
reporting a strict ordering between two dielectrics that share a crystalline
proxy and are therefore the same calculation.

Those paths are pure functions over tables, so they are tested here against the
figures actually produced on Vertex AI, which is stronger than synthetic data:
each case below is a run that happened.
"""

import pandas as pd

from pvdlowe.ml import MAX_SITE_SPREAD_FRACTION, judge_wetting
from pvdlowe.electrical.calibrate import deembed_parallel, deembed_series


# Measured on Vertex AI, MACE-MP-0, float64, 6 adatom placements per surface.
MEASURED_AG = pd.DataFrame([
    {"dielectric": "ITO",   "proxy": "In2O3", "dE_wet_eV": -3.5747, "site_spread_eV": 1.6656},
    {"dielectric": "Si3N4", "proxy": "Si3N4", "dE_wet_eV": -0.5020, "site_spread_eV": 0.2149},
    {"dielectric": "GZO",   "proxy": "ZnO",   "dE_wet_eV": +0.6962, "site_spread_eV": 0.0124},
    {"dielectric": "AZO",   "proxy": "ZnO",   "dE_wet_eV": +0.6962, "site_spread_eV": 0.0124},
    {"dielectric": "TiO2",  "proxy": "TiO2",  "dE_wet_eV": +0.8509, "site_spread_eV": 0.1529},
    {"dielectric": "SnO2",  "proxy": "SnO2",  "dE_wet_eV": +1.1527, "site_spread_eV": 0.0249},
])


def test_unreliable_surfaces_are_excluded_from_the_verdict():
    """The defect: a cleaved nitride set the verdict and inverted it.

    On beta-Si3N4 the spread across six placements was 43% of the binding
    energy, against 2% on the oxides -- the adatom was falling into
    dangling-bond pockets on an artificially reactive surface. Letting that row
    win produced "NOT consistent with the measured ordering", a conclusion
    driven entirely by the proxy already documented as weakest.
    """
    df = judge_wetting(MEASURED_AG.copy(), "Ag")
    excluded = set(df.loc[~df.reliable, "dielectric"])
    assert excluded == {"Si3N4", "ITO"}, excluded
    assert "AZO" in df.attrs["verdict"] or "GZO" in df.attrs["verdict"]
    assert "Consistent with the measured growth ordering" in df.attrs["verdict"]


def test_shared_proxies_are_reported_as_tied_not_ranked():
    """The second defect: GZO and AZO are the same calculation.

    Both resolve to ZnO(0001), so they return identical energies and a strict
    ordering between them is a sort artifact. Reporting "Ag wets GZO best"
    implied a material difference the method cannot see.
    """
    df = judge_wetting(MEASURED_AG.copy(), "Ag")
    assert "tied" in df.attrs, "identical-proxy entries must be flagged"
    assert "AZO" in df.attrs["tied"] and "GZO" in df.attrs["tied"]
    assert "same calculation" in df.attrs["tied"]


def test_verdict_refuses_when_every_surface_is_unreliable():
    """No ordering may be claimed from data that is all noise."""
    noisy = pd.DataFrame([
        {"dielectric": "A", "proxy": "A", "dE_wet_eV": -1.0, "site_spread_eV": 0.9},
        {"dielectric": "B", "proxy": "B", "dE_wet_eV": +1.0, "site_spread_eV": 0.8},
    ])
    df = judge_wetting(noisy, "Ag")
    assert "no ordering can be claimed" in df.attrs["verdict"]


def test_verdict_refuses_on_fewer_than_two_surfaces():
    """One converged surface is not a comparison."""
    one = pd.DataFrame([
        {"dielectric": "AZO", "proxy": "ZnO", "dE_wet_eV": 0.7, "site_spread_eV": 0.01}])
    df = judge_wetting(one, "Ag", n_requested=4,
                       failures={"Si3N4": "RuntimeError: no slab"})
    assert "no ordering can be claimed" in df.attrs["verdict"]
    assert "Si3N4" in df.attrs["verdict"]


def test_reliability_threshold_is_explicit_and_strict():
    """The threshold must be a named constant, not a literal buried in a filter."""
    assert 0.0 < MAX_SITE_SPREAD_FRACTION <= 0.5
    boundary = pd.DataFrame([
        {"dielectric": "A", "proxy": "A", "dE_wet_eV": 1.0,
         "site_spread_eV": MAX_SITE_SPREAD_FRACTION * 1.01},
        {"dielectric": "B", "proxy": "B", "dE_wet_eV": 1.0,
         "site_spread_eV": MAX_SITE_SPREAD_FRACTION * 0.99},
    ])
    df = judge_wetting(boundary, "Ag")
    assert not df.set_index("dielectric").loc["A", "reliable"]
    assert df.set_index("dielectric").loc["B", "reliable"]


def test_trilayer_deembedding_is_non_linear_where_it_matters():
    """Skipping the oxide de-embed biases toward 'the copper is fine'.

    A poorly conducting metal layer is shunted proportionally harder by the
    oxide, so the raw trilayer reading understates it more the worse the metal
    is: +5% at 3 ohm/sq but +36% at 16.6, which is exactly the literature value
    under investigation.
    """
    from pvdlowe.materials.tco import tco
    shunt = tco("AZO").sheet_resistance(40.0)
    low = deembed_parallel(3.0, shunt, shunt)
    high = deembed_parallel(16.6, shunt, shunt)
    assert (low - 3.0) / 3.0 < 0.10
    assert (high - 16.6) / 16.6 > 0.30
    assert (high - 16.6) / 16.6 > (low - 3.0) / 3.0


def test_deembedding_refuses_when_the_shunt_explains_everything():
    """If the oxide alone accounts for the measurement, the metal is not
    conducting and returning a number would invent one."""
    from pvdlowe.materials.tco import tco
    shunt = tco("AZO").sheet_resistance(40.0)
    try:
        deembed_parallel(shunt / 2.0, shunt, shunt)
    except ValueError as exc:
        assert "discontinuous" in str(exc) or "shunt" in str(exc)
    else:
        raise AssertionError("de-embedding invented a metal sheet resistance "
                             "the measurement cannot support")


def test_open_circuit_films_survive_de_embedding_as_infinite():
    """A sub-percolation film reads open; it must stay open, not become a
    number. The fitter uses those rows as a bound on d_c."""
    import numpy as np
    out = deembed_series([float("nan"), 3.0, 2.5], "AZO", 40.0, 40.0)
    assert np.isinf(out[0])
    assert np.isfinite(out[1]) and np.isfinite(out[2])
