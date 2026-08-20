"""ML interatomic potentials as a DFT surrogate.

Optional. Requires one of mace-torch, chgnet, matgl or sevenn, plus ase and
pymatgen. Nothing else in pvdlowe depends on this subpackage.
"""
from .surrogate import (BACKENDS, DIELECTRIC_PROXY, MAX_LATTICE_MISMATCH,
                        MP_REFERENCE,
                        MLIPSurrogate, SurrogateUnavailable,
                        adhesion_comparison, adhesion_energy,
                        mixing_energy_series, validate_against_mp,
                        what_mlips_cannot_do)

__all__ = ["MLIPSurrogate", "SurrogateUnavailable", "BACKENDS", "MP_REFERENCE",
           "DIELECTRIC_PROXY", "MAX_LATTICE_MISMATCH", "validate_against_mp", "mixing_energy_series",
           "adhesion_energy", "adhesion_comparison", "what_mlips_cannot_do"]
