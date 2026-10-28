"""The harness's kernel filter against program starts (`harness.install_exec_deny`), installed when a guard is armed.

The filter cannot be removed, so every case that installs it runs the harness, or a script that loads it, in a
subprocess of its own. The cases that need the kernel run on Linux on the two machines the renderer image is built
for; the BPF program itself is checked everywhere by a small interpreter, and the install's decisions in process,
with libc, `execv` and the audit hook stood in.
"""

import errno
import io
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from agents.anyplot.render import harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE


DENY = harness.SECCOMP_RET_ERRNO | errno.EPERM
AUDIT_ARCH_I386 = 0x40000003
AUDIT_ARCH_ARM = 0x40000028
KERNEL = pytest.mark.skipif(
    not sys.platform.startswith("linux") or platform.machine() not in harness.EXEC_DENY_MACHINES,
    reason="the filter is installed on Linux on x86_64 and aarch64 only",
)


def run_filter(program: list[tuple[int, int, int, int]], arch: int, number: int) -> int:
    """What the kernel's classic BPF interpreter answers for one syscall: the program's return value."""
    data = {harness.SECCOMP_DATA_NR: number, harness.SECCOMP_DATA_ARCH: arch}
    accumulator, pc = 0, 0
    for _ in program:  # classic BPF jumps only forward, so a program ends within its length
        code, jt, jf, k = program[pc]
        if code == harness.BPF_LD_W_ABS:
            accumulator, pc = data[k], pc + 1
        elif code == harness.BPF_JEQ_K:
            pc += 1 + (jt if accumulator == k else jf)
        elif code == harness.BPF_JGE_K:
            pc += 1 + (jt if accumulator >= k else jf)
        elif code == harness.BPF_RET_K:
            return k
        else:
            raise AssertionError(f"unexpected instruction {code:#x}")
    raise AssertionError("the program ran past its end")


@pytest.mark.parametrize("machine", sorted(harness.EXEC_DENY_MACHINES))
class TestProgram:
    def program(self, machine: str) -> tuple[tuple[int, int, tuple[int, int], bool], list[tuple[int, int, int, int]]]:
        rule = harness.EXEC_DENY_MACHINES[machine]
        arch, _, denied, x32 = rule
        return rule, harness.exec_deny_program(arch, denied, x32)

    def test_execve_and_execveat_fail_with_eperm(self, machine: str) -> None:
        (arch, _, denied, _), program = self.program(machine)
        assert [run_filter(program, arch, number) for number in denied] == [DENY, DENY]

    def test_every_other_syscall_of_the_machine_is_allowed(self, machine: str) -> None:
        (arch, _, denied, _), program = self.program(machine)
        refused = [number for number in range(1024) if run_filter(program, arch, number) != harness.SECCOMP_RET_ALLOW]
        assert refused == sorted(denied)

    def test_another_architecture_s_syscalls_all_fail(self, machine: str) -> None:
        """A 32-bit `int 0x80` on x86_64 (or an AArch32 one) numbers `execve` 11, past the machine's own checks."""
        _, program = self.program(machine)
        for arch in (AUDIT_ARCH_I386, AUDIT_ARCH_ARM):
            assert {run_filter(program, arch, number) for number in (0, 3, 11, 59, 221, 322)} == {DENY}

    def test_jumps_stay_inside_and_the_program_ends_in_its_two_returns(self, machine: str) -> None:
        _, program = self.program(machine)
        for pc, (code, jt, jf, _) in enumerate(program):
            if code in (harness.BPF_JEQ_K, harness.BPF_JGE_K):
                assert pc + 1 + max(jt, jf) < len(program), pc
        assert program[-2:] == [(harness.BPF_RET_K, 0, 0, harness.SECCOMP_RET_ALLOW), (harness.BPF_RET_K, 0, 0, DENY)]


def test_every_x32_syscall_fails_on_x86_64() -> None:
    """x32 calls carry `X32_SYSCALL_BIT` and numbers of their own (`execve` is 520 there), under x86_64's arch."""
    arch, _, denied, x32 = harness.EXEC_DENY_MACHINES["x86_64"]
    program = harness.exec_deny_program(arch, denied, x32)
    assert x32 and not harness.EXEC_DENY_MACHINES["aarch64"][3]
    for number in (0, 59, 520, 545):
        assert run_filter(program, arch, harness.X32_SYSCALL_BIT | number) == DENY


