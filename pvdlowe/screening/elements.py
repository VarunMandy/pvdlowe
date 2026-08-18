"""Stage 1 of the brief's workflow: element screening.

The brief proposes starting from the RSC periodic table and scoring elements
for abundance, supply risk, conductivity, melting point, cost and toxicity.
That is the right first filter, with one caveat worth being blunt about:
element-level screening can only *exclude*. It tells you indium is a supply
problem and gold is a cost problem. It cannot tell you whether AZO/Ag-Cu/AZO
beats AZO/Cu/AZO, because that depends on the multilayer optics, not on any
property of silver or copper as elements.

So this module is deliberately a filter rather than a ranker. Use it to cut
the candidate space before the expensive stages, and let the optical model
decide among what survives.

Prices carry provenance ESTIMATE and a date, because they move. Two things
to keep in mind when using them: commodity price is not sputtering-target
price -- targets typically cost several times the metal, more for bonded or
rotatable geometries -- and target utilisation in a planar magnetron is
often only 30-40%, so metal *purchased* per square metre can be two to three
times metal *deposited*. :func:`coating_material_cost` handles both.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..provenance import Provenance, Quantity

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ELEMENTS_CSV = DATA_DIR / "elements.csv"

#: Date the price column was last reviewed. Prices are ESTIMATE grade.
PRICE_AS_OF = "2025-01"

#: Multiplier from commodity metal price to sputtering-target price.
DEFAULT_TARGET_PREMIUM = 3.0

#: Fraction of a planar magnetron target that is actually eroded and
#: deposited before the target is retired.
DEFAULT_TARGET_UTILISATION = 0.35


def load_elements(path: Path | None = None) -> pd.DataFrame:
    """Load the element table."""
    df = pd.read_csv(path or ELEMENTS_CSV)
    return df.set_index("symbol", drop=False)


@dataclass
class ElementCriteria:
    """Exclusion thresholds for stage-1 screening.

    Defaults encode the brief's sustainability intent: exclude anything with
    a supply-risk score above 8 (which removes indium) and anything costing
    more than 5000 USD/kg (which removes gold), while keeping silver in as
    the benchmark it is meant to be.
    """

    max_supply_risk: float = 8.0
    max_price_usd_per_kg: float = 5000.0
    max_toxicity: float = 5.0
    min_abundance_ppm: float = 0.0
    roles: tuple | None = None

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = (
            (df["supply_risk_score"] <= self.max_supply_risk)
            & (df["price_usd_per_kg"] <= self.max_price_usd_per_kg)
            & (df["toxicity_score"] <= self.max_toxicity)
            & (df["crustal_abundance_ppm"] >= self.min_abundance_ppm)
        )
        if self.roles:
            mask &= df["role"].fillna("").apply(
                lambda r: any(role in str(r).split(",") for role in self.roles))
        return df[mask]

    def rejections(self, df: pd.DataFrame) -> pd.DataFrame:
        """Which elements were excluded and why -- screening you can defend."""
        rows = []
        for sym, row in df.iterrows():
            reasons = []
            if row["supply_risk_score"] > self.max_supply_risk:
                reasons.append(f"supply risk {row['supply_risk_score']:.1f}"
                               f" > {self.max_supply_risk}")
            if row["price_usd_per_kg"] > self.max_price_usd_per_kg:
                reasons.append(f"price {row['price_usd_per_kg']:.0f}"
                               f" > {self.max_price_usd_per_kg} USD/kg")
            if row["toxicity_score"] > self.max_toxicity:
                reasons.append(f"toxicity {row['toxicity_score']:.0f}"
                               f" > {self.max_toxicity}")
            if row["crustal_abundance_ppm"] < self.min_abundance_ppm:
                reasons.append(f"abundance {row['crustal_abundance_ppm']:g}"
                               f" < {self.min_abundance_ppm} ppm")
            if reasons:
                rows.append({"symbol": sym, "name": row["name"],
                             "reason": "; ".join(reasons)})
        return pd.DataFrame(rows)


def sustainability_score(df: pd.DataFrame) -> pd.Series:
    """0-100 sustainability score from abundance, supply risk and toxicity.

    Abundance enters logarithmically because crustal abundance spans eight
    orders of magnitude and a linear scale would make every element except
    aluminium and silicon indistinguishable.
    """
    log_ab = np.log10(df["crustal_abundance_ppm"].clip(lower=1e-4))
    ab_score = 100 * (log_ab - log_ab.min()) / max(log_ab.max() - log_ab.min(), 1e-9)
    risk_score = 100 * (1.0 - df["supply_risk_score"] / 10.0)
    tox_score = 100 * (1.0 - df["toxicity_score"] / 10.0)
    return (0.4 * ab_score + 0.4 * risk_score + 0.2 * tox_score).round(1)


def screen(criteria: ElementCriteria | None = None,
           path: Path | None = None) -> dict:
    """Run stage-1 screening and return the survivors, rejections and scores."""
    crit = criteria or ElementCriteria()
    df = load_elements(path)
    df = df.assign(sustainability=sustainability_score(df))
    kept = crit.apply(df)
    return {
        "all": df,
        "kept": kept.sort_values("sustainability", ascending=False),
        "rejected": crit.rejections(df),
        "criteria": crit,
        "note": ("element screening excludes, it does not rank architectures; "
                 "surviving elements go to stage 2 compound screening"),
    }


def coating_material_cost(element_areal_mass_g_m2: dict,
                          target_premium: float = DEFAULT_TARGET_PREMIUM,
                          utilisation: float = DEFAULT_TARGET_UTILISATION,
                          path: Path | None = None) -> dict:
    """Material cost of a coating in USD per square metre.

        cost = sum_i  m_i [g/m2] * price_i [USD/kg] * premium
                      / (1000 * utilisation)

    Only the metal layer is usually worth costing this way: the oxides are
    made from cheap Zn and Al and their cost is dominated by process time,
    not by material. The silver term normally dominates everything.
    """
    df = load_elements(path)
    breakdown = {}
    for sym, mass in element_areal_mass_g_m2.items():
        if sym not in df.index:
            continue
        price = float(df.loc[sym, "price_usd_per_kg"])
        breakdown[sym] = float(mass * price * target_premium
                               / (1000.0 * max(utilisation, 1e-6)))
    total = float(sum(breakdown.values()))
    return {
        "total_usd_per_m2": total,
        "breakdown_usd_per_m2": breakdown,
        "target_premium": target_premium,
        "utilisation": utilisation,
        "price_as_of": PRICE_AS_OF,
        "provenance": Provenance.ESTIMATE,
        "note": "metal cost only; excludes gas, energy, capital, yield and "
                "the oxide layers. Prices are ESTIMATE grade -- refresh "
                "before quoting a cost per square metre.",
    }


def cost_quantity(element_areal_mass_g_m2: dict, **kwargs) -> Quantity:
    result = coating_material_cost(element_areal_mass_g_m2, **kwargs)
    return Quantity(result["total_usd_per_m2"], "USD/m2", Provenance.ESTIMATE,
                    source="metal cost model",
                    note=result["note"], retrieved=PRICE_AS_OF)


def price_sensitivity(element_areal_mass_g_m2: dict,
                      silver_price_range: tuple = (600.0, 1600.0),
                      n: int = 9, **kwargs) -> pd.DataFrame:
    """Coating metal cost across a range of silver prices.

    Silver has moved by more than a factor of two within single years. Any
    conclusion of the form "composition X is cheaper than composition Y"
    should be shown to survive that range, or stated as conditional on price.
    """
    df = load_elements(kwargs.pop("path", None))
    base = df.copy()
    rows = []
    for price in np.linspace(*silver_price_range, n):
        base.loc["Ag", "price_usd_per_kg"] = price
        premium = kwargs.get("target_premium", DEFAULT_TARGET_PREMIUM)
        util = kwargs.get("utilisation", DEFAULT_TARGET_UTILISATION)
        total = sum(
            mass * float(base.loc[sym, "price_usd_per_kg"]) * premium
            / (1000.0 * util)
            for sym, mass in element_areal_mass_g_m2.items() if sym in base.index)
        rows.append({"silver_price_usd_per_kg": float(price),
                     "coating_cost_usd_per_m2": float(total)})
    return pd.DataFrame(rows)


__all__ = ["load_elements", "ElementCriteria", "sustainability_score", "screen",
           "coating_material_cost", "cost_quantity", "price_sensitivity",
           "PRICE_AS_OF", "DEFAULT_TARGET_PREMIUM", "DEFAULT_TARGET_UTILISATION"]
