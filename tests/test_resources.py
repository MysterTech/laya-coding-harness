"""The packaged data, compared field by field with tables copied from the spec (§4.5, §4.8, §4.13)."""

import hashlib

from laya_harness import resources

ALL_EFFORT = ["low", "medium", "high", "xhigh", "max"]
NO_XHIGH = ["low", "medium", "high", "max"]

EXPECTED_QUESTIONS = {
    "id": "profile_v0",
    "questions": {
        "difficulty": {
            "type": "choice",
            "instructions": "How much work does the request in this message need?",
            "criteria": {
                "quick": "quick question or tiny edit",
                "routine": "routine single-area change",
                "multi_file": "multi-file feature or debugging",
                "architecture": "architecture, migration or hard reasoning",
            },
        },
        "plan_first": {"type": "noul", "instructions": "Should this request be planned before any file is edited?"},
        "parallel": {"type": "noul", "instructions": "Does it contain independent subtasks that could run in parallel?"},
    },
    "display": {
        "difficulty": {"min_tier_p": 0.8},
        "plan_first": {"show_threshold": 0.85, "min_chars": 200},
        "parallel": {"show_threshold": 0.85, "shown": False},
    },
}

EXPECTED_CHECKPOINT = {
    "repo": "aac6fef/laya-mlx",
    "revision": "047678560251f28113ee8f5df4be82102c7bf336",
    "weights_sha256": "b9c07bf14be2fa5c78a9193a3e6d840ac80e89e62fc40f425834c3d8a6eaa3de",
    "files": ["model.safetensors", "rl_agent_config.json", "encoder/config.json", "tokenizer/*", "mlx_config.json"],
    "required": ["model.safetensors", "rl_agent_config.json", "encoder/config.json",
                 "tokenizer/tokenizer.json", "tokenizer/tokenizer_config.json"],
    "settings": {"dtype": "float16", "batch_size": 1, "pad_to_multiple": 128, "max_len": 512},
    "warmup_words": [0, 60, 150, 260, 380, 600],
}


def _row(display, family, version, price, effort, menu, allowed):
    return {"display": display, "family": family, "version": version, "price": price,
            "effort_levels": effort, "in_picker": True, "menu": menu, "allowed": allowed}


EXPECTED_MODELS = {  # spec §4.13 starting catalog
    "claude-opus-5-5": _row("Opus 5.5", "opus", "5.5", {"input": 4.0, "output": 20.0}, ALL_EFFORT, "main", True),
    "claude-sonnet-5-5": _row("Sonnet 5.5", "sonnet", "5.5", {"input": 2.0, "output": 10.0}, ALL_EFFORT, "main", True),
    "claude-haiku-5-5": _row("Haiku 5.5", "haiku", "5.5", {"input": 0.1, "output": 0.5, "input_above_100k": 0.5,
                                                         "output_above_100k": 2.5}, ALL_EFFORT, "main", True),
    "claude-opus-5": _row("Opus 5", "opus", "5", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-8": _row("Opus 4.8", "opus", "4.8", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-7": _row("Opus 4.7", "opus", "4.7", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-6": _row("Opus 4.6", "opus", "4.6", {"input": 5.0, "output": 25.0}, NO_XHIGH, "more", False),
    "claude-sonnet-5": _row("Sonnet 5", "sonnet", "5", {"input": 2.0, "output": 10.0}, ALL_EFFORT, "more", False),
    "claude-sonnet-4-6": _row("Sonnet 4.6", "sonnet", "4.6", {"input": 3.0, "output": 15.0}, NO_XHIGH, "more", False),
    "claude-haiku-4-5": _row("Haiku 4.5", "haiku", "4.5", {"input": 1.0, "output": 5.0}, [], "more", False),
    "claude-fable-5-1": _row("Fable 5.1", "fable", "5.1", {"input": 10.0, "output": 50.0}, ALL_EFFORT, "main", False),
    "claude-fable-5": _row("Fable 5", "fable", "5", {"input": 10.0, "output": 50.0}, ALL_EFFORT, "more", False),
}


def test_question_set_matches_spec_4_8():
    q = resources.questions()
    assert q == EXPECTED_QUESTIONS
    assert list(q["questions"]["difficulty"]["criteria"]) == ["quick", "routine", "multi_file", "architecture"]


def test_checkpoint_is_pinned_per_spec_4_5():
    assert resources.checkpoint() == EXPECTED_CHECKPOINT


def test_catalog_matches_spec_4_13():
    catalog = resources.catalog()
    assert "docs/reference/model-picker-2026-10-08.png" in catalog["source"]
    rows = {m["id"]: m for m in catalog["models"]}
    assert len(rows) == len(catalog["models"]) == 12
    assert set(rows) == set(EXPECTED_MODELS)
    for model_id, expected in EXPECTED_MODELS.items():
        assert rows[model_id] == {"id": model_id, **expected}, model_id


def test_fit_table_defaults_match_spec_4_13():
    assert resources.fit()["classes"] == {
        "quick": [{"family": "haiku", "effort": "low"}, {"family": "sonnet", "effort": "low"}],
        "routine": [{"family": "sonnet", "effort": "medium"}],
        "multi_file": [{"family": "opus", "effort": "high"}],
        "architecture": [{"family": "opus", "effort": "xhigh"}],
    }


def test_hashes_match_hashlib(tmp_path, monkeypatch):
    assert resources.questions_sha256() == hashlib.sha256(resources.QUESTIONS.read_bytes()).hexdigest()
    both = resources.CATALOG.read_bytes() + resources.FIT.read_bytes()
    assert resources.catalog_sha256() == hashlib.sha256(both).hexdigest()

    before = resources.catalog_sha256()
    edited = tmp_path / "fit.json"
    edited.write_bytes(resources.FIT.read_bytes() + b" ")
    monkeypatch.setattr(resources, "FIT", edited)
    assert resources.catalog_sha256() != before  # editing the fit table changes the recorded hash

    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * (3 * (1 << 20) + 7))  # several 1 MiB chunks, as for the weights
    assert resources.sha256_file(big) == hashlib.sha256(big.read_bytes()).hexdigest()
