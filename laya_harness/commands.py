"""`laya-harness setup | status | stop | mode` (spec §4.5, §4.11). Only `setup` touches the
network, and only to download the pinned checkpoint."""

import argparse
import json
import os
import signal
import subprocess
import sys

from . import codex_resources, catalog, config, hookargv, paths, resources, service_client

SETUP_SESSION = "laya-setup-check"


def _download(checkpoint: dict, model_dir) -> None:
    from huggingface_hub import snapshot_download

    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(checkpoint["repo"], revision=checkpoint["revision"], local_dir=str(model_dir),
                      allow_patterns=checkpoint["files"])


def _complete(model_dir, checkpoint: dict) -> bool:
    return all((model_dir / name).is_file() for name in checkpoint["required"])


def setup(download=None, out=None) -> int:
    out = out or sys.stdout
    paths.ensure_home()
    ck = resources.checkpoint()
    model_dir = paths.models_dir() / f"laya-mlx@{ck['revision']}"
    weights = model_dir / "model.safetensors"
    if _complete(model_dir, ck) and resources.sha256_file(weights) == ck["weights_sha256"]:
        print(f"checkpoint already in place: {model_dir}", file=out)
    else:
        print(f"downloading the pinned checkpoint (about 807 MB) from {ck['repo']}@{ck['revision'][:12]} "
              f"into {model_dir}", file=out)
        (download or _download)(ck, model_dir)
        if not _complete(model_dir, ck) or resources.sha256_file(weights) != ck["weights_sha256"]:
            print("the download is incomplete or does not match the pinned sha256", file=out)
            return 1
    cfg = config.load()
    cfg.update(interpreter=sys.executable, model_dir=str(model_dir), repo=ck["repo"], revision=ck["revision"])
    config.save(cfg)

    argv = hookargv.hook_argv(sys.executable, "claude-code", "PostModelSwitch")
    probe = {"session_id": SETUP_SESSION, "hook_event_name": "PostModelSwitch"}
    result = subprocess.run(argv, input=json.dumps(probe).encode(), capture_output=True, timeout=30)
    (paths.sessions_dir() / f"{SETUP_SESSION}.json").unlink(missing_ok=True)
    if result.returncode != 0 or result.stdout:
        print(f"the hook command failed its check (exit {result.returncode})", file=out)
        return 1
    print("Add these hooks to ~/.claude/settings.json (spec §10):", file=out)
    print(json.dumps(hookargv.settings_snippet(sys.executable), indent=2), file=out)
    return 0


def unknown_models() -> set:
    known = {"codex": catalog.known(codex_resources.catalog()),
             "claude-code": catalog.known(resources.catalog())}
    seen = set()
    path = paths.decisions_path()
    if not path.is_file():
        return seen
    with open(path, encoding="utf-8", errors="replace") as f:  # line by line: the log can be large
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            session = row.get("session") if isinstance(row, dict) else None
            model = session.get("model") if isinstance(session, dict) else None
            name = catalog.canonical(model) if isinstance(model, str) else None
            harness = row.get("harness") if isinstance(row, dict) else None
            if harness is None:
                harness = "claude-code"
            elif not isinstance(harness, str) or not harness:
                continue
            if name and name not in known.get(harness, set()):
                seen.add(name)
    return seen


def status(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        state = "down"
    elif outcome == "ok":
        state = body["state"] + (f" ({body['reason']})" if body.get("reason") else "")
    else:
        state = f"unreachable ({outcome})"
    revision = (cfg.get("revision") or "")[:12] or "not set up"
    print(f"laya-harness: {state} · mode {cfg['mode']} · checkpoint {revision} · logs {paths.home()}", file=out)
    unknown = unknown_models()
    if unknown:
        print("models in the log that the catalog does not list: " + ", ".join(sorted(unknown)), file=out)
    return 0


def stop(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        print("laya-harness: not running", file=out)
        return 0
    if outcome != "ok":
        print(f"laya-harness: port {config.port(cfg)} did not answer as laya-harness ({outcome}); "
              "nothing stopped", file=out)
        return 1
    pid = body.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1 or pid == os.getpid():
        print(f"laya-harness: the service reported an invalid pid {pid!r}; nothing stopped", file=out)
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:  # it exited between the health check and the signal
        print("laya-harness: not running", file=out)
        return 0
    print(f"stopped the service (pid {body['pid']})", file=out)
    if cfg["mode"] != "off":
        print("note: the next prompt starts it again; `laya-harness mode off` keeps it down", file=out)
    return 0


def set_mode(value: str, out=None) -> int:
    out = out or sys.stdout
    if value not in config.MODES:
        raise ValueError(f"mode must be one of {', '.join(config.MODES)}, not {value!r}")
    cfg = config.load()
    cfg["mode"] = value
    config.save(cfg)
    print(f"mode: {value}", file=out)
    return 0


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="laya-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="download the pinned checkpoint and print the hooks snippet")
    sub.add_parser("status", help="one line: service state, mode, checkpoint, logs")
    sub.add_parser("stop", help="stop the running service")
    mode = sub.add_parser("mode", help="show, log-only or off")
    mode.add_argument("value", choices=config.MODES)
    args = parser.parse_args(argv)
    if args.command == "setup":
        return setup()
    if args.command == "status":
        return status()
    if args.command == "stop":
        return stop()
    return set_mode(args.value)
