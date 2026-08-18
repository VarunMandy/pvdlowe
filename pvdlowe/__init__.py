"""pvdlowe -- computational framework for sustainable Low-E PVD coatings.

Implements the workflow of the project brief: element screening, Materials
Project compound screening, optical multilayer modelling, design of
experiments, and multi-objective scoring, with provenance tracking on every
number.
"""
__version__ = "0.1.0"

from .provenance import Provenance, Quantity, Record

__all__ = ["Provenance", "Quantity", "Record", "__version__"]
