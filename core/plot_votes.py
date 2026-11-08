"""Which version of a plot a 👍/👎 belongs to: the one definition the API, the debug page and the audit skill share.

A plot vote belongs to the image it was cast on. An implementation's current version began at its `updated` (the
metadata's `updated`, synced into `impls.updated`): a vote cast at that moment or later is on the current version,
one cast before it on an earlier version. A regeneration deletes nothing; the `feedback` table keeps every row, and
the earlier versions' votes stay countable as such. An implementation without an `updated` has a single version,
so every vote is on it.

Within one version, one vote counts per visitor session, the newest; the router refuses a second vote from the same
session on the same version, and a session may rate each new version once.

`feedback.created_at` and `impls.updated` are naive UTC, so both sides of every comparison are taken as naive UTC.
The SQL form of `on_current_version` is `Feedback.created_at >= naive_utc(start)`
(`core.database.repositories.FeedbackRepository`).
"""

from __future__ import annotations

from datetime import UTC, datetime


PLOT_VOTE_REACTIONS = ("thumbs_up", "thumbs_down")
"""The two reactions the plot buttons send: the only ones counted per image and version."""

VOTE_SORTS = ("thumbs_down", "thumbs_up", "total")
"""How the debug dashboard's vote list ranks the plots: by the current version's thumbs down, thumbs up, or both."""


def naive_utc(moment: datetime) -> datetime:
    """`moment` as naive UTC, the form `feedback.created_at` and `impls.updated` store; a naive value is UTC."""
    return moment.astimezone(UTC).replace(tzinfo=None) if moment.tzinfo else moment


def on_current_version(cast_at: datetime, start: datetime | None) -> bool:
    """True when a vote cast at `cast_at` is on the version that began at `start`; None: every vote is.

    Inclusive: a vote cast in the second the version began is on it."""
    return start is None or naive_utc(cast_at) >= naive_utc(start)
