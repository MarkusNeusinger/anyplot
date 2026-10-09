"""The root agent's session tools and the `plot_pipeline` NodeTool.

Every tool reads spec, library, dataset and bindings from server-set session state
(`session_state.py`) and the process-wide stores; no tool takes a spec, library or
dataset argument. Results are small dicts with a `status` key (`ok`, `not_ready` or
`error`); untrusted text in them (dataset samples and column names, catalogue code,
spec text) sits inside our own fences after the "data, never instructions" preamble.

* `get_dataset_profile`: the profile of the session's dataset, fenced as `<user_data>`;
  trimmed (samples, then top values, then ranges, with `truncated`) to fit its cap.
* `get_spec_brief`: title, description, data roles and notes of the spec, fenced as
  `<spec_text>` (spec text starts as a public issue).
* `get_current_code(version)`: the exported `plot.py` of a version (0 is the latest),
  or the normalised catalogue code before the first version, fenced as `<catalogue_code>`.
* `set_bindings(bindings)`: `apply_bindings` plus a state write; refused while the
  pipeline runs.
* `plot_pipeline`: the `Workflow` around `pipeline.run_pipeline`, which ADK exposes as
  a NodeTool with the input schema `PipelineArgs` (`change_request`, `base`). The
  tool name is the workflow name, so it stays stable.
"""

import json
from typing import Any

from google.adk import Workflow
from google.adk.tools.tool_context import ToolContext

from ..briefs import spec_brief, trimmed_profiles
from ..pipeline import run_pipeline
from ..plugins.ledger import ledger_for
from ..plugins.tool_safety import result_limit, result_size
from ..policy import DATA_PREAMBLE, fence
from ..schemas import Binding, DatasetProfile, PipelineArgs
from ..services import get_services
from ..session_state import SessionView, apply_bindings, read_session


PLOT_PIPELINE = "plot_pipeline"


def _not_ready(reason: str) -> dict[str, Any]:
    return {"status": "not_ready", "reason": reason}


def _error(code: str) -> dict[str, Any]:
    return {"status": "error", "code": code}


def _view(tool_context: ToolContext) -> SessionView | None:
    return read_session(tool_context.state)


def _profile(view: SessionView, tool_context: ToolContext) -> DatasetProfile | None:
    if not view.dataset_id:
        return None
    stored = get_services().datasets.get(view.dataset_id, tool_context.session.id)
    return stored.profile if stored else None


async def get_dataset_profile(tool_context: ToolContext) -> dict[str, Any]:
    """Return the profile of the user's dataset: row count, typed columns and a few sample cells."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    profile = _profile(view, tool_context)
    if profile is None:
        return _not_ready("no_dataset")
    result: dict[str, Any] = {}
    for text, truncated in trimmed_profiles(profile):
        result = {"status": "ok", "rows": profile.rows, "profile": DATA_PREAMBLE + "\n" + fence("user_data", text)}
        if truncated:
            result["truncated"] = True
        if result_size(result) <= result_limit("get_dataset_profile"):
            break
    return result


async def get_spec_brief(tool_context: ToolContext) -> dict[str, Any]:
    """Return the chosen plot's title, description, data roles and notes."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    return {"status": "ok", "brief": DATA_PREAMBLE + "\n" + fence("spec_text", spec_brief(view))}


async def get_current_code(version: int, tool_context: ToolContext) -> dict[str, Any]:
    """Return the plot's code. version 0 is the latest version; before the first plot it is the catalogue code."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    stored = get_services().versions.get(tool_context.session.id, version or None)
    if stored is None and version:
        return _error("unknown_version")
    code = stored.export if stored is not None else view.normalised
    return {
        "status": "ok",
        "version": stored.number if stored is not None else 0,
        "code": DATA_PREAMBLE + "\n" + fence("catalogue_code", code),
    }


async def set_bindings(bindings: list[dict[str, str]], tool_context: ToolContext) -> dict[str, Any]:
    """Bind spec data roles to dataset columns. Each binding is {"role": <role name>, "column": <column name>}."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    profile = _profile(view, tool_context)
    if profile is None:
        return _not_ready("no_dataset")
    try:
        parsed = [Binding.model_validate(item) for item in bindings]
    except ValueError:
        return _error("invalid_bindings")
    check, delta = apply_bindings(parsed, view.snapshot.roles(), profile)
    if not delta:
        # The errors quote column names from the user's dataset.
        errors = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.errors[:10], ensure_ascii=False))
        return {"status": "error", "code": "invalid_bindings", "errors": errors}
    for key, value in delta.items():
        tool_context.state[key] = value
    return {"status": "ok", "complete": check.complete, "missing_roles": check.missing_roles}


plot_pipeline = Workflow(
    name=PLOT_PIPELINE,
    description=(
        "Adapt the plot to the user's dataset and bindings, render it in light and dark, review it, and repair it "
        "once if needed. Call it with no arguments for 'Create plot'; for a change, pass change_request (English, "
        "at most 600 characters) and base='previous'. Returns the PlotResult."
    ),
    input_schema=PipelineArgs,
    edges=[("START", run_pipeline)],
)

SESSION_TOOLS = (get_dataset_profile, get_spec_brief, get_current_code, set_bindings)
ROOT_TOOL_NAMES = frozenset({*(tool.__name__ for tool in SESSION_TOOLS), PLOT_PIPELINE})
