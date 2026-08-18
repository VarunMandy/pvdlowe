"""Materials Project client -- stage 2 of the brief's workflow.

Two things this module is careful about.

**It degrades honestly when offline.** Query results are cached to disk on
first retrieval, so a screening run is reproducible and works without a
network afterwards. With no network and no cache, it raises rather than
returning anything that might be mistaken for data. There is no fallback
table of plausible-looking formation energies, because a fabricated
E_above_hull is worse than a missing one.

**It records what the database can and cannot answer.** The Materials
Project holds DFT results for ordered crystalline phases at 0 K. The central
material in this project -- a sputtered, possibly metastable, possibly
phase-separated Ag-Cu thin film 10 nm thick -- is none of those things. So
the database can tell you that Ag-Cu has a positive mixing energy and no
stable intermediate compounds, which is exactly the segregation tendency the
brief flags. It cannot tell you whether your sputtered film is mixed, because
that is a kinetics question about a metastable state. :func:`applicability`
spells this out per query so the limitation travels with the result.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from ..provenance import Provenance, Quantity

MP_BASE_URL = "https://api.materialsproject.org"
DEFAULT_CACHE = Path.home() / ".cache" / "pvdlowe" / "mp"

#: Fields worth pulling for this project, mapped to why.
SUMMARY_FIELDS = {
    "material_id": "identifier to cite",
    "formula_pretty": "composition",
    "energy_above_hull": "thermodynamic stability (brief section 15B)",
    "formation_energy_per_atom": "formation energy",
    "band_gap": "optical transparency screen (brief section 9)",
    "is_stable": "on the convex hull",
    "density": "areal mass and cost",
    "symmetry": "crystal system",
    "nsites": "cell size",
    "theoretical": "whether the entry is hypothetical",
}


class MPUnavailable(RuntimeError):
    """Raised when the API cannot be reached and nothing is cached."""


@dataclass
class MPClient:
    """Thin REST client with an on-disk cache.

    Uses the `mp_api` package if it is installed, otherwise plain urllib
    against the summary endpoint. An API key is required either way; get one
    from the Materials Project dashboard and set MP_API_KEY.
    """

    api_key: str | None = None
    cache_dir: Path = field(default_factory=lambda: DEFAULT_CACHE)
    offline: bool = False
    timeout: float = 30.0

    def __post_init__(self):
        self.api_key = self.api_key or os.environ.get("MP_API_KEY")
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- cache -----------------------------------------------------------
    def _cache_path(self, key: str) -> Path:
        safe = urllib.parse.quote(key, safe="")[:180]
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str):
        p = self._cache_path(key)
        if p.exists():
            with open(p) as fh:
                return json.load(fh)
        return None

    def _write_cache(self, key: str, payload) -> None:
        with open(self._cache_path(key), "w") as fh:
            json.dump(payload, fh, indent=1)

    def cached_queries(self) -> list:
        return sorted(p.stem for p in self.cache_dir.glob("*.json"))

    # -- requests --------------------------------------------------------
    def _request(self, endpoint: str, params: dict):
        key = f"{endpoint}?{urllib.parse.urlencode(sorted(params.items()))}"
        cached = self._read_cache(key)
        if cached is not None:
            return cached
        if self.offline:
            raise MPUnavailable(
                f"offline and no cached result for {key}. Run this query once "
                "with a network connection to populate the cache.")
        if not self.api_key:
            raise MPUnavailable(
                "no Materials Project API key. Set MP_API_KEY, or pass "
                "api_key=..., or work from a populated cache with offline=True.")
        url = f"{MP_BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"X-API-KEY": self.api_key,
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise MPUnavailable(
                f"Materials Project request failed: {exc}. If the network is "
                "unavailable, populate the cache elsewhere and copy "
                f"{self.cache_dir} across.") from exc
        self._write_cache(key, payload)
        return payload

    # -- queries ---------------------------------------------------------
    def summary(self, fields: list | None = None, **criteria) -> list:
        """Query the summary endpoint.

        Examples
        --------
        >>> client.summary(chemsys="Ag-Cu")                    # doctest: +SKIP
        >>> client.summary(elements="Zn,O", band_gap_min=3.0)  # doctest: +SKIP
        """
        params = {k: v for k, v in criteria.items() if v is not None}
        params["_fields"] = ",".join(fields or list(SUMMARY_FIELDS))
        params.setdefault("_limit", 200)
        payload = self._request("materials/summary/", params)
        return payload.get("data", payload if isinstance(payload, list) else [])

    def chemical_system(self, chemsys: str, **kwargs) -> list:
        """All entries in a chemical system, e.g. 'Ag-Cu' or 'Zn-Al-O'."""
        return self.summary(chemsys=chemsys, **kwargs)

    def by_id(self, material_id: str) -> dict:
        results = self.summary(material_ids=material_id)
        return results[0] if results else {}

    def as_quantities(self, entry: dict) -> dict:
        """Wrap an entry's numbers with MP_API provenance and its material id."""
        mid = entry.get("material_id", "?")
        out = {}
        for key in ("energy_above_hull", "formation_energy_per_atom",
                    "band_gap", "density"):
            if entry.get(key) is not None:
                out[key] = Quantity(
                    entry[key],
                    {"energy_above_hull": "eV/atom",
                     "formation_energy_per_atom": "eV/atom",
                     "band_gap": "eV", "density": "g/cm3"}[key],
                    Provenance.MP_API, source=f"Materials Project {mid}",
                    citation=f"https://next-gen.materialsproject.org/materials/{mid}")
        return out


def applicability(chemsys: str) -> dict:
    """What a Materials Project query can and cannot settle for this project.

    Attach this to any MP-derived claim. The distinction is the one the brief
    draws in its section 12 -- published first-principles evidence exists for
    a material family, which is not the same as a calculated value for the
    specific sputtered film.
    """
    metallic = all(el not in chemsys for el in ("O", "N", "F"))
    return {
        "chemsys": chemsys,
        "can_answer": [
            "which ordered crystalline phases exist in this system at 0 K",
            "energy above hull for each of them",
            "whether any intermediate compound is thermodynamically stable",
            "band gap and DFT-level electronic structure of stable phases",
        ] + ([] if metallic else ["dielectric tensor, where computed"]),
        "cannot_answer": [
            "properties of a disordered or metastable sputtered solid solution",
            "whether a given deposition condition produces a mixed film",
            "thin-film optical constants at 10 nm thickness",
            "interface energies against an amorphous or textured oxide",
            "deposition rate, adhesion, durability or cost",
        ],
        "implication": (
            "absence of a stable intermediate compound in a binary metal system "
            "is evidence for a segregation tendency, not evidence that a "
            "sputtered film will segregate -- the film may be kinetically "
            "trapped. Settle that with XRD, TEM and resistivity-versus-anneal, "
            "not with a database query."),
    }


__all__ = ["MPClient", "MPUnavailable", "SUMMARY_FIELDS", "MP_BASE_URL",
           "DEFAULT_CACHE", "applicability"]
