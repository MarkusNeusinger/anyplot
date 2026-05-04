"""Read/write the `.regen-plan.md` state file.

Replaces inline markdown manipulation that used to live across regen.md
steps 1c (list libraries), 1d (spec title), 1e (write plan), 2a (parse
next library), 2k (mark complete), per-library failure (mark failed),
and Done mode (archive).

`.regen-plan.md` shape:

    # Regen plan: {spec_id}

    - Spec: `{spec_id}`
    - Title: `{title}`
    - Latest implementation update: `{latest_iso}`
    - Plan created: `{plan_created_iso}`

    ## Libraries

    - [ ] altair
    - [x] matplotlib
    - [!] pygal

    ## Change Requests

    - altair: Spec is vague on data; current matches bokeh exactly. Pick a different domain ...

    ## Log

    - altair: PR ..., score 90, ai-approved (timestamp)

The `## Change Requests` section is optional — written only when at least one
entry exists. Plan-mode similarity analysis (in `regen.md`) populates it; if
nothing's flagged, the section is omitted entirely.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import PlanSpec


PLAN_PATH = Path(".regen-plan.md")
HISTORY_DIR = Path(".regen-history")


@dataclass(frozen=True)
class PlanLine:
    library: str
    state: str  # " " (unchecked), "x" (done), "!" (failed)


# ---------------------------------------------------------------------------
# Read helpers (called from regen.md steps 1c, 1d, 2a)
# ---------------------------------------------------------------------------


def list_libraries(spec_id: str, plots_root: Path = Path("plots")) -> list[str]:
    """Sorted list of `{library}.py` files in the spec's python impl dir."""
    impl_dir = plots_root / spec_id / "implementations" / "python"
    if not impl_dir.is_dir():
        return []
    libs = []
    for f in sorted(impl_dir.iterdir()):
        if f.suffix == ".py" and f.name != "__init__.py":
            libs.append(f.stem)
    return libs


def spec_title(spec_id: str, plots_root: Path = Path("plots")) -> str:
    """First `# ` heading of `specification.md`, stripped of the `spec-id: ` prefix."""
    spec_md = plots_root / spec_id / "specification.md"
    text = spec_md.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            heading = line[2:].strip()
            # Common form: "spec-id: Title" → return just "Title" if prefix matches
            prefix = f"{spec_id}:"
            if heading.startswith(prefix):
                return heading[len(prefix) :].strip()
            return heading
    raise ValueError(f"No top-level heading in {spec_md}")


# ---------------------------------------------------------------------------
# Write / scaffold (regen.md step 1e)
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_plan(spec: PlanSpec, plan_path: Path = PLAN_PATH) -> Path:
    """Write a fresh `.regen-plan.md` for the given spec. Overwrites if present."""
    lines = [
        f"# Regen plan: {spec.spec_id}",
        "",
        f"- Spec: `{spec.spec_id}`",
        f"- Title: `{spec.title}`",
        f"- Latest implementation update: `{spec.latest_update}`",
        f"- Plan created: `{_now_iso()}`",
        "",
        "## Libraries",
        "",
    ]
    for lib in spec.libraries:
        lines.append(f"- [ ] {lib}")
    lines.append("")
    if spec.change_requests:
        # Emit only entries whose key matches a library in this plan. This keeps
        # the section ordered consistently with `## Libraries` and silently drops
        # stray keys (typos in the JSON the dispatcher receives).
        ordered_entries = [(lib, spec.change_requests[lib]) for lib in spec.libraries if spec.change_requests.get(lib)]
        if ordered_entries:
            lines.append("## Change Requests")
            lines.append("")
            for lib, text in ordered_entries:
                lines.append(f"- {lib}: {text}")
            lines.append("")
    lines.append("## Log")
    lines.append("")
    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


# ---------------------------------------------------------------------------
# Parse / inspect (regen.md step 2a)
# ---------------------------------------------------------------------------


_RE_LIB_LINE = re.compile(r"^- \[(?P<state>[ x!])\]\s+(?P<lib>\S+)\s*$")
_RE_CHANGE_REQUEST_LINE = re.compile(r"^- (?P<lib>\S+):\s+(?P<text>.+)$")


