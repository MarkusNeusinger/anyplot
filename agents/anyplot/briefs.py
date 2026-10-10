"""Text briefs of the spec and the dataset, shared by the root's tools, the adapter and the reviewer.

`spec_brief` is the spec's title, description, data roles and notes, bounded;
`profile_summary` is the dataset without a single cell (row count and typed column
names), which is all the reviewer needs; `profile_json` is the full profile (with its
at most five fenced sample rows) for the root and the adapter. No ADK import.
"""

import json
from collections.abc import Iterator

from .data.roles import DataRole
from .schemas import DatasetProfile
from .session_state import SessionView


MAX_BRIEF_CHARS = 4_000
MAX_DESCRIPTION_CHARS = 1_500
MAX_NOTE_CHARS = 300
MAX_SUMMARY_CHARS = 2_000
MAX_ADAPTER_PROFILE_CHARS = 16 * 1024
"""The dataset profile in an adapter request, at most: the root's `get_dataset_profile` result limit."""


def describe_role(role: DataRole) -> str:
    kinds = "/".join(role.kinds) if role.kinds else "any"
    name = f"{role.name}1, {role.name}2, ..." if role.variadic else role.name
    return f"{name} ({kinds}, {'required' if role.required else 'optional'})"


def spec_brief(view: SessionView) -> str:
    """Title, description, data roles and notes of the session's spec, at most 4,000 characters."""
    snapshot = view.snapshot
    roles = snapshot.roles()
    lines = [f"Spec: {snapshot.title} ({snapshot.spec_id}), library {view.library}"]
    if snapshot.description:
        lines.append("Description: " + snapshot.description[:MAX_DESCRIPTION_CHARS])
    if roles:
        lines.append("Data roles: " + "; ".join(describe_role(role) for role in roles))
    for note in snapshot.notes:
        lines.append("Note: " + note[:MAX_NOTE_CHARS])
    return "\n".join(lines)[:MAX_BRIEF_CHARS]


def profile_summary(profile: DatasetProfile) -> str:
    """Row count and typed columns, without any cell."""
    columns = ", ".join(f"{json.dumps(column.name, ensure_ascii=False)} ({column.dtype})" for column in profile.columns)
    return f"{profile.rows} rows; columns: {columns}"[:MAX_SUMMARY_CHARS]


def profile_json(profile: DatasetProfile) -> str:
    """The profile as JSON, warnings left out (they name parse details, not data)."""
    return profile.model_dump_json(exclude={"warnings"})


def adapter_profile(profile: DatasetProfile, limit: int = MAX_ADAPTER_PROFILE_CHARS) -> tuple[str, bool]:
    """The adapter's profile JSON: the first of `trimmed_profiles` within `limit` characters, and whether it was trimmed.

    The last version (every column's name, type and counts) goes out even over the
    limit, because the adapter cannot bind a column it never saw; at the parser's 50
    columns of at most 64 characters it stays far below it.
    """
    last = ("", False)
    for version in trimmed_profiles(profile):
        if len(version[0]) <= limit:
            return version
        last = version
    return last


def trimmed_profiles(profile: DatasetProfile) -> Iterator[tuple[str, bool]]:
    """The profile JSON, then ever smaller versions of it, each with whether it was trimmed.

    The order of what goes: the sample rows one by one, then every column's top values,
    then the min and max. Every version keeps every column name, its type and counts,
    so a caller with a size cap takes the first version that fits.
    """
    yield profile_json(profile), False
    for keep in range(len(profile.sample) - 1, -1, -1):
        yield profile.model_copy(update={"sample": profile.sample[:keep]}).model_dump_json(exclude={"warnings"}), True
    bare = profile.model_copy(
        update={"sample": [], "columns": [column.model_copy(update={"top": []}) for column in profile.columns]}
    )
    yield bare.model_dump_json(exclude={"warnings"}), True
    yield bare.model_dump_json(exclude={"warnings": True, "columns": {"__all__": {"min", "max", "top"}}}), True
