"""Codex recommendation subset and provisional fits, kept separate from Claude (C4)."""

import hashlib
import json
from pathlib import Path

CATALOG = Path(__file__).parent / "data" / "codex_models.json"
FIT = Path(__file__).parent / "data" / "codex_fit.json"


def catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def fit() -> dict:
    return json.loads(FIT.read_text(encoding="utf-8"))


def catalog_sha256() -> str:
    """One provenance hash over the catalog followed by the fit table's raw bytes."""
    return hashlib.sha256(CATALOG.read_bytes() + FIT.read_bytes()).hexdigest()
