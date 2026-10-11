"""The exact strings of the copy deck (spec §4.12). Numbers are formatted to two decimals."""

MAX_LEN = 120


def model_line(tier: str, tier_p: float, display: str, effort) -> str:
    fits = f"{display} at {effort} effort fits this task" if effort else f"{display} fits this task"
    return f"laya · {tier} task (p={tier_p:.2f}) → {fits}"


def plan_line(noul: float) -> str:
    return (
        f"laya · reads like a multi-step change (p={noul:.2f}) → "
        "Plan mode (mode menu, then 4), or tell Claude to plan first"
    )
