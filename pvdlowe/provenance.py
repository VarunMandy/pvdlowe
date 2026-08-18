"""Provenance tracking for every number that enters the framework.

The project brief is explicit on this point (sections 12, 13 and "One
caution"): published first-principles evidence for AZO or Cu:ZnO is *not*
the same thing as a calculated value for Ag70Cu29Ti1, and neither is the
same as a measured sheet resistance. Mixing the three is how a screening
table turns into a thesis claim that cannot be defended in a viva.

So provenance is not documentation here, it is a type. A `Quantity` carries
its origin, and :func:`assert_reportable` refuses to let HYPOTHESIS-grade
numbers leave the framework as headline results unless the caller has
explicitly opted in.

Grades, in decreasing order of how much weight they can carry:

MEASURED        this lab's own measurement
LITERATURE      published experimental value, primary source verified
LITERATURE_UNVERIFIED
                value quoted in the brief whose primary source has not yet
                been opened and checked. Every number transcribed from the
                brief starts here.
MP_API          retrieved from the Materials Project at a recorded date
DFT_OWN         computed by this project, with an input record
DFT_LITERATURE  a first-principles result published by someone else
MODEL           output of a parametric/semi-empirical model in this package
CALIBRATED      model parameter tuned to reproduce a known measurement
ESTIMATE        order-of-magnitude engineering estimate
HYPOTHESIS      a candidate/target value that has not been calculated or
                measured at all
"""

from __future__ import annotations

import datetime as _dt
import enum
from dataclasses import dataclass, field
from typing import Any


class Provenance(enum.Enum):
    MEASURED = "measured"
    LITERATURE = "literature"
    LITERATURE_UNVERIFIED = "literature_unverified"
    MP_API = "materials_project"
    DFT_OWN = "dft_own"
    DFT_LITERATURE = "dft_literature"
    MODEL = "model"
    CALIBRATED = "calibrated"
    ESTIMATE = "estimate"
    HYPOTHESIS = "hypothesis"

    @property
    def rank(self) -> int:
        return _RANK[self]

    @property
    def is_empirical(self) -> bool:
        return self in (Provenance.MEASURED, Provenance.LITERATURE,
                        Provenance.LITERATURE_UNVERIFIED)

    @property
    def needs_verification(self) -> bool:
        """True if this value must not be quoted without further work."""
        return self in (Provenance.LITERATURE_UNVERIFIED, Provenance.HYPOTHESIS,
                        Provenance.ESTIMATE)


_RANK = {
    Provenance.MEASURED: 100,
    Provenance.LITERATURE: 90,
    Provenance.MP_API: 70,
    Provenance.DFT_OWN: 65,
    Provenance.DFT_LITERATURE: 60,
    Provenance.LITERATURE_UNVERIFIED: 55,
    Provenance.CALIBRATED: 45,
    Provenance.MODEL: 40,
    Provenance.ESTIMATE: 20,
    Provenance.HYPOTHESIS: 0,
}

#: Grades that may appear in a headline result table without an explicit
#: opt-in from the caller.
REPORTABLE = frozenset({
    Provenance.MEASURED, Provenance.LITERATURE, Provenance.MP_API,
    Provenance.DFT_OWN, Provenance.DFT_LITERATURE, Provenance.MODEL,
    Provenance.CALIBRATED,
})


class ProvenanceError(RuntimeError):
    """Raised when a value is used more strongly than its provenance allows."""


