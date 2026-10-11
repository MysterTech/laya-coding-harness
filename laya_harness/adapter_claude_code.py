"""Claude Code adapter rules for stage 0 (spec §4.9). Deterministic: profile × harness state.

Gating uses laya-mlx's values as returned (four decimals); the tier sum is rounded to four
decimals. Laya's `confidence` field is never used.
"""

from . import catalog as catalog_mod
from . import copytext

RULES_VERSION = "claude_code_v0"


def tier_and_class(probabilities: dict):
    light = round(probabilities["quick"] + probabilities["routine"], 4)
    heavy = round(probabilities["multi_file"] + probabilities["architecture"], 4)
    if light >= heavy:
        cls = "quick" if probabilities["quick"] >= probabilities["routine"] else "routine"
        return "light", light, cls
    cls = "multi_file" if probabilities["multi_file"] >= probabilities["architecture"] else "architecture"
    return "heavy", heavy, cls


def decide(answers: dict, *, first_human: bool, plan_shown: bool, permission_mode, prompt: str,
           display: dict, catalog: dict, fit: dict, session: dict) -> dict:
    """Return {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}.

    `lines` holds at most two strings: the model line first, then the plan line.
    `line_for` names them: {"model": line or None, "plan": line or None}.
    `suppress_reason` is per line: {"model": reason or None, "plan": reason or None}.
    """
    line_for, reasons, suggestion = {"model": None, "plan": None}, {"model": None, "plan": None}, None

    tier, tier_p, cls = tier_and_class(answers["difficulty"]["probabilities"])
    if not first_human:
        reasons["model"] = "not_first_prompt"
    elif tier_p < display["difficulty"]["min_tier_p"]:
        reasons["model"] = "below_threshold"
    else:
        suggestion = catalog_mod.select(cls, catalog, fit)
        if suggestion is None:
            reasons["model"] = "no_fit"
        else:
            line_for["model"] = copytext.model_line(tier, tier_p, suggestion["display"], suggestion["effort"])

    plan = answers["plan_first"]["noul"]
    plan_rules = display["plan_first"]
    if plan < plan_rules["show_threshold"]:
        reasons["plan"] = "below_threshold"
    elif permission_mode == "plan" or prompt.lstrip().startswith("/plan"):
        reasons["plan"] = "plan_mode"
    elif not (first_human or len(prompt) >= plan_rules["min_chars"]):
        reasons["plan"] = "too_short"
    elif plan_shown:
        reasons["plan"] = "already_shown"
    else:
        line_for["plan"] = copytext.plan_line(plan)

    mismatches = [
        {"type": "MODEL+REASONING", "profile": {"tier": tier, "tier_p": tier_p, "class": cls},
         "state": {"model": session.get("model"), "effort": session.get("effort")},
         "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": plan},
         "state": {"permission_mode": permission_mode}, "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": answers["parallel"]["noul"]},
         "state": {}, "channel_later": "harness"},
    ]
    lines = [line for line in (line_for["model"], line_for["plan"]) if line]
    return {"lines": lines, "line_for": line_for, "suppress_reason": reasons, "suggestion": suggestion,
            "mismatches": mismatches}
