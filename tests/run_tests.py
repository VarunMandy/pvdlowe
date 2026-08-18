#!/usr/bin/env python3
"""Self-contained test runner.

pytest is not installable in every environment this framework has to run in,
so this discovers and executes test functions directly. It is deliberately
pytest-compatible: `pytest tests/` works identically wherever pytest exists.
"""

from __future__ import annotations

import importlib.util
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None) -> int:
    pattern = (argv or [None])[0]
    files = sorted(p for p in HERE.glob("test_*.py"))
    passed = failed = 0
    failures = []
    started = time.time()

    for path in files:
        try:
            module = load(path)
        except Exception:
            print(f"\n{path.name}: COLLECTION ERROR")
            traceback.print_exc()
            failed += 1
            failures.append((path.name, "<import>"))
            continue
        names = [n for n in dir(module) if n.startswith("test_")]
        if pattern:
            names = [n for n in names if pattern in n]
        if not names:
            continue
        print(f"\n{path.name}")
        for name in names:
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                fn()
            except Exception as exc:                    # noqa: BLE001
                failed += 1
                failures.append((path.name, name))
                print(f"  FAIL  {name}")
                print(f"        {type(exc).__name__}: {exc}")
            else:
                passed += 1
                print(f"  ok    {name}")

    elapsed = time.time() - started
    print("\n" + "=" * 64)
    print(f"{passed} passed, {failed} failed in {elapsed:.1f}s")
    if failures:
        print("\nfailures:")
        for f, n in failures:
            print(f"  {f}::{n}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
