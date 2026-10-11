import hashlib
import io
import json
import subprocess
import sys

import pytest

from conftest import write_config
from laya_harness import commands, config, hookargv, resources
from procs import env_for, start_service, stop, wait_health

FAKE_WEIGHTS = b"not really weights"


@pytest.fixture
def fake_checkpoint(monkeypatch):
    ck = dict(resources.checkpoint(), weights_sha256=hashlib.sha256(FAKE_WEIGHTS).hexdigest())
    monkeypatch.setattr(commands.resources, "checkpoint", lambda: ck)
    return ck


def place(model_dir, content, skip=()):
    """Write every required checkpoint file, with `content` as the weights."""
    for name in resources.checkpoint()["required"]:
        if name in skip:
            continue
        path = model_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if name == "model.safetensors" else b"{}")


def writer(content, skip=()):
    calls = []

    def download(ck, model_dir):
        calls.append(model_dir)
        place(model_dir, content, skip)

    download.calls = calls
    return download


def test_setup_downloads_writes_config_and_prints_snippet(home, fake_checkpoint):
    out = io.StringIO()
    download = writer(FAKE_WEIGHTS)
    assert commands.setup(download=download, out=out) == 0
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    assert download.calls == [model_dir]
    cfg = config.load()
    assert cfg["model_dir"] == str(model_dir) and cfg["interpreter"] == sys.executable
    assert cfg["revision"] == "047678560251f28113ee8f5df4be82102c7bf336"
    assert out.getvalue().startswith("downloading the pinned checkpoint (about 807 MB) from aac6fef/laya-mlx@047678560251")
    snippet = json.loads(out.getvalue().split("(spec §10):\n", 1)[1])
    assert snippet == hookargv.settings_snippet(sys.executable)
    assert not (home / "sessions" / f"{commands.SETUP_SESSION}.json").exists()


def test_setup_rerun_preserves_user_port_and_mode(home, fake_checkpoint):
    config.save({"port": 5555, "mode": "log-only"})
    assert commands.setup(download=writer(FAKE_WEIGHTS), out=io.StringIO()) == 0
    cfg = config.load()
    assert (cfg["port"], cfg["mode"]) == (5555, "log-only")