class FakeLibc:
    """libc's `prctl` and `syscall` as `install_exec_deny` calls them: each answers what the case sets, and every call
    is recorded. Nothing reaches the kernel."""

    class Call:
        def __init__(self, calls: list[tuple[str, tuple[object, ...]]], name: str, answer: int) -> None:
            self.calls, self.name, self.answer = calls, name, answer

        def __call__(self, *args: object) -> int:
            self.calls.append((self.name, args))
            return self.answer

    def __init__(self, *, prctl: int = 0, seccomp: int = 0) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.prctl = self.Call(self.calls, "prctl", prctl)
        self.syscall = self.Call(self.calls, "syscall", seccomp)


class TestInstallDecisions:
    """Every way `install_exec_deny` answers, in process: libc, the probe's `execv` and the machine are stood in."""

    def install(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        machine: str = "x86_64",
        probes: tuple[int, ...] = (errno.ENOENT, errno.EPERM),
        libc: FakeLibc | None = None,
        cdll_error: Exception | None = None,
    ) -> tuple[str, FakeLibc, list[str]]:
        answers, tried, fake = iter(probes), [], libc or FakeLibc()

        def execv(path: str, args: list[str]) -> None:
            tried.append(path)
            raise OSError(next(answers), "probe")

        def cdll(*args: object, **kwargs: object) -> FakeLibc:
            if cdll_error is not None:
                raise cdll_error
            return fake

        monkeypatch.setattr(harness.os, "execv", execv)
        monkeypatch.setattr("platform.machine", lambda: machine)
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("ctypes.CDLL", cdll)
        return harness.install_exec_deny(), fake, tried

    def test_on_takes_the_probe_from_enoent_to_eperm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        state, libc, tried = self.install(monkeypatch)
        assert state == "on" and tried == [harness.EXEC_PROBE_PATH] * 2
        (prctl, prctl_args), (syscall, syscall_args) = libc.calls
        assert (prctl, prctl_args) == ("prctl", (harness.PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
        assert syscall == "syscall" and syscall_args[:3] == (317, 1, 1)  # seccomp(SET_MODE_FILTER, TSYNC, &prog)

    def test_aarch64_calls_its_own_seccomp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        state, libc, _ = self.install(monkeypatch, machine="aarch64")
        assert state == "on" and libc.calls[1][1][0] == 277

    def test_another_machine_is_unsupported_and_untouched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        state, libc, tried = self.install(monkeypatch, machine="riscv64")
        assert (state, libc.calls, tried) == ("unsupported", [], [])

    def test_a_sandbox_that_refuses_execve_already_proves_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The probe answers EPERM before the filter: a policy of the sandbox, not this filter (Copilot, #12410)."""
        state, libc, tried = self.install(monkeypatch, probes=(errno.EPERM,))
        assert (state, libc.calls, len(tried)) == ("unavailable", [], 1)

    @pytest.mark.parametrize(
        ("options", "calls"),
        [
            pytest.param({"cdll_error": OSError("no libc")}, 0, id="no libc"),
            pytest.param({"libc": FakeLibc(prctl=-1)}, 1, id="prctl refused"),
            pytest.param({"libc": FakeLibc(seccomp=-1)}, 2, id="seccomp refused"),
            pytest.param({"libc": FakeLibc(seccomp=4242)}, 2, id="a thread refused TSYNC"),
            pytest.param({"probes": (errno.ENOENT, errno.ENOENT)}, 2, id="accepted but not enforced"),
            pytest.param({"probes": (errno.ENOENT, errno.EACCES)}, 2, id="EACCES is no proof"),
        ],
    )
    def test_anything_short_of_the_change_is_unavailable(
        self, monkeypatch: pytest.MonkeyPatch, options: dict[str, Any], calls: int
    ) -> None:
        state, libc, _ = self.install(monkeypatch, **options)
        assert state == "unavailable" and len(libc.calls) == calls


class TestArming:
    """`DataGuard.arm` installs the filter before the hook and, where it is required, refuses to arm without it. The
    hook and the replaced calls are stood in, so this process keeps both."""

    @pytest.fixture
    def hooks(self, monkeypatch: pytest.MonkeyPatch) -> list[object]:
        added: list[object] = []
        monkeypatch.setattr(harness, "disable_unaudited_calls", lambda: None)
        monkeypatch.setattr(sys, "addaudithook", added.append)
        return added

    @pytest.mark.parametrize(
        ("required", "state", "armed"),
        [
            (False, "on", True),
            (False, "unavailable", True),
            (True, "on", True),
            (True, "unavailable", False),
            (True, "unsupported", False),
        ],
    )
    def test_the_filter_comes_first_and_a_required_one_is_not_skipped(
        self, monkeypatch: pytest.MonkeyPatch, hooks: list[object], required: bool, state: str, armed: bool
    ) -> None:
        monkeypatch.setattr(harness, "install_exec_deny", lambda: state)
        guard = harness.DataGuard()
        guard.exec_deny_required = required
        if armed:
            guard.arm()
        else:
            with pytest.raises(harness.ExecDenyUnavailable, match=state):
                guard.arm()
        assert (guard.exec_deny, guard.armed, hooks) == (state, armed, [guard] if armed else [])

    def test_every_guard_reads_the_requirement_from_its_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")
        assert all(
            guard.exec_deny_required for guard in (harness.PlotGuard(()), harness.DataGuard(), harness.ConvertGuard())
        )
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "no")
        assert harness.PlotGuard(()).exec_deny_required is False
        monkeypatch.delenv(harness.EXEC_DENY_ENV)
        assert harness.DataGuard().exec_deny_required is False

    def test_a_data_run_that_cannot_arm_ends_as_exec_deny_in_its_status(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """In process: a guard whose arm refuses, as a required filter that is not in place makes it."""

        class Refusing(harness.DataGuard):
            def arm(self, entry: object = None) -> None:
                raise harness.ExecDenyUnavailable("unavailable")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        (tmp_path / "snippet.py").write_text("import pandas as pd\ndf = pd.DataFrame({'a': [1]})\n", encoding="utf-8")

        assert harness.main_data("snippet.py", Refusing()) == harness.DATA_EXIT["exec_deny"]
        assert json.loads((tmp_path / harness.DATA_STATUS_FILE).read_text(encoding="utf-8"))["exit"] == 9
        assert (tmp_path / harness.DATA_OUT_FILE).read_text(encoding="utf-8") == ""

    def test_a_conversion_that_cannot_arm_ends_as_exec_deny_in_its_status(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import numpy as np

        class Refusing(harness.ConvertGuard):
            def arm(self, entry: object = None) -> None:
                raise harness.ExecDenyUnavailable("unsupported")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        buffer = io.BytesIO()
        np.save(buffer, np.ones((2, 2)))
        (tmp_path / "input.bin").write_bytes(buffer.getvalue())

        assert harness.main_convert("input.bin", Refusing()) == harness.CONVERT_EXIT["exec_deny"]
        assert json.loads((tmp_path / harness.DATA_STATUS_FILE).read_text(encoding="utf-8"))["exit"] == 9
        assert (tmp_path / harness.DATA_OUT_FILE).read_text(encoding="utf-8") == ""


KERNEL_CHECK = """
import ctypes, importlib.util, os, subprocess, sys, threading

spec = importlib.util.spec_from_file_location("harness", sys.argv[1])
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def probe():
    try:
        os.execv(harness.EXEC_PROBE_PATH, [harness.EXEC_PROBE_PATH])
    except OSError as exc:
        return type(exc).__name__


ready, go, seen = threading.Event(), threading.Event(), {}


def worker():
    ready.set()
    go.wait()
    seen["thread"] = probe()


thread = threading.Thread(target=worker)
thread.start()
ready.wait()
print(probe())
print(harness.install_exec_deny())
go.set()
thread.join()
print(seen["thread"])
print(ctypes.CDLL(None).system(b"exit 0") != 0)
try:
    subprocess.run(["true"], check=False)
    print("ran")
except PermissionError:
    print("PermissionError")
descriptor = os.open("/bin/true", os.O_RDONLY)
try:
    os.execve(descriptor, ["true"], {})  # fexecve: execveat on the descriptor
except PermissionError:
    print("PermissionError")
pid = os.fork()
if pid == 0:
    try:
        os.execv("/bin/true", ["true"])
    except PermissionError:
        os._exit(7)
    os._exit(9)
print(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]))
"""
KERNEL_CHECK_OUTPUT = ["FileNotFoundError", "on", "PermissionError", "True", "PermissionError", "PermissionError", "7"]


@KERNEL
def test_the_kernel_refuses_every_program_start_once_installed() -> None:
    """Before the filter the probe reaches the path lookup (ENOENT); after it, a thread that was already running, libc's
    `system` (what a native library calls), `subprocess`, `fexecve` and a forked child all get EPERM, and `fork` still
    works. `ci-image.yml` runs the same check in the renderer image."""
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", KERNEL_CHECK, str(HARNESS_SOURCE)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == KERNEL_CHECK_OUTPUT


@KERNEL
def test_a_filter_the_kernel_accepted_but_does_not_enforce_is_not_on() -> None:
    """The probe is the proof: a `seccomp` call that answers 0 and installs nothing leaves the probe's path lookup
    reachable (ENOENT), so the state is `unavailable`, never `on`."""
    code = (
        "import ctypes, importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('harness', sys.argv[1])\n"
        "harness = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(harness)\n"
        "class Call:\n    def __call__(self, *args):\n        return 0\n"
        "class Libc:\n    prctl = Call()\n    syscall = Call()\n"
        "ctypes.CDLL = lambda *args, **kwargs: Libc()\n"
        "print(harness.install_exec_deny())\n"
    )
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", code, str(HARNESS_SOURCE)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == ["unavailable"]


@KERNEL
def test_a_filter_already_in_place_is_not_taken_for_this_one() -> None:
    """A second install meets EPERM before its own filter, as under a sandbox policy that refuses `execve`."""
    code = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('harness', sys.argv[1])\n"
        "harness = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(harness)\n"
        "print(harness.install_exec_deny())\n"
        "print(harness.install_exec_deny())\n"
    )
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", code, str(HARNESS_SOURCE)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == ["on", "unavailable"]


def run_harness(tmp_path: Path, argv: list[str], env: dict[str, str], *, state: str | None = None):
    """The harness's `main` on `argv` in `tmp_path`; with `state`, as if `install_exec_deny` answered it."""
    driver = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('harness', sys.argv[1])\n"
        "harness = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(harness)\n"
        + (f"harness.install_exec_deny = lambda: {state!r}\n" if state else "")
        + "sys.exit(harness.main(['harness.py', *sys.argv[2:]]))\n"
    )
    return subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", driver, str(HARNESS_SOURCE), *argv],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "ANYPLOT_THEME": "light",
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
            "ANYPLOT_RLIMIT_CPU_S": "120",
            **env,
        },
    )


