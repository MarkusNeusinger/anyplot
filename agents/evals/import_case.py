"""Import a feedback case into the regression harness as a local eval case.

Run it from the repository root:

    uv run --extra agents python -m agents.evals.import_case anyplot-session-AbCdEf12.json
    uv run --extra agents python -m agents.evals.import_case path/to/cases/20261012T143005Z-1a2b3c4d \\
        --expected rejected

`<source>` is one of:

* a session bundle, the JSON file the chat page's `.save()` downloads
  (`anyplot-session-<id>.json`, saved with `# include data.csv` ticked). It holds every
  version of the session; `--version N` picks one, the newest by default;
* a case directory as `POST /debug/agent/sessions/{sid}/feedback` stores it under
  `cases/<case_id>/` in the private case bucket (`manifest.json`, `data.csv`, ...),
  copied to this machine by hand. Its manifest names the version, the reaction and
  the library.

A `gs://` source is out of scope: reading cases from the bucket comes with the triage
change that also adds the `agent_feedback` table and the "Agent cases" section of the
debug page (`docs/concepts/agent-network.md`, "Feedback capture").

The case goes to `agents/evals/.cases/<id>/`, the git-ignored directory the harness
reads as promoted cases (`agents/evals/cases.py`, origin `promoted`), and nowhere
else: a feedback case holds a user's data, and everything under
`agents/evals/fixtures/` is committed and ships under the repository's MIT licence.
`--save-baseline` refuses a run that holds promoted cases. Run the case with
`python -m agents.evals.matrix --cases <id>`. The directory holds:

* `case.json`: the spec, library, locale and bindings of the session; `expected` from
  `--expected`, else from the manifest's reaction (`thumbs_up` and `idea` → `accepted`,
  `thumbs_down` and `bug` → `rejected`; a bundle without a manifest → `unknown`);
  `tags` `["imported", <reaction>]`; and `source`, where the case came from;
* `data.csv`: the version's data. A source without it is refused: the harness pastes
  it like a user would, so a case without data cannot run;
* `change_request.txt`, when the version came from a change the user typed. The
  transcript carries no version markers, so the request is found by position: the
  turns that can produce a version are the `create_plot` action and every message
  typed after the first one, and version `n` is taken as the `n`-th of those. A
  question in between shifts the count, so the tool prints what it picked; edit or
  delete the file when it is wrong.

The case id is `--id`, or `case-<the case id, lower case>` for a case directory and
`session-<first 8 hex digits of the file's SHA-256>-v<n>` for a bundle. An existing
case is refused unless `--force` replaces it; an id the committed fixtures use is
refused always. The case is written to a temporary directory first and checked with
the harness's own loader (`load_case`), so a refused import leaves nothing behind.
Exit codes: 0 written, 1 refused, 2 bad arguments.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVALS_DIR = Path(__file__).resolve().parent
PROMOTED_DIR = EVALS_DIR / ".cases"
FIXTURES_DIR = EVALS_DIR / "fixtures" / "cases"
MANIFEST_NAME = "manifest.json"
EXPECTED_BY_REACTION = {"thumbs_up": "accepted", "idea": "accepted", "thumbs_down": "rejected", "bug": "rejected"}
"""The default outcome per reaction of the site's set; `--expected` overrides it."""
IMPORTED_TAG = "imported"
ACTION_PREFIX = "[action] "
"""How the agents service records the page's actions as user messages (`agents/main.py`, `ACTION_MESSAGES`)."""
CREATE_PLOT_MESSAGE = "[action] Create the plot from my dataset and bindings."
WITHHELD = "[message withheld by scope policy]"
"""The placeholder of a message the scope judge refused (`agents/anyplot/plugins/scope_guard.py`)."""
MAX_CHANGE_REQUEST_CHARS = 600
"""`agents/evals/cases.py`'s cap on `change_request.txt`; a longer request is left out with a note."""
# The first line of an exported `plot.py` (`agents/anyplot/code/export.py`, `attribution`).
_EXPORT_LIBRARY = re.compile(r"\A# Adapted by anyplot\.ai from [a-z0-9-]+ \(([a-z][a-z0-9]*)[ )]")


class ImportRefused(ValueError):
    """The source cannot become a runnable case; the message says why."""


@dataclass(frozen=True)
class Source:
    """What the source holds, whichever kind it is."""

    bundle: dict[str, Any]
    version: dict[str, Any]
    data_csv: str | None
    manifest: dict[str, Any] | None
    default_id: str
    description: str


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ImportRefused(f"{path}: not a readable JSON file ({type(exc).__name__})") from exc


def _versions(bundle: Any, where: str) -> list[dict[str, Any]]:
    if not isinstance(bundle, dict) or not isinstance(bundle.get("versions"), list):
        raise ImportRefused(f"{where}: not a session bundle (no `versions` list)")
    versions = [item for item in bundle["versions"] if isinstance(item, dict) and isinstance(item.get("number"), int)]
    if not versions:
        raise ImportRefused(f"{where}: the session has no plot version")
    return versions


