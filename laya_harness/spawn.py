"""Request the service asynchronously (spec §4.3).

Darwin production uses the bounded launchd broker; other platforms and ordinary tests
start the service directly. Both paths isolate stdio and never wait in the hook.
"""

import os
import subprocess
import sys

from . import config, paths


def service_argv(interpreter: str) -> list:
    return [interpreter, "-I", "-m", "laya_harness.service"]


def spawn_service(cfg: dict) -> None:
    home = paths.ensure_home()
    fd = os.open(paths.service_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "ab") as log:
        subprocess.Popen(
            ([config.interpreter(cfg), "-I", "-m", "laya_harness.launchd"]
             if sys.platform == "darwin" and not paths.testing()
             else service_argv(config.interpreter(cfg))),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
            close_fds=True,
            cwd=str(home),
        )
