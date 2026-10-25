"""Rendering of adapted code: the contract, runtimes, backends, host gates, PNG hardening and the render store.

No ADK import. The backend is chosen by `AGENT_RENDERER` in `make_backend`; a job's
runtime by its library in `runtimes.runtime_for`.
"""

from typing import TYPE_CHECKING

from .backends.fake import FakeBackend
from .backends.local import LocalDockerBackend
from .backends.remote import IdTokenSource, RemoteBackend
from .backends.sandbox import SandboxBackend
from .contract import RenderBackend, RendererUnavailable
from .runtimes import runtime_for
from .runtimes.python import PythonRuntime


if TYPE_CHECKING:
    from ..settings import AgentSettings


def make_backend(settings: "AgentSettings") -> RenderBackend:
    """The render backend `AGENT_RENDERER` names.

    Phase 1 renders through `remote`, the anyplot-renderer service. The `sandbox`
    backend (sandboxes inside the agents service) stays as a stub for that in-process
    variant and is not used in phase 1. The settings already refuse `fake` and
    `local` outside their environments; the checks here are the second line for a
    settings object built without validation. The backend holds no semaphore:
    `Services.backend` wraps it in `SerialRenderer` (`serial.py`), the one place
    `AGENT_RENDER_CONCURRENCY` is enforced.

    The `local` and `sandbox` backends resolve a render job's runtime by its library
    (`runtime_for`, with the render timeout as the CPU limit); data runs and
    conversions always run on the Python runtime.
    """
    # Imported here: `settings` imports this package's registry for its library check.
    from ..settings import FAKE_RENDERER_ENVIRONMENTS

    def resolve(library: str) -> PythonRuntime:
        runtime = runtime_for(library, cpu_seconds=settings.render_timeout_s)
        assert isinstance(runtime, PythonRuntime)  # the registry's only runtime class in phase 1
        return runtime

    python_runtime = PythonRuntime(cpu_seconds=settings.render_timeout_s)
    if settings.renderer == "fake":
        if settings.environment not in FAKE_RENDERER_ENVIRONMENTS:
            raise RendererUnavailable(
                f"AGENT_RENDERER=fake runs no code and is refused when ENVIRONMENT={settings.environment!r}"
            )
        return FakeBackend()
    if settings.renderer == "local":
        return LocalDockerBackend(
            image=settings.render_image, runtime=python_runtime, environment=settings.environment, runtime_for=resolve
        )
    if settings.renderer == "sandbox":
        return SandboxBackend(runtime=python_runtime)
    if not settings.render_url:
        raise RendererUnavailable("AGENT_RENDERER=remote needs AGENT_RENDER_URL, the anyplot-renderer service URL")
    static_token = settings.render_token.get_secret_value() if settings.render_token is not None else None
    tokens = IdTokenSource(settings.render_url, development=settings.is_development, static_token=static_token)
    return RemoteBackend(url=settings.render_url, tokens=tokens)
