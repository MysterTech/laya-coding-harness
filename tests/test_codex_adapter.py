import copy

import pytest

from laya_harness import adapter_codex as adapter, resources

DISPLAY = resources.questions()["display"]
CATALOG = {"models": [
    {"id": "gpt-6-luna", "display": "GPT-6 Luna", "family": "luna", "version": "6", "price": {"input": .1}, "effort_levels": ["low"], "allowed": True, "in_picker": True},
    {"id": "gpt-6.1-sol", "display": "GPT-6.1 Sol", "family": "sol", "version": "6.1", "price": {"input": 2}, "effort_levels": ["low", "medium", "high"], "allowed": True, "in_picker": True},
    {"id": "gpt-6-astra", "display": "GPT-6 Astra", "family": "astra", "version": "6", "price": {"input": 10}, "effort_levels": ["xhigh"], "allowed": True, "in_picker": True},
]}
FIT = {"classes": {"quick": [{"family": "luna", "effort": "low"}, {"family": "sol", "effort": "low"}], "routine": [{"family": "sol", "effort": "medium"}], "multi_file": [{"family": "sol", "effort": "high"}], "architecture": [{"family": "astra", "effort": "xhigh"}]}}
LIGHT = "laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task"
HEAVY = "laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task"
PLAN = "laya · reads like a multi-step change (p=0.88) → Plan mode (/plan), or tell Codex to plan first"


def answers(quick=.6, routine=.26, multi=.08, arch=.06, plan=.2, parallel=.1, confidence=.99):
    return {"difficulty": {"probabilities": {"quick": quick, "routine": routine, "multi_file": multi, "architecture": arch}}, "plan_first": {"noul": plan, "confidence": confidence}, "parallel": {"noul": parallel}}


def run(a=None, **kwargs):
    params = dict(first_human=True, plan_shown=False, permission_mode="auto", prompt="fix typo", display=DISPLAY, catalog=CATALOG, fit=FIT, session={"model": "gpt-6-luna", "effort": None})
    params.update(kwargs)
    return adapter.decide(a if a is not None else answers(), **params)


@pytest.mark.parametrize("a,lines", [
    (answers(), [LIGHT]),
    (answers(quick=.03, routine=.06, multi=.3, arch=.61), [HEAVY]),
    (answers(quick=.4, routine=.3, multi=.2, arch=.1, plan=.88), [PLAN]),
    (answers(plan=.88), [LIGHT, PLAN]),
    (answers(quick=.4, routine=.3, multi=.2, arch=.1), []),
])
def test_copy_states_and_exact_return_keys(a, lines):
    d = run(a)
    assert d["lines"] == lines
    assert set(d) == {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}
    assert d["line_for"] == {"model": next((x for x in lines if " task (" in x), None), "plan": next((x for x in lines if "multi-step" in x), None)}
    assert adapter.RULES_VERSION == "codex_v0"


@pytest.mark.parametrize("quick,routine,expected", [(.1,.7,"0.80"), (.4501,.3501,"0.80"), (.4501,.3551,"0.81"), (.4,.3999,None)])
def test_tier_gate_and_display_boundary(quick, routine, expected):
    d = run(answers(quick=quick, routine=routine, multi=.1, arch=1-quick-routine-.1))
    if expected is None:
        assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold"
    else:
        assert f"(p={expected})" in d["lines"][0]


@pytest.mark.parametrize("p,expected", [(.85,"0.85"), (.8496,None), (.8567,"0.86")])
def test_independent_plan_gate_ignores_confidence(p, expected):
    d = run(answers(quick=.4, routine=.3, plan=p, confidence=1-p))
    assert d["lines"] == ([] if expected is None else [f"laya · reads like a multi-step change (p={expected}) → Plan mode (/plan), or tell Codex to plan first"])


@pytest.mark.parametrize("probs,expected", [
    ({"quick": .25, "routine": .25, "multi_file": .25, "architecture": .25}, ("light", .5, "quick")),
    ({"quick": .05, "routine": .05, "multi_file": .45, "architecture": .45}, ("heavy", .9, "multi_file")),
])
def test_tie_rules(probs, expected):
    assert adapter.tier_and_class(probs) == expected


