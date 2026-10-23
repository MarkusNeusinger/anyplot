"""Text briefs of the spec and the dataset, shared by the root's tools, the adapter and the reviewer.

`spec_brief` is the spec's title, description, data roles and notes, bounded;
`profile_summary` is the dataset without a single cell (row count and typed column
names), which is all the reviewer needs; `profile_json` is the full profile (with its
at most five fenced sample rows) for the root and the adapter. No ADK import.
"""

import json
from collections.abc import Iterator, Sequence
from typing import Any

from core.spec_roles import DataRole

from .policy import fence
from .schemas import MAX_TOP_VALUES, Binding, DatasetProfile
from .session_state import SessionView


def bindings_text(bindings: Sequence[Binding]) -> str:
    """The bindings in force, one `role: column` per line in the stored order, for the root's `get_dataset_profile`."""
    return "\n".join(f"{binding.role}: {binding.column}" for binding in bindings)


MAX_BRIEF_CHARS = 4_000
MAX_DESCRIPTION_CHARS = 1_500
MAX_NOTE_CHARS = 300
MAX_SUMMARY_CHARS = 2_000
MAX_ADAPTER_PROFILE_BYTES = 16 * 1024
"""The fenced dataset profile in an adapter request, at most, in UTF-8 bytes like the root's `get_dataset_profile` limit.

Bytes, not characters: a CJK or emoji cell is three or four bytes, so a character
count would let a profile of such cells grow the request several times past the cap.
"""


MAX_COMPUTED_DESCRIPTION_CHARS = 200
"""The spec's own words for a computed role in the brief: its formula and window (review of 2026-10-15)."""


def describe_role(role: DataRole, bound: bool = False, companions: Sequence[str] = ()) -> str:
    """One role for the brief; a role the plot can compute says whether its column is bound or the code computes it.

    Owner decision of 2026-10-15, "both allowed" (`data/computed.py`): bound, the plot uses the
    column; open, the plot code computes the value from the bound data. A computed role keeps
    the spec's description, which names its formula and window (`typically 20-period`), and an
    open one computed beside bound `companions` (other computed roles of the spec with a column)
    is computed from them, so the parts agree: the bands around the bound middle band, a
    balance from the bound loads (review of 2026-10-15).
    """
    kinds = "/".join(role.kinds) if role.kinds else "any"
    name = f"{role.name}1, {role.name}2, ..." if role.variadic else role.name
    if not role.computed:
        return f"{name} ({kinds}, {'required' if role.required else 'optional'})"
    spec = _clipped(role.description, MAX_COMPUTED_DESCRIPTION_CHARS)
    described = f"; the spec: {spec}" if spec else ""
    if bound:
        return f"{name} ({kinds}, bound: use its column as it is, do not compute it{described})"
    built = (
        f"; build it on the bound {', '.join(companions)} where the spec relates them, not independently"
        if companions
        else ""
    )
    return f"{name} ({kinds}, not bound: compute it in the plot code from the bound data{built}{described})"


def _clipped(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def spec_brief(view: SessionView) -> str:
    """Title, description, data roles and notes of the session's spec, at most 4,000 characters."""
    snapshot = view.snapshot
    roles = snapshot.roles()
    bound = {binding.role for binding in view.bindings}
    lines = [f"Spec: {snapshot.title} ({snapshot.spec_id}), library {view.library}"]
    if snapshot.description:
        lines.append("Description: " + snapshot.description[:MAX_DESCRIPTION_CHARS])
    if roles:
        companions = [role.name for role in roles if role.computed and role.name in bound]
        described = [describe_role(role, role.name in bound, companions) for role in roles]
        lines.append("Data roles: " + "; ".join(described))
    for note in snapshot.notes:
        lines.append("Note: " + note[:MAX_NOTE_CHARS])
    return "\n".join(lines)[:MAX_BRIEF_CHARS]


def profile_summary(profile: DatasetProfile) -> str:
    """Row count and typed columns, without any cell."""
    columns = ", ".join(f"{json.dumps(column.name, ensure_ascii=False)} ({column.dtype})" for column in profile.columns)
    return f"{profile.rows} rows; columns: {columns}"[:MAX_SUMMARY_CHARS]


def profile_json(profile: DatasetProfile) -> str:
    """The profile as JSON, warnings left out (they name parse details, not data)."""
    return _dump(profile)


def _dump(profile: DatasetProfile, exclude: dict[str, Any] | None = None) -> str:
    """The profile JSON a model reads: no warnings, and no field without a value (a text column's `min`, `mean`, ...)."""
    return profile.model_dump_json(exclude={"warnings": True, **(exclude or {})}, exclude_none=True)


def adapter_profile(profile: DatasetProfile, limit: int = MAX_ADAPTER_PROFILE_BYTES) -> tuple[str, bool]:
    """The adapter's profile JSON: the first of `trimmed_profiles` within `limit` UTF-8 bytes, and whether it was trimmed.

    The limit applies to the version as the adapter request carries it, inside its
    `<user_data>` fence: `fence` escapes every fence tag in the data (`<user_data>`
    becomes `&lt;user_data>`), so cells full of tag text grow the profile after a check
    on the raw JSON. The last version (every column's name, type and counts) goes out
    even over the limit, because the adapter cannot bind a column it never saw; at the
    parser's 50 columns of at most 64 characters it stays far below it.
    """
    last = ("", False)
    for version in trimmed_profiles(profile):
        if len(fence("user_data", version[0]).encode("utf-8")) <= limit:
            return version
        last = version
    return last


def trimmed_profiles(profile: DatasetProfile) -> Iterator[tuple[str, bool]]:
    """The profile JSON, then ever smaller versions of it, each with whether it was trimmed.

    The order of what goes: the sample rows one by one, then the values past the
    `MAX_TOP_VALUES` most frequent of a column that lists all of its values
    (`schemas.listed_values`; `unique` still counts them), then every column's top values,
    then the ranges and the statistics (min, max, mean, median). Every version keeps
    every column name, its type and counts, so a caller with a size cap takes the first
    version that fits.
    """
    yield profile_json(profile), False
    for keep in range(len(profile.sample) - 1, -1, -1):
        yield _dump(profile.model_copy(update={"sample": profile.sample[:keep]})), True
    if any(len(column.top) > MAX_TOP_VALUES for column in profile.columns):
        short = [column.model_copy(update={"top": column.top[:MAX_TOP_VALUES]}) for column in profile.columns]
        yield _dump(profile.model_copy(update={"sample": [], "columns": short})), True
    bare = profile.model_copy(
        update={"sample": [], "columns": [column.model_copy(update={"top": []}) for column in profile.columns]}
    )
    yield _dump(bare), True
    yield _dump(bare, {"columns": {"__all__": {"min", "max", "mean", "median", "top"}}}), True
