"""Multi-objective scoring: the brief's sections 14 and 16.

Each criterion is mapped to a desirability in [0, 1] by a Derringer-Suich
function, then the desirabilities are aggregated.

On the choice of aggregation. The brief proposes a weighted arithmetic sum,
``Score = sum_i w_i S_i``, and states the purpose plainly: to stop a material
"winning simply because it has excellent conductivity while being
unacceptable optically or economically". A weighted *sum* does not do that.
A candidate scoring 1.0 on conductivity and 0 on transmittance still collects
0.15 of the total and can outrank a balanced candidate. The weighted
*geometric* mean does do it -- any zero drives the product to zero -- so it
is the default here. The arithmetic form is available with
``aggregation="arithmetic"`` for comparison, and
:func:`compare_aggregations` shows where the two disagree on a given
candidate set, which is usually the most informative thing to look at.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..provenance import Provenance, Quantity

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TARGETS_YAML = DATA_DIR / "targets.yaml"


@dataclass
class Criterion:
    """One scored objective with its acceptable range."""

    key: str
    label: str
    direction: str          # 'higher' | 'lower' | 'target'
    floor: float
    target: float
    exponent: float = 1.0
    unit: str = ""
    source: str = ""
    upper: float | None = None      # for two-sided 'target' criteria

    def desirability(self, value) -> float:
        """Map a value onto [0, 1]."""
        v = np.asarray(value, dtype=float)
        if self.direction == "higher":
            d = (v - self.floor) / (self.target - self.floor)
        elif self.direction == "lower":
            d = (self.floor - v) / (self.floor - self.target)
        elif self.direction == "target":
            if self.upper is None:
                raise ValueError(f"criterion {self.key}: 'target' needs an upper")
            lo = (v - self.floor) / (self.target - self.floor)
            hi = (self.upper - v) / (self.upper - self.target)
            d = np.minimum(lo, hi)
        else:
            raise ValueError(f"unknown direction {self.direction!r}")
        d = np.clip(d, 0.0, 1.0) ** self.exponent
        return float(d) if np.isscalar(value) or np.ndim(value) == 0 else d


@dataclass
class ScoringScheme:
    """Criteria, weights and an aggregation rule."""

    criteria: dict
    weights: dict
    aggregation: str = "geometric"
    epsilon: float = 1e-3       # floor on desirability, keeps log finite

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "ScoringScheme":
        with open(path or TARGETS_YAML) as fh:
            cfg = yaml.safe_load(fh)
        criteria = {k: Criterion(key=k, **v) for k, v in cfg["criteria"].items()}
        return cls(criteria, cfg["weights"], cfg.get("aggregation", "geometric"))

    # -- scoring ---------------------------------------------------------
    def desirabilities(self, record: dict) -> dict:
        """Per-criterion desirability for one candidate.

        Criteria absent from `record` are skipped, not defaulted -- a missing
        thermal-stability measurement must not silently count as zero.
        """
        out = {}
        for key, crit in self.criteria.items():
            if key in record and record[key] is not None \
                    and np.isfinite(np.asarray(record[key], dtype=float)):
                out[key] = crit.desirability(record[key])
        return out

    def score(self, record: dict) -> dict:
        """Aggregate score in [0, 100] plus the full breakdown."""
        d = self.desirabilities(record)
        if not d:
            return {"score": 0.0, "desirabilities": {}, "weights_used": {},
                    "missing": sorted(self.criteria), "aggregation": self.aggregation}
        w = {k: float(self.weights.get(k, 0.0)) for k in d}
        total_w = sum(w.values())
        if total_w <= 0:
            w = {k: 1.0 / len(d) for k in d}
            total_w = 1.0
        w = {k: v / total_w for k, v in w.items()}

        if self.aggregation == "geometric":
            logs = sum(w[k] * np.log(max(d[k], self.epsilon)) for k in d)
            value = float(np.exp(logs))
        elif self.aggregation == "arithmetic":
            value = float(sum(w[k] * d[k] for k in d))
        elif self.aggregation == "minimum":
            value = float(min(d.values()))
        else:
            raise ValueError(f"unknown aggregation {self.aggregation!r}")

        limiting = min(d, key=d.get)
        return {
            "score": round(100.0 * value, 2),
            "desirabilities": {k: round(v, 4) for k, v in d.items()},
            "weights_used": {k: round(v, 4) for k, v in w.items()},
            "missing": sorted(set(self.criteria) - set(d)),
            "limiting_criterion": limiting,
            "limiting_desirability": round(d[limiting], 4),
            "aggregation": self.aggregation,
        }

    def score_quantity(self, record: dict) -> Quantity:
        res = self.score(record)
        note = ""
        if res["missing"]:
            note = ("scored on a subset; missing criteria: "
                    + ", ".join(res["missing"]))
        return Quantity(res["score"], "/100", Provenance.MODEL,
                        source=f"{self.aggregation} desirability score",
                        note=note)

    def score_frame(self, records) -> pd.DataFrame:
        """Score candidates into a sorted DataFrame.

        Accepts a list of dicts or a DataFrame of evaluated candidates.
        """
        if isinstance(records, pd.DataFrame):
            records = records.to_dict("records")
        rows = []
        for rec in records:
            res = self.score(rec)
            row = {"label": rec.get("label", "?"), "score": res["score"],
                   "limiting": res["limiting_criterion"],
                   "limiting_d": res["limiting_desirability"]}
            row.update({f"d_{k}": v for k, v in res["desirabilities"].items()})
            row.update({k: v for k, v in rec.items()
                        if k != "label" and not isinstance(v, (dict, list))})
            rows.append(row)
        return pd.DataFrame(rows).sort_values("score", ascending=False)

    def with_aggregation(self, aggregation: str) -> "ScoringScheme":
        return ScoringScheme(self.criteria, self.weights, aggregation, self.epsilon)

    def subset(self, keep=None, drop=None) -> "ScoringScheme":
        """A scheme scoring on a subset of the criteria.

        Weights renormalise over what remains, so dropping a criterion
        redistributes its weight proportionally rather than silently
        shrinking the total. Use `drop` to remove a redundant criterion --
        R_sheet correlates with emissivity at r = 0.996, so scoring both
        puts 40% of the weight on one physical property.
        """
        names = set(keep) if keep is not None else set(self.criteria)
        if drop:
            names -= set(drop)
        missing = names - set(self.criteria)
        if missing:
            raise KeyError(f"unknown criteria: {sorted(missing)}")
        criteria = {k: v for k, v in self.criteria.items() if k in names}
        weights = {k: v for k, v in self.weights.items() if k in names}
        return ScoringScheme(criteria, weights, self.aggregation, self.epsilon)


def compare_aggregations(scheme: ScoringScheme, records) -> pd.DataFrame:
    """Rank candidates under each aggregation rule and show where they differ.

    A large rank change between geometric and arithmetic aggregation is a
    warning that the winner under the arithmetic sum is unbalanced -- strong
    on a couple of heavily-weighted criteria and weak somewhere that matters.
    """
    frames = {}
    for agg in ("geometric", "arithmetic", "minimum"):
        f = scheme.with_aggregation(agg).score_frame(records)
        f = f.reset_index(drop=True)
        frames[agg] = f.set_index("label")["score"]
    out = pd.DataFrame(frames)
    for agg in frames:
        out[f"rank_{agg}"] = out[agg].rank(ascending=False).astype(int)
    out["rank_shift"] = (out["rank_arithmetic"] - out["rank_geometric"]).abs()
    return out.sort_values("geometric", ascending=False)


def criterion_correlations(records, keys=None) -> pd.DataFrame:
    """Pearson correlation between raw criterion values across candidates.

    The check the brief's weighting table needs. If two criteria correlate at
    |r| > 0.9 they are one objective wearing two hats, and their weights add
    up rather than balancing each other.
    """
    df = pd.DataFrame(records)
    numeric = df.select_dtypes(include=[np.number])
    if keys:
        numeric = numeric[[k for k in keys if k in numeric.columns]]
    return numeric.corr(method="pearson")


def redundant_criteria(records, scheme: ScoringScheme,
                       threshold: float = 0.9) -> list:
    """Criterion pairs that are effectively the same objective.

    Returns the pairs, their correlation, and their combined weight -- the
    number to quote when arguing that a weighting table double-counts.
    """
    corr = criterion_correlations(records)
    found = []
    keys = [k for k in scheme.criteria if k in corr.columns]
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            r = corr.loc[a, b]
            if np.isfinite(r) and abs(r) >= threshold:
                found.append({
                    "criterion_a": a, "criterion_b": b, "pearson_r": round(float(r), 3),
                    "weight_a": scheme.weights.get(a, 0.0),
                    "weight_b": scheme.weights.get(b, 0.0),
                    "combined_weight": round(
                        scheme.weights.get(a, 0.0) + scheme.weights.get(b, 0.0), 3),
                })
    return sorted(found, key=lambda d: -d["combined_weight"])


def sensitivity_to_weights(scheme: ScoringScheme, records, n_trials: int = 400,
                           spread: float = 0.5, seed: int = 0) -> pd.DataFrame:
    """How stable is the ranking under perturbed weights?

    Randomly rescales each weight by a factor drawn log-uniformly within
    +/- `spread` and records how often each candidate comes first. A winner
    that only wins for one exact weighting is not a winner, and this is the
    cheapest way to find that out before it is discovered in a review.
    """
    rng = np.random.default_rng(seed)
    labels = [r.get("label", f"cand{i}") for i, r in enumerate(records)]
    wins = {lab: 0 for lab in labels}
    mean_rank = {lab: [] for lab in labels}
    base = scheme.weights
    for _ in range(n_trials):
        pert = {k: float(v * np.exp(rng.uniform(-spread, spread)))
                for k, v in base.items()}
        s = ScoringScheme(scheme.criteria, pert, scheme.aggregation, scheme.epsilon)
        scores = [(lab, s.score(rec)["score"]) for lab, rec in zip(labels, records)]
        scores.sort(key=lambda t: -t[1])
        wins[scores[0][0]] += 1
        for rank, (lab, _) in enumerate(scores, start=1):
            mean_rank[lab].append(rank)
    return pd.DataFrame([
        {"label": lab,
         "win_fraction": round(wins[lab] / n_trials, 3),
         "mean_rank": round(float(np.mean(mean_rank[lab])), 2),
         "rank_std": round(float(np.std(mean_rank[lab])), 2)}
        for lab in labels]).sort_values("win_fraction", ascending=False)


__all__ = ["Criterion", "ScoringScheme", "compare_aggregations",
           "criterion_correlations", "redundant_criteria",
           "sensitivity_to_weights", "TARGETS_YAML"]
