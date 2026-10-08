"""Controller-only gate: the pinned checkpoint loads offline with the stage-0 settings and
answers the three stage-0 questions (spec §4.4, §4.5, §4.8, check 6)."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.real_model

MODEL_DIR = (
    Path.home() / ".laya-harness/models/laya-mlx@047678560251f28113ee8f5df4be82102c7bf336"
)
QUESTIONS = {
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
    "plan_first": {
        "type": "noul",
        "instructions": "Should this request be planned before any file is edited?",
    },
    "parallel": {
        "type": "noul",
        "instructions": "Does it contain independent subtasks that could run in parallel?",
    },
}


def test_pinned_checkpoint_answers_offline():
    if not MODEL_DIR.is_dir():
        pytest.fail(f"pinned checkpoint missing: {MODEL_DIR}")
    import laya_mlx as laya

    agent = laya.load(str(MODEL_DIR), dtype="float16", batch_size=1, pad_to_multiple=128)
    agent.cfg["max_len"] = 512
    result = agent.predict("rename the variable foo to bar in utils.py", QUESTIONS)

    answers = result["answers"]
    probabilities = answers["difficulty"]["probabilities"]
    assert set(probabilities) == {"quick", "routine", "multi_file", "architecture"}
    assert abs(sum(probabilities.values()) - 1) <= 0.0002
    for field in ("plan_first", "parallel"):
        assert 0 <= answers[field]["noul"] <= 1
    assert result["usage"]["truncated"] is False