def parse_plan(plan_path: Path = PLAN_PATH) -> tuple[str, str, list[PlanLine], dict[str, str]]:
    """Return `(spec_id, title, [PlanLine,...], change_requests)` from `.regen-plan.md`.

    `change_requests` is keyed by library name. Empty dict if the plan has no
    `## Change Requests` section (the common case — the section is only written
    when Plan-mode similarity analysis flags at least one library).
    """
    text = plan_path.read_text(encoding="utf-8")
    spec_id = _extract_field(text, "Spec")
    title = _extract_field(text, "Title")
    lines: list[PlanLine] = []
    for raw in text.splitlines():
        m = _RE_LIB_LINE.match(raw)
        if m:
            lines.append(PlanLine(library=m.group("lib"), state=m.group("state")))
    change_requests: dict[str, str] = {}
    for raw in _extract_section_lines(text, "Change Requests"):
        m = _RE_CHANGE_REQUEST_LINE.match(raw)
        if m:
            change_requests[m.group("lib")] = m.group("text").strip()
    return spec_id, title, lines, change_requests


def _extract_field(text: str, label: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}:\s*`([^`]+)`\s*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        raise ValueError(f"`{label}` field not found in plan file")
    return m.group(1)


def _extract_section_lines(text: str, heading: str) -> list[str]:
    """Return raw lines under `## {heading}` until the next `## ` heading or EOF.

    Section-scoping is required for change_requests because their bullet shape
    `- {lib}: {text}` would otherwise collide with `## Log` entries (which also
    start with `- {lib}: PR ...` / `- {lib}: FAILED — ...`).
    """
    in_section = False
    out: list[str] = []
    for line in text.splitlines():
        if line.strip() == f"## {heading}":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return out


def next_unchecked(plan_path: Path = PLAN_PATH) -> tuple[str, str, str, str] | None:
    """Return `(spec_id, title, library, change_request)` for the first unchecked library, or None.

    `change_request` is the empty string when no entry exists for the library.
    """
    spec_id, title, lines, change_requests = parse_plan(plan_path)
    for line in lines:
        if line.state == " ":
            return spec_id, title, line.library, change_requests.get(line.library, "")
    return None


def change_request_for(library: str, plan_path: Path = PLAN_PATH) -> str:
    """Return the change_request for `library`, or empty string if none."""
    _spec_id, _title, _lines, change_requests = parse_plan(plan_path)
    return change_requests.get(library, "")


# ---------------------------------------------------------------------------
# Mutate (regen.md step 2k, per-library failure)
# ---------------------------------------------------------------------------


def _replace_lib_state(text: str, library: str, new_state: str) -> str:
    pattern = re.compile(rf"^- \[[ x!]\]\s+{re.escape(library)}\s*$", re.MULTILINE)
    new_line = f"- [{new_state}] {library}"
    text, n = pattern.subn(new_line, text, count=1)
    if n == 0:
        raise ValueError(f"Library {library!r} not found in plan")
    return text


def _append_log(text: str, line: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    return text + line + "\n"


def mark_done(library: str, pr_url: str, score: int, verdict: str, plan_path: Path = PLAN_PATH) -> None:
    text = plan_path.read_text(encoding="utf-8")
    text = _replace_lib_state(text, library, "x")
    label = "ai-approved" if score >= 50 else "quality-poor"
    log = f"- {library}: PR {pr_url}, score {score}, label {label}, verdict {verdict} ({_now_iso()})"
    text = _append_log(text, log)
    plan_path.write_text(text, encoding="utf-8")


def mark_failed(library: str, reason: str, plan_path: Path = PLAN_PATH) -> None:
    text = plan_path.read_text(encoding="utf-8")
    text = _replace_lib_state(text, library, "!")
    text = _append_log(text, f"- {library}: FAILED — {reason} ({_now_iso()})")
    plan_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Done mode (archive)
# ---------------------------------------------------------------------------


def archive(plan_path: Path = PLAN_PATH, history_dir: Path = HISTORY_DIR) -> Path:
    """Move the plan to `.regen-history/{spec_id}-{ts}.md`. Returns the archived path."""
    spec_id, _title, _lines, _change_requests = parse_plan(plan_path)
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = history_dir / f"{spec_id}-{ts}.md"
    shutil.move(str(plan_path), str(dest))
    return dest


# ---------------------------------------------------------------------------
# Cleanup helpers shared by mark_failed callers
# ---------------------------------------------------------------------------


def cleanup_worktree(spec_id: str, library: str) -> None:
    """Best-effort: remove .worktrees/{spec}-{lib} and prune."""
    worktree = Path(".worktrees") / f"{spec_id}-{library}"
    if worktree.exists():
        subprocess.run(["git", "worktree", "remove", str(worktree), "--force"], check=False)
    subprocess.run(["git", "worktree", "prune"], check=False)


def cleanup_preview(spec_id: str, library: str) -> None:
    """Best-effort: remove .regen-preview/{library}/."""
    preview = Path("plots") / spec_id / "implementations" / "python" / ".regen-preview" / library
    if preview.exists():
        shutil.rmtree(preview, ignore_errors=True)
