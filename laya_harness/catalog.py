"""Cheapest model and effort that the fit table accepts (spec §4.13, D12, D13)."""

import re

NEVER = ("fable", "mythos")  # the user's rule: never Fable (Mythos is its sibling line)
_DATE = re.compile(r"-\d{8}$")


def canonical(model_id):
    """Lower-case, without a trailing "[1m]" or "-YYYYMMDD"; None stays None."""
    if not model_id:
        return None
    name = model_id.strip().lower()
    if name.endswith("[1m]"):
        name = name[: -len("[1m]")]
    return _DATE.sub("", name)


def _version_key(version: str):
    return tuple(int(part) for part in version.split("."))


def never(model: dict) -> bool:
    """True for any Fable or Mythos model, judged by family, id or display name, in any case."""
    text = " ".join(str(model.get(key) or "") for key in ("family", "id", "display")).lower()
    return any(name in text for name in NEVER)


def eligible(model: dict) -> bool:
    return not never(model) and bool(model.get("allowed")) and bool(model.get("in_picker"))


def _resolve(option: dict, models: list):
    if "model" in option:
        wanted = canonical(option["model"])
        for m in models:
            if canonical(m["id"]) == wanted and eligible(m):
                return m
        return None
    family = [m for m in models if m.get("family") == option.get("family") and eligible(m)]
    return max(family, key=lambda m: _version_key(m["version"]), default=None)


def select(cls: str, catalog: dict, fit: dict):
    """Return {"model", "display", "effort", "class"} for the cheapest qualifying option, or None."""
    models = catalog["models"]
    candidates = []
    for option in fit["classes"].get(cls, []):
        model = _resolve(option, models)
        if model is None:
            continue
        effort = option.get("effort")
        if effort is not None and effort not in model["effort_levels"]:
            continue
        candidates.append((model["price"]["input"], _version_key(model["version"]), model, effort))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[1], reverse=True)  # newest first (5.5 > 5, 4.10 > 4.8)...
    candidates.sort(key=lambda c: c[0])  # ...then cheapest; the sort is stable, so ties keep newest first
    _, _, model, effort = candidates[0]
    return {"model": model["id"], "display": model["display"], "effort": effort, "class": cls}


def known(catalog: dict) -> set:
    return {canonical(m["id"]) for m in catalog["models"]}
