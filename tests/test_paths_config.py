import json
import os
import stat
import sys

import pytest

from laya_harness import config, paths


def mode_of(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_home_honours_override_under_test_flag(home):
    assert paths.home() == home


@pytest.mark.parametrize("alias", [
    str(paths.REAL_HOME),
    "~/.laya-harness",
    f"{paths.REAL_HOME}/.",
    str(paths.REAL_HOME / "inside"),
    str(paths.REAL_HOME.parent),
])
def test_home_refuses_real_state_dir_its_children_and_parents(monkeypatch, alias):
    monkeypatch.setenv("LAYA_HARNESS_HOME", alias)
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_home_refuses_a_symlink_to_the_real_state_dir(monkeypatch, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(paths.REAL_HOME)
    monkeypatch.setenv("LAYA_HARNESS_HOME", str(link))
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_home_requires_override_under_test_flag(monkeypatch):
    monkeypatch.delenv("LAYA_HARNESS_HOME", raising=False)
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_override_ignored_without_test_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("LAYA_HARNESS_TEST", "0")
    monkeypatch.setenv("LAYA_HARNESS_HOME", str(tmp_path))
    assert paths.home() == paths.REAL_HOME


def test_state_file_names(home):
    names = [p.name for p in (paths.config_path(), paths.decisions_path(), paths.client_log(),
                              paths.service_log(), paths.sessions_dir(), paths.models_dir())]
    assert names == ["config.json", "decisions.jsonl", "client.log", "service.log", "sessions", "models"]
    assert {p.parent for p in (paths.config_path(), paths.sessions_dir(), paths.models_dir())} == {home}


def test_ensure_home_is_private(home):
    paths.ensure_home()
    assert mode_of(home) == 0o700 and mode_of(home / "sessions") == 0o700


def test_ensure_home_tightens_existing_dirs(home):
    (home / "sessions").mkdir(parents=True)
    home.chmod(0o755)
    (home / "sessions").chmod(0o755)
    paths.ensure_home()
    assert mode_of(home) == 0o700 and mode_of(home / "sessions") == 0o700


def test_load_returns_defaults_without_file(home):
    cfg = config.load()
    assert cfg["port"] == 47913 and cfg["mode"] == "show" and cfg["model_mode"] == "real"
    assert cfg["idle_seconds"] == 900
    assert cfg["interpreter"] is None and cfg["model_dir"] is None


def test_load_does_not_share_the_defaults(home):
    cfg = config.load()
    cfg["port"] = 1
    assert config.DEFAULTS["port"] == 47913 and config.load()["port"] == 47913


def test_save_round_trips_and_is_private(home):
    config.save({"port": 5555, "mode": "log-only"})
    assert config.load()["mode"] == "log-only"
    assert mode_of(home / "config.json") == 0o600
    assert json.loads((home / "config.json").read_text())["port"] == 5555


@pytest.mark.parametrize("mode", ["show", "log-only", "off"])
def test_every_spec_mode_is_accepted(home, mode):
    config.save({"mode": mode})
    assert config.load()["mode"] == mode


def test_unknown_mode_rejected(home):
    home.mkdir(parents=True)
    (home / "config.json").write_text(json.dumps({"mode": "loud"}))
    with pytest.raises(ValueError):
        config.load()


def test_port_refuses_real_port_under_test_flag(home):
    with pytest.raises(paths.StateDirError):
        config.port({"port": 47913})
    with pytest.raises(paths.StateDirError):
        config.port({"port": "47913"})
    assert config.port({"port": 5555}) == 5555


def test_port_allows_the_default_outside_tests(monkeypatch):
    monkeypatch.setenv("LAYA_HARNESS_TEST", "0")
    assert config.port({"port": 47913}) == 47913


def test_port_ignores_a_conflicting_environment_variable(monkeypatch):
    monkeypatch.setenv("LAYA_HARNESS_PORT", "43210")
    assert config.port({"port": 5555}) == 5555


@pytest.mark.parametrize("bad", [0, -1, 65536])
def test_port_out_of_range_is_rejected(bad):
    with pytest.raises(ValueError):
        config.port({"port": bad})


def test_interpreter_defaults_to_the_running_python():
    assert config.interpreter({"interpreter": None}) == sys.executable
    assert config.interpreter({"interpreter": "/x/python"}) == "/x/python"


def test_write_private_uses_unique_temps_and_cleans_up(home, monkeypatch):
    paths.ensure_home()
    target = home / "state.json"
    seen, real_replace = [], os.replace

    def recording(src, dst):
        seen.append(os.path.basename(src))
        real_replace(src, dst)

    monkeypatch.setattr(paths.os, "replace", recording)
    paths.write_private(target, "a")
    paths.write_private(target, "b")
    assert len(set(seen)) == 2 and target.read_text() == "b" and mode_of(target) == 0o600

    def failing(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(paths.os, "replace", failing)
    with pytest.raises(OSError):
        paths.write_private(target, "c")
    assert target.read_text() == "b" and list(home.glob("*.tmp")) == []


def test_append_private_creates_user_only_file(home):
    paths.ensure_home()
    target = home / "log.jsonl"
    paths.append_private(target, "a")
    paths.append_private(target, "b\n")
    assert target.read_text() == "a\nb\n" and mode_of(target) == 0o600


def test_append_private_tightens_an_existing_file(home):
    paths.ensure_home()
    target = home / "loose.log"
    target.write_text("old\n")
    target.chmod(0o644)
    paths.append_private(target, "new")
    assert target.read_text() == "old\nnew\n" and mode_of(target) == 0o600
