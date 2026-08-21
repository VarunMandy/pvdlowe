"""Predicted signatures for the characterisation measurements this project needs.

Nothing here computes a coating property. These are predictions of what an
instrument would show under each competing hypothesis, so that a measurement
can discriminate them rather than merely produce a number.
"""
from .xrd import (CU_KALPHA1, FCC_REFLECTIONS, LATTICE_A, SCHERRER_K,
                  grain_size_from_fwhm, grain_size_ladder,
                  microstructure_signatures, scherrer_fwhm, texture_note,
                  two_theta, vegard_lattice)

__all__ = ["CU_KALPHA1", "LATTICE_A", "FCC_REFLECTIONS", "SCHERRER_K",
           "two_theta", "vegard_lattice", "scherrer_fwhm",
           "grain_size_from_fwhm", "microstructure_signatures",
           "grain_size_ladder", "texture_note"]
