"""Entry point: `python -I -m laya_harness hook claude-code <Event>` (hooks) and the
`laya-harness` console script (commands)."""

import time

_STARTED = time.monotonic()  # the hook's duration is measured from process start (spec §8)

import os  # noqa: E402
import sys  # noqa: E402


def _hook(args: list) -> None:
    """Never raises, always exits 0, and writes at most one JSON object to stdout (spec §4.2).

    Exit code 2 would block the prompt in every project, so argument errors, bad input and
    crashes all end the same way: nothing on stdout, exit 0, a line in client.log.
    """
    harness, event = (list(args) + [None, None])[:2]
    if harness == "codex":
        # Whole-process budget, including stdin and potentially blocked private paths.
        try:
            import signal

            def expired(signum, frame):
                os._exit(0)

            signal.signal(signal.SIGALRM, expired)
            budget = 4.5 if event == "SessionStart" else 1.5
            remaining = _STARTED + budget - time.monotonic()
            if remaining <= 0:
                os._exit(0)
            signal.setitimer(signal.ITIMER_REAL, remaining)
        except BaseException:  # noqa: BLE001 — watchdog failure must not touch state
            os._exit(0)
    out = None
    real_stdout = None
    try:
        real_stdout = os.dup(1)
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)  # nothing a library or child writes reaches Claude
        sys.stdout = sys.stderr  # stray prints must never reach Claude's context
        from . import paths

        try:
            paths.ensure_home()
            log_fd = os.open(paths.client_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            os.fchmod(log_fd, 0o600)
            os.dup2(log_fd, 2)
        except BaseException:  # noqa: BLE001
            pass
        harness, event = (list(args) + [None, None])[:2]
        if harness == "codex" and len(args) != 2:
            raise ValueError("Codex hook requires exactly harness and event")
        raw = sys.stdin.buffer.read()  # read stdin to the end before anything is spawned
        from . import client

        out = client.run(harness, event, raw, _STARTED)
    except BaseException as exc:  # noqa: BLE001
        try:
            from . import decision_log

            decision_log.problem(f"hook failed: {type(exc).__name__}: {exc}")
        except BaseException:  # noqa: BLE001
            pass
    try:
        if out and real_stdout is not None:
            os.write(real_stdout, out.encode("utf-8"))
    finally:
        os._exit(0)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["hook"]:
        _hook(argv[1:])
    from . import commands

    return commands.main(argv)


if __name__ == "__main__":
    sys.exit(main())
