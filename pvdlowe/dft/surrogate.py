"""Deprecated. The ML surrogate now lives in :mod:`pvdlowe.ml`.

Three separate implementations of this capability accumulated during
development -- ``pvdlowe/dft/surrogate.py``, ``pvdlowe/surrogate/mlip.py`` and
``pvdlowe/ml/surrogate.py`` -- because each was written before the previous one
was found. Only ``pvdlowe.ml`` is maintained; it is the one with the validation
gate, the lattice-mismatch guard and the termination handling.

This module is retained as a shim so that the older import path fails loudly
with a pointer rather than silently resolving to stale code. It will be removed.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from ..ml.surrogate import (MP_REFERENCE as _MP_FULL, MLIPSurrogate,
                            SurrogateUnavailable, mixing_energy_series as _series,
                            validate_against_mp)

warnings.warn(
    "pvdlowe.dft.surrogate is deprecated; import from pvdlowe.ml instead",
    DeprecationWarning, stacklevel=2)

#: Kept in the flat {formula: e_above_hull} shape the old callers expected.
MP_REFERENCE = {v["formula"]: v["e_above_hull"] for v in _MP_FULL.values()}


@dataclass
class SurrogateResult:
    """Retained for the old import path. New code uses the DataFrames that
    :mod:`pvdlowe.ml` returns, which carry their provenance in ``.attrs``."""
    label: str = ""
    frame: object = None
    note: str = ""


def available_models():
    """Backends that can be loaded, or an empty tuple."""
    try:
        return (MLIPSurrogate().name,)
    except Exception:                                       # noqa: BLE001
        return ()


def _require():
    return MLIPSurrogate()          # raises SurrogateUnavailable with advice


def mixing_energy_series(*args, **kwargs):
    """Deprecated alias for :func:`pvdlowe.ml.mixing_energy_series`."""
    return _series(_require(), *args, **kwargs)


def validate_against_hull(*args, **kwargs):
    """Deprecated alias for :func:`pvdlowe.ml.validate_against_mp`."""
    return validate_against_mp(_require(), *args, **kwargs)


def screen_ternaries(*args, **kwargs):
    """Never implemented beyond a stub; use pvdlowe.ml directly."""
    _require()
    raise NotImplementedError(
        "ternary screening was never implemented here; pvdlowe.ml provides "
        "mixing_energy_series, adatom_wetting and adhesion_energy")


def install_hint() -> str:
    return "pip install mace-torch   # or chgnet, matgl, sevenn"


__all__ = ["MP_REFERENCE", "SurrogateResult", "SurrogateUnavailable",
           "available_models",
           "mixing_energy_series", "validate_against_hull", "screen_ternaries",
           "install_hint"]
