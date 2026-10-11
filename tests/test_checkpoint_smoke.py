"""Controller-only gate (`pytest -m real_model`): the pinned checkpoint, the packaged question
set and the check-6 settings, end to end through the real service (spec §4.4, §4.5, check 6).
The weights are read from ~/.laya-harness/models; all other state uses a temporary directory."""

import time
from pathlib import Path

import pytest

from conftest import write_config
from laya_harness import resources
from procs import request, start_service, stop, wait_health

pytestmark = pytest.mark.real_model

MODEL_DIR = Path.home() / ".laya-harness" / "models" / f"laya-mlx@{resources.checkpoint()['revision']}"


def test_real_service_answers_the_stage0_questions(configured, home):
    if not MODEL_DIR.is_dir():
        pytest.fail(f"pinned checkpoint missing: {MODEL_DIR} (run `laya-harness setup`)")
    write_config(home, model_mode="real", model_dir=str(MODEL_DIR))
    started = time.monotonic()
    proc = start_service(home)
    try:
        health = wait_health(configured["port"], want=("ready", "not_ready"), timeout=30)
        assert health["state"] == "ready", health
        cold = time.monotonic() - started
        assert cold < 6.0, f"cold start {cold:.2f}s"

        t = time.monotonic()
        status, body = request(configured["port"], "POST", "/v1/profile",
                               {"prompt": "rename the variable foo to bar in utils.py"}, timeout=5)
        warm = time.monotonic() - t
        assert status == 200 and warm < 1.0, (status, warm)

        answers = body["answers"]
        assert sorted(answers) == ["difficulty", "parallel", "plan_first"]
        probabilities = answers["difficulty"]["probabilities"]
        assert set(probabilities) == {"quick", "routine", "multi_file", "architecture"}
        assert abs(sum(probabilities.values()) - 1) <= 0.0002
        for field in ("plan_first", "parallel"):
            assert 0 <= answers[field]["noul"] <= 1
        assert body["usage"]["truncated"] is False
        assert body["versions"]["laya_mlx"] == "0.3.0"

        status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "word " * 900}, timeout=5)
        assert status == 200 and body["usage"]["truncated"] is True

        log = (home / "service.log").read_text() if (home / "service.log").exists() else ""
        assert log == ""  # started directly by the test, so stderr went to DEVNULL, not the log
    finally:
        stop(proc)