def end_line(stdout: str) -> dict[str, object]:
    lines = [line for line in stdout.splitlines() if line.startswith(f"{harness.MARKER} ")]
    report = json.loads(lines[-1].split(" ", 1)[1])
    assert report["event"] == "end"
    return report


PLOT = (
    "import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
    "open('plot-light.png', 'wb').close()\n"  # a mark that the plot ran, at the one path the guard lets it write
    "fig, ax = plt.subplots(figsize=(4, 3))\nax.plot([0, 1], [0, 1])\nplt.savefig('plot-light.png')\n"
)


@KERNEL
def test_a_render_runs_under_the_filter_and_reports_it(tmp_path: Path) -> None:
    (tmp_path / "plot.py").write_text(PLOT, encoding="utf-8")
    done = run_harness(tmp_path, ["plot.py"], {harness.EXEC_DENY_ENV: "required"})
    assert done.returncode == 0, done.stderr
    assert (tmp_path / "plot-light.png").stat().st_size > 0
    assert end_line(done.stdout)["exec_deny"] == "on"


@pytest.mark.parametrize("state", ["unavailable", "unsupported"])
def test_a_required_filter_that_is_not_in_place_stops_the_render_before_the_plot(tmp_path: Path, state: str) -> None:
    (tmp_path / "plot.py").write_text(PLOT, encoding="utf-8")
    done = run_harness(tmp_path, ["plot.py"], {harness.EXEC_DENY_ENV: "required"}, state=state)
    assert done.returncode == harness.EXEC_DENY_EXIT
    assert f"could not refuse process starts ({state})" in done.stderr
    assert not (tmp_path / "plot-light.png").exists()
    assert end_line(done.stdout)["exec_deny"] == state


