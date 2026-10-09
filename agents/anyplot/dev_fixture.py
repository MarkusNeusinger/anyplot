"""Development-only session seed from an eval fixture case, so `adk web` has something to plot.

With `ENVIRONMENT=development` and `AGENT_DEV_FIXTURE=<case-id>`, every new session
is seeded from `agents/evals/fixtures/cases/<case-id>/`:

* `case.json`: `{"spec_id", "library", "locale"?, "bindings"?: [{"role", "column"}]}`;
* `data.csv`: the dataset, parsed exactly as the `/dataset` route parses pasted text;
* `snapshot.json` (optional): the `CatalogueSnapshot` fields. Without it the snapshot
  is built from the repository's `plots/<spec>/` files (title and sections of
  `specification.md`, the implementation file with `# noqa` comments stripped, and the
  library version from its metadata), the way `sync_to_postgres.py` and the BFF build
  it from the database.

`AgentSettings` refuses `AGENT_DEV_FIXTURE` outside development, and `DevFixturePlugin`
checks the environment again before it seeds. The plugin seeds in
`on_user_message_callback`, the first hook of the first invocation, by appending one
state-delta event to the session; the dataset goes into the dataset store under the
session id.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from core.utils import strip_noqa_comments

from .opening import assess, ingest_dataset, opening_state
from .schemas import Binding
from .services import get_services
from .session_state import BINDINGS, SPEC_ID, CatalogueSnapshot
from .settings import FIXTURE_PATTERN, AgentSettings, get_settings


REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = REPO_ROOT / "agents" / "evals" / "fixtures" / "cases"
SEED_AUTHOR = "user"  # a content-free state event, authored like ADK's own state-only events


class FixtureError(ValueError):
    """The fixture case is missing, malformed or not eligible."""


@dataclass(frozen=True)
class FixtureCase:
    case_id: str
    spec_id: str
    library: str
    locale: str
    bindings: list[Binding] | None
    data_text: str
    snapshot: CatalogueSnapshot


def _section(markdown: str, name: str) -> str:
    match = re.search(rf"## {re.escape(name)}\s*\n(.+?)(?=\n##|\Z)", markdown, re.DOTALL)
    return match.group(1).strip() if match else ""


def _bullets(text: str) -> list[str]:
    return [line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith(("- ", "* "))]


def snapshot_from_repo(spec_id: str, library: str, repo_root: Path = REPO_ROOT) -> CatalogueSnapshot:
    """The catalogue snapshot of one pair, built from the repository like the BFF builds it from the DB."""
    spec_dir = repo_root / "plots" / spec_id
    markdown = (spec_dir / "specification.md").read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+[\w-]+:\s*(.+)$", markdown, re.MULTILINE)
    code = strip_noqa_comments((spec_dir / "implementations" / "python" / f"{library}.py").read_text(encoding="utf-8"))
    metadata = spec_dir / "metadata" / "python" / f"{library}.yaml"
    version_match = re.search(r"^library_version:\s*['\"]?([^'\"\n]+)", metadata.read_text(encoding="utf-8"), re.M)
    return CatalogueSnapshot(
        spec_id=spec_id,
        title=title_match.group(1).strip() if title_match else spec_id,
        description=_section(markdown, "Description"),
        data_roles=_bullets(_section(markdown, "Data")),
        notes=_bullets(_section(markdown, "Notes")),
        code=code or "",
        library_version=version_match.group(1).strip() if version_match else None,
    )


def load_case(case_id: str, cases_dir: Path = CASES_DIR) -> FixtureCase:
    if not re.fullmatch(FIXTURE_PATTERN, case_id):
        raise FixtureError(f"not a fixture case id: {case_id!r}")
    case_dir = cases_dir / case_id
    try:
        case: dict[str, Any] = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        data_text = (case_dir / "data.csv").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise FixtureError(f"fixture case {case_id!r} is missing case.json or data.csv") from exc
    spec_id, library = str(case["spec_id"]), str(case["library"])
    snapshot_file = case_dir / "snapshot.json"
    if snapshot_file.is_file():
        snapshot = CatalogueSnapshot.model_validate_json(snapshot_file.read_text(encoding="utf-8"))
    else:
        snapshot = snapshot_from_repo(spec_id, library)
    raw_bindings = case.get("bindings")
    bindings = [Binding.model_validate(item) for item in raw_bindings] if raw_bindings is not None else None
    return FixtureCase(case_id, spec_id, library, str(case.get("locale", "en")), bindings, data_text, snapshot)


def seed_delta(case: FixtureCase, session_id: str, settings: AgentSettings) -> dict[str, Any]:
    """The state delta that opens a session on the fixture case, with its dataset stored."""
    eligibility, normalised = assess(case.snapshot, case.library, settings)
    if not eligibility.eligible:
        raise FixtureError(f"fixture {case.case_id} is not eligible: {'; '.join(eligibility.reasons)}")
    delta = opening_state(
        spec_id=case.spec_id,
        library=case.library,
        locale=case.locale,
        snapshot=case.snapshot,
        normalised=normalised,
        eligibility=eligibility,
    )
    ingested = ingest_dataset(get_services().datasets, session_id, case.data_text, case.snapshot)
    delta.update(ingested.state_delta())
    if case.bindings is not None:
        delta[BINDINGS] = [binding.model_dump() for binding in case.bindings]
    return delta


class DevFixturePlugin(BasePlugin):
    """Seeds every new session from `AGENT_DEV_FIXTURE`; refuses to exist outside development."""

    def __init__(self, case_id: str, name: str = "anyplot_dev_fixture") -> None:
        if not get_settings().is_development:
            raise FixtureError("the fixture seed runs only with ENVIRONMENT=development")
        super().__init__(name=name)
        self.case = load_case(case_id)

    async def on_user_message_callback(
        self, *, invocation_context: InvocationContext, user_message: types.Content
    ) -> types.Content | None:
        session = invocation_context.session
        if session.state.get(SPEC_ID) or not get_settings().is_development:
            return None
        delta = seed_delta(self.case, session.id, get_settings())
        event = Event(
            invocation_id=invocation_context.invocation_id, author=SEED_AUTHOR, actions=EventActions(state_delta=delta)
        )
        await invocation_context.session_service.append_event(session=session, event=event)
        return None
