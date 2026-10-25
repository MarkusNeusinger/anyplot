"""Language runtimes of the renderer, and the registry that maps a catalogue library to its `RuntimeAdapter`.

A library's language is fixed by the catalogue (`agents/renderer/commands.py`,
`LIBRARY_LANGUAGES`, the renderer's copy of `core.constants.LIBRARY_LANGUAGES`); its
runtime is the `RuntimeAdapter` of that language, built for the library, which binds the
deterministic code modules (normaliser, regions, readiness, validator, edits, loader,
export) and the render command to one object the pipeline, the theme toggle, the local
Docker backend and the eval harness use alike. `RUNTIME_LIBRARIES` is the set the registry
serves; the settings refuse any other library in `AGENT_LIBRARIES`, and the readiness scan
blocks it as `unsupported-library`.

`PythonRuntime` serves matplotlib, seaborn, plotnine and altair: each has a save rule
(`code.regions.SAVE_RULES`) and a validator profile (`code.validate.LIBRARY_IMPORTS`),
and the renderer image installs it. A later language adds a runtime module here and its
libraries to `RUNTIME_LIBRARIES`; a later Python library (pygal, lets-plot) adds its
validator profile and save rule to the Python code modules and its id to
`PYTHON_LIBRARIES` (`agentic/specs/261024-agent-all-libraries.md`).
"""

from collections.abc import Callable

from agents.renderer.commands import LIBRARY_LANGUAGES, command_for

from ..contract import RuntimeAdapter
from .python import PythonRuntime


PYTHON_LIBRARIES: frozenset[str] = frozenset({"matplotlib", "seaborn", "plotnine", "altair"})
"""The Python libraries with a complete runtime profile (`code.normalise.SUPPORTED_LIBRARIES`, pinned equal)."""

RUNTIME_LIBRARIES: frozenset[str] = PYTHON_LIBRARIES
"""Every library the registry serves; a library of `core.constants.SUPPORTED_LIBRARIES` outside it has no runtime yet."""

RuntimeResolver = Callable[[str], RuntimeAdapter]
"""What a backend takes to find a job's runtime by its library."""


def language_of(library: str) -> str:
    """The catalogue language of `library`; `ValueError` for a library outside the catalogue."""
    try:
        return LIBRARY_LANGUAGES[library]
    except KeyError:
        raise ValueError(f"unknown library {library!r}") from None


def has_runtime(library: str) -> bool:
    return library in RUNTIME_LIBRARIES


def runtime_for(library: str, *, cpu_seconds: int = 60) -> RuntimeAdapter:
    """The runtime of `library`; `ValueError` for a library without one.

    `cpu_seconds` is the render's CPU limit (`AGENT_RENDER_TIMEOUT_S`), which the local
    Docker backend passes into the sandbox's environment.
    """
    if library not in RUNTIME_LIBRARIES:
        raise ValueError(f"no runtime for {library!r} yet (the registry serves {', '.join(sorted(RUNTIME_LIBRARIES))})")
    command = command_for(language_of(library), library)
    return PythonRuntime(library=library, cpu_seconds=cpu_seconds, render_p95_s=command.render_p95_s)


__all__ = [
    "PYTHON_LIBRARIES",
    "RUNTIME_LIBRARIES",
    "PythonRuntime",
    "RuntimeResolver",
    "has_runtime",
    "language_of",
    "runtime_for",
]