def _pick(versions: list[dict[str, Any]], number: int | None, where: str) -> dict[str, Any]:
    if number is None:
        return max(versions, key=lambda item: item["number"])
    for item in versions:
        if item["number"] == number:
            return item
    numbers = ", ".join(str(item["number"]) for item in versions)
    raise ImportRefused(f"{where}: no version {number} (the source holds {numbers})")


def read_bundle_file(path: Path, number: int | None) -> Source:
    """A bundle the page's `.save()` downloaded: every version, each with its `data_csv` when it was ticked."""
    bundle = _read_json(path)
    version = _pick(_versions(bundle, str(path)), number, str(path))
    data = version.get("data_csv")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    return Source(
        bundle=bundle,
        version=version,
        data_csv=data if isinstance(data, str) else None,
        manifest=None,
        default_id=f"session-{digest}-v{version['number']}",
        description=f"saved session {path.name}, version {version['number']}",
    )


def read_case_dir(path: Path, number: int | None) -> Source:
    """A stored feedback case: the manifest, with the bundle inside, and the sibling files."""
    manifest = _read_json(path / MANIFEST_NAME)
    if not isinstance(manifest, dict):
        raise ImportRefused(f"{path / MANIFEST_NAME}: not a case manifest")
    where = str(path / MANIFEST_NAME)
    result_version = manifest.get("result_version")
    if number is not None and number != result_version:
        raise ImportRefused(f"{where}: the case is about version {result_version}, not {number}")
    wanted = result_version if isinstance(result_version, int) else number
    version = _pick(_versions(manifest.get("bundle"), where), wanted, where)
    data_file = path / "data.csv"
    case_id = str(manifest.get("id") or path.name)
    return Source(
        bundle=manifest["bundle"],
        version=version,
        data_csv=data_file.read_text(encoding="utf-8") if data_file.is_file() else None,
        manifest=manifest,
        default_id=f"case-{case_id.lower()}",
        description=f"feedback case {case_id}, version {version['number']}",
    )


def library_of(source: Source) -> str | None:
    """The manifest's `library_id`, else the version's own, else the one its `plot.py` names, else the session's."""
    if source.manifest and isinstance(source.manifest.get("library_id"), str):
        return str(source.manifest["library_id"])
    if isinstance(source.version.get("library"), str):
        return str(source.version["library"])
    code = source.version.get("plot_py")
    match = _EXPORT_LIBRARY.match(code) if isinstance(code, str) else None
    if match:
        return match.group(1)
    session = source.bundle.get("session")
    library = session.get("library") if isinstance(session, dict) else None
    return library if isinstance(library, str) else None


def change_request(transcript: Any, number: int) -> str | None:
    """The message the user typed for version `number`, when that version came from one; see the module notes."""
    if not isinstance(transcript, list):
        return None
    turns: list[str] = []
    started = False
    for entry in transcript:
        if not isinstance(entry, dict) or entry.get("role") != "user" or not isinstance(entry.get("text"), str):
            continue
        text = entry["text"].strip()
        if text == CREATE_PLOT_MESSAGE:
            started = True
            turns.append(text)
        elif started and text and not text.startswith(ACTION_PREFIX) and text != WITHHELD:
            turns.append(text)
    if number > len(turns):
        return None
    text = turns[number - 1]
    return None if text == CREATE_PLOT_MESSAGE else text