def test_without_the_requirement_a_render_goes_on_and_reports_the_missing_filter(tmp_path: Path) -> None:
    """Every row but lets-plot's: a platform that refuses the filter must not stop matplotlib's renders."""
    (tmp_path / "plot.py").write_text(PLOT, encoding="utf-8")
    done = run_harness(tmp_path, ["plot.py"], {}, state="unavailable")
    assert done.returncode == 0, done.stderr
    assert (tmp_path / "plot-light.png").stat().st_size > 0
    assert end_line(done.stdout)["exec_deny"] == "unavailable"


def test_a_render_that_fails_before_arming_reports_off(tmp_path: Path) -> None:
    (tmp_path / "plot.py").write_text("x = (\n", encoding="utf-8")
    done = run_harness(tmp_path, ["plot.py"], {})
    assert done.returncode == 1 and "SyntaxError" in done.stderr
    assert end_line(done.stdout)["exec_deny"] == "off"


@KERNEL
def test_a_data_run_is_armed_with_the_filter_too(tmp_path: Path) -> None:
    (tmp_path / "snippet.py").write_text("import pandas as pd\ndf = pd.DataFrame({'a': [1, 2]})\n", encoding="utf-8")
    done = run_harness(tmp_path, [harness.DATA_FLAG, "snippet.py"], {})
    assert done.returncode == harness.DATA_EXIT["ok"], done.stderr
    assert end_line(done.stdout)["exec_deny"] == "on"
    assert (tmp_path / harness.DATA_OUT_FILE).read_text(encoding="utf-8").splitlines() == ["a", "1", "2"]


