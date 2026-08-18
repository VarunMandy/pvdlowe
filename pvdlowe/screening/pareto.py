"""Pareto analysis for the multi-objective problem.

A weighted score collapses several objectives into one number, which is
convenient and lossy: it hides the fact that some candidates are not worse
than the winner, merely different. The Pareto front is the honest version of
the same question, and for this project it is the more useful one, because
the trade the brief actually cares about -- silver consumption against
performance -- is a two-objective trade whose shape matters more than any
single optimum.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def pareto_mask(objectives: np.ndarray, directions) -> np.ndarray:
    """Boolean mask of non-dominated rows.

    Parameters
    ----------
    objectives : (n_candidates, n_objectives) array
    directions : sequence of 'higher' or 'lower', one per objective
    """
    obj = np.asarray(objectives, dtype=float)
    if obj.ndim != 2:
        raise ValueError("objectives must be 2-D")
    signed = obj.copy()
    for j, d in enumerate(directions):
        if d == "lower":
            signed[:, j] = -signed[:, j]
        elif d != "higher":
            raise ValueError("directions must be 'higher' or 'lower'")

    n = signed.shape[0]
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        # j dominates i if it is >= everywhere and > somewhere
        dominates = np.all(signed >= signed[i], axis=1) & \
                    np.any(signed > signed[i], axis=1)
        if np.any(dominates):
            keep[i] = False
    return keep


def pareto_front(df: pd.DataFrame, objectives: dict) -> pd.DataFrame:
    """Non-dominated subset of a candidate table.

    `objectives` maps column name -> 'higher' or 'lower'.
    """
    cols = list(objectives)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing objective columns: {missing}")
    sub = df[cols].astype(float)
    valid = np.isfinite(sub.to_numpy()).all(axis=1)
    mask = np.zeros(len(df), dtype=bool)
    mask[np.where(valid)[0]] = pareto_mask(sub.to_numpy()[valid],
                                           [objectives[c] for c in cols])
    return df[mask]


def knee_point(df: pd.DataFrame, x: str, y: str,
               x_direction: str = "lower", y_direction: str = "higher"):
    """Point of maximum curvature on a two-objective front.

    Normalises both axes, then picks the front point furthest from the chord
    joining its two extremes -- the standard "best compromise" heuristic.
    For the silver-versus-performance trade this identifies where further
    silver reduction starts costing disproportionate performance, which is
    the number the brief is really asking for.
    """
    front = pareto_front(df, {x: x_direction, y: y_direction}).copy()
    if len(front) < 3:
        return front.iloc[0] if len(front) else None
    xs = front[x].to_numpy(dtype=float)
    ys = front[y].to_numpy(dtype=float)
    xn = (xs - xs.min()) / max(np.ptp(xs), 1e-12)
    yn = (ys - ys.min()) / max(np.ptp(ys), 1e-12)
    order = np.argsort(xn)
    xn, yn = xn[order], yn[order]
    front = front.iloc[order]
    p0 = np.array([xn[0], yn[0]])
    p1 = np.array([xn[-1], yn[-1]])
    chord = p1 - p0
    norm = np.linalg.norm(chord)
    if norm < 1e-12:
        return front.iloc[0]
    dist = np.abs(np.cross(chord, np.stack([xn, yn], axis=1) - p0)) / norm
    return front.iloc[int(np.argmax(dist))]


def dominance_summary(df: pd.DataFrame, objectives: dict) -> pd.DataFrame:
    """For each candidate, how many others dominate it. 0 means on the front."""
    cols = list(objectives)
    signed = df[cols].to_numpy(dtype=float).copy()
    for j, c in enumerate(cols):
        if objectives[c] == "lower":
            signed[:, j] = -signed[:, j]
    counts = []
    for i in range(len(df)):
        dom = np.all(signed >= signed[i], axis=1) & np.any(signed > signed[i], axis=1)
        counts.append(int(dom.sum()))
    out = df.copy()
    out["dominated_by"] = counts
    out["on_front"] = out["dominated_by"] == 0
    return out.sort_values(["dominated_by"])


__all__ = ["pareto_mask", "pareto_front", "knee_point", "dominance_summary"]