def _bindings(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = bundle.get("bindings")
    if not isinstance(bindings, list):
        return []
    # Only bound roles: the harness sends these with `PUT /bindings`, where an entry names a column.
    return [
        {"role": item["role"], "column": item["column"]}
        for item in bindings
        if isinstance(item, dict) and isinstance(item.get("role"), str) and isinstance(item.get("column"), str)
    ]


@dataclass(frozen=True)
class ImportedCase:
    """The files of the eval case and the notes to print."""

    case: dict[str, Any]
    data_csv: str
    change_request: str | None
    notes: list[str]


def build_case(source: Source, expected: str | None) -> ImportedCase:
    """The eval case of a source; raises `ImportRefused` when it cannot run."""
    from core.constants import SUPPORTED_LIBRARIES

    raw_session = source.bundle.get("session")
    session: dict[str, Any] = raw_session if isinstance(raw_session, dict) else {}
    spec_id = session.get("spec_id")
    if not isinstance(spec_id, str) or not re.fullmatch(r"[a-z0-9-]{1,100}", spec_id):
        raise ImportRefused("the source names no spec id")
    library = library_of(source)
    if library not in SUPPORTED_LIBRARIES:
        raise ImportRefused(f"the source names no catalogue library ({library!r})")
    if not source.data_csv or not source.data_csv.strip():
        raise ImportRefused(
            "the source holds no data.csv: save the session with `# include data.csv` ticked, "
            "or send the feedback with the box ticked, so the harness has the data to paste"
        )
    notes: list[str] = []
    reaction = source.manifest.get("reaction") if source.manifest else None
    reaction = reaction if isinstance(reaction, str) and reaction in EXPECTED_BY_REACTION else None
    if expected is None:
        expected = EXPECTED_BY_REACTION[reaction] if reaction else "unknown"
        if reaction in ("bug", "idea"):
            notes.append(f"expected {expected} from the reaction {reaction}; pass --expected to choose")
    request = change_request(source.bundle.get("transcript"), source.version["number"])
    if request is not None and len(request) > MAX_CHANGE_REQUEST_CHARS:
        notes.append(f"left out a change request of {len(request)} characters (at most {MAX_CHANGE_REQUEST_CHARS})")
        request = None
    locale = session.get("locale")
    case = {
        "spec_id": spec_id,
        "library": library,
        "locale": locale if isinstance(locale, str) and locale else "en",
        "bindings": _bindings(source.bundle),
        "expected": expected,
        "tags": [IMPORTED_TAG, reaction] if reaction else [IMPORTED_TAG],
        "source": source.description,
    }
    return ImportedCase(case=case, data_csv=source.data_csv, change_request=request, notes=notes)


def write_case(
    case_id: str,
    imported: ImportedCase,
    *,
    force: bool = False,
    promoted_dir: Path | None = None,
    fixtures_dir: Path | None = None,
) -> Path:
    """Write the case under `promoted_dir/<case_id>/` (`.cases/`), checked with the harness's loader first."""
    from agents.anyplot.settings import FIXTURE_PATTERN
    from agents.evals.cases import CaseError, load_case

    promoted_dir = PROMOTED_DIR if promoted_dir is None else promoted_dir
    fixtures_dir = FIXTURES_DIR if fixtures_dir is None else fixtures_dir
    # Checked before the id becomes part of any path.
    if not re.fullmatch(FIXTURE_PATTERN, case_id):
        raise ImportRefused(f"{case_id!r} is not a case id ({FIXTURE_PATTERN})")
    if (fixtures_dir / case_id).exists():
        raise ImportRefused(f"{case_id} is a committed fixture case; choose another --id")
    target = promoted_dir / case_id
    if target.exists() and not force:
        raise ImportRefused(f"{target} exists; pass --force to replace it")
    # Staged in a temporary directory, never in `promoted_dir`: the harness loads every
    # directory there, and a half-written one would stop its next run.
    with tempfile.TemporaryDirectory(prefix="anyplot-import-") as tmp:
        staging = Path(tmp) / case_id
        staging.mkdir()
        case_text = json.dumps(imported.case, indent=2, ensure_ascii=False) + "\n"
        (staging / "case.json").write_text(case_text, encoding="utf-8")
        (staging / "data.csv").write_text(imported.data_csv, encoding="utf-8")
        if imported.change_request:
            (staging / "change_request.txt").write_text(imported.change_request + "\n", encoding="utf-8")
        try:
            load_case(staging, "promoted")
        except CaseError as exc:
            raise ImportRefused(f"the harness would refuse the case: {exc}") from exc
        promoted_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(staging, target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.import_case",
        description="Import a saved session bundle or a stored feedback case as a local eval case.",
    )
    parser.add_argument("source", type=Path, help="a bundle JSON file (.save()) or a case directory with manifest.json")
    parser.add_argument("--id", dest="case_id", help="the eval case id (default: derived from the source)")
    parser.add_argument("--expected", choices=("accepted", "rejected"), help="the outcome the case expects")
    parser.add_argument("--version", type=int, help="the plot version (default: the case's, or the newest)")
    parser.add_argument("--force", action="store_true", help="replace an imported case of the same id")
    args = parser.parse_args(argv)
    if str(args.source).startswith("gs:/"):
        parser.error("a gs:// source is not supported yet; copy the case directory down first")
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"  # importing agents.anyplot reads settings; never from a .env file
    os.environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    try:
        if args.source.is_dir():
            source = read_case_dir(args.source, args.version)
        elif args.source.is_file():
            source = read_bundle_file(args.source, args.version)
        else:
            raise ImportRefused(f"{args.source}: no such file or directory")
        imported = build_case(source, args.expected)
        target = write_case(args.case_id or source.default_id, imported, force=args.force)
    except ImportRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    for note in imported.notes:
        print(f"note: {note}", file=sys.stderr)
    case = imported.case
    files = ["case.json", "data.csv"] + (["change_request.txt"] if imported.change_request else [])
    print(f"wrote {target} ({', '.join(files)}): {case['spec_id']} {case['library']}, expected {case['expected']}")
    if imported.change_request:
        print(f"change request (check it): {imported.change_request}")
    print(f"run it with: uv run --extra agents python -m agents.evals.matrix --cases {target.name} --renderer ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
