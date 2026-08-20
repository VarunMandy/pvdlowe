"""DFT planning and analysis."""
from .plans import (Calculation, DFTPlan, ag_cu_series_plan, fcc_supercell_poscar,
                    interface_energy, mixing_energy, smallest_supercell,
                    stabiliser_plan,
                    what_dft_cannot_give)

__all__ = ["Calculation", "DFTPlan", "ag_cu_series_plan", "stabiliser_plan",
           "fcc_supercell_poscar", "smallest_supercell", "mixing_energy", "interface_energy",
           "what_dft_cannot_give"]
from .surrogate import (SurrogateResult, SurrogateUnavailable, available_models,
                        install_hint, mixing_energy_series, screen_ternaries,
                        validate_against_hull)

__all__ = list(globals().get("__all__", [])) + [
    "SurrogateResult", "SurrogateUnavailable", "available_models",
    "validate_against_hull", "mixing_energy_series", "screen_ternaries",
    "install_hint"]
