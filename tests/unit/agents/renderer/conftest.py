"""Fixtures: a hermetic environment, a fake `sandbox` launcher, and an executor that runs the real harness here."""

import json
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from agents.anyplot.render.runtimes.python import HARNESS_SOURCE
from agents.renderer.executor import ExecutorConfig, SandboxExecutor
from agents.renderer.main import get_renderer
from agents.renderer.settings import get_settings

from .helpers import FAKE_LAUNCHER


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """No RENDERER_* values, no Cloud Run variables and no ENVIRONMENT from the shell or CI."""
    for name in list(os.environ):
        upper = name.upper()
        if upper.startswith(("RENDERER_", "FAKE_SANDBOX_")) or upper in ("ENVIRONMENT", "K_SERVICE", "K_REVISION"):
            monkeypatch.delenv(name)
    get_settings.cache_clear()
    get_renderer.cache_clear()
    yield
    get_settings.cache_clear()
    get_renderer.cache_clear()


@dataclass
class FakeLauncher:
    """The fake `sandbox` binary and its call log."""

    binary: Path
    log: Path
    failures: Path

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def launches(self) -> list[str]:
        """The sandbox names of every `do` call, in order."""
        return [call[2] for call in self.calls() if call[:1] == ["do"]]

    def deletes(self) -> list[str]:
        return [call[2] for call in self.calls() if call[:2] == ["delete", "--force"]]

    def fail_next(self, count: int) -> None:
        self.failures.write_text(str(count), encoding="utf-8")


@pytest.fixture
def launcher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeLauncher:
    binary = tmp_path / "bin" / "sandbox"
    binary.parent.mkdir()
    binary.write_text(f"#!{sys.executable}\n{FAKE_LAUNCHER}", encoding="utf-8")
    binary.chmod(0o755)
    log = tmp_path / "sandbox.log"
    failures = tmp_path / "failures"
    monkeypatch.setenv("FAKE_SANDBOX_LOG", str(log))
    monkeypatch.setenv("FAKE_SANDBOX_FAIL", str(failures))
    return FakeLauncher(binary, log, failures)


@pytest.fixture
def config(tmp_path: Path, launcher: FakeLauncher) -> ExecutorConfig:
    """The deployed configuration, except that RLIMIT_AS and RLIMIT_NPROC stay off.

    Outside a sandbox `RLIMIT_NPROC` counts every process of this user, so setting it
    here would break the machine running the tests, not the code under test.
    """
    return ExecutorConfig(
        sandbox_binary=str(launcher.binary),
        python=sys.executable,
        harness=str(HARNESS_SOURCE),
        runs_dir=tmp_path / "runs",
        mpl_seed=str(tmp_path / "no-seed"),
        mplconfig=str(tmp_path / "mpl"),
        run_budget_bytes=8 * 1024 * 1024,
        watch_interval_s=0.02,
        rlimit_cpu_s=60,
        rlimit_fsize_mb=50,
        rlimit_as_mb=0,
        rlimit_nproc=0,
        kill_grace_s=5.0,
        bind_tmp=False,
    )


@pytest.fixture
def executor(config: ExecutorConfig) -> SandboxExecutor:
    return SandboxExecutor(config)
