import copy

import pytest

from laya_harness import adapter_claude_code as adapter
from laya_harness import catalog, copytext, resources

DISPLAY = resources.questions()["display"]
CATALOG = resources.catalog()
FIT = resources.fit()


def answers(quick=0.4, routine=0.3, multi=0.2, arch=0.1, plan=0.2, parallel=0.1, plan_confidence=None):
    plan_answer = {"type": "noul", "noul": plan}
    if plan_confidence is not None:
        plan_answer["confidence"] = plan_confidence
    return {
        "difficulty": {"type": "choice", "probabilities": {
            "quick": quick, "routine": routine, "multi_file": multi, "architecture": arch}},
        "plan_first": plan_answer,
        "parallel": {"type": "noul", "noul": parallel},
    }


def run(a, *, first_human=True, plan_shown=False, permission_mode="auto", prompt="fix the typo",
        cat=CATALOG, fit=FIT, session=None):
    return adapter.decide(a, first_human=first_human, plan_shown=plan_shown,
                          permission_mode=permission_mode, prompt=prompt, display=DISPLAY,
                          catalog=cat, fit=fit, session=session or {"model": None, "effort": None})


def allow(*ids):
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        if m["id"] in ids:
            m["allowed"] = True
    return cat


# --- catalog selection (spec §4.13) ---------------------------------------------------

