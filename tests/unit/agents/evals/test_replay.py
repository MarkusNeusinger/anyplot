"""`agents/evals/replay.py`: a promoted case replays only on the model route its sender was told about.

Every case here is invented and written to `tmp_path`; no test reads `agents/evals/.cases/`. No test calls a
model: the routes come from settings built in the test, `run_matrix` is a stand-in that records what it was handed,
and the scorer's clients fail the test when anything builds one.
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

import agents.evals.cases as cases_module
from agents.anyplot.settings import AgentSettings
from agents.evals import matrix, replay, score
from agents.evals.cases import CaseError, EvalCase, load_cases, select_cases
from agents.evals.matrix import EXIT_SETUP, MatrixConfig, base_record, build_stamp, select_for_run
from agents.evals.replay import (
    CUTOFF,
    NO_MODEL_CALL,
    SENT_AT_FORMAT,
    ReplayRefused,
    Route,
    RoutesDiffer,
    built_routes,
    check,
    checked_routes,
    earlier_case_of,
    is_pinned,
    lane_of,
    parse_sent_at,
    record_facts,
    routes_of,
)
from agents.evals.report import summarize, summary_markdown


CASE = {
    "spec_id": "scatter-basic",
    "library": "matplotlib",
    "locale": "en",
    "bindings": [{"role": "x", "column": "a"}, {"role": "y", "column": "b"}],
    "expected": "rejected",
    "tags": ["imported", "thumbs_down"],
    "source": "invented for the replay tests",
}
DATA = "a,b\n1,2\n3,4\n"
NOW = datetime(2026, 11, 19, 12, 0, 0, tzinfo=UTC)
"""The `now` of the unit checks; the paths through `matrix.main` and `score.main` use the real clock."""
ADMIN = "case-invented-admin"
"""Sent before the cut-off from the admin lane: free."""
AT = "case-invented-at"
"""Sent from the public lane at the cut-off's exact second, correcting none: free."""
BEFORE = "case-invented-before"
"""Sent from the public lane one second before the cut-off: pinned."""
CORRECTION = "case-invented-correction"
"""Sent from the public lane after the cut-off, correcting a case sent before it: pinned."""
OWNER = "case-invented-owner"
"""Sent from the public lane before the cut-off, its data marked as the operator's own: free."""
UNKNOWN = "case-invented-unknown"
"""No `sent_at`, no `lane`, no `earlier_case`, as every case imported before the fields: pinned."""
SAVED = "session-invented-saved"
"""A saved session: no manifest, so no send time, lane or correction, ever: pinned."""
FIXTURE = "scatter-basic-invented-fixture"
GEMINI = {"AGENT_PROVIDER": "gemini", "AGENT_MODEL": "gemini-3.8-flash", "AGENT_JUDGE_MODEL": "gemini-3.8-flash"}
"""The Gemini arm from the environment, without a flag."""
PINNED_ROUTES = tuple(
    Route(role, "claude-haiku-5-5", "anthropic-vertex", "vertex", "eu") for role in ("root", "adapter", "reviewer")
) + (Route("judge", "claude-haiku-5-5", "anthropic-vertex", "vertex", "eu"),)
NOT_CLAUDE = "the provider is not Claude on Vertex AI; the model is not a Claude model"
GATEWAY = "https://gateway.invalid/v1"
REAL_BUILT_ROUTES = built_routes
FRESH = {"case_id": "x", "origin": "promoted", "sent_at": "2026-11-19T00:00:00Z"}
"""A run record of a promoted case sent at the cut-off, to which a test adds what it checks."""


def write_case(root: Path, case_id: str, **fields: object) -> Path:
    directory = root / case_id
    directory.mkdir(parents=True)
    (directory / "case.json").write_text(json.dumps({**CASE, **fields}), encoding="utf-8")
    (directory / "data.csv").write_text(DATA, encoding="utf-8")
    return directory


@pytest.fixture
def on_disk(tmp_path: Path) -> list[EvalCase]:
    """One fixture and seven promoted cases, loaded from `tmp_path` as the harness loads them."""
    fixtures, promoted = tmp_path / "fixtures", tmp_path / ".cases"
    write_case(fixtures, FIXTURE, tags=["smoke"])
    write_case(promoted, ADMIN, sent_at="2026-11-02T10:00:00Z", lane="admin", earlier_case="none")
    write_case(promoted, AT, sent_at="2026-11-19T00:00:00Z", lane="public", earlier_case="none")
    write_case(promoted, BEFORE, sent_at="2026-11-18T23:59:59Z", lane="public", earlier_case="none")
    write_case(promoted, CORRECTION, sent_at="2026-11-19T06:00:00Z", lane="public", earlier_case="before_cutoff")
    write_case(promoted, OWNER, sent_at="2026-11-02T10:00:00Z", lane="public", owner_chat=True, earlier_case="none")
    write_case(promoted, UNKNOWN)
    write_case(promoted, SAVED, saved_session=True)
    return load_cases(fixtures_dir=fixtures, promoted_dir=promoted)


def by_id(cases: list[EvalCase]) -> dict[str, EvalCase]:
    return {case.case_id: case for case in cases}


