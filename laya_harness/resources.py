"""Data shipped inside the package: the question set, the pinned checkpoint, and the Claude
Code model catalog and fit table (spec §4.5, §4.8, §4.13)."""

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).parent
QUESTIONS = PACKAGE / "questions" / "profile_v0.json"
CHECKPOINT = PACKAGE / "checkpoint.json"
CATALOG = PACKAGE / "data" / "claude_code_models.json"
FIT = PACKAGE / "data" / "claude_code_fit.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def questions() -> dict:
    return _read(QUESTIONS)


def questions_snapshot() -> tuple[dict, str]:
    """Definitions and provenance from one read, even if the file changes during startup."""
    data = QUESTIONS.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def questions_sha256() -> str:
    return sha256_file(QUESTIONS)


def checkpoint() -> dict:
    return _read(CHECKPOINT)


def catalog() -> dict:
    return _read(CATALOG)


def fit() -> dict:
    return _read(FIT)


def catalog_sha256() -> str:
    """One hash over the catalog and the fit table, recorded in every decision row."""
    digest = hashlib.sha256()
    digest.update(CATALOG.read_bytes())
    digest.update(FIT.read_bytes())
    return digest.hexdigest()
