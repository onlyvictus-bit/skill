#!/usr/bin/env python3
"""Read-only optional dependency discovery for Claude Mon."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def status() -> dict:
    return {
        "python": sys.executable,
        "core": True,
        "optional": {
            "tiktoken": module_available("tiktoken"),
            "docling": module_available("docling"),
            "aider": module_available("aider"),
            "graphify": module_available("graphify"),
            "repomix_cli": shutil.which("repomix") is not None,
        },
        "note": "Discovery only. Availability does not prove an adapter executed successfully and no dependency is installed automatically.",
    }


if __name__ == "__main__":
    print(json.dumps(status(), sort_keys=True))