class TestTheRule:
    def test_the_cut_off_second_is_free_and_the_second_before_is_pinned(self, on_disk) -> None:
        cases = by_id(on_disk)

        assert cases[BEFORE].sent_at == CUTOFF - timedelta(seconds=1)
        assert cases[AT].sent_at == CUTOFF
        assert is_pinned(cases[BEFORE], now=NOW) and not is_pinned(cases[AT], now=NOW)

    def test_a_promoted_case_without_its_fields_is_pinned(self, on_disk) -> None:
        case = by_id(on_disk)[UNKNOWN]

        assert (case.sent_at, case.lane, case.earlier_case) == (None, None, "unknown") and is_pinned(case, now=NOW)

    def test_a_send_time_later_than_now_is_no_send_time(self, on_disk) -> None:
        future = replace(by_id(on_disk)[AT], sent_at=NOW + timedelta(seconds=1))

        assert is_pinned(future, now=NOW) and not is_pinned(by_id(on_disk)[AT], now=NOW)

    def test_a_correction_of_an_old_case_is_an_old_case(self, on_disk) -> None:
        """A session lives in one page load: the correction came from a tab that showed the old consent line."""
        correction = by_id(on_disk)[CORRECTION]

        assert correction.sent_at is not None and correction.sent_at >= CUTOFF
        assert correction.earlier_case == "before_cutoff" and is_pinned(correction, now=NOW)
        assert not is_pinned(replace(correction, earlier_case="after_cutoff"), now=NOW)
        assert is_pinned(replace(correction, earlier_case="unknown"), now=NOW)
        assert not is_pinned(replace(correction, earlier_case="none"), now=NOW)
        assert is_pinned(replace(correction, earlier_case="other"), now=NOW)  # outside the vocabulary pins

    def test_the_admin_lane_frees_a_case_whenever_it_was_sent(self, on_disk) -> None:
        case = by_id(on_disk)[ADMIN]

        assert case.lane == "admin" and case.sent_at is not None and case.sent_at < CUTOFF
        assert not is_pinned(case, now=NOW) and not is_pinned(replace(case, earlier_case="unknown"), now=NOW)

    def test_the_owner_mark_frees_a_case_whenever_it_was_sent(self, on_disk) -> None:
        case = by_id(on_disk)[OWNER]

        assert case.owner_chat is True and case.lane == "public" and case.sent_at is not None
        assert case.sent_at < CUTOFF and not is_pinned(case, now=NOW)

    def test_a_saved_session_is_pinned(self, on_disk) -> None:
        case = by_id(on_disk)[SAVED]

        assert case.saved_session and is_pinned(case, now=NOW)

    def test_a_fixture_is_never_pinned(self, on_disk) -> None:
        assert by_id(on_disk)[FIXTURE].origin == "fixtures"
        assert not is_pinned(by_id(on_disk)[FIXTURE], now=NOW)

    @pytest.mark.parametrize(
        ("record", "pinned"),
        [
            ({"case_id": "x"}, True),  # defensive: no origin
            ({"case_id": "x", "origin": "promoted"}, True),  # a promoted run of a report from before the rule
            ({**FRESH, "sent_at": "2026-11-18T23:59:59Z", "earlier_case": "none"}, True),
            ({**FRESH, "earlier_case": "none"}, False),
            (FRESH, True),  # no earlier_case: unknown
            ({**FRESH, "earlier_case": "before_cutoff"}, True),
            ({**FRESH, "earlier_case": "after_cutoff"}, False),
            ({**FRESH, "earlier_case": "2026-11-18"}, True),  # outside the vocabulary
            ({"case_id": "x", "origin": "promoted", "sent_at": "2026-11-19T00:00:00+00:00"}, True),  # not the form
            ({"case_id": "x", "origin": "promoted", "owner_chat": True}, False),
            ({"case_id": "x", "origin": "promoted", "owner_chat": "true"}, True),  # exactly true, nothing else
            ({"case_id": "x", "origin": "promoted", "lane": "admin"}, False),
            ({"case_id": "x", "origin": "promoted", "lane": "public"}, True),
            ({"case_id": "x", "origin": "promoted", "lane": "Admin"}, True),  # a closed value, nothing like it
            ({"case_id": "x", "origin": "fixtures"}, False),  # an older report's fixture runs are free
            ({"case_id": "x", "origin": "Fixtures"}, True),
        ],
    )
    def test_a_run_record_fails_closed(self, record, pinned) -> None:
        assert is_pinned(record_facts(record), now=NOW) is pinned

    def test_a_kept_record_carries_its_cases_pin(self, on_disk) -> None:
        """`--keep-attempts` keeps a case's renders, code and data; the record beside them decides as the case did."""
        for case in on_disk:
            record = base_record(case, 1)
            facts = (record["origin"], record["lane"], record["owner_chat"], record["saved_session"])
            assert facts == (case.origin, case.lane, case.owner_chat, case.saved_session)
            assert is_pinned(record_facts(record), now=NOW) is is_pinned(case, now=NOW), case.case_id
        assert base_record(by_id(on_disk)[BEFORE], 1)["sent_at"] == "2026-11-18T23:59:59Z"
        assert base_record(by_id(on_disk)[CORRECTION], 1)["earlier_case"] == "before_cutoff"
        assert base_record(by_id(on_disk)[UNKNOWN], 1)["earlier_case"] == "unknown"
        assert base_record(by_id(on_disk)[FIXTURE], 1)["sent_at"] is None

    def test_the_send_time_has_the_manifests_form(self) -> None:
        from core.agent_cases import _CREATED_AT_FORMAT

        assert SENT_AT_FORMAT == _CREATED_AT_FORMAT

    @pytest.mark.parametrize(
        "value",
        [
            "2026-11-19t00:00:00z",  # lower case
            "2026-1-9T0:0:0Z",  # unpadded
            "２０２６-11-19T00:00:00Z",  # full-width digits
            "2026-11-19T00:00:00Z\n",
            " 2026-11-19T00:00:00Z",
            "2026-11-19T00:00:00+00:00",
            "2026-11-19T00:00:00",
            "2026-11-18T23:59:60Z",
            1795000000,
        ],
    )
    def test_a_send_time_is_the_exact_form_in_ascii_digits(self, value) -> None:
        with pytest.raises(ValueError):
            parse_sent_at(value)

    @pytest.mark.parametrize(
        ("replaces", "code"),
        [
            (None, "none"),
            ("20261118T235959Z-0a1b2c3d", "before_cutoff"),
            ("20261119T000000Z-0a1b2c3d", "after_cutoff"),  # the cut-off's own second
            ("20261118T080000Z-0A1B2C3D", "unknown"),  # not the id's form
            ("20261318T080000Z-0a1b2c3d", "unknown"),  # month 13: no time
            ("20261118T080000Z", "unknown"),
            ("2026-11-18T08:00:00Z", "unknown"),
            (17, "unknown"),
        ],
    )
    def test_the_earlier_case_is_a_closed_code_by_the_side_of_the_cut_off(self, replaces, code) -> None:
        assert earlier_case_of(replaces) == code


