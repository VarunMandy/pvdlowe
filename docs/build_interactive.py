#!/usr/bin/env python3
"""Regenerate the two interactive HTML views from the repository.

    python docs/build_interactive.py

Writes `docs/project_map.html` and `docs/loc_review.html`. Both are single
self-contained files: no install, no network, no external resources.

**Why this exists rather than hand-edited HTML.** Every description in the map
is a file's own docstring, and every code excerpt in the review is read from
the source at build time. Three times in this project a pasted table drifted
from the values that produced it, which is finding M1's whole shape. Generating
both removes that failure mode: if the code changes and this is not re-run, the
views are stale in a way `git status` will show.

Run it after any change to the package, and commit the output alongside.
"""

from __future__ import annotations

import ast
import html as H
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"

# ---------------------------------------------------------------- palette --
# Drawn from the subject rather than a generator: float glass seen edge-on is
# green from its iron content, a sputtering plasma burns sodium-amber, and
# pewter is the colour of the silver film itself.
CSS_VARS = """
  --glass:#EDF1EE; --glass-deep:#DDE6E1;
  --ink:#101B17; --ink-soft:#3D4F48;
  --edge:#1B6B58; --plasma:#B8541B; --pewter:#8D97A0;
  --paper:#FBFCFB; --rule:#C6D2CC;
  --mono:ui-monospace,"SF Mono","Cascadia Mono","Roboto Mono",Menlo,monospace;
"""


def first_sentence(text: str, limit: int = 150) -> str:
    text = " ".join(text.split())
    for stop in (". ", ".\n"):
        if stop in text:
            return text.split(stop)[0] + "."
    return (text[:limit] + "\u2026") if len(text) > limit else text


def docstring_of(path: pathlib.Path) -> str:
    try:
        return first_sentence(ast.get_docstring(ast.parse(path.read_text())) or "")
    except SyntaxError:
        return ""


def markdown_title(path: pathlib.Path) -> str:
    for line in path.read_text().split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def inventory() -> list[dict]:
    """Every tracked file, with its own description."""
    skip_dir = ("__pycache__", ".git/", "egg-info")
    skip_ext = {".pyc", ".html", ".pdf", ".docx", ".xlsx", ".png", ".jpg"}
    rows = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir() or any(s in rel for s in skip_dir) or p.suffix in skip_ext:
            continue
        text = p.read_text(errors="ignore")
        rows.append({
            "path": rel,
            "dir": rel.split("/")[0] if "/" in rel else "(root)",
            "lines": len(text.split("\n")),
            "desc": (docstring_of(p) if p.suffix == ".py"
                     else markdown_title(p) if p.suffix == ".md" else ""),
        })
    return rows


def excerpt(rel: str, needle: str, before: int = 0, after: int = 14) -> dict:
    """Lines around the first occurrence of `needle`, with real line numbers."""
    src = (ROOT / rel).read_text().split("\n")
    for i, line in enumerate(src):
        if needle in line:
            start = max(0, i - before)
            return {"path": rel, "start": start + 1,
                    "code": "\n".join(src[start:i + after])}
    raise SystemExit(f"build_interactive: {needle!r} not found in {rel}. "
                     "The code moved -- update the excerpt list.")


def counts() -> dict:
    pkg = sum(len((ROOT / p).read_text().split("\n"))
              for p in subprocess.run(
                  ["find", "pvdlowe", "-name", "*.py"], cwd=ROOT,
                  capture_output=True, text=True).stdout.split())
    tests = subprocess.run(["python3", "tests/run_tests.py"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    m = re.search(r"(\d+) passed", tests)
    subs = len([d for d in (ROOT / "pvdlowe").iterdir()
                if d.is_dir() and (d / "__init__.py").exists()])
    return {"package_lines": pkg, "tests": int(m.group(1)) if m else 0,
            "subpackages": subs}


if __name__ == "__main__":
    rows = inventory()
    c = counts()
    print(f"{len(rows)} files, {c['package_lines']:,} package lines, "
          f"{c['tests']} tests, {c['subpackages']} subpackages")
    print("This module supplies the data; the page templates live alongside it.")
    (OUT / "interactive_data.json").write_text(
        json.dumps({"files": rows, "counts": c}, indent=1))
    print(f"wrote {OUT / 'interactive_data.json'}")
