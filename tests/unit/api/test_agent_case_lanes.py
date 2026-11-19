"""The two facts the eval harness's replay guard reads from a stored feedback case's `user_hash`.

`agents/evals/replay.py` treats a case whose `user_hash` has the admin lane's form as the operator's, which may
replay on any model route; every other case sent before 2026-11-19 keeps to Claude on Vertex AI in `eu`. That rests
on two facts of this API, pinned here: every user id of the admin lane, on either door, has the admin form, and the
public lane's case user never does, whatever tab id the browser sends. The prefixes are written once on the harness
side (`ADMIN_LANE_PREFIX`, `PUBLIC_LANE_PREFIX`); a change of either lane's form fails here before the guard could
read a visitor's case as the operator's. The ids below are invented.
"""

import pytest
from fastapi import Response

from agents.evals.replay import ADMIN_LANE_PREFIX, PUBLIC_LANE_PREFIX, lane_of
from api.routers.agent import AgentConfig, AgentContext, agent_context, derive_user_id
from api.routers.agent_public import PublicIdentity, public_context
from api.routers.debug import AdminIdentity


CONFIG = AgentConfig(service_url="http://agents.invalid", user_id_key=b"an invented key")


def case_user(ctx: AgentContext) -> str:
    """What the feedback route stores as the case's `user_hash` (`api/routers/agent.py`, `submit_feedback`)."""
    return ctx.case_user or ctx.user_id


@pytest.mark.parametrize(
    "identity",
    [AdminIdentity(email="someone@example.com", via="cf_access"), AdminIdentity(email=None, via="token")],
    ids=["cloudflare-access", "admin-token"],
)
def test_every_admin_case_user_has_the_admin_form(identity) -> None:
    ctx = agent_context(Response(), identity=identity, config=CONFIG)

    assert ctx.tier == "admin" and ctx.case_user is None
    assert case_user(ctx) == derive_user_id(CONFIG.user_id_key, identity)
    assert case_user(ctx).startswith(ADMIN_LANE_PREFIX) and lane_of(case_user(ctx)) == "admin"


@pytest.mark.parametrize(
    "anon_id",
    ["3f9d6c1e-8a2b-4c7d-9e0f-1a2b3c4d5e6f", "adm_0123456789abcdef0123"],
    ids=["tab-id", "tab-id-that-starts-like-an-admin-id"],
)
def test_the_public_case_user_never_has_the_admin_form(anon_id) -> None:
    """A tab id is the browser's to choose, so one that looks like an admin id must still come out public."""
    ctx = public_context(Response(), identity=PublicIdentity(anon_id=anon_id, network="198.51.100.7"), config=CONFIG)

    assert ctx.tier == "public"
    assert case_user(ctx).startswith(PUBLIC_LANE_PREFIX) and not case_user(ctx).startswith(ADMIN_LANE_PREFIX)
    assert lane_of(case_user(ctx)) == "public"