def replace(case: EvalCase, **fields: object) -> EvalCase:
    from dataclasses import replace as dataclass_replace

    return dataclass_replace(case, **fields)


class TestTheLane:
    @pytest.mark.parametrize(
        ("user_hash", "lane"),
        [
            ("adm_0123456789abcdef", "admin"),
            ("pub_0123456789abcdef", "public"),
            ("adm_0123456789abcde", None),  # one digit short
            ("adm_0123456789abcdef0", None),  # one digit long
            ("adm_0123456789ABCDEF", None),  # the BFF writes lower-case hex
            ("adm_", None),
            (" adm_0123456789abcdef", None),
            ("0123456789abcdef", None),  # a bare hash, as no lane has written one
            ("", None),
            (None, None),
            (17, None),
        ],
    )
    def test_only_the_exact_form_of_a_lane_names_it(self, user_hash, lane) -> None:
        assert lane_of(user_hash) == lane


class TestTheRoute:
    @pytest.mark.parametrize(
        ("route", "keeps"),
        [
            (Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "eu"), True),
            # The pin is the provider, the transport and the location the consent named, not a model id.
            (Route("scorer", "claude-opus-5-5", "anthropic-vertex", "vertex", "eu"), True),
            (Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "global"), False),
            (Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "us"), False),
            (Route("scorer", "claude-opus-5-5", "anthropic-vertex", "vertex", "europe-west4"), False),
            (Route("root", "gemini-3.8-flash", "gemini", "vertex", "eu"), False),
            (Route("judge", "gemini-3.5-flash-lite", "anthropic-vertex", "vertex", "eu"), False),
            (Route("adapter", "claude-haiku-5-5", "anthropic-vertex", "claude-cli", "eu"), False),
            (Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "eu", "ANTHROPIC_VERTEX_BASE_URL"), False),
        ],
    )
    def test_only_claude_on_vertex_ai_in_eu_keeps_the_pin(self, route, keeps) -> None:
        assert route.keeps_pin is keeps

    def test_each_departure_is_named(self) -> None:
        everything = Route("r", "gemini-3.8-flash", "gemini", "claude-cli", "us", "ANTHROPIC_VERTEX_BASE_URL")
        assert everything.departures() == [
            "the provider is not Claude on Vertex AI",
            "the model is not a Claude model",
            "the transport is not Vertex AI",
            "the location is not eu",
            "ANTHROPIC_VERTEX_BASE_URL sends the calls to another endpoint",
        ]
        assert PINNED_ROUTES[0].departures() == []


