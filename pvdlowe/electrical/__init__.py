"""Thin-film transport."""
from .thinfilm import (PERCOLATION, PercolationModel, ThinFilmResistivity,
                       fuchs_sondheimer_ratio, mayadas_shatzkes_ratio,
                       parallel_sheet_resistance)

__all__ = ["ThinFilmResistivity", "PercolationModel", "PERCOLATION",
           "fuchs_sondheimer_ratio", "mayadas_shatzkes_ratio",
           "parallel_sheet_resistance"]
from .calibrate import (CalibrationResult, apply_to_coating, diagnose,
                        fit_series, load_series)

__all__ = list(globals().get("__all__", [])) + [
    "CalibrationResult", "fit_series", "diagnose", "load_series",
    "apply_to_coating"]
