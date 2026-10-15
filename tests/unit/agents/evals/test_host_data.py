"""The prep eval's data runs (agents/evals/host_data.py): the real harness, answered as `POST /run-data` answers.

The contract under test is the one `run_data_code` reads (`DataOutput`): the table the
snippet computed after exit code 0, and the harness's own exit code with its measured
value and cap for a refusal. These run the harness in a subprocess, as the harness's
data-mode tests do.
"""

import asyncio

import pytest

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.render.backends.fake import FIXTURE_CSV
from agents.anyplot.render.contract import DataJob, DataOutput, RendererUnavailable
from agents.anyplot.render.harness import DATA_EXIT
from agents.anyplot.render.runtimes.python import PythonRuntime
from agents.anyplot.schemas import MAX_ROWS
from agents.anyplot.tools.session import _run_failure
from agents.evals.host_data import HOST_ENV_DROPPED, HostDataBackend, host_data_env


def run(source: str, timeout_s: float = 20.0) -> DataOutput:
    """The harness run (`execute`), past the validator, so a test can reach the harness's own refusals."""
    return asyncio.run(HostDataBackend().execute(DataJob(job_id="dtest0001", source=source, timeout_s=timeout_s)))


def test_a_run_answers_with_the_table_the_snippet_computed() -> None:
    """Not the fake's fixture table: 500 steps come back as 500 rows of the snippet's own columns."""
    output = run(
        "import numpy as np\nimport pandas as pd\nrng = np.random.default_rng(42)\n"
        "df = pd.DataFrame({'step': np.arange(1, 501), 'walk': rng.normal(0, 1, 500).cumsum()})\n"
    )

    assert output.exit_code == 0 and _run_failure(output) is None
    assert output.csv_text is not None and output.csv_text != FIXTURE_CSV
    profile = parse_dataset(output.csv_text, find_table=False).profile
    assert profile.rows == 500 and [column.name for column in profile.columns] == ["step", "walk"]


def test_a_refusal_carries_the_harness_exit_code_and_caps() -> None:
    """Too many rows: the exit code, the measured value and the cap, which the tool turns into its thinning hint."""
    output = run(f"import pandas as pd\ndf = pd.DataFrame({{'x': range({MAX_ROWS + 1})}})\n")

    assert output.exit_code == DATA_EXIT["too_many_rows"] and output.csv_text is None
    assert (output.measured, output.limit) == (MAX_ROWS + 1, MAX_ROWS)
    assert _run_failure(output) is not None and _run_failure(output)[0] == "run_failed"  # type: ignore[index]


@pytest.mark.parametrize(
    ("source", "exit_name"),
    [
        ("import pandas as pd\nx = 1\n", "no_frame"),
        ("import pandas as pd\nraise ValueError('boom')\n", "error"),
        ("import pandas as pd\nopen('secret.txt')\ndf = pd.DataFrame({'x': [1]})\n", "blocked"),
    ],
)
def test_a_failed_run_has_the_harness_exit_code(source: str, exit_name: str) -> None:
    output = run(source)

    assert output.exit_code == DATA_EXIT[exit_name] and output.csv_text is None


def test_a_run_past_its_timeout_is_killed() -> None:
    output = run("while True:\n    pass\n", timeout_s=1.0)

    assert output.timed_out and output.exit_code is None
    assert _run_failure(output) == ("timeout", [_run_failure(output)[1][0]])  # type: ignore[index]


def test_a_run_that_floods_stderr_past_its_timeout_is_killed_and_reaped() -> None:
    """The kill drains stderr while it reaps, so a full pipe cannot keep the cleanup waiting."""
    output = run("import sys\nwhile True:\n    sys.stderr.write('x' * 65536)\n", timeout_s=1.0)

    assert output.timed_out and output.exit_code is None


def test_the_environment_is_the_renderers_data_environment() -> None:
    """The renderer's data-run limits, except the process count, which outside a container counts the user's."""
    from pathlib import Path

    env = host_data_env(Path("/tmp/run"), 60)
    renderer = PythonRuntime(cpu_seconds=60).data_env()

    assert HOST_ENV_DROPPED == ("ANYPLOT_RLIMIT_NPROC",)
    for key, value in renderer.items():
        if key not in HOST_ENV_DROPPED and key != "HOME":
            assert env[key] == value, key
    assert "ANYPLOT_RLIMIT_NPROC" not in env and env["HOME"] == "/tmp/run"