class TestTheCheck:
    def test_a_run_on_the_pinned_route_says_nothing(self, on_disk) -> None:
        assert check(on_disk, PINNED_ROUTES, now=NOW) is None

    def test_a_claude_run_with_a_gemini_judge_is_refused(self, on_disk) -> None:
        judge = Route("judge", "gemini-3.5-flash-lite", "gemini", "vertex", "eu")

        with pytest.raises(ReplayRefused) as refused:
            check(on_disk, (*PINNED_ROUTES[:3], judge), now=NOW)

        assert [case.case_id for case in refused.value.cases] == [BEFORE, CORRECTION, UNKNOWN, SAVED]
        assert refused.value.routes == (judge,)

    @pytest.mark.parametrize(
        "route",
        [
            Route("root", "gemini-3.8-flash", "gemini", "vertex", "eu"),
            Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "global"),
            Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "us"),
            Route("adapter", "claude-sonnet-5-5", "anthropic-vertex", "claude-cli", "eu"),
            Route("root", "claude-haiku-5-5", "anthropic-vertex", "vertex", "eu", "ANTHROPIC_VERTEX_BASE_URL"),
        ],
    )
    def test_the_free_cases_run_on_every_route(self, on_disk, route) -> None:
        free = [case for case in on_disk if case.case_id in (FIXTURE, ADMIN, AT, OWNER)]

        assert check(free, [route], now=NOW) is None

    def test_a_caller_without_a_model_holds_every_case_and_an_empty_list_is_no_such_caller(self, on_disk) -> None:
        assert check(on_disk, NO_MODEL_CALL) is None
        with pytest.raises(ValueError, match="NO_MODEL_CALL"):
            check(on_disk, ())

    def test_the_message_names_each_case_the_pin_and_the_runs_route(self, on_disk) -> None:
        judge = Route("judge", "gemini-3.5-flash-lite", "gemini", "vertex", "eu")
        selected = [case for case in on_disk if case.case_id != SAVED]

        with pytest.raises(ReplayRefused) as refused:
            check(selected, (*PINNED_ROUTES[:3], judge), now=NOW)

        assert str(refused.value) == (
            "3 pinned eval cases may replay only on Claude by Anthropic through Vertex AI in location eu, and this "
            "run would send them elsewhere.\n"
            "A promoted case sent before 2026-11-19T00:00:00Z, or without a recorded send time, keeps to the route "
            "its sender was told about, and so does a correction of such a case, unless it comes from the admin lane "
            "or you marked its data as your own.\n"
            "  case-invented-before: sent 2026-11-18T23:59:59Z, from the public lane.\n"
            "  case-invented-correction: sent 2026-11-19T06:00:00Z, from the public lane, it follows a case sent "
            "before the cut-off.\n"
            "  case-invented-unknown: no send time recorded, no lane recorded, no readable record of whether it "
            "corrects an earlier case.\n"
            "This run resolved this model call to another route:\n"
            f"  judge gemini-3.5-flash-lite: provider gemini, transport vertex, location eu ({NOT_CLAUDE}).\n"
            "Run on the pinned route (provider anthropic-vertex, transport vertex, location eu, a claude-* model, no "
            "endpoint override), or pass --skip-pinned to leave the pinned cases out.\n"
            "A stored case imported before these fields existed gets them when you import it again: python -m "
            "agents.evals.sync_cases --force, or python -m agents.evals.import_case <case directory> --force; a "
            "report gets them from a new matrix run."
        )
        assert refused.value.left_out() == (
            "left out 3 pinned eval cases (--skip-pinned), which replay only on Claude by Anthropic through Vertex AI "
            "in location eu: case-invented-before, case-invented-correction, case-invented-unknown"
        )

    def test_a_saved_session_says_so_and_gets_no_import_hint(self, on_disk) -> None:
        """Importing a saved session again changes nothing: it has no manifest to read the fields from."""
        with pytest.raises(ReplayRefused) as refused:
            check([by_id(on_disk)[SAVED]], [Route("root", "gemini-3.8-flash", "gemini", "vertex", "eu")], now=NOW)

        text = str(refused.value)
        assert f"  {SAVED}: a saved session, which records no send time and no lane.\n" in text
        assert "import it again" not in text

    def test_one_case_of_a_known_lane_and_time_reads_in_the_singular_without_the_import_hint(self, on_disk) -> None:
        routes = [Route(role, "claude-haiku-5-5", "anthropic-vertex", "vertex", "global") for role in ("root", "judge")]

        with pytest.raises(ReplayRefused) as refused:
            check([by_id(on_disk)[BEFORE]], routes, now=NOW)

        text = str(refused.value)
        assert text.startswith("1 pinned eval case may replay only on Claude by Anthropic through Vertex AI in")
        assert "would send it elsewhere." in text and "these model calls" in text
        where = "provider anthropic-vertex, transport vertex, location global (the location is not eu)."
        assert f"  root claude-haiku-5-5: {where}" in text and f"  judge claude-haiku-5-5: {where}" in text
        assert "import it again" not in text
        assert refused.value.left_out().startswith("left out 1 pinned eval case (--skip-pinned), which")

    def test_a_case_listed_twice_is_named_once(self, on_disk) -> None:
        case = by_id(on_disk)[BEFORE]

        assert [item.case_id for item in ReplayRefused([case, case], PINNED_ROUTES).cases] == [BEFORE]


