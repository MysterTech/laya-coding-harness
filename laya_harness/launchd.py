"""Bounded on-demand macOS service registration; never loads the predictor."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import signal
import stat
import subprocess
import sys
import tempfile
import time

from . import config, paths, spawn

BUDGET = 0.6
WALL_BUDGET = 3.5


def definition(home, interpreter):
    home = Path(home)
    if not home.is_absolute() or home != home.resolve():
        raise ValueError("canonical absolute state home required")
    info = home.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("owned directory required")
    if not os.path.isabs(interpreter) or not os.access(interpreter, os.X_OK):
        raise ValueError("absolute executable interpreter required")
    digest = hashlib.sha256(f"{os.getuid()}\0{home}\0{interpreter}".encode()).hexdigest()[:24]
    label = "local.laya-harness.service." + digest
    environment = {"HF_HUB_OFFLINE": "1"}
    if paths.testing():
        if home != paths.home().resolve():
            raise paths.StateDirError("test home mismatch")
        environment.update({"LAYA_HARNESS_TEST": "1", "LAYA_HARNESS_HOME": str(home),
                            "CODEX_HOME": str(home / "codex")})
    job = {"Label": label, "ProgramArguments": spawn.service_argv(interpreter),
           "WorkingDirectory": str(home), "EnvironmentVariables": environment,
           "KeepAlive": False, "RunAtLoad": False, "ThrottleInterval": 0,
           "StandardInPath": "/dev/null", "StandardOutPath": "/dev/null",
           "StandardErrorPath": str(home / "service.log")}
    return home / "launchd" / (label + ".plist"), job


def directory(home):
    path = home / "launchd"
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("owned launch directory required")
    path.chmod(0o700)
    return path


def private_file(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_uid != os.getuid():
        os.close(fd)
        raise ValueError('owned regular file required')
    os.fchmod(fd, 0o600)
    return fd


@contextlib.contextmanager
def locked(home):
    fd = private_file(home / 'launchd' / 'launch.lock')
    end = time.monotonic() + BUDGET
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= end:
                    raise TimeoutError('lock budget')
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)


class LaunchFailure(Exception):
    def __init__(self, stage, returncode=None, exception_class=None):
        self.stage = stage
        self.returncode = returncode
        self.exception_class = exception_class


def command(run, *args):
    try:
        return run(['/bin/launchctl', *args], stdin=subprocess.DEVNULL,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=BUDGET)
    except Exception as exc:
        raise LaunchFailure(args[0], exception_class=type(exc).__name__) from None


def owned(result, path, job):
    if result.returncode != 0:
        return False
    lines = [line.strip() for line in result.stdout.splitlines()]
    for name, expected in (('path', str(path)),
                           ('program', job['ProgramArguments'][0]),
                           ('working directory', job['WorkingDirectory'])):
        found = [line[len(name) + 3:] for line in lines if line.startswith(name + ' = ')]
        if found != [expected]:
            return False
    starts = [index for index, line in enumerate(lines) if line == 'arguments = {']
    if len(starts) != 1:
        return False
    start = starts[0] + 1
    try:
        end = lines.index('}', start)
    except ValueError:
        return False
    return lines[start:end] == job['ProgramArguments']


def diagnostic(home, exc):
    try:
        fd = private_file(home / 'launcher.log')
        try:
            os.lseek(fd, 0, os.SEEK_END)
            row = {'stage': exc.stage} if isinstance(exc, LaunchFailure) else {'stage': 'validation'}
            if isinstance(exc, LaunchFailure) and exc.returncode is not None:
                row['returncode'] = exc.returncode
            else:
                row['exception_class'] = exc.exception_class if isinstance(exc, LaunchFailure) else type(exc).__name__
            os.write(fd, (json.dumps(row, sort_keys=True) + '\n').encode())
        finally:
            os.close(fd)
    except Exception:
        pass


def launch(home, interpreter, run=None):
    run = subprocess.run if run is None else run
    safe_home = None
    try:
        path, job = definition(home, interpreter)
        safe_home = Path(home)
        home = Path(home)
        home.chmod(0o700)
        directory(home)
        with locked(home):
            # Validate every file before issuing an OS command.
            fd = private_file(home / 'service.log')
            os.close(fd)
            encoded = plistlib.dumps(job, sort_keys=True)
            if path.exists() or path.is_symlink():
                fd = private_file(path)
                try:
                    if os.read(fd, len(encoded)+1) != encoded:
                        raise ValueError('immutable definition mismatch')
                finally:
                    os.close(fd)
            else:
                fd, temp = tempfile.mkstemp(dir=path.parent, suffix='.plist.tmp')
                try:
                    with os.fdopen(fd, 'wb') as stream:
                        stream.write(encoded)
                    os.replace(temp, path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
            target = f'gui/{os.getuid()}/{job["Label"]}'
            result = command(run, 'print', target)
            if result.returncode != 0:
                # Missing-job code must be established by native preflight;
                # arbitrary launchctl failure must never trigger registration.
                if result.returncode != 113:
                    raise LaunchFailure('print', result.returncode)
                registered = command(run, 'bootstrap', f'gui/{os.getuid()}', str(path))
                if registered.returncode != 0:
                    raise LaunchFailure('bootstrap', registered.returncode)
                result = command(run, 'print', target)
            if result.returncode != 0:
                raise LaunchFailure('print', result.returncode)
            if not owned(result, path, job):
                raise LaunchFailure('ownership', result.returncode)
            started = command(run, 'kickstart', target)
            if started.returncode != 0:
                raise LaunchFailure('kickstart', started.returncode)
            return True
    except Exception as exc:
        if safe_home is not None:
            diagnostic(safe_home, exc)
        return False


def cleanup(home, interpreter, run=None):
    run = subprocess.run if run is None else run
    safe_home = None
    try:
        path, job = definition(home, interpreter)
        safe_home = Path(home)
        directory(Path(home))
        with locked(Path(home)):
            fd = private_file(path)
            try:
                encoded = plistlib.dumps(job, sort_keys=True)
                if os.read(fd, len(encoded)+1) != encoded:
                    return False
            finally:
                os.close(fd)
            target = f'gui/{os.getuid()}/{job["Label"]}'
            result = command(run, 'print', target)
            if result.returncode == 113:
                return True
            if result.returncode != 0:
                raise LaunchFailure('print', result.returncode)
            if not owned(result, path, job):
                raise LaunchFailure('ownership', result.returncode)
            removed = command(run, 'bootout', target)
            if removed.returncode != 0:
                raise LaunchFailure('bootout', removed.returncode)
            return True
    except Exception as exc:
        if safe_home is not None:
            diagnostic(safe_home, exc)
        return False


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args:
        return 0
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *unused: os._exit(1))
    signal.setitimer(signal.ITIMER_REAL, WALL_BUDGET)
    home = None
    try:
        home = paths.ensure_home().resolve()
        cfg = config.load()
        config.port(cfg)  # enforce isolated test-port guard before any OS command
        return 0 if launch(home, config.interpreter(cfg)) else 1
    except Exception as exc:
        if home is not None:
            diagnostic(home, exc)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0]:
            remaining = max(0.000001, previous_timer[0] - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, previous_timer[1])


if __name__ == "__main__":
    sys.exit(main())
