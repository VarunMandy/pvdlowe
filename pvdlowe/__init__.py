"""pvdlowe -- computational framework for sustainable Low-E PVD coatings.

Implements the workflow of the project brief: element screening, Materials
Project compound screening, optical multilayer modelling, design of
experiments, and multi-objective scoring, with provenance tracking on every
number.
"""
__version__ = "0.1.0"

from .provenance import Provenance, Quantity, Record

__all__ = ["Provenance", "Quantity", "Record", "__version__"]

# -- convenience re-exports -------------------------------------------------
# The dozen entry points people actually start with. Deep imports still work
# and are what the internals use; these exist so the first five minutes do not
# require knowing the package layout.
#
# Deliberately lazy: importing optics at module import time would pull scipy
# and every dispersion model into any `import pvdlowe`, including the ones that
# only want `Provenance`.

def __getattr__(name):
    _lazy = {
        "LowECoating": ("pvdlowe.optics.stack", "LowECoating"),
        "MultiMetalCoating": ("pvdlowe.optics.stack", "MultiMetalCoating"),
        "dmd": ("pvdlowe.optics.stack", "dmd"),
        "dmdmd": ("pvdlowe.optics.stack", "dmdmd"),
        "performance_summary": ("pvdlowe.optics.integrate", "performance_summary"),
        "ScoringScheme": ("pvdlowe.screening.scoring", "ScoringScheme"),
        "evaluate": ("pvdlowe.screening.candidates", "evaluate"),
        "evaluate_all": ("pvdlowe.screening.candidates", "evaluate_all"),
        "record_for": ("pvdlowe.screening.candidates", "record_for"),
        "load_candidates": ("pvdlowe.screening.candidates", "load_candidates"),
        "tco": ("pvdlowe.materials.tco", "tco"),
        "metal": ("pvdlowe.materials.metals", "metal"),
        "validate_model": ("pvdlowe.validate", "validate_model"),
    }
    if name in _lazy:
        import importlib
        module, attr = _lazy[name]
        return getattr(importlib.import_module(module), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(globals().get("__all__", [])) + [
    "LowECoating", "MultiMetalCoating", "dmd", "dmdmd", "performance_summary",
    "ScoringScheme", "evaluate", "evaluate_all", "record_for",
    "load_candidates", "tco", "metal", "validate_model"]
