"""Rendering of adapted code: the contract, runtimes, backends, host gates, PNG hardening and the render store.

No ADK import. The backend is chosen by `AGENT_RENDERER` in `make_backend`.
"""

from ..settings import FAKE_RENDERER_ENVIRONMENTS, AgentSettings
from .backends.fake import FakeBackend
from .backends.local import LocalDockerBackend
from .backends.sandbox import SandboxBackend
from .contract import RenderBackend, RendererUnavailable
from .runtimes.python import PythonRuntime


def make_backend(settings: AgentSettings) -> RenderBackend:
    """The render backend `AGENT_RENDERER` names; `remote` arrives with the phase-2 renderer split.

    The settings already refuse `fake` and `local` outside their environments; the
    checks here are the second line for a settings object built without validation.
    """
    runtime = PythonRuntime(cpu_seconds=settings.render_timeout_s)
    if settings.renderer == "fake":
        if settings.environment not in FAKE_RENDERER_ENVIRONMENTS:
            raise RendererUnavailable(
                f"AGENT_RENDERER=fake runs no code and is refused when ENVIRONMENT={settings.environment!r}"
            )
        return FakeBackend()
    if settings.renderer == "local":
        return LocalDockerBackend(
            image=settings.render_image,
            runtime=runtime,
            environment=settings.environment,
            concurrency=settings.render_concurrency,
        )
    if settings.renderer == "sandbox":
        return SandboxBackend(runtime=runtime, concurrency=settings.render_concurrency)
    raise RendererUnavailable("AGENT_RENDERER=remote is the phase-2 renderer split and is not built yet")