def test_setup_announces_size_source_and_target_before_download(home, fake_checkpoint):
    out = io.StringIO()
    calls = []

    def download(ck, model_dir):
        notice = out.getvalue()
        assert "about 807 MB" in notice
        assert f"{ck['repo']}@{ck['revision'][:12]}" in notice
        assert str(model_dir) in notice
        calls.append(model_dir)
        place(model_dir, FAKE_WEIGHTS)

    assert commands.setup(download=download, out=out) == 0
    assert calls == [home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"]


def test_setup_reuses_a_complete_matching_checkpoint(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, FAKE_WEIGHTS)
    download = writer(FAKE_WEIGHTS)
    out = io.StringIO()
    assert commands.setup(download=download, out=out) == 0
    assert download.calls == [] and "already in place" in out.getvalue()


@pytest.mark.parametrize("argv, output", [
    (["status"], b"laya-harness: down"),
    (["stop"], b"laya-harness: not running\n"),
    (["mode", "off"], b"mode: off\n"),
])
def test_shared_command_paths_import_only_stdlib(configured, home, argv, output):
    probe = """import runpy, sys
before = set(sys.modules)
sys.argv = ['laya_harness'] + sys.argv[1:]
try:
    runpy.run_module('laya_harness', run_name='__main__')
except SystemExit as exc:
    rc = exc.code
roots = {name.partition('.')[0] for name in set(sys.modules) - before}
unexpected = roots - set(sys.stdlib_module_names) - {'laya_harness'}
sys.stderr.write(' '.join(sorted(unexpected)) or 'stdlib only')
sys.exit(rc if not unexpected else 1)
"""
    result = subprocess.run([sys.executable, "-I", "-c", probe, *argv], capture_output=True,
                            env=env_for(home), timeout=3)
    assert result.returncode == 0 and result.stderr == b"stdlib only"
    assert result.stdout.startswith(output)


def test_setup_repairs_a_checkpoint_missing_its_tokenizer(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, FAKE_WEIGHTS, skip=("tokenizer/tokenizer.json",))
    download = writer(FAKE_WEIGHTS)
    assert commands.setup(download=download, out=io.StringIO()) == 0
    assert download.calls == [model_dir]
    assert (model_dir / "tokenizer" / "tokenizer.json").is_file()


def test_setup_replaces_a_complete_checkpoint_whose_weights_do_not_match(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, b"tampered")
    download = writer(FAKE_WEIGHTS)
    out = io.StringIO()
    assert commands.setup(download=download, out=out) == 0
    assert download.calls == [model_dir] and "already in place" not in out.getvalue()


def test_download_fetches_only_the_pinned_revision_and_listed_files(tmp_path, monkeypatch):
    import huggingface_hub

    calls = []
    monkeypatch.setattr(huggingface_hub, "snapshot_download", lambda *a, **k: calls.append((a, k)))
    ck = resources.checkpoint()
    commands._download(ck, tmp_path / "m")
    assert calls == [(("aac6fef/laya-mlx",), {"revision": "047678560251f28113ee8f5df4be82102c7bf336",
                                              "local_dir": str(tmp_path / "m"), "allow_patterns": ck["files"]})]


def test_setup_fails_when_the_hook_command_fails(home, fake_checkpoint, monkeypatch):
    monkeypatch.setattr(commands.hookargv, "hook_argv", lambda *a: [sys.executable, "-c", "import sys; sys.exit(3)"])
    out = io.StringIO()
    assert commands.setup(download=writer(FAKE_WEIGHTS), out=out) == 1
    assert "failed its check (exit 3)" in out.getvalue() and '"hooks"' not in out.getvalue()


def test_setup_rejects_a_checksum_mismatch(home, fake_checkpoint):
    out = io.StringIO()
    assert commands.setup(download=writer(b"tampered"), out=out) == 1
    assert "does not match" in out.getvalue()
    assert not (home / "config.json").exists()


def test_setup_rejects_an_incomplete_download(home, fake_checkpoint):
    out = io.StringIO()
    assert commands.setup(download=writer(FAKE_WEIGHTS, skip=("encoder/config.json",)), out=out) == 1
    assert "incomplete" in out.getvalue()
    assert not (home / "config.json").exists()


def test_mode_sets_config_and_rejects_unknown(home):
    assert commands.main(["mode", "log-only"]) == 0
    assert config.load()["mode"] == "log-only"
    with pytest.raises(SystemExit):
        commands.main(["mode", "loud"])
    with pytest.raises(ValueError):
        commands.set_mode("loud")
    assert config.load()["mode"] == "log-only"


def test_status_down_and_ready(configured, home):
    out = io.StringIO()
    commands.status(out=out)
    assert out.getvalue().startswith("laya-harness: down · mode show · checkpoint not set up ·")
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        commands.status(out=out)
        assert out.getvalue().startswith("laya-harness: ready · mode show")
    finally:
        stop(proc)


@pytest.mark.parametrize("outcome, body, shown", [
    ("ok", {"app": "laya-harness", "state": "not_ready", "reason": "FileNotFoundError: missing x"},
     "not_ready (FileNotFoundError: missing x)"),
    ("ok", {"app": "laya-harness", "state": "loading"}, "loading"),
    ("timeout", None, "unreachable (timeout)"),
    ("foreign", None, "unreachable (foreign)"),
])
def test_status_line_for_each_health_outcome(configured, home, monkeypatch, outcome, body, shown):
    write_config(home, revision="047678560251f28113ee8f5df4be82102c7bf336")
    monkeypatch.setattr(commands.service_client, "health", lambda port, timeout: (outcome, body))
    out = io.StringIO()
    assert commands.status(out=out) == 0
    assert out.getvalue() == f"laya-harness: {shown} · mode show · checkpoint 047678560251 · logs {home}\n"


def test_status_skips_rows_it_cannot_read(configured, home):
    lines = ['{"trunc', "123", "null", "[1]", '{"session": "x"}', '{"session": {"model": 5}}',
             json.dumps({"session": {"model": "claude-opus-6"}})]
    (home / "decisions.jsonl").write_bytes(("\n".join(lines) + "\n").encode() + b"\xff\n")
    out = io.StringIO()
    assert commands.status(out=out) == 0
    assert out.getvalue().splitlines()[1] == "models in the log that the catalog does not list: claude-opus-6"


def test_status_lists_models_the_catalog_does_not_know(configured, home):
    rows = [{"session": {"model": "claude-opus-5-5[1m]"}}, {"session": {"model": "claude-opus-6"}},
            {"session": {"model": None}}]
    (home / "decisions.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = io.StringIO()
    commands.status(out=out)
    assert "models in the log that the catalog does not list: claude-opus-6" in out.getvalue()


def test_stop_kills_the_service_and_warns(configured, home):
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        assert commands.stop(out=out) == 0
        proc.wait(timeout=5)
        assert "stopped the service" in out.getvalue() and "mode off" in out.getvalue()
        out = io.StringIO()
        assert commands.stop(out=out) == 0
        assert out.getvalue().strip() == "laya-harness: not running"
    finally:
        stop(proc)


def test_stop_in_mode_off_does_not_warn(configured, home):
    write_config(home, mode="off")
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        commands.stop(out=out)
        proc.wait(timeout=5)
        assert "mode off" not in out.getvalue()
    finally:
        stop(proc)


@pytest.mark.parametrize("outcome", ["timeout", "foreign", "error"])
def test_stop_reports_a_port_it_cannot_identify(configured, monkeypatch, outcome):
    monkeypatch.setattr(commands.service_client, "health", lambda port, timeout: (outcome, None))
    monkeypatch.setattr(commands.os, "kill", lambda *a: pytest.fail("os.kill called"))
    out = io.StringIO()
    assert commands.stop(out=out) == 1
    assert "not running" not in out.getvalue() and f"({outcome})" in out.getvalue()


@pytest.mark.parametrize("pid", [0, -1, None, "123", True])
def test_stop_never_signals_an_invalid_pid(configured, monkeypatch, pid):
    monkeypatch.setattr(commands.service_client, "health",
                        lambda port, timeout: ("ok", {"app": "laya-harness", "pid": pid, "state": "ready"}))
    monkeypatch.setattr(commands.os, "kill", lambda *a: pytest.fail("os.kill called"))
    assert commands.stop(out=io.StringIO()) == 1