class TestTheRoutesARunResolves:
    """`routes_of` reads the settings the agents are built from; `development_env` clears every `AGENT_*` first."""

    def test_the_defaults_keep_the_pin(self) -> None:
        routes = routes_of(AgentSettings(), environ={})

        assert [route.role for route in routes] == ["root", "adapter", "reviewer", "judge"]
        assert routes == PINNED_ROUTES

    @pytest.mark.parametrize(
        ("environment", "field", "value"),
        [
            ({"AGENT_LOCATION": "global"}, "location", "global"),
            ({"AGENT_LOCATION": "us"}, "location", "us"),
            (GEMINI, "provider", "gemini"),
        ],
    )
    def test_the_environment_decides_where_no_flag_does(self, monkeypatch, environment, field, value) -> None:
        for name, setting in environment.items():
            monkeypatch.setenv(name, setting)

        routes = routes_of(AgentSettings(), environ={})

        assert {getattr(route, field) for route in routes} == {value}
        assert not any(route.keeps_pin for route in routes)

    def test_on_the_cli_each_role_takes_its_own_route_and_the_run_is_refused(self, monkeypatch, on_disk) -> None:
        """The CLI hands the root's chat to Vertex AI and answers every other call itself (`cli_transport`)."""
        monkeypatch.setenv("AGENT_TRANSPORT", "claude-cli")

        routes = {route.role: route for route in routes_of(AgentSettings(), environ={})}

        assert routes["root"].transport == "vertex" and routes["root"].keeps_pin
        assert {role: routes[role].transport for role in ("adapter", "reviewer", "judge")} == dict.fromkeys(
            ("adapter", "reviewer", "judge"), "claude-cli"
        )
        with pytest.raises(ReplayRefused) as refused:
            check(on_disk, tuple(routes.values()), now=NOW)
        assert [route.role for route in refused.value.routes] == ["adapter", "reviewer", "judge"]
        line = "  adapter claude-haiku-5-5: provider anthropic-vertex, transport claude-cli, location eu"
        assert f"{line} (the transport is not Vertex AI).\n" in str(refused.value)

    def test_an_experiments_adapter_model_is_the_adapters_route(self, monkeypatch) -> None:
        monkeypatch.setenv("AGENT_TRANSPORT", "claude-cli")
        monkeypatch.setenv("AGENT_ADAPTER_MODEL", "claude-sonnet-5-5")

        routes = {route.role: route for route in routes_of(AgentSettings(), environ={})}

        assert (routes["adapter"].model, routes["root"].model) == ("claude-sonnet-5-5", "claude-haiku-5-5")

    def test_an_endpoint_override_takes_every_claude_call_off_the_pin(self) -> None:
        """The Claude-on-Vertex client takes `ANTHROPIC_VERTEX_BASE_URL` ahead of the region it is given."""
        routes = routes_of(AgentSettings(), environ={"ANTHROPIC_VERTEX_BASE_URL": GATEWAY})

        assert {route.endpoint for route in routes} == {"ANTHROPIC_VERTEX_BASE_URL"}
        assert not any(route.keeps_pin for route in routes)
        assert routes_of(AgentSettings(), environ={"ANTHROPIC_VERTEX_BASE_URL": "  "}) == PINNED_ROUTES

    def test_a_gemini_judge_on_claude_is_refused_by_the_settings_and_by_the_route(self) -> None:
        """The settings refuse the mix today; the route still checks each model's family, should they ever allow it."""
        with pytest.raises(ValidationError, match="does not match AGENT_PROVIDER"):
            AgentSettings(judge_model="gemini-3.5-flash-lite")

        defaults = AgentSettings().model_dump()
        mixed = AgentSettings.model_construct(**{**defaults, "judge_model": "gemini-3.5-flash-lite"})
        (judge,) = [route for route in routes_of(mixed, environ={}) if not route.keeps_pin]
        assert (judge.role, judge.model) == ("judge", "gemini-3.5-flash-lite")
        assert judge.departures() == ["the model is not a Claude model"]


class TestTheAgentsAsBuilt:
    """This test process built its agents when it first imported `agents.anyplot`, on the default settings."""

    def test_the_built_agents_are_read_as_routes(self) -> None:
        routes = built_routes(environ={})

        assert {route.role for route in routes} == {"root", "adapter", "reviewer"}
        assert {(route.model, route.provider, route.transport, route.location) for route in routes} == {
            ("claude-haiku-5-5", "anthropic-vertex", "vertex", "eu")
        }

    def test_settings_that_match_the_built_agents_pass(self) -> None:
        assert checked_routes(AgentSettings(), environ={}) == PINNED_ROUTES

    def test_settings_other_than_the_built_agents_stop_the_check(self) -> None:
        with pytest.raises(RoutesDiffer) as differ:
            checked_routes(AgentSettings(location="global"), environ={})

        text = str(differ.value)
        assert text.startswith("the agents were built for another configuration than the one this run checked")
        built = "built root claude-haiku-5-5: provider anthropic-vertex, transport vertex, location eu"
        checked = "checked root claude-haiku-5-5: provider anthropic-vertex, transport vertex, location global"
        assert f"  {built}; {checked}.\n" in text


class TestTheSelection:
    def test_a_selected_pinned_case_stops_the_selection(self, on_disk) -> None:
        routes = routes_of(AgentSettings(location="global"), environ={})

        with pytest.raises(ReplayRefused):
            select_cases(on_disk, "case-*", routes=routes)
        selected = select_cases(on_disk, f"{ADMIN},{AT},{OWNER}", routes=routes)
        assert [case.case_id for case in selected] == [ADMIN, AT, OWNER]

    def test_a_pinned_case_that_is_not_selected_stops_nothing(self, on_disk) -> None:
        settings = AgentSettings(provider="gemini", model="gemini-3.8-flash", judge_model="gemini-3.8-flash")

        assert [case.case_id for case in select_cases(on_disk, "smoke", routes=routes_of(settings))] == [FIXTURE]

    def test_a_malformed_send_time_stops_the_load(self, tmp_path) -> None:
        write_case(tmp_path / ".cases", "case-invented-naive", sent_at="2026-11-18T23:59:59")

        with pytest.raises(CaseError, match="sent_at must be a UTC time"):
            load_cases(fixtures_dir=tmp_path / "none", promoted_dir=tmp_path / ".cases")


