"""The readiness scan of the JavaScript profile: can a catalogue file be adapted, and what must the adapter know?

The JavaScript counterpart of `profiles/julia/readiness.py`, with its `Readiness` result
and reason format. `scan` runs on the normalised original (`normalise.py`) and answers,
with three levels as for the other languages (owner decision of 2026-10-29):

* `blocked`, for real reasons only: one of the 13 map specs (`map-spec`), a library that
  is not enabled (`library-disabled`), code tree-sitter cannot read (`syntax`), a
  SECURITY finding (`security: <rule> at line N: ...`, the first five and a count; a URL
  in qrcode-basic's encoded text is one, `url-literal`), nothing that reads the theme
  (`no-theme`), or an orientation directive the harness would read outside a comment of
  its own (`savefig-target`). A missing marker never blocks, and neither does a MUI X 7
  import (owner decision of 2026-10-30): it is the `deprecated-api` hint.
* `coupled`: eligible, with one hint per category of `coupling.py` (`data-block`,
  `synthetic-data`, `limits`, `color-scale`, `annotations`, `statistics`, `palette`,
  `deprecated-api`), each a note of at most 300 characters that names the lines, and a
  `reasons` entry (`limits: 3 lines`).
* `clean`: both markers, column constants and nothing else to point out; the adapter
  swaps the data block.

The canvas is the harness's (`normalise.measure_canvas`), always 3200x1800 or 2400x2400,
so no `canvas:` reason appears for JavaScript.

The clean or coupled decision and the structural reasons live in `coupling.py`, which
imports nothing from `agents.*` but `treesitter.py`, `regions.py` and `allowlist.py`; this
module adds the validator and the wording.
"""

from collections.abc import Iterable

from core.spec_roles import MAP_SPECS

from ...readiness import MAX_SECURITY_REASONS, Readiness, clip_reason, format_hint
from ...treesitter import Source
from .coupling import CATEGORIES, coupling, structure_reasons
from .regions import find_regions, grammar_for
from .validate import validate_security


def scan(normalised_code: str, *, spec_id: str, enabled_libraries: Iterable[str], library: str) -> Readiness:
    """Classify the normalised original of `spec_id` in `library`; never raises."""
    blocked: list[str] = []
    if spec_id in MAP_SPECS:
        blocked.append(f"map-spec: {spec_id} is one of the 13 map specs, which need network access for geodata")
    if library not in set(enabled_libraries):
        blocked.append(f"library-disabled: {library} is not enabled")
    source = Source(normalised_code, grammar_for(library))
    regions = find_regions(source)
    structure = structure_reasons(source, regions)
    if structure and structure[0].startswith("syntax:"):
        return Readiness("blocked", [*blocked, clip_reason(structure[0])])
    blocked.extend(_security(normalised_code, library))
    blocked.extend(structure)
    if blocked:
        return Readiness("blocked", [clip_reason(reason) for reason in blocked])

    found = coupling(source, regions)
    reasons: list[str] = []
    hints: list[str] = []
    present = found.categories
    for category, prefix, advice in CATEGORIES:
        if category not in present:
            continue
        items = found.findings.get(category, [])
        if category == "data-block":
            reasons.append(f"data-block: {found.layout}")
            hints.append(clip_reason(f"{prefix} {found.layout}: {advice}"))
            continue
        if category == "synthetic-data" and found.block_synthetic and found.block is not None:
            head = f"Synthetic data generation in the // Data block at lines {found.block[0]}-{found.block[1]}"
            count = len(items) + 1
            hint = format_hint(f"{head} and at", items, advice) if items else clip_reason(f"{head}: {advice}")
        else:
            count = len(items)
            hint = format_hint(prefix, items, advice)
        reasons.append(f"{category}: {count} line{'s' if count != 1 else ''}")
        hints.append(hint)
    return Readiness("coupled" if hints else "clean", reasons, hints)


def _security(code: str, library: str) -> list[str]:
    """SECURITY findings as blocking reasons; a validator that fails blocks too."""
    try:
        findings = validate_security(code, library=library)
    except Exception as exc:  # fail closed: a crashing validator never passes code
        return [f"security: the validator failed ({type(exc).__name__})"]
    reasons = [
        clip_reason(f"security: {finding.rule} at line {finding.line}: {finding.message}")
        if finding.line is not None
        else clip_reason(f"security: {finding.rule}: {finding.message}")
        for finding in findings[:MAX_SECURITY_REASONS]
    ]
    if len(findings) > MAX_SECURITY_REASONS:
        reasons.append(f"security: {len(findings) - MAX_SECURITY_REASONS} more findings")
    return reasons