@dataclass(frozen=True)
class Quantity:
    """A number that knows where it came from.

    Examples
    --------
    >>> rs = Quantity(4.36, "ohm/sq", Provenance.LITERATURE_UNVERIFIED,
    ...               source="AZO/Ag(13nm)/AZO, brief section 3",
    ...               citation="doi:10.1016/j.ceramint.2014.05.010")
    >>> rs.value
    4.36
    >>> rs.reportable
    False
    """

    value: Any
    unit: str = ""
    provenance: Provenance = Provenance.ESTIMATE
    source: str = ""
    citation: str = ""
    uncertainty: float | None = None
    retrieved: str | None = None
    note: str = ""

    def __post_init__(self):
        if self.retrieved is None and self.provenance is Provenance.MP_API:
            object.__setattr__(self, "retrieved",
                               _dt.date.today().isoformat())

    # -- behaviour ------------------------------------------------------
    @property
    def reportable(self) -> bool:
        return self.provenance in REPORTABLE

    def __float__(self) -> float:
        return float(self.value)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        u = f" {self.unit}" if self.unit else ""
        flag = "" if self.reportable else "  [NOT REPORTABLE]"
        return f"<{self.value}{u} :: {self.provenance.value}{flag}>"

    def label(self) -> str:
        """Short human string for tables."""
        u = f" {self.unit}" if self.unit else ""
        mark = "*" if self.provenance.needs_verification else ""
        return f"{self.value}{u}{mark}"

    def with_value(self, value) -> "Quantity":
        """Copy carrying a new value and the same provenance chain."""
        return Quantity(value, self.unit, self.provenance, self.source,
                        self.citation, self.uncertainty, self.retrieved,
                        self.note)


def combine(*quantities: Quantity) -> Provenance:
    """Provenance of a result derived from several inputs.

    A derived number is only as strong as its weakest input, and any model
    step degrades an empirical input to MODEL -- a transfer-matrix emissivity
    built on measured n,k is a model output, not a measurement.
    """
    if not quantities:
        return Provenance.ESTIMATE
    weakest = min(quantities, key=lambda q: q.provenance.rank).provenance
    if weakest.is_empirical:
        return Provenance.MODEL
    return weakest


def assert_reportable(*quantities: Quantity, allow: frozenset | None = None,
                      context: str = "") -> None:
    """Raise unless every quantity is fit to appear in a results table.

    Call this at the boundary where numbers become claims -- report
    generation, the CLI's headline table, a figure caption.
    """
    allowed = REPORTABLE if allow is None else (REPORTABLE | allow)
    bad = [q for q in quantities if q.provenance not in allowed]
    if bad:
        lines = [f"  {q.source or '<unnamed>'}: {q.provenance.value}"
                 for q in bad]
        where = f" in {context}" if context else ""
        raise ProvenanceError(
            f"{len(bad)} value(s){where} are not reportable as-is:\n"
            + "\n".join(lines)
            + "\nEither compute/measure them, or pass allow={Provenance.X} "
              "to state explicitly that they are being shown as hypotheses."
        )


@dataclass
class Record:
    """Provenance ledger for a whole calculation.

    Attach one to a screening run so the resulting table can be audited
    line by line -- which is what a reviewer will ask for.
    """

    entries: dict[str, Quantity] = field(default_factory=dict)

    def add(self, key: str, quantity: Quantity) -> Quantity:
        self.entries[key] = quantity
        return quantity

    def get(self, key: str) -> Quantity:
        return self.entries[key]

    def weakest(self) -> Provenance:
        if not self.entries:
            return Provenance.ESTIMATE
        return min(self.entries.values(),
                   key=lambda q: q.provenance.rank).provenance

    def unverified(self) -> list[str]:
        return sorted(k for k, q in self.entries.items()
                      if q.provenance.needs_verification)

    def to_rows(self) -> list[dict]:
        return [
            {
                "key": k,
                "value": q.value,
                "unit": q.unit,
                "provenance": q.provenance.value,
                "source": q.source,
                "citation": q.citation,
                "retrieved": q.retrieved or "",
                "note": q.note,
            }
            for k, q in sorted(self.entries.items())
        ]

    def audit(self) -> str:
        """Human-readable provenance audit."""
        lines = ["provenance audit", "=" * 60]
        for row in self.to_rows():
            flag = " <-- verify" if Provenance(row["provenance"]).needs_verification else ""
            lines.append(
                f"{row['key']:<34} {row['value']!s:>12} {row['unit']:<8}"
                f" {row['provenance']}{flag}")
        lines.append("-" * 60)
        lines.append(f"weakest link: {self.weakest().value}")
        return "\n".join(lines)


__all__ = ["Provenance", "Quantity", "ProvenanceError", "Record", "REPORTABLE",
           "combine", "assert_reportable"]