def test_default_fit_picks_cheapest_allowed():
    assert catalog.select("quick", CATALOG, FIT) == {
        "model": "claude-haiku-5-5", "display": "Haiku 5.5", "effort": "low", "class": "quick"}
    assert catalog.select("routine", CATALOG, FIT) == {
        "model": "claude-sonnet-5-5", "display": "Sonnet 5.5", "effort": "medium", "class": "routine"}
    assert catalog.select("multi_file", CATALOG, FIT) == {
        "model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "high", "class": "multi_file"}
    assert catalog.select("architecture", CATALOG, FIT) == {
        "model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "xhigh", "class": "architecture"}


@pytest.mark.parametrize("options", [
    [{"model": "claude-sonnet-5", "effort": "medium"}, {"model": "claude-sonnet-5-5", "effort": "medium"}],
    [{"model": "claude-sonnet-5-5", "effort": "medium"}, {"model": "claude-sonnet-5", "effort": "medium"}],
    [{"family": "sonnet", "effort": "medium"}, {"model": "claude-sonnet-5", "effort": "medium"}],
])
def test_price_ties_go_to_the_newest_version(options):
    # Sonnet 5 and Sonnet 5.5 cost the same; "5" must not beat "5.5"
    choice = catalog.select("routine", allow("claude-sonnet-5"), {"classes": {"routine": options}})
    assert choice["model"] == "claude-sonnet-5-5"


def test_versions_compare_number_by_number():
    cat = {"models": [
        {"id": "x-4-8", "display": "X 4.8", "family": "x", "version": "4.8", "price": {"input": 1.0},
         "effort_levels": ["low"], "in_picker": True, "allowed": True},
        {"id": "x-4-10", "display": "X 4.10", "family": "x", "version": "4.10", "price": {"input": 1.0},
         "effort_levels": ["low"], "in_picker": True, "allowed": True},
    ]}
    fit = {"classes": {"quick": [{"model": "x-4-8", "effort": "low"}, {"model": "x-4-10", "effort": "low"}]}}
    assert catalog.select("quick", cat, fit)["model"] == "x-4-10"
    assert catalog.select("quick", cat, {"classes": {"quick": [{"family": "x", "effort": "low"}]}})["model"] == "x-4-10"


def test_base_price_decides_even_when_tiered():
    # Haiku 5.5's above-100k input price (0.5) would lose to a 0.2 model; its base price (0.1) wins
    cat = copy.deepcopy(CATALOG)
    cat["models"].append({"id": "y-1", "display": "Y 1", "family": "y", "version": "1", "price": {"input": 0.2},
                          "effort_levels": ["low"], "in_picker": True, "allowed": True})
    fit = {"classes": {"quick": [{"model": "y-1", "effort": "low"}, {"family": "haiku", "effort": "low"}]}}
    assert catalog.select("quick", cat, fit)["model"] == "claude-haiku-5-5"


def test_unresolvable_option_falls_through_to_the_next():
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        if m["family"] == "haiku":
            m["allowed"] = False
    assert catalog.select("quick", cat, FIT) == {
        "model": "claude-sonnet-5-5", "display": "Sonnet 5.5", "effort": "low", "class": "quick"}
    fit = {"classes": {"quick": [{"model": "claude-unknown-9", "effort": "low"}, {"family": "sonnet", "effort": "low"}]}}
    assert catalog.select("quick", CATALOG, fit)["model"] == "claude-sonnet-5-5"


@pytest.mark.parametrize("family, model_id, display", [
    ("fable", "claude-fable-5-1", "Fable 5.1"),
    ("Fable", "claude-fable-5-1", "Fable 5.1"),
    (None, "claude-fable-5", "Fable 5"),
    ("opus", "claude-fable-5", "Fable 5"),
    ("opus", "claude-x", "Claude Mythos 5.1"),
    ("fable", "claude-x", "X"),
    ("opus", "claude-fable-9", "X 9"),
])
def test_fable_and_mythos_never_suggested_in_any_form(family, model_id, display):
    model = {"id": model_id, "display": display, "version": "9", "price": {"input": 0.01},
             "effort_levels": ["high"], "in_picker": True, "allowed": True}
    if family is not None:
        model["family"] = family
    cat = {"models": [model]}
    for fit in ({"classes": {"architecture": [{"model": model_id, "effort": "high"}]}},
                {"classes": {"architecture": [{"family": family or "opus", "effort": "high"}]}}):
        assert catalog.select("architecture", cat, fit) is None


def test_fable_never_suggested_even_if_the_catalog_allows_it():
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        m["allowed"] = True
    fit = {"classes": {"architecture": [{"family": "fable", "effort": "high"},
                                        {"model": "claude-fable-5-1", "effort": "high"}]}}
    assert catalog.select("architecture", cat, fit) is None


def test_disallowed_or_not_in_picker_is_skipped():
    fit = {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": None}]}}
    assert catalog.select("quick", CATALOG, fit) is None  # Haiku 4.5 is opt-in
    cat = allow("claude-haiku-4-5")
    for m in cat["models"]:
        if m["id"] == "claude-haiku-4-5":
            m["in_picker"] = False
    assert catalog.select("quick", cat, fit) is None


def test_older_version_only_when_named_and_nothing_cheaper():
    cat = allow("claude-opus-4-8")
    named = {"classes": {"multi_file": [{"model": "claude-opus-4-8", "effort": "high"}]}}
    assert catalog.select("multi_file", cat, named)["model"] == "claude-opus-4-8"
    both = {"classes": {"multi_file": [{"model": "claude-opus-4-8", "effort": "high"},
                                       {"family": "opus", "effort": "high"}]}}
    assert catalog.select("multi_file", cat, both)["model"] == "claude-opus-5-5"
    assert catalog.select("multi_file", cat, FIT)["model"] == "claude-opus-5-5"


def test_model_without_effort_levels_is_named_without_one():
    cat = allow("claude-haiku-4-5")
    lone = {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": None}]}}
    assert catalog.select("quick", cat, lone) == {
        "model": "claude-haiku-4-5", "display": "Haiku 4.5", "effort": None, "class": "quick"}


def test_option_with_an_unsupported_effort_does_not_qualify():
    cat = allow("claude-haiku-4-5", "claude-opus-4-6")
    assert catalog.select("quick", cat, {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": "low"}]}}) is None
    fit = {"classes": {"architecture": [{"model": "claude-opus-4-6", "effort": "xhigh"},
                                        {"family": "opus", "effort": "xhigh"}]}}
    assert catalog.select("architecture", cat, fit)["model"] == "claude-opus-5-5"


def test_cheapest_beats_newest():
    # Haiku 4.5 (older, opted in, $1) beats Sonnet 5.5 ($2) whichever the fit table lists first
    cat = allow("claude-haiku-4-5")
    for order in ([{"model": "claude-sonnet-5-5", "effort": "low"}, {"model": "claude-haiku-4-5"}],
                  [{"model": "claude-haiku-4-5"}, {"model": "claude-sonnet-5-5", "effort": "low"}]):
        assert catalog.select("quick", cat, {"classes": {"quick": order}}) == {
            "model": "claude-haiku-4-5", "display": "Haiku 4.5", "effort": None, "class": "quick"}


def test_effort_stays_with_its_own_option():
    fit = {"classes": {"quick": [{"family": "sonnet", "effort": "medium"}, {"family": "haiku", "effort": "low"}]}}
    assert catalog.select("quick", CATALOG, fit)["effort"] == "low"


def test_canonical_names():
    assert catalog.canonical("claude-opus-5-5[1m]") == "claude-opus-5-5"
    assert catalog.canonical("Claude-Sonnet-4-5-20250929") == "claude-sonnet-4-5"
    assert catalog.canonical(None) is None


def test_known_lists_every_catalog_id_canonically():
    known = catalog.known(CATALOG)
    assert known == {catalog.canonical(m["id"]) for m in CATALOG["models"]}
    assert len(known) == 12 and {"claude-fable-5-1", "claude-fable-5"} <= known
    assert catalog.canonical("claude-opus-5-5[1m]") in known


# --- tier gate and model line (spec §4.9) ----------------------------------------------

def test_tier_sum_is_rounded_and_picks_more_likely_class():
    assert adapter.tier_and_class({"quick": 0.1, "routine": 0.7, "multi_file": 0.1, "architecture": 0.1}) == (
        "light", 0.8, "routine")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.3, "architecture": 0.6}) == (
        "heavy", 0.9, "architecture")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.6, "architecture": 0.3}) == (
        "heavy", 0.9, "multi_file")


def test_ties_go_lighter():
    assert adapter.tier_and_class({"quick": 0.25, "routine": 0.25, "multi_file": 0.25, "architecture": 0.25}) == (
        "light", 0.5, "quick")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.45, "architecture": 0.45}) == (
        "heavy", 0.9, "multi_file")


