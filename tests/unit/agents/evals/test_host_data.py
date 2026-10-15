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
    return asyncio.run(HostDataBackend().run_data(DataJob(job_id="dtest0001", source=source, timeout_s=timeout_s)))


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


def test_production_is_refused() -> None:
    with pytest.raises(RendererUnavailable):
        HostDataBackend(environment="production")


def test_a_scripted_data_run_still_wins() -> None:
    """Like the fake, a test can script the data run instead of executing it."""
    scripted = DataOutput(exit_code=0, csv_text="a,b\n1,2\n")
    backend = HostDataBackend(data_script=lambda job: scripted)

    assert asyncio.run(backend.run_data(DataJob(job_id="dtest0002", source="x = 1\n"))) is scripted
    assert len(backend.data_jobs) == 1
