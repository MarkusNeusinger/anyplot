"""The exec filter's preload library of the exec-mode rows (agents/renderer/execdeny/execdeny.c, step 2b).

Compiled with the host's gcc and loaded into `/bin/sh`, which starts a program the way R's `system()` and
`popen` do. The toolchain image's build runs the same library under R (agents/renderer/toolchain/smoke.R).
"""

from __future__ import annotations

import os
import resource
import signal
import subprocess
import sys
from pathlib import Path

import pytest


KILLED_BY_THE_FILTER = 128 + signal.SIGSYS


@pytest.fixture
def library(execdeny_library: Path) -> Path:
    """The library built once per session (`conftest.execdeny_library`; skipped where it cannot be built)."""
    return execdeny_library


def run(library: Path, script: str, mode: str | None, *, nproc: int | None = None) -> tuple[int, str, str]:
    """Run `/bin/sh -c script` with the library preloaded; the exit code, its output and what the pipe said."""
    read_end, write_end = os.pipe()
    env = {"PATH": "/usr/bin:/bin", "LD_PRELOAD": str(library), "ANYPLOT_EXEC_DENY_FD": str(write_end)}
    if mode is not None:
        env["ANYPLOT_DENY_EXEC"] = mode

    def limit() -> None:
        if nproc is not None:
            resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))

    try:
        result = subprocess.run(
            ["/bin/sh", "-c", script.replace("{fd}", str(write_end))],
            env=env,
            pass_fds=(write_end,),
            preexec_fn=limit,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        os.close(write_end)
    with os.fdopen(read_end, "rb") as reader:
        state = reader.read().decode()
    return result.returncode, result.stdout.strip(), state


def test_required_kills_every_program_start_and_reports_on(library: Path) -> None:
    code, output, state = run(library, "/bin/true; echo $?", "required")
    assert (code, output, state) == (0, str(KILLED_BY_THE_FILTER), "on")


def test_any_other_mode_installs_it_too(library: Path) -> None:
    assert run(library, "/bin/true; echo $?", "optional")[1:] == (str(KILLED_BY_THE_FILTER), "on")


def test_the_preflight_ends_the_program_before_its_main(library: Path) -> None:
    """`ANYPLOT_EXEC_DENY_PREFLIGHT`: the library installs and reports, then ends the program before its code runs,
    with 0 when the filter is on (the harness's check before any user code, `harness.main_exec`)."""
    read_end, write_end = os.pipe()
    env = {
        "PATH": "/usr/bin:/bin",
        "LD_PRELOAD": str(library),
        "ANYPLOT_DENY_EXEC": "required",
        "ANYPLOT_EXEC_DENY_FD": str(write_end),
        "ANYPLOT_EXEC_DENY_PREFLIGHT": "1",
    }
    try:
        result = subprocess.run(
            ["/bin/sh", "-c", "echo ran"],
            env=env,
            pass_fds=(write_end,),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        os.close(write_end)
    with os.fdopen(read_end, "rb") as reader:
        state = reader.read().decode()
    assert (result.returncode, result.stdout, state) == (0, "", "on")


def test_without_the_variable_nothing_changes(library: Path) -> None:
    assert run(library, "/bin/true; echo $?", None) == (0, "0", "")
    assert run(library, "/bin/true; echo $?", "") == (0, "0", "")


def test_the_pipe_is_closed_and_named_nowhere_before_user_code(library: Path) -> None:
    """User code can neither forge the state on the descriptor nor find its number."""
    # A subshell: a failed redirection ends a non-interactive POSIX shell.
    script = 'echo "${ANYPLOT_EXEC_DENY_FD-unset}"; (echo forged >&{fd}) 2>/dev/null && echo written || echo refused'
    code, output, state = run(library, script, "required")
    assert state == "on"
    assert output.splitlines() == ["unset", "refused"]
    assert code == 0


def test_the_program_is_not_dumpable_so_a_killed_child_dumps_no_core(library: Path) -> None:
    """Before Linux 5.16 a core dump kills every process sharing the dumping one's memory, so the SIGSYS of a vfork
    child (R's popen and system()) took R with it; the first Cloud Build of the toolchain died that way. Not
    dumpable, the child dumps no core and dies alone on every kernel (PR_GET_DUMPABLE is 3)."""
    read_end, write_end = os.pipe()
    probe = "import ctypes; print(ctypes.CDLL(None, use_errno=True).prctl(3, 0, 0, 0, 0))"
    env = {
        "PATH": "/usr/bin:/bin",
        "LD_PRELOAD": str(library),
        "ANYPLOT_DENY_EXEC": "required",
        "ANYPLOT_EXEC_DENY_FD": str(write_end),
    }
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", probe],
            env=env,
            pass_fds=(write_end,),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        os.close(write_end)
    with os.fdopen(read_end, "rb") as reader:
        state = reader.read().decode()
    assert (result.returncode, result.stdout.strip(), state) == (0, "0", "on"), result.stderr


@pytest.mark.skipif(os.geteuid() == 0, reason="RLIMIT_NPROC does not bind root")
def test_required_stops_the_program_when_the_filter_cannot_be_proven(library: Path) -> None:
    """With no process left to fork, the probe cannot prove the filter: required ends the program with exit code 3
    before its main, so the script never runs; without required it runs and the pipe says why."""
    code, output, state = run(library, "echo ran", "required", nproc=1)
    assert (code, output, state) == (3, "", "unavailable")
    assert run(library, "echo ran", "optional", nproc=1) == (0, "ran", "unavailable")