def test_model_line_on_first_prompt_above_gate():
    d = run(answers(quick=0.5, routine=0.36))
    assert d["lines"] == ["laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task"]
    assert d["suggestion"]["model"] == "claude-haiku-5-5"
    assert d["suppress_reason"]["model"] is None


def test_tier_exactly_at_the_gate_shows():
    d = run(answers(quick=0.1, routine=0.7, multi=0.1, arch=0.1))  # 0.1 + 0.7 carries float noise
    assert d["lines"] == ["laya · light task (p=0.80) → Sonnet 5.5 at medium effort fits this task"]


@pytest.mark.parametrize("quick, routine", [(0.4, 0.3999), (0.4501, 0.3498)])
def test_tier_just_under_the_gate_is_silent(quick, routine):
    d = run(answers(quick=quick, routine=routine, multi=0.1, arch=1 - quick - routine - 0.1))
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold" and d["suggestion"] is None


def test_multi_file_line():
    d = run(answers(quick=0.03, routine=0.06, multi=0.61, arch=0.3))
    assert d["lines"] == ["laya · heavy task (p=0.91) → Opus 5.5 at high effort fits this task"]


def test_heavy_line_matches_copy_deck():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61))
    assert d["lines"][0] == "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task"


def test_model_line_only_on_first_human_prompt():
    d = run(answers(quick=0.5, routine=0.36), first_human=False)
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "not_first_prompt" and d["suggestion"] is None


def test_no_fit_is_silent():
    d = run(answers(quick=0.5, routine=0.36), fit={"classes": {}})
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "no_fit" and d["suggestion"] is None


def test_display_formats_gated_value_to_two_decimals():
    d = run(answers(quick=0.4401, routine=0.3401, multi=0.11, arch=0.1098))  # 0.7802
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold"
    d = run(answers(quick=0.4501, routine=0.3501, multi=0.1, arch=0.0998))  # 0.8002
    assert d["lines"][0].startswith("laya · light task (p=0.80) →")
    d = run(answers(quick=0.4501, routine=0.3551, multi=0.1, arch=0.0948))  # 0.8052 rounds up
    assert d["lines"] == ["laya · light task (p=0.81) → Haiku 5.5 at low effort fits this task"]


# --- copy deck (spec §4.12): the literal spec text --------------------------------------

@pytest.mark.parametrize("line, spec_text", [
    (lambda: copytext.model_line("light", 0.86, "Haiku 5.5", "low"),
     "laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task"),
    (lambda: copytext.model_line("light", 0.86, "Sonnet 5.5", "medium"),
     "laya · light task (p=0.86) → Sonnet 5.5 at medium effort fits this task"),
    (lambda: copytext.model_line("light", 0.86, "Haiku 4.5", None),
     "laya · light task (p=0.86) → Haiku 4.5 fits this task"),
    (lambda: copytext.model_line("heavy", 0.91, "Opus 5.5", "xhigh"),
     "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task"),
    (lambda: copytext.plan_line(0.88),
     "laya · reads like a multi-step change (p=0.88) → Plan mode (mode menu, then 4), or tell Claude to plan first"),
])
def test_copy_deck_rows(line, spec_text):
    assert line() == spec_text


def test_display_rounds_to_two_decimals():
    assert "(p=0.86)" in copytext.plan_line(0.8567)
    assert "(p=0.81)" in copytext.model_line("light", 0.8051, "Haiku 5.5", "low")
    assert "(p=0.78)" in copytext.model_line("light", 0.7802, "Haiku 5.5", "low")


