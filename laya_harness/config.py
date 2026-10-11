"""`~/.laya-harness/config.json` (spec §4.2, §4.4, §4.5, §4.11).

The port always comes from this file: hooks in the desktop app do not inherit variables
exported in the user's shell.
"""

import json
import sys

from . import paths

DEFAULT_PORT = 47913
MODES = ("show", "log-only", "off")
DEFAULTS = {
    "port": DEFAULT_PORT,
    "mode": "show",
    "model_mode": "real",  # "real" loads laya-mlx; "fake" returns `fake_answers`
    "idle_seconds": 900,
    "interpreter": None,  # None means the interpreter running the client
    "model_dir": None,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    path = paths.config_path()
    if path.is_file():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    if cfg["mode"] not in MODES:
        raise ValueError(f"unknown mode: {cfg['mode']!r}")
    return cfg


def save(cfg: dict) -> None:
    paths.ensure_home()
    paths.write_private(paths.config_path(), json.dumps(cfg, indent=2, sort_keys=True) + "\n")


def port(cfg: dict) -> int:
    value = int(cfg["port"])
    if not 1 <= value <= 65535:
        raise ValueError(f"port out of range: {value}")
    if paths.testing() and value == DEFAULT_PORT:
        raise paths.StateDirError("tests must not use port 47913")
    return value


def interpreter(cfg: dict) -> str:
    return cfg.get("interpreter") or sys.executable