@pytest.fixture
def stand_in_run(monkeypatch, on_disk) -> list[tuple[list[EvalCase], MatrixConfig]]:
    """`matrix.main` over the invented cases, with `run_matrix` replaced: the stand-in records what it was handed and
    stops the run, so the test sees whether a run would have started, and no test reaches the preflight or a model.

    The built agents count as built from the run's own settings, as in a fresh `python -m agents.evals.matrix`
    process; `TestTheMatrix.test_agents_built_for_other_settings_stop_the_run` takes this out."""
    handed: list[tuple[list[EvalCase], MatrixConfig]] = []

    async def stand_in(cases: list[EvalCase], config: MatrixConfig) -> None:
        handed.append((cases, config))
        raise matrix.SetupError("stand-in run")

    monkeypatch.setattr(cases_module, "load_cases", lambda: on_disk)
    monkeypatch.setattr(matrix, "run_matrix", stand_in)
    monkeypatch.setattr(replay, "built_routes", lambda environ=None: ())
    return handed


def run_main(tmp_path: Path, *flags: str, cases: str = "case-*") -> int:
    with patch.dict(os.environ):  # `configure` writes the flags into the process environment
        return matrix.main(
            ["--cases", cases, "--renderer", "fake", "--no-baseline", "--out", str(tmp_path / "out"), *flags]
        )


class TestTheMatrix:
    CLAUDE = "claude-haiku-5-5: provider anthropic-vertex"
    GEMINI_JUDGE = "judge gemini-3.5-flash-lite: provider gemini"
    CLI = "transport claude-cli, location eu (the transport is not Vertex AI)"
    GLOBAL = "transport vertex, location global (the location is not eu)"
    GATEWAY_ROUTE = (
        "transport vertex, location eu, endpoint from ANTHROPIC_VERTEX_BASE_URL (ANTHROPIC_VERTEX_BASE_URL sends the "
        "calls to another endpoint)"
    )

    @pytest.mark.parametrize(
        ("flags", "environment", "route"),
        [
            (["--location", "global"], {}, f"root {CLAUDE}, {GLOBAL}"),
            (["--location", "us"], {}, f"judge {CLAUDE}, transport vertex, location us (the location is not eu)"),
            (["--provider", "gemini"], {}, f"{GEMINI_JUDGE}, transport vertex, location eu ({NOT_CLAUDE})"),
            ([], {"AGENT_LOCATION": "global"}, f"adapter {CLAUDE}, {GLOBAL}"),
            ([], {"AGENT_TRANSPORT": "claude-cli"}, f"reviewer {CLAUDE}, {CLI}"),
            ([], GEMINI, f"root gemini-3.8-flash: provider gemini, transport vertex, location eu ({NOT_CLAUDE})"),
            ([], {"ANTHROPIC_VERTEX_BASE_URL": GATEWAY}, f"root {CLAUDE}, {GATEWAY_ROUTE}"),
        ],
    )
    def test_a_run_that_would_send_a_pinned_case_elsewhere_never_starts(
        self, tmp_path, monkeypatch, capsys, stand_in_run, flags, environment, route
    ) -> None:
        for name, value in environment.items():
            monkeypatch.setenv(name, value)

        assert run_main(tmp_path, *flags) == EXIT_SETUP

        assert stand_in_run == []  # no preflight, no case, no model call
        err = capsys.readouterr().err
        assert err.startswith(
            "setup: 3 pinned eval cases may replay only on Claude by Anthropic through Vertex AI in location eu"
        ), err
        assert f"  {BEFORE}: sent 2026-11-18T23:59:59Z, from the public lane.\n" in err
        correction = f"  {CORRECTION}: sent 2026-11-19T06:00:00Z, from the public lane, it follows a case sent before"
        assert f"{correction} the cut-off.\n" in err
        assert f"  {route}" in err
        assert not (tmp_path / "out").exists()

    def test_agents_built_for_other_settings_stop_the_run(self, tmp_path, monkeypatch, capsys, stand_in_run) -> None:
        """This process built its agents on `eu`; a run checked on `global` would be about models it does not call."""
        monkeypatch.setattr(replay, "built_routes", REAL_BUILT_ROUTES)

        assert run_main(tmp_path, "--location", "global", cases=FIXTURE) == EXIT_SETUP

        assert stand_in_run == []
        err = capsys.readouterr().err
        assert "setup: the agents were built for another configuration than the one this run checked" in err
        assert "Start the run in a fresh process" in err

    def test_a_run_on_the_pinned_route_starts_and_says_nothing_new(self, tmp_path, capsys, stand_in_run) -> None:
        assert run_main(tmp_path, "--provider", "anthropic-vertex", "--location", "eu") == EXIT_SETUP

        ((cases, config),) = stand_in_run
        assert [case.case_id for case in cases] == [ADMIN, AT, BEFORE, CORRECTION, OWNER, UNKNOWN]
        assert config.pinned_left_out == 0
        assert capsys.readouterr().err == "setup: stand-in run\n"  # the stand-in's own stop, and nothing else

    def test_skip_pinned_runs_the_rest_names_what_it_left_out_on_stderr_and_counts_it(
        self, tmp_path, capsys, stand_in_run
    ) -> None:
        assert run_main(tmp_path, "--location", "global", "--skip-pinned") == EXIT_SETUP

        ((cases, config),) = stand_in_run
        assert [case.case_id for case in cases] == [ADMIN, AT, OWNER]
        assert config.pinned_left_out == 3
        line = (
            "left out 3 pinned eval cases (--skip-pinned), which replay only on Claude by Anthropic through Vertex AI "
            f"in location eu: {BEFORE}, {CORRECTION}, {UNKNOWN}\n"
        )
        assert line in capsys.readouterr().err
        stamp = build_stamp(AgentSettings(location="global"), config, cases, datetime.now(UTC))
        assert stamp["pinned_left_out"] == 3
        page = summary_markdown({"schema": 2, "stamp": stamp, "summary": summarize([]), "runs": []})
        assert "**Left out:** 3 pinned promoted cases (`--skip-pinned`)" in page
        assert not any(case_id in page or case_id in json.dumps(stamp) for case_id in (BEFORE, CORRECTION, UNKNOWN))
        one = summary_markdown(
            {"schema": 2, "stamp": {**stamp, "pinned_left_out": 1}, "summary": summarize([]), "runs": []}
        )
        assert "**Left out:** 1 pinned promoted case (`--skip-pinned`)" in one

    def test_skip_pinned_that_leaves_every_selected_case_out_says_so(self, on_disk, monkeypatch) -> None:
        monkeypatch.setattr(replay, "built_routes", lambda environ=None: ())
        pinned_only = [case for case in on_disk if case.case_id in (BEFORE, UNKNOWN)]

        with pytest.raises(matrix.SetupError, match=r"--skip-pinned left out every case --cases 'case-\*' selects"):
            select_for_run(
                "case-*", AgentSettings(location="us"), skip_pinned=True, load=lambda: pinned_only, echo=lambda _: None
            )

    def test_the_static_stage_calls_no_model_and_holds_every_case(self, tmp_path, capsys, stand_in_run) -> None:
        code = run_main(tmp_path, "--static", "--location", "global")

        assert code != EXIT_SETUP, capsys.readouterr().err
        assert "may replay only on" not in capsys.readouterr().err