def test_every_copy_string_fits_120_chars():
    for m in CATALOG["models"]:
        for effort in m["effort_levels"] + [None]:
            for tier in ("light", "heavy"):
                assert len(copytext.model_line(tier, 0.99, m["display"], effort)) <= 120
    assert len(copytext.plan_line(0.99)) <= 120


# --- MODE line (spec §4.9) -------------------------------------------------------------

def test_plan_line_shown_on_first_prompt():
    d = run(answers(plan=0.88))
    assert d["lines"][-1] == ("laya · reads like a multi-step change (p=0.88) → Plan mode (mode menu, "
                              "then 4), or tell Claude to plan first")


def test_plan_exactly_at_the_threshold_shows():
    d = run(answers(plan=0.85))
    assert d["lines"] == [copytext.plan_line(0.85)] and "(p=0.85)" in d["lines"][0]


def test_plan_below_threshold_even_if_it_would_display_as_threshold():
    d = run(answers(plan=0.8496))
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "below_threshold"


@pytest.mark.parametrize("noul, confidence, shown", [(0.30, 0.70, False), (0.90, 0.10, True), (0.30, 0.99, False)])
def test_plan_uses_noul_never_confidence(noul, confidence, shown):
    d = run(answers(plan=noul, plan_confidence=confidence))
    assert d["lines"] == ([copytext.plan_line(noul)] if shown else [])


@pytest.mark.parametrize("mode, prompt", [("plan", "x" * 300), ("auto", "/plan " + "x" * 300),
                                         ("auto", "   /plan " + "x" * 300), ("auto", "/plan"),
                                         ("auto", "/planning-notes " + "x" * 300)])
def test_no_plan_line_in_plan_mode(mode, prompt):
    d = run(answers(plan=0.95), permission_mode=mode, prompt=prompt)
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "plan_mode"


def test_plan_mentioned_mid_prompt_does_not_suppress():
    d = run(answers(plan=0.95), prompt="see the /plan command docs " + "x" * 200)
    assert d["lines"] == [copytext.plan_line(0.95)]


def test_plan_needs_first_prompt_or_200_chars():
    assert run(answers(plan=0.9), first_human=False, prompt="x" * 199)["suppress_reason"]["plan"] == "too_short"
    assert len(run(answers(plan=0.9), first_human=False, prompt="x" * 200)["lines"]) == 1


def test_plan_line_once_per_session():
    d = run(answers(plan=0.9), plan_shown=True)
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "already_shown"


@pytest.mark.parametrize("kwargs, model_reason, plan_reason", [
    (dict(a=answers(quick=0.4, routine=0.3, plan=0.5), first_human=False), "not_first_prompt", "below_threshold"),
    (dict(a=answers(plan=0.5), permission_mode="plan"), "below_threshold", "below_threshold"),
    (dict(a=answers(plan=0.9), permission_mode="plan", first_human=False, prompt="x", plan_shown=True),
     "not_first_prompt", "plan_mode"),
    (dict(a=answers(plan=0.9), first_human=False, prompt="x", plan_shown=True), "not_first_prompt", "too_short"),
])
def test_suppress_reason_precedence(kwargs, model_reason, plan_reason):
    kwargs = dict(kwargs)
    d = run(kwargs.pop("a"), **kwargs)
    assert d["suppress_reason"] == {"model": model_reason, "plan": plan_reason}


def test_both_lines_model_first():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61, plan=0.91))
    assert len(d["lines"]) == 2 and d["lines"][0].startswith("laya · heavy task")
    assert d["lines"][1].startswith("laya · reads like")
    assert d["line_for"] == {"model": d["lines"][0], "plan": d["lines"][1]}


def test_mismatches_record_profile_state_and_channel():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61, plan=0.91, parallel=0.42),
            permission_mode="acceptEdits", session={"model": "claude-opus-4-7", "effort": "high"})
    assert d["mismatches"] == [
        {"type": "MODEL+REASONING", "profile": {"tier": "heavy", "tier_p": 0.91, "class": "architecture"},
         "state": {"model": "claude-opus-4-7", "effort": "high"}, "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": 0.91}, "state": {"permission_mode": "acceptEdits"},
         "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": 0.42}, "state": {}, "channel_later": "harness"},
    ]


def test_parallel_is_logged_never_shown():
    d = run(answers(parallel=0.99))
    assert d["lines"] == []
    assert {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": 0.99}, "state": {},
            "channel_later": "harness"} in d["mismatches"]


def test_never_a_decision_key():
    for a in (answers(quick=0.5, routine=0.36, plan=0.9), answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61)):
        d = run(a)
        assert set(d) == {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}
