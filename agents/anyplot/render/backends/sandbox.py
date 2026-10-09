"""The Cloud Run sandbox render backend (phase 1 production): a typed stub until spike S reports.

The design runs each theme as

    /usr/local/gcp/bin/sandbox do --sandbox-name r-<job_id>-<theme> --write
        --mount type=bind,source=/tmp/runs/<job>,destination=/work -w /work
        --env ANYPLOT_THEME=<theme> --env MPLBACKEND=Agg --env MPLCONFIGDIR=/opt/mplconfig --env HOME=/tmp
        -- /app/.venv/bin/python -I /opt/anyplot/harness.py plot.py

(docs/concepts/agent-network.md, "Render"). Spike S measures the real command shape,
the timing, the memory per sandbox and the probe suite in europe-west4; until then
this backend refuses to run, so `AGENT_RENDERER=sandbox` fails loudly instead of
guessing a command line. Use `local` (Docker) or `fake` in development.
"""

from ..contract import RenderJob, RenderResult, RuntimeAdapter


SANDBOX_BINARY = "/usr/local/gcp/bin/sandbox"
FORBIDDEN_FLAGS = ("--allow-egress",)


class SandboxBackend:
    """Cloud Run `sandbox do` per theme; not implemented before spike S."""

    name = "sandbox"

    def __init__(self, *, runtime: RuntimeAdapter, concurrency: int) -> None:
        self.runtime = runtime
        self.concurrency = concurrency

    async def render(self, job: RenderJob) -> RenderResult:
        raise NotImplementedError(
            "the sandbox renderer waits for spike S (Cloud Run sandbox command shape, see "
            "docs/concepts/agent-network.md, 'Phase 0'); use AGENT_RENDERER=local or fake"
        )