def score_report(tmp_path: Path, *records: dict) -> Path:
    """A matrix report of runs with kept attempts, as `--keep-attempts` writes it; the kept files are not needed,
    because the scorer decides before it reads one."""
    entry = {"turn": "t1", "render": 1, "theme": "light", "png": "a/r.png", "code": "a/r.py.txt", "data": "a/r.csv"}
    runs = [
        {"repeat": 1, "spec_id": "scatter-basic", "library": "matplotlib", "status": "ok", "attempt_renders": [entry]}
        | record
        for record in records
    ]
    path = tmp_path / "2026-11-19-claude-haiku-5-5.json"
    path.write_text(json.dumps({"schema": 2, "runs": runs}), encoding="utf-8")
    return path


@pytest.fixture
def no_scorer_client(monkeypatch) -> None:
    """Any scoring client the scorer builds fails the test: the check comes before the probe. The scorer's case
    lookup sees no case, so even a scorer that skipped the check never reads `agents/evals/.cases/`."""

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the scorer built a model client")

    monkeypatch.setattr("agents.anyplot.models.make_anthropic_client", refuse)
    monkeypatch.setattr("agents.anyplot.cli_transport.ClaudeCliClient", refuse)
    monkeypatch.setattr(cases_module, "load_named", lambda *args, **kwargs: {})


