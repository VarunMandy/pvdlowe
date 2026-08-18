"""Design of experiments and sputter process modelling."""
from .design import (Design, Factor, SPUTTER_FACTORS, alias_structure,
                     box_behnken, central_composite, fractional_factorial,
                     full_factorial, latin_hypercube, recommended_screening)
from .sputter import (SputterModel, deposition_efficiency, quality_penalty,
                      rate_ratios, stack_deposition_time)

__all__ = ["Design", "Factor", "SPUTTER_FACTORS", "full_factorial",
           "fractional_factorial", "alias_structure", "box_behnken",
           "central_composite", "latin_hypercube", "recommended_screening",
           "SputterModel", "deposition_efficiency", "stack_deposition_time",
           "rate_ratios", "quality_penalty"]
