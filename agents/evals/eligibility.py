"""The catalogue's eligibility sweep: which matplotlib and seaborn files the agent network can adapt at all.

Spike X reports, besides the adaptation matrix, post-normaliser eligibility under the
SECURITY profile and the files blocked for a missing `THEME` block or a non-literal
savefig target. This module answers that without a model call or a render. Run it
from the repository root:

    uv run --extra agents python -m agents.evals.eligibility
    uv run --extra agents python -m agents.evals.eligibility --out agents/evals/reports/spike-x

For every `plots/<spec>/implementations/python/{matplotlib,seaborn}.py` it does what
`POST /v1/sessions` does with a catalogue snapshot (`opening.assess`): strip the
`# noqa` comments, normalise, and run the readiness scan, which applies the SECURITY
validator, the `THEME` and savefig-target checks and the map-spec rule. It counts the
pairs by status (`clean`, `coupled`, `blocked`) per library, the blocked pairs by
reason category (`security`, `no-theme`, `savefig-target`, `map-spec`, `syntax`), and
the SECURITY findings by rule id, and writes `<out>/<date>-eligibility.json` and its
Markdown table (default `agents/evals/reports/`, git-ignored). A file whose
normalisation raises counts as `error` with the exception class.

Every reason category and rule id is a fixed identifier from the scan; the report
carries no code.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[1]
DEFAULT_OUT = EVALS_DIR / "reports"
LIBRARIES: tuple[str, ...] = ("matplotlib", "seaborn")
STATUSES: tuple[str, ...] = ("clean", "coupled", "blocked", "error")
_SECURITY_RULE = re.compile(r"^security: ([a-z][a-z0-9-]*)(?: at line \d+)?:")


def reason_category(reason: str) -> str:
    """The fixed category a readiness reason starts with (`security`, `no-theme`, ...)."""
    return reason.split(":", 1)[0].strip()


def security_rule(reason: str) -> str | None:
    """The validator rule id of a `security:` reason; None for another reason or a summary line."""
    match = _SECURITY_RULE.match(reason)
    return match.group(1) if match else None


def scan_pair(code: str, *, spec_id: str, library: str) -> tuple[str, list[str]]:
    """The readiness status of one catalogue file and its reasons, as `POST /v1/sessions` sees it."""
    from agents.anyplot.code.normalise import normalise
    from agents.anyplot.code.readiness import scan
    from core.utils import strip_noqa_comments

    try:
        normalised = normalise(strip_noqa_comments(code) or "", library=library)
    except Exception as exc:  # a file the normaliser cannot take is ineligible; its class says why
        return "error", [f"normalise: {type(exc).__name__}"]
    readiness = scan(normalised, spec_id=spec_id, library=library, enabled_libraries=LIBRARIES)
    return readiness.status, list(readiness.reasons)


def sweep(plots_dir: Path, libraries: tuple[str, ...] = LIBRARIES) -> dict[str, Any]:
    """Scan every implementation of `libraries` under `plots_dir`; the counts and the blocked pairs."""
    by_library: dict[str, dict[str, Any]] = {}
    blocked: list[dict[str, Any]] = []
    for library in libraries:
        statuses: Counter[str] = Counter()
        categories: Counter[str] = Counter()
        rules: Counter[str] = Counter()
        for path in sorted(plots_dir.glob(f"*/implementations/python/{library}.py")):
            spec_id = path.parents[2].name
            status, reasons = scan_pair(path.read_text(encoding="utf-8"), spec_id=spec_id, library=library)
            statuses[status] += 1
            if status not in ("blocked", "error"):
                continue
            found = sorted({reason_category(reason) for reason in reasons})
            categories.update(found)
            rules.update({rule for reason in reasons if (rule := security_rule(reason))})
            blocked.append({"spec_id": spec_id, "library": library, "status": status, "categories": found})
        total = sum(statuses.values())
        eligible = statuses["clean"] + statuses["coupled"]
        by_library[library] = {
            "files": total,
            "statuses": {status: statuses[status] for status in STATUSES},
            "eligible": eligible,
            "eligible_rate": eligible / total if total else None,
            "blocked_by_category": dict(sorted(categories.items())),
            "security_rules": dict(sorted(rules.items())),
        }
    return {"by_library": by_library, "blocked": blocked}


def markdown(result: dict[str, Any], date: str) -> str:
    """The sweep as Markdown tables."""
    by_library = result["by_library"]
    lines = [
        f"# Catalogue eligibility {date}",
        "",
        "| Library | Files | Eligible | Clean | Coupled | Blocked | Error |",
        "|---|---|---|---|---|---|---|",
    ]
    for library, item in by_library.items():
        rate = item["eligible_rate"]
        share = f" ({rate * 100:.1f} %)" if rate is not None else ""
        counts = item["statuses"]
        lines.append(
            f"| {library} | {item['files']} | {item['eligible']}{share} | {counts['clean']} | {counts['coupled']} | "
            f"{counts['blocked']} | {counts['error']} |"
        )
    lines += ["", "Blocked files by reason (a file can have several):", ""]
    lines += ["| Reason | " + " | ".join(by_library) + " |", "|---|" + "---|" * len(by_library)]
    categories = sorted({name for item in by_library.values() for name in item["blocked_by_category"]})
    for name in categories:
        cells = " | ".join(str(item["blocked_by_category"].get(name, 0)) for item in by_library.values())
        lines.append(f"| `{name}` | {cells} |")
    rules = sorted({name for item in by_library.values() for name in item["security_rules"]})
    if rules:
        lines += ["", "SECURITY findings by rule (files with at least one):", ""]
        lines += ["| Rule | " + " | ".join(by_library) + " |", "|---|" + "---|" * len(by_library)]
        for name in rules:
            cells = " | ".join(str(item["security_rules"].get(name, 0)) for item in by_library.values())
            lines.append(f"| `{name}` | {cells} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.eligibility",
        description="Count the catalogue's matplotlib and seaborn files the agent network can adapt.",
    )
    parser.add_argument("--plots", type=Path, default=REPO_ROOT / "plots", help="the catalogue directory (plots/)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (agents/evals/reports)")
    args = parser.parse_args(argv)
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"  # importing agents.anyplot reads settings; never from a .env file
    os.environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    if not args.plots.is_dir():
        print(f"error: {args.plots} is not a directory", file=sys.stderr)
        return 2
    date = datetime.now(UTC).date().isoformat()
    result = {"date": date, "plots": str(args.plots), **sweep(args.plots)}
    text = markdown(result, date)
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / f"{date}-eligibility.json"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(text, encoding="utf-8")
    print(text)
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
