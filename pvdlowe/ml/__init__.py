"""ML interatomic potentials as a DFT surrogate.

Optional. Requires one of mace-torch, chgnet, matgl or sevenn, plus ase and
pymatgen. Nothing else in pvdlowe depends on this subpackage.
"""
from .surrogate import (BACKENDS, DIELECTRIC_PROXY, MAX_LATTICE_MISMATCH,
                        MP_REFERENCE,
                        MLIPSurrogate, SurrogateUnavailable,
                        MAX_SITE_SPREAD_FRACTION, adatom_wetting,
                        adhesion_comparison, adhesion_energy, judge_wetting,
                        mixing_energy_series, termination_spread,
                        validate_against_mp, wetting_comparison,
                        what_mlips_cannot_do)

__all__ = ["MLIPSurrogate", "SurrogateUnavailable", "BACKENDS", "MP_REFERENCE",
           "DIELECTRIC_PROXY", "MAX_LATTICE_MISMATCH", "validate_against_mp", "mixing_energy_series",
           "adhesion_energy", "adhesion_comparison", "adatom_wetting",
           "judge_wetting", "MAX_SITE_SPREAD_FRACTION", "wetting_comparison", "termination_spread", "what_mlips_cannot_do"]
