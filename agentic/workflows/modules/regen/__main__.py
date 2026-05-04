"""CLI dispatcher for the regen helpers.

Usage (from `regen.md`):

    uv run python -m agentic.workflows.modules.regen pick-oldest
    uv run python -m agentic.workflows.modules.regen validate-spec <spec_id>
    uv run python -m agentic.workflows.modules.regen list-libraries <spec_id>
    uv run python -m agentic.workflows.modules.regen spec-title <spec_id>
    uv run python -m agentic.workflows.modules.regen write-plan <spec_id>     # optional {lib: change_request} JSON on stdin
    uv run python -m agentic.workflows.modules.regen next-library              # outputs spec\ttitle\tlibrary\tchange_request
    uv run python -m agentic.workflows.modules.regen render <spec_id> <library>
    uv run python -m agentic.workflows.modules.regen write-metadata <spec_id> <library>  # JSON eval on stdin
    uv run python -m agentic.workflows.modules.regen update-impl-header <spec_id> <library> <score>
    uv run python -m agentic.workflows.modules.regen stage-images <spec_id> <library>
    uv run python -m agentic.workflows.modules.regen create-pr <spec_id> <library>      # JSON eval on stdin
    uv run python -m agentic.workflows.modules.regen mark-done <library> <pr_url> <score> <verdict>
    uv run python -m agentic.workflows.modules.regen mark-failed <library> "<reason>"
    uv run python -m agentic.workflows.modules.regen archive

Mirrors the `if __name__ == "__main__"` dispatcher in `core/images.py`.
"""

from __future__ import annotations

import json
import sys

from . import PlanSpec, QualityEval


def _print_usage() -> None:
    print(__doc__ or "")
    sys.exit(1)


def _read_eval_from_stdin() -> QualityEval:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"::error::stdin is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)
    return QualityEval.from_json(data)


def _read_change_requests_from_stdin() -> dict[str, str]:
    """Optionally read `{lib: change_request_text}` JSON from stdin.

    Returns empty dict when stdin is a TTY (interactive run) or empty/whitespace.
    Exits non-zero on malformed JSON. Whitespace inside each value is collapsed
    to single spaces so a multi-line change_request can't corrupt the
    one-line-per-entry plan format.
    """
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"::error::stdin is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(f"::error::stdin must be a JSON object, got {type(data).__name__}", file=sys.stderr)
        sys.exit(1)
    return {str(k): " ".join(str(v).split()) for k, v in data.items() if v and str(v).strip()}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        _print_usage()
    command = argv[1]
    args = argv[2:]

    if command == "pick-oldest":
        from .picker import pick_oldest

        spec_id, latest = pick_oldest()
        print(f"{spec_id}\t{latest}")
        return 0

    if command == "validate-spec":
        if len(args) < 1:
            _print_usage()
        from .picker import validate_spec

        try:
            spec_id, latest = validate_spec(args[0])
        except LookupError as exc:
            print(f"::error::{exc}", file=sys.stderr)
            return 1
        print(f"{spec_id}\t{latest}")
        return 0

    if command == "list-libraries":
        if len(args) < 1:
            _print_usage()
        from .plan import list_libraries

        for lib in list_libraries(args[0]):
            print(lib)
        return 0

    if command == "spec-title":
        if len(args) < 1:
            _print_usage()
        from .plan import spec_title

        print(spec_title(args[0]))
        return 0

    if command == "write-plan":
        if len(args) < 1:
            _print_usage()
        spec_id = args[0]
        from .picker import validate_spec
        from .plan import list_libraries, spec_title, write_plan

        _id, latest = validate_spec(spec_id)
        title = spec_title(spec_id)
        libs = list_libraries(spec_id)
        if not libs:
            print(f"::error::No python implementations found for {spec_id}", file=sys.stderr)
            return 1
        change_requests = _read_change_requests_from_stdin()
        path = write_plan(
            PlanSpec(
                spec_id=spec_id, title=title, latest_update=latest, libraries=libs, change_requests=change_requests
            )
        )
        print(f"Plan written: {path}")
        print(f"- Spec: {spec_id} ({title})")
        print(f"- Libraries: {', '.join(libs)}")
        flagged = [lib for lib in libs if change_requests.get(lib)]
        if flagged:
            print(f"- Change requests: {', '.join(flagged)}")
        else:
            print("- Change requests: none")
        return 0

    if command == "next-library":
        from .plan import next_unchecked

        nxt = next_unchecked()
        if nxt is None:
            return 2  # exit code 2 = no more unchecked items
        spec_id, title, library, change_request = nxt
        print(f"{spec_id}\t{title}\t{library}\t{change_request}")
        return 0

    if command == "render":
        if len(args) < 2:
            _print_usage()
        from .render import run_theme_renders

        result = run_theme_renders(args[0], args[1])
        print(f"Rendered: {result.light_png} {result.dark_png}")
        if result.light_html:
            print(f"HTML: {result.light_html} {result.dark_html}")
        return 0

    if command == "write-metadata":
        if len(args) < 2:
            _print_usage()
        from .metadata import write_metadata

        quality = _read_eval_from_stdin()
        path = write_metadata(args[0], args[1], quality)
        print(f"Metadata: {path}")
        return 0

    if command == "update-impl-header":
        if len(args) < 3:
            _print_usage()
        from .metadata import update_impl_header

        update_impl_header(args[0], args[1], int(args[2]))
        return 0

    if command == "stage-images":
        if len(args) < 2:
            _print_usage()
        from .staging import stage_images_to_gcs

        path = stage_images_to_gcs(args[0], args[1])
        print(f"Staged: {path}")
        return 0

    if command == "create-pr":
        if len(args) < 2:
            _print_usage()
        from .pr_create import create_regen_pr

        quality = _read_eval_from_stdin()
        result = create_regen_pr(args[0], args[1], quality)
        print(result.pr_url)
        print(result.pr_number)
        return 0

    if command == "mark-done":
        if len(args) < 4:
            _print_usage()
        from .plan import mark_done

        mark_done(library=args[0], pr_url=args[1], score=int(args[2]), verdict=args[3])
        return 0

    if command == "mark-failed":
        if len(args) < 2:
            _print_usage()
        from .plan import cleanup_preview, cleanup_worktree, mark_failed, parse_plan

        spec_id, _title, _lines, _change_requests = parse_plan()
        mark_failed(library=args[0], reason=args[1])
        cleanup_worktree(spec_id, args[0])
        cleanup_preview(spec_id, args[0])
        return 0

    if command == "archive":
        from .plan import archive

        dest = archive()
        print(f"Archived: {dest}")
        return 0

    print(f"Unknown command: {command}", file=sys.stderr)
    _print_usage()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
