import os
from pathlib import Path

import pytest

from laya_harness import codex_context

EMPTY = {"model": None, "effort": None, "source": None}


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    return tmp_path


def test_only_defaults_and_provenance(codex_home):
    (codex_home / "config.toml").write_text('model="gpt-6.1-sol"\nmodel_reasoning_effort="high"\nsecret="private"\n[profiles.other]\nmodel="other"\n')
    assert codex_context.defaults() == {"model": "gpt-6.1-sol", "effort": "high", "source": "user_config_default"}


@pytest.mark.parametrize("text,expected", [
    ('model=1\nmodel_reasoning_effort=false', {"model": None, "effort": None, "source": "user_config_default"}),
    ('model="uncatalogued"', {"model": "uncatalogued", "effort": None, "source": "user_config_default"}),
    ('model_reasoning_effort="ultra"', {"model": None, "effort": "ultra", "source": "user_config_default"}),
    ('', {"model": None, "effort": None, "source": "user_config_default"}),
    ('model=[', EMPTY),
    ('model="x"\nmodel="y"', EMPTY),
])
def test_missing_fields_types_and_invalid_toml(codex_home, text, expected):
    (codex_home / "config.toml").write_text(text)
    assert codex_context.defaults() == expected


def test_missing_and_unreadable(codex_home, monkeypatch):
    assert codex_context.defaults() == EMPTY
    (codex_home / "config.toml").mkdir()
    assert codex_context.defaults() == EMPTY


@pytest.mark.parametrize("size,expected", [(65536, "gpt-6-luna"), (65537, None)])
def test_size_limit(codex_home, size, expected):
    prefix = b'model="gpt-6-luna"\n#'
    (codex_home / "config.toml").write_bytes(prefix + b'x' * (size - len(prefix)))
    assert codex_context.defaults()["model"] == expected
    if expected is None:
        assert codex_context.defaults() == EMPTY


def test_fifo_is_refused_without_opening(codex_home):
    os.mkfifo(codex_home / "config.toml")
    assert codex_context.defaults() == EMPTY


def test_device_is_refused(codex_home):
    (codex_home / "config.toml").symlink_to('/dev/null')
    assert codex_context.defaults() == EMPTY


def test_unset_home_uses_user_codex_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    user = tmp_path / ".codex"
    user.mkdir()
    (user / "config.toml").write_text('model="gpt-6-astra"')
    assert codex_context.defaults() == {"model": "gpt-6-astra", "effort": None, "source": "user_config_default"}


def test_unreadable_file_fails_open(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    def refuse(*args, **kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(os, "open", refuse)
    assert codex_context.defaults() == EMPTY


def test_invalid_utf8_fails_open(codex_home):
    (codex_home / "config.toml").write_bytes(b'\xff')
    assert codex_context.defaults() == EMPTY


def test_never_reads_more_than_64k(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    fdopen = os.fdopen
    class BoundedStream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            self.stream.__enter__()
            return self
        def __exit__(self, *args):
            return self.stream.__exit__(*args)
        def fileno(self):
            return self.stream.fileno()
        def read(self, n):
            assert n <= 65536
            return self.stream.read(n)
    monkeypatch.setattr(os, "fdopen", lambda *a, **kw: BoundedStream(fdopen(*a, **kw)))
    assert codex_context.defaults()["model"] == "gpt-6-luna"


def test_replaced_fifo_refused_after_open(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    fifo = codex_home / "fifo"
    os.mkfifo(fifo)
    real_open = os.open
    def replace_open(path, flags):
        assert flags & os.O_NONBLOCK
        return real_open(fifo, flags)
    monkeypatch.setattr(os, "open", replace_open)
    assert codex_context.defaults() == EMPTY


def test_unrelated_deep_toml_yields_null_defaults(codex_home):
    text = 'model = "gpt-6.1-sol"\nignored = ' + '{v = ' * 1100 + '1' + '}' * 1100
    (codex_home / "config.toml").write_text(text)
    assert codex_context.defaults() == EMPTY