@pytest.mark.parametrize("kwargs,model,plan", [
    ({"first_human": False}, "not_first_prompt", "too_short"),
    ({"permission_mode": "plan"}, None, "plan_mode"),
    ({"prompt": "  /plan stuff"}, None, "plan_mode"),
    ({"plan_shown": True}, None, "already_shown"),
    ({"first_human": False, "prompt": "x"*199, "plan_shown": True}, "not_first_prompt", "too_short"),
    ({"first_human": False, "prompt": "x"*200}, "not_first_prompt", None),
    ({"first_human": False, "permission_mode": "plan", "plan_shown": True}, "not_first_prompt", "plan_mode"),
])
def test_suppression_precedence(kwargs, model, plan):
    d = run(answers(plan=.88), **kwargs)
    assert d["suppress_reason"] == {"model": model, "plan": plan}


def test_same_model_unknown_effort_does_not_suppress():
    d = run()
    assert d["lines"] == [LIGHT]
    assert d["suggestion"] == {"model": "gpt-6-luna", "display": "GPT-6 Luna", "effort": "low", "class": "quick"}


@pytest.mark.parametrize("cls,a,model,effort", [
    ("routine", answers(quick=.1,routine=.7,multi=.1,arch=.1), "gpt-6.1-sol", "medium"),
    ("multi_file", answers(quick=.03,routine=.06,multi=.61,arch=.3), "gpt-6.1-sol", "high"),
])
def test_other_fit_classes(cls,a,model,effort):
    assert run(a)["suggestion"] == {"model": model, "display": "GPT-6.1 Sol", "effort": effort, "class": cls}


@pytest.mark.parametrize("change", ["allowed", "in_picker", "effort_levels"])
def test_ineligible_cheapest_falls_back(change):
    cat = copy.deepcopy(CATALOG)
    cat["models"][0][change] = [] if change == "effort_levels" else False
    assert run(catalog=cat)["suggestion"]["model"] == "gpt-6.1-sol"


@pytest.mark.parametrize("field,text", [("id", "gpt-fable-6"), ("family", "Fable"), ("display", "GPT Mythos")])
def test_injected_forbidden_catalog_cannot_recommend(field, text):
    cat = copy.deepcopy(CATALOG)
    cat["models"][0][field] = text
    fit = {"classes": {"quick": [{"model": cat["models"][0]["id"], "effort": "low"}]}}
    d = run(catalog=cat, fit=fit)
    assert d["lines"] == [] and d["suggestion"] is None and d["suppress_reason"]["model"] == "no_fit"


def test_no_fit_does_not_gate_plan():
    d = run(answers(plan=.88), fit={"classes": {}})
    assert d["lines"] == [PLAN] and d["suppress_reason"]["model"] == "no_fit"


def test_cheapest_then_newest_numeric_version():
    cat = copy.deepcopy(CATALOG)
    old = copy.deepcopy(cat["models"][0])
    old.update(id="gpt-luna-5", version="5", display="Luna 5")
    newer = copy.deepcopy(old)
    newer.update(id="gpt-luna-6.10",version="6.10",display="Luna 6.10")
    cat["models"] += [old,newer]
    fit = {"classes": {"quick": [{"model": m["id"], "effort": "low"} for m in (cat["models"][0], old, newer)]}}
    assert run(catalog=cat, fit=fit)["suggestion"]["model"] == "gpt-luna-6.10"
    newer["price"] = {"input": .2}
    assert run(catalog=cat, fit=fit)["suggestion"]["model"] == "gpt-6-luna"


def test_three_mismatch_entries_and_parallel_log_only():
    d = run(answers(quick=.4,routine=.3,multi=.2,arch=.1,parallel=.99))
    assert d["lines"] == []
    assert d["mismatches"] == [
        {"type": "MODEL+REASONING", "profile": {"tier": "light", "tier_p": .7, "class": "quick"}, "state": {"model": "gpt-6-luna", "effort": None}, "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": .2}, "state": {"permission_mode": "auto"}, "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": .99}, "state": {}, "channel_later": "harness"},
    ]