class TestTheScorer:
    PINNED = {
        "case_id": BEFORE,
        "origin": "promoted",
        "sent_at": "2026-11-18T23:59:59Z",
        "lane": "public",
        "earlier_case": "none",
    }
    FREE = {
        "case_id": AT,
        "origin": "promoted",
        "sent_at": "2026-11-19T00:00:00Z",
        "lane": "public",
        "earlier_case": "none",
    }
    OLD = {"case_id": UNKNOWN, "origin": "promoted"}
    """A promoted run of a report from before the rule: `origin` (since #12116), and nothing the rule reads."""
    ORPHAN = {"case_id": "case-invented-orphan"}
    """Defensive: a record with no origin at all, as no report writes one."""
    OWNED = {"case_id": OWNER, "origin": "promoted", "sent_at": "2026-11-02T10:00:00Z", "owner_chat": True}
    ADMINS = {"case_id": ADMIN, "origin": "promoted", "sent_at": "2026-11-02T10:00:00Z", "lane": "admin"}
    FIXED = {"case_id": FIXTURE, "origin": "fixtures", "sent_at": None, "lane": None, "owner_chat": False}

    def test_a_pinned_record_on_another_location_stops_before_the_probe(
        self, tmp_path, capsys, no_scorer_client
    ) -> None:
        report = score_report(tmp_path, self.PINNED, self.FREE, self.ADMINS, self.FIXED)

        assert score.main([str(report), "--location", "global"]) == 2

        err = capsys.readouterr().err
        assert err.startswith("refused: 1 pinned eval case may replay only on Claude by Anthropic through Vertex AI in")
        assert f"  {BEFORE}: sent 2026-11-18T23:59:59Z, from the public lane.\n" in err
        assert (
            "  scorer claude-opus-5-5: provider anthropic-vertex, transport vertex, location global "
            "(the location is not eu).\n"
        ) in err

    def test_an_endpoint_override_stops_the_scorer_on_its_default_route(
        self, tmp_path, capsys, monkeypatch, no_scorer_client
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_VERTEX_BASE_URL", GATEWAY)

        assert score.main([str(score_report(tmp_path, self.PINNED))]) == 2

        assert "(ANTHROPIC_VERTEX_BASE_URL sends the calls to another endpoint)." in capsys.readouterr().err

    def test_a_report_from_before_the_rule_pins_its_promoted_runs(self, tmp_path, capsys, no_scorer_client) -> None:
        report = score_report(tmp_path, self.OLD, self.ORPHAN, self.FIXED)

        assert score.main([str(report), "--transport", "claude-cli"]) == 2

        err = capsys.readouterr().err
        assert err.startswith("refused: 2 pinned eval cases")
        assert f"  {UNKNOWN}: no send time recorded, no lane recorded, no readable record of whether it" in err
        assert "  case-invented-orphan: its origin is not recorded.\n" in err
        assert FIXTURE not in err  # an older report's fixture runs are free
        assert "transport claude-cli, location eu (the transport is not Vertex AI)." in err
        assert "a report gets them from a new matrix run" in err

    def test_skip_pinned_with_nothing_left_scores_nothing(self, tmp_path, capsys, no_scorer_client) -> None:
        report = score_report(tmp_path, self.PINNED, self.OLD)

        assert score.main([str(report), "--location", "us", "--skip-pinned"]) == 2

        err = capsys.readouterr().err
        assert "left out 2 pinned eval cases (--skip-pinned), which replay only on Claude by Anthropic through " in err
        assert err.endswith("--skip-pinned left out every run, so nothing is left to score\n")

    def test_the_default_scorer_keeps_the_pin(self, tmp_path) -> None:
        args = score.parse_args([str(score_report(tmp_path, self.PINNED))])

        assert score.scorer_route(args).keeps_pin

    def test_the_free_records_score_anywhere_and_skip_pinned_leaves_the_rest_out(self, tmp_path, capsys) -> None:
        records = [self.PINNED, self.FREE, self.OLD, self.OWNED, self.ADMINS, self.FIXED, {**self.PINNED, "repeat": 2}]
        route = Route("scorer", "claude-opus-5-5", "anthropic-vertex", "claude-cli", "eu")

        kept, left_out = score.admit(records, route, skip_pinned=True)

        assert [record["case_id"] for record in kept] == [AT, OWNER, ADMIN, FIXTURE]
        assert left_out == 2
        assert "left out 2 pinned eval cases (--skip-pinned)" in capsys.readouterr().err
        summary = {**score.summarize([], [], "claude-opus-5-5"), "pinned_left_out": left_out}
        page = score.markdown(summary)
        assert "Left out: 2 pinned promoted cases (--skip-pinned)" in page and BEFORE not in page
        assert "Left out: 1 pinned promoted case (--skip-pinned)" in score.markdown({**summary, "pinned_left_out": 1})
        with pytest.raises(ReplayRefused):
            score.admit(records, route, skip_pinned=False)
        default = score.scorer_route(score.parse_args(["r.json"]))
        assert score.admit(records, default, skip_pinned=False) == (records, 0)

    def test_the_scorer_asks_only_for_the_cases_of_its_admitted_runs(
        self, tmp_path, capsys, monkeypatch, no_scorer_client
    ) -> None:
        asked: list[dict[str, str]] = []

        def named(wanted: dict[str, str]) -> dict:
            asked.append(wanted)
            return {}

        def listed(*args: object, **kwargs: object) -> None:
            raise AssertionError("the scorer listed every stored case")

        monkeypatch.setattr(cases_module, "load_named", named)
        monkeypatch.setattr(cases_module, "load_cases", listed)
        report = score_report(tmp_path, self.PINNED, self.FREE, self.FIXED)

        assert score.main([str(report), "--location", "global", "--skip-pinned", "--estimate-only"]) == 0

        assert asked == [{AT: "promoted", FIXTURE: "fixtures"}]

    def test_the_scorer_reads_only_the_cases_its_admitted_records_name(self, tmp_path, monkeypatch) -> None:
        """For the bindings, by id from the record's origin, and no other stored case: the directory is not listed."""
        promoted = tmp_path / ".cases"
        for case_id in (AT, "case-invented-other"):
            write_case(promoted, case_id, sent_at="2026-11-19T00:00:00Z", lane="public", earlier_case="none")
        monkeypatch.setattr(cases_module.import_case, "PROMOTED_DIR", promoted)
        read: list[Path] = []
        real_load_case = cases_module.load_case

        def recorded(directory: Path, origin: str) -> EvalCase:
            read.append(directory)
            return real_load_case(directory, origin)

        monkeypatch.setattr(cases_module, "load_case", recorded)

        found = cases_module.load_named({AT: "promoted", FIXTURE: "fixtures", "case-invented-gone": "promoted"})

        assert list(found) == [AT] and read == [promoted / AT]