@pytest.mark.parametrize("environment", ["production", "staging", ""])
def test_only_development_and_test_may_build_it(environment: str) -> None:
    """An allow-list, the fake renderer's own: the backend executes code on this machine."""
    with pytest.raises(RendererUnavailable):
        HostDataBackend(environment=environment)
    assert HostDataBackend(environment="test").environment == "test"


def test_a_snippet_the_validator_refuses_never_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defence in depth: `run_data` validates the job itself, so a caller that skipped the tool still cannot run it."""

    async def no_process(*args: object, **kwargs: object) -> None:
        raise AssertionError("no process may start for a refused snippet")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", no_process)
    source = "import os\nimport pandas as pd\ndf = pd.DataFrame({'n': [len(os.environ)]})\n"

    output = asyncio.run(HostDataBackend().run_data(DataJob(job_id="dtest0003", source=source)))

    assert output.exit_code == DATA_EXIT["blocked"] and output.csv_text is None
    assert _run_failure(output) is not None and _run_failure(output)[0] == "run_failed"  # type: ignore[index]


def test_the_cpu_cap_is_clamped_to_the_runs_timeout_as_the_renderer_clamps_it() -> None:
    """The renderer gives a 20-second data run 20 CPU seconds; the local backend and the host runs do the same."""
    from pathlib import Path

    from agents.anyplot.render.backends.local import LocalDockerBackend
    from agents.renderer.wire import run_cpu_seconds

    assert run_cpu_seconds(60, 20.0) == 20 and run_cpu_seconds(60, 0.2) == 1 and run_cpu_seconds(10, 20.0) == 10
    assert host_data_env(Path("/tmp/run"), 60, 20.0)["ANYPLOT_RLIMIT_CPU_S"] == "20"
    local = LocalDockerBackend(
        image="anyplot-renderer:dev", runtime=PythonRuntime(), environment="development", docker="/bin/true"
    )
    argv = local.data_argv(DataJob(job_id="dtest0004", source="x", timeout_s=20.0), Path("/tmp/run"))
    assert "ANYPLOT_RLIMIT_CPU_S=20" in argv


def test_a_cancelled_run_kills_its_process_group_and_removes_its_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    started: list[asyncio.subprocess.Process] = []
    original = asyncio.create_subprocess_exec

    async def spy(*args: object, **kwargs: object) -> asyncio.subprocess.Process:
        process = await original(*args, **kwargs)  # type: ignore[arg-type]
        started.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spy)

    async def cancel_midway() -> None:
        job = DataJob(job_id="dtest0005", source="while True:\n    pass\n", timeout_s=20.0)
        task = asyncio.ensure_future(HostDataBackend().execute(job))
        while not started:
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_midway())

    (process,) = started
    assert process.returncode is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(process.pid, 0)


def test_an_oversized_table_is_output_rejected_with_its_size_and_cap(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """As the renderer's `_collect_data` answers it: the reason, the measured size and the cap."""
    from agents.anyplot.data.parse import MAX_COMPUTED_BYTES
    from agents.anyplot.render.backends.local import collect_data_run
    from agents.anyplot.render.harness import DATA_OUT_FILE

    (tmp_path / DATA_OUT_FILE).write_bytes(b"x\n" + b"1\n" * (MAX_COMPUTED_BYTES // 2 + 1))

    output = collect_data_run(tmp_path, 0, "", 0.1)

    assert output.reason == "output_rejected" and output.csv_text is None
    assert output.limit == MAX_COMPUTED_BYTES and output.measured == (tmp_path / DATA_OUT_FILE).stat().st_size


def test_a_scripted_data_run_still_wins() -> None:
    """Like the fake, a test can script the data run instead of executing it."""
    scripted = DataOutput(exit_code=0, csv_text="a,b\n1,2\n")
    backend = HostDataBackend(data_script=lambda job: scripted)

    assert asyncio.run(backend.run_data(DataJob(job_id="dtest0002", source="x = 1\n"))) is scripted
    assert len(backend.data_jobs) == 1