@KERNEL
def test_a_conversion_is_armed_with_the_filter_too(tmp_path: Path) -> None:
    import numpy as np

    buffer = io.BytesIO()
    np.save(buffer, np.ones((2, 2)))
    (tmp_path / "input.bin").write_bytes(buffer.getvalue())
    done = run_harness(tmp_path, [harness.CONVERT_FLAG, "input.bin"], {"ARROW_DEFAULT_MEMORY_POOL": "system"})
    assert done.returncode == harness.CONVERT_EXIT["ok"], done.stderr
    assert end_line(done.stdout)["exec_deny"] == "on"


def test_a_required_filter_that_is_not_in_place_stops_a_data_run_before_the_snippet(tmp_path: Path) -> None:
    """The code reaches the host through `status.json`, which Cloud Run's launcher (-13 for every exit) cannot lose."""
    (tmp_path / "snippet.py").write_text(
        "import pandas as pd\ndf = pd.DataFrame({'a': [1]})\nprint('snippet ran')\n", encoding="utf-8"
    )
    done = run_harness(
        tmp_path, [harness.DATA_FLAG, "snippet.py"], {harness.EXEC_DENY_ENV: "required"}, state="unavailable"
    )
    assert done.returncode == harness.DATA_EXIT["exec_deny"] == 9
    assert "could not refuse process starts (unavailable)" in done.stderr and "snippet ran" not in done.stdout
    status = json.loads((tmp_path / harness.DATA_STATUS_FILE).read_text(encoding="utf-8"))
    assert status["exit"] == harness.DATA_EXIT["exec_deny"]
    assert (tmp_path / harness.DATA_OUT_FILE).read_text(encoding="utf-8") == ""


def test_a_required_filter_that_is_not_in_place_stops_a_conversion_before_the_reader(tmp_path: Path) -> None:
    import numpy as np

    from agents.renderer import wire

    buffer = io.BytesIO()
    np.save(buffer, np.ones((2, 2)))
    (tmp_path / "input.bin").write_bytes(buffer.getvalue())
    done = run_harness(
        tmp_path,
        [harness.CONVERT_FLAG, "input.bin"],
        {"ARROW_DEFAULT_MEMORY_POOL": "system", harness.EXEC_DENY_ENV: "required"},
        state="unsupported",
    )
    assert done.returncode == harness.CONVERT_EXIT["exec_deny"] == wire.CONVERT_EXEC_DENY_EXIT
    assert json.loads((tmp_path / harness.DATA_STATUS_FILE).read_text(encoding="utf-8"))["exit"] == 9
    assert (tmp_path / harness.DATA_OUT_FILE).read_text(encoding="utf-8") == ""


def test_without_the_requirement_a_data_run_goes_on_and_reports_the_missing_filter(tmp_path: Path) -> None:
    """A test or a developer running the harness directly sets no requirement."""
    (tmp_path / "snippet.py").write_text("import pandas as pd\ndf = pd.DataFrame({'a': [1]})\n", encoding="utf-8")
    done = run_harness(tmp_path, [harness.DATA_FLAG, "snippet.py"], {}, state="unavailable")
    assert done.returncode == harness.DATA_EXIT["ok"], done.stderr
    assert end_line(done.stdout)["exec_deny"] == "unavailable"
