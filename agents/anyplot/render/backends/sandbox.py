"""The in-process sandbox render backend: a typed stub that phase 1 does not use.

Phase 1 renders through the anyplot-renderer service (`AGENT_RENDERER=remote`,
`backends/remote.py`): the owner decided on 2026-10-10 that the sandbox launcher
runs in a service of its own, with a zero-role service account, so a local
`adk web` and the deployed agents service share one renderer. The command shape,
the kill path, the byte watchdog and the retry that spikes S and S2 settled live in
`agents/renderer/executor.py`.

This backend stays for the variant that launches sandboxes inside the agents
service itself. It refuses to run, so `AGENT_RENDERER=sandbox` fails loudly instead
of guessing; an implementation would reuse the renderer's executor rather than copy
it. It needs no semaphore of its own: `SerialRenderer` (`render/serial.py`), which
`Services.backend` puts in front of every backend, hands it one theme at a time.
"""

from ..contract import RenderJob, RenderResult, RuntimeAdapter


SANDBOX_BINARY = "/usr/local/gcp/bin/sandbox"
FORBIDDEN_FLAGS = ("--allow-egress", "--write")


class SandboxBackend:
    """Cloud Run `sandbox do` inside the agents service; not used in phase 1."""

    name = "sandbox"

    def __init__(self, *, runtime: RuntimeAdapter) -> None:
        self.runtime = runtime

    async def render(self, job: RenderJob) -> RenderResult:
        raise NotImplementedError(
            "the in-process sandbox backend is not used in phase 1: renders go through the anyplot-renderer "
            "service (AGENT_RENDERER=remote, AGENT_RENDER_URL); use local or fake in development"
        )
