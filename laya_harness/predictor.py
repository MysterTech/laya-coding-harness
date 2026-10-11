"""What answers the three questions (spec §4.4, §4.5).

`FakePredictor` never imports laya_mlx; tests and acceptance step 1 use it. `RealPredictor`
loads the pinned checkpoint from an absolute local directory, offline, with the check-6
settings, and warms every padded length before it is ready.
"""

import copy
import json
import os
import sys
import time
from pathlib import Path

from . import paths, resources

DEFAULT_FAKE_USAGE = {"truncated": False, "state_tokens": 0, "state_tokens_dropped": 0}
PROMPT_CHAR_CAP = 65536  # far more than 512 tokens; tokenizing a huge paste would hold the GIL for seconds


class FakePredictor:
    laya_mlx_version = None

    def __init__(self, cfg: dict):
        self.answers = cfg.get("fake_answers") or {}
        self.load_seconds = float(cfg.get("fake_load_seconds", 0))
        self.predict_seconds = float(cfg.get("fake_predict_seconds", 0))
        self.load_error = cfg.get("fake_load_error")
        self.predict_error = cfg.get("fake_predict_error")
        self.print_stdout = bool(cfg.get("fake_print_stdout"))

    def load(self) -> None:
        if self.print_stdout:  # proves the spawn contract keeps this away from the hook
            print("fake service noise on stdout", flush=True)
            print("fake service noise on stderr", file=sys.stderr, flush=True)
        paths.append_private(paths.home() / "fake_loads.txt", str(os.getpid()))
        time.sleep(self.load_seconds)
        if self.load_error:
            raise RuntimeError(self.load_error)

    def predict(self, prompt: str) -> dict:
        time.sleep(self.predict_seconds)
        if self.predict_error:
            raise RuntimeError(self.predict_error)
        return {"answers": copy.deepcopy(self.answers), "usage": dict(DEFAULT_FAKE_USAGE),
                "input_chars_dropped": 0}


class RealPredictor:
    def __init__(self, cfg: dict, questions: dict | None = None):
        self.checkpoint = resources.checkpoint()
        self.questions = resources.questions_snapshot()[0]["questions"] if questions is None else questions
        self.model_dir = cfg.get("model_dir")
        self.revision = cfg.get("revision")
        self.agent = None
        self.laya_mlx_version = None

    def missing(self) -> list:
        root = Path(self.model_dir)
        return [name for name in self.checkpoint["required"] if not (root / name).is_file()]

    def load(self) -> None:
        if not self.model_dir or not os.path.isabs(self.model_dir):
            raise FileNotFoundError("model_dir must be an absolute local directory")
        pinned = self.checkpoint["revision"]
        if self.revision is not None and self.revision != pinned:
            raise ValueError(f"config.json names revision {str(self.revision)[:12]}, not the pinned "
                             f"{pinned[:12]}: run laya-harness setup")
        missing = self.missing()
        if missing:
            raise FileNotFoundError("missing " + ", ".join(missing))
        os.environ["HF_HUB_OFFLINE"] = "1"
        import laya_mlx

        s = self.checkpoint["settings"]
        self.agent = laya_mlx.load(self.model_dir, dtype=s["dtype"], batch_size=s["batch_size"],
                                   pad_to_multiple=s["pad_to_multiple"])
        self.agent.cfg["max_len"] = s["max_len"]
        print(json.dumps({"temperature": list(self.agent.temperature),
                          "temperature_by_options": dict(self.agent.temperature_by_options)}),
              file=sys.stderr, flush=True)
        for words in self.checkpoint["warmup_words"]:
            self.agent.predict(("word " * words) or "warm-up", self.questions)
        self.laya_mlx_version = laya_mlx.__version__

    def predict(self, prompt: str) -> dict:
        result = self.agent.predict(prompt[:PROMPT_CHAR_CAP], self.questions)
        return {**result, "input_chars_dropped": max(0, len(prompt) - PROMPT_CHAR_CAP)}


def make(cfg: dict, questions: dict | None = None):
    return FakePredictor(cfg) if cfg.get("model_mode") == "fake" else RealPredictor(cfg, questions)
