"""Tests for automation/gcp/budget-guard/main.py — the Vertex AI budget guard.

The guard is a deploy unit, not a package (the directory name has a hyphen and
is uploaded as is by ``gcloud run deploy --source``), so the module is loaded
from its path. ``functions_framework`` is not a repository dependency; its
``cloud_event`` decorator only registers the signature type and returns the
function unchanged, so a pass-through stub stands in for it. No test touches the
network: the Service Usage API is a fake session that records every call.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import sys
import types
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest import mock

import google.auth.credentials
import google.auth.exceptions
import pytest
import requests


MODULE_PATH = Path(__file__).resolve().parents[4] / "automation" / "gcp" / "budget-guard" / "main.py"
API = "https://serviceusage.googleapis.com/v1"
SERVICE = "aiplatform.googleapis.com"
SERVICE_NAME = f"projects/anyplot/services/{SERVICE}"
BUDGET = "anyplot Vertex AI cap"


def load_guard(env: Mapping[str, str] | None = None) -> types.ModuleType:
    """Import main.py under a unique name with a stub functions_framework and a controlled env.

    Only the two sys.modules keys this sets are restored afterwards: the module
    must be registered while it executes (``dataclass`` resolves its string
    annotations through ``sys.modules``), and the stub must not leak.
    """
    name = "vertex_budget_guard_main"
    stub = types.SimpleNamespace(cloud_event=lambda func: func)
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("BUDGET_GUARD_")}
    clean_env.update(env or {})
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved = {key: sys.modules.get(key) for key in (name, "functions_framework")}
    sys.modules.update({name: module, "functions_framework": stub})
    try:
        with mock.patch.dict(os.environ, clean_env, clear=True):
            spec.loader.exec_module(module)
    finally:
        for key, previous in saved.items():
            if previous is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = previous
    return module


guard = load_guard()


def notification(**overrides: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "budgetDisplayName": BUDGET,
        "alertThresholdExceeded": 1.0,
        "costAmount": 5.12,
        "costIntervalStart": "2026-10-01T07:00:00Z",
        "budgetAmount": 5.0,
        "budgetAmountType": "SPECIFIED_AMOUNT",
        "currencyCode": "CHF",
    }
    message.update(overrides)
    return {k: v for k, v in message.items() if v is not ...}


def event_data(payload: Any) -> dict[str, Any]:
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return {
        "message": {
            "data": base64.b64encode(raw).decode(),
            "attributes": {"billingAccountId": "01C36E-578B56-0054F8", "budgetId": "b-1", "schemaVersion": "1.0"},
            "messageId": "1",
        },
        "subscription": "projects/anyplot/subscriptions/eventarc-sub",
    }


def config(**overrides: Any) -> Any:
    values: dict[str, Any] = {"project": "anyplot", "budget_name": BUDGET, "services": (SERVICE,), "dry_run": False}
    values.update(overrides)
    return guard.Config(**values)


class FakeResponse:
    def __init__(self, status_code: int, body: Any = None, *, not_json: bool = False) -> None:
        self.status_code = status_code
        self._body = body
        self._not_json = not_json

    def json(self) -> Any:
        if self._not_json:
            raise requests.JSONDecodeError("Expecting value", "<html>", 0)
        return self._body


class FakeSession:
    """Answers GETs and POSTs from per-URL queues and records every call.

    It refuses any POST that is not a ``:disable`` — the guard must never enable.
    """

    def __init__(
        self, gets: dict[str, list[FakeResponse]] | None = None, posts: dict[str, list[FakeResponse]] | None = None
    ) -> None:
        self.gets = gets or {}
        self.posts = posts or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("GET", url, kwargs))
        return self.gets[url].pop(0)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("POST", url, kwargs))
        assert url.endswith(":disable"), f"the guard posted to a non-disable URL: {url}"
        return self.posts[url].pop(0)


def state(value: str) -> FakeResponse:
    return FakeResponse(200, {"name": SERVICE_NAME, "state": value})


def done_operation(**extra: Any) -> FakeResponse:
    return FakeResponse(200, {"name": "operations/op-1", "done": True, **extra})


def session_for_disable(*, initial_state: str = "ENABLED", post: FakeResponse | None = None) -> FakeSession:
    return FakeSession(
        gets={f"{API}/{SERVICE_NAME}": [state(initial_state)]},
        posts={f"{API}/{SERVICE_NAME}:disable": [post or done_operation()]},
    )


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def log_lines(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


# ===== decide =====


class TestDecide:
    @pytest.mark.parametrize("cost", [5.0, 5.12, 400])
    def test_cost_at_or_above_the_budget_disables(self, cost: float) -> None:
        decision = guard.decide(notification(costAmount=cost), budget_name=BUDGET)
        assert decision.disable is True
        assert decision.reason == "budget_reached"
        assert (decision.budget, decision.cost, decision.amount, decision.currency) == (BUDGET, cost, 5.0, "CHF")

    def test_cost_below_the_budget_is_a_no_op(self) -> None:
        decision = guard.decide(notification(costAmount=4.99, alertThresholdExceeded=0.8), budget_name=BUDGET)
        assert decision.disable is False
        assert decision.reason == "below_budget"
        assert decision.cost == 4.99

    def test_threshold_key_is_neither_required_nor_sufficient(self) -> None:
        # alertThresholdExceeded is absent until a threshold is crossed, and a
        # 100 % threshold with the cost still below the amount does not count.
        reached = guard.decide(notification(alertThresholdExceeded=...), budget_name=BUDGET)
        assert reached.disable is True
        below = guard.decide(notification(costAmount=4.0, alertThresholdExceeded=1.0), budget_name=BUDGET)
        assert below.disable is False

    def test_a_forecast_never_disables(self) -> None:
        message = notification(costAmount=1.0, alertThresholdExceeded=..., forecastThresholdExceeded=1.0)
        assert guard.decide(message, budget_name=BUDGET).reason == "below_budget"

    def test_other_budget_is_a_no_op_that_names_the_budget(self) -> None:
        decision = guard.decide(notification(budgetDisplayName="anyplot Cloud Run"), budget_name=BUDGET)
        assert decision.disable is False
        assert decision.reason == "other_budget"
        assert decision.budget == "anyplot Cloud Run"
        assert decision.cost is None

    def test_budget_name_must_match_exactly(self) -> None:
        for name in ("anyplot vertex ai cap", f"{BUDGET} ", f"{BUDGET} 30"):
            assert guard.decide(notification(budgetDisplayName=name), budget_name=BUDGET).reason == "other_budget"

    @pytest.mark.parametrize("value", [..., None, 42])
    def test_missing_budget_name(self, value: Any) -> None:
        decision = guard.decide(notification(budgetDisplayName=value), budget_name=BUDGET)
        assert (decision.disable, decision.reason) == (False, "missing_budget_name")

    @pytest.mark.parametrize("value", [..., None, "5.12", True, float("nan"), float("inf")])
    def test_missing_or_invalid_cost(self, value: Any) -> None:
        decision = guard.decide(notification(costAmount=value), budget_name=BUDGET)
        assert (decision.disable, decision.reason) == (False, "invalid_cost_amount")
        assert decision.amount == 5.0

    @pytest.mark.parametrize("value", [..., None, "5", False, 0, -5.0, float("nan"), float("inf")])
    def test_missing_invalid_or_non_positive_budget_amount(self, value: Any) -> None:
        decision = guard.decide(notification(budgetAmount=value), budget_name=BUDGET)
        assert (decision.disable, decision.reason) == (False, "invalid_budget_amount")
        assert decision.cost == 5.12

    def test_empty_message(self) -> None:
        assert guard.decide({}, budget_name=BUDGET).reason == "missing_budget_name"

    @pytest.mark.parametrize("currency", ["CHF", "USD", "EUR", ..., None, 7])
    def test_currency_is_ignored(self, currency: Any) -> None:
        reached = guard.decide(notification(currencyCode=currency), budget_name=BUDGET)
        below = guard.decide(notification(currencyCode=currency, costAmount=1.0), budget_name=BUDGET)
        assert (reached.disable, below.disable) == (True, False)
        assert reached.currency == (currency if isinstance(currency, str) else None)


# ===== decode =====


class TestDecode:
    def test_decodes_base64_json(self) -> None:
        assert guard.decode_pubsub_message(event_data(notification())) == notification()

    def test_accepts_bytes_data(self) -> None:
        data = event_data(notification())
        data["message"]["data"] = data["message"]["data"].encode()
        assert guard.decode_pubsub_message(data)["costAmount"] == 5.12

    @pytest.mark.parametrize(
        ("data", "reason"),
        [
            (None, "event_without_data"),
            ("not a mapping", "event_without_data"),
            ({}, "event_without_message"),
            ({"message": "x"}, "event_without_message"),
            ({"message": {}}, "message_without_data"),
            ({"message": {"data": ""}}, "message_without_data"),
            ({"message": {"data": 5}}, "message_without_data"),
            ({"message": {"data": "!!not base64!!"}}, "invalid_base64"),
            ({"message": {"data": "Zm9vé"}}, "invalid_base64"),
        ],
    )
    def test_rejects_events_without_a_decodable_message(self, data: Any, reason: str) -> None:
        with pytest.raises(guard.MessageError, match=f"^{reason}$"):
            guard.decode_pubsub_message(data)

    @pytest.mark.parametrize(
        ("raw", "reason"),
        [(b"{not json", "invalid_json"), (b"\xff\xfe", "invalid_json"), (b"[1, 2]", "payload_not_object")],
    )
    def test_rejects_malformed_payloads(self, raw: bytes, reason: str) -> None:
        with pytest.raises(guard.MessageError, match=f"^{reason}$"):
            guard.decode_pubsub_message(event_data(raw))


# ===== configuration =====


class TestConfig:
    def test_defaults(self) -> None:
        cfg = guard.Config.from_env({})
        assert cfg == guard.Config(project="anyplot", budget_name=BUDGET, services=(SERVICE,), dry_run=False)
        assert guard.CONFIG == cfg

    def test_overrides(self) -> None:
        cfg = guard.Config.from_env(
            {
                "BUDGET_GUARD_PROJECT": "239660669828",
                "BUDGET_GUARD_BUDGET_NAME": "  test cap  ",
                "BUDGET_GUARD_SERVICES": f" {SERVICE}, ,generativelanguage.googleapis.com,{SERVICE}",
                "BUDGET_GUARD_DRY_RUN": "TRUE",
            }
        )
        assert cfg.project == "239660669828"
        assert cfg.budget_name == "test cap"
        assert cfg.services == (SERVICE, "generativelanguage.googleapis.com")
        assert cfg.dry_run is True

    @pytest.mark.parametrize(("raw", "expected"), [("1", True), ("yes", True), ("on", True), ("", False), ("0", False)])
    def test_dry_run_values(self, raw: str, expected: bool) -> None:
        assert guard.Config.from_env({"BUDGET_GUARD_DRY_RUN": raw}).dry_run is expected

    @pytest.mark.parametrize(
        "env",
        [
            {"BUDGET_GUARD_DRY_RUN": "maybe"},
            {"BUDGET_GUARD_PROJECT": "Anyplot"},
            {"BUDGET_GUARD_PROJECT": "projects/anyplot"},
            {"BUDGET_GUARD_BUDGET_NAME": "   "},
            {"BUDGET_GUARD_SERVICES": " , "},
            {"BUDGET_GUARD_SERVICES": "aiplatform"},
            {"BUDGET_GUARD_SERVICES": "aiplatform.googleapis.com/../x.googleapis.com"},
        ],
    )
    def test_invalid_values_are_refused(self, env: dict[str, str]) -> None:
        with pytest.raises(guard.ConfigError):
            guard.Config.from_env(env)

    def test_invalid_env_fails_at_import(self) -> None:
        # The deploy fails (the container cannot start) instead of the first real
        # alert. The reloaded module defines its own ConfigError class, so match
        # the ValueError base and the message.
        with pytest.raises(ValueError, match="BUDGET_GUARD_DRY_RUN must be true or false"):
            load_guard({"BUDGET_GUARD_DRY_RUN": "ture"})

    def test_env_is_read_at_import(self) -> None:
        module = load_guard({"BUDGET_GUARD_DRY_RUN": "true"})
        assert module.CONFIG.dry_run is True


# ===== Service Usage calls =====


class TestDisableService:
    def test_already_disabled_makes_no_disable_call(self) -> None:
        session = session_for_disable(initial_state="DISABLED")
        assert guard.disable_service(session, "anyplot", SERVICE) == "already_disabled"
        assert [method for method, _, _ in session.calls] == ["GET"]

    def test_disables_with_the_documented_request(self) -> None:
        session = session_for_disable()
        assert guard.disable_service(session, "anyplot", SERVICE) == "disabled"
        method, url, kwargs = session.calls[1]
        assert (method, url) == ("POST", f"{API}/{SERVICE_NAME}:disable")
        assert kwargs["json"] == {"disableDependentServices": False, "checkIfServiceHasUsage": "SKIP"}
        assert kwargs["timeout"] == guard.HTTP_TIMEOUT_S

    def test_polls_a_running_operation_until_done(self) -> None:
        session = session_for_disable(post=FakeResponse(200, {"name": "operations/op-1", "done": False}))
        session.gets[f"{API}/operations/op-1"] = [
            FakeResponse(200, {"name": "operations/op-1"}),
            done_operation(response={}),
        ]
        clock = FakeClock()
        result = guard.disable_service(session, "anyplot", SERVICE, sleep=clock.sleep, clock=clock)
        assert result == "disabled"
        assert clock.sleeps == [guard.OPERATION_POLL_INTERVAL_S] * 2

    def test_operation_still_running_at_the_deadline_is_pending(self) -> None:
        running = {"name": "operations/op-1", "done": False}
        session = session_for_disable(post=FakeResponse(200, running))
        session.gets[f"{API}/operations/op-1"] = [FakeResponse(200, running) for _ in range(10)]
        clock = FakeClock()
        result = guard.disable_service(session, "anyplot", SERVICE, sleep=clock.sleep, clock=clock, timeout_s=5)
        assert result == "disable_pending"
        assert clock.now >= 5

    @pytest.mark.parametrize(
        ("error", "text"),
        [({"code": 9, "message": "depended on by notebooks.googleapis.com"}, "notebooks"), ("boom", "boom")],
    )
    def test_failed_operation_raises(self, error: Any, text: str) -> None:
        session = session_for_disable(post=done_operation(error=error))
        with pytest.raises(guard.ServiceUsageError, match=text):
            guard.disable_service(session, "anyplot", SERVICE)

    def test_running_operation_without_a_name_raises(self) -> None:
        session = session_for_disable(post=FakeResponse(200, {"done": False}))
        with pytest.raises(guard.ServiceUsageError, match="no name"):
            guard.disable_service(session, "anyplot", SERVICE)

    def test_operation_poll_error_raises(self) -> None:
        session = session_for_disable(post=FakeResponse(200, {"name": "operations/op-1"}))
        session.gets[f"{API}/operations/op-1"] = [FakeResponse(503, {"error": {"status": "UNAVAILABLE"}})]
        clock = FakeClock()
        with pytest.raises(guard.ServiceUsageError, match="HTTP 503 UNAVAILABLE"):
            guard.disable_service(session, "anyplot", SERVICE, sleep=clock.sleep, clock=clock)

    def test_race_with_a_redelivery_counts_as_already_disabled(self) -> None:
        # Between our GET and POST a duplicate delivery disabled the service; the
        # API answers FAILED_PRECONDITION and the second GET shows DISABLED.
        rejected = FakeResponse(400, {"error": {"status": "FAILED_PRECONDITION", "message": "not enabled"}})
        session = session_for_disable(post=rejected)
        session.gets[f"{API}/{SERVICE_NAME}"].append(state("DISABLED"))
        assert guard.disable_service(session, "anyplot", SERVICE) == "already_disabled"

    def test_rejected_disable_raises_with_the_api_error(self) -> None:
        rejected = FakeResponse(403, {"error": {"status": "PERMISSION_DENIED", "message": "denied"}})
        session = session_for_disable(post=rejected)
        session.gets[f"{API}/{SERVICE_NAME}"].append(state("ENABLED"))
        with pytest.raises(guard.ServiceUsageError, match="HTTP 403 PERMISSION_DENIED: denied"):
            guard.disable_service(session, "anyplot", SERVICE)

    @pytest.mark.parametrize(
        ("response", "text"),
        [
            (FakeResponse(403, {"error": {"status": "PERMISSION_DENIED"}}), "HTTP 403 PERMISSION_DENIED$"),
            (FakeResponse(404, {"error": {}}), "HTTP 404$"),
            (FakeResponse(500, ["unexpected"]), "HTTP 500$"),
            (FakeResponse(502, not_json=True), "HTTP 502$"),
            (FakeResponse(200, not_json=True), "not JSON"),
            (FakeResponse(200, ["state"]), "not a JSON object"),
        ],
    )
    def test_state_lookup_failures_raise(self, response: FakeResponse, text: str) -> None:
        session = FakeSession(gets={f"{API}/{SERVICE_NAME}": [response]})
        with pytest.raises(guard.ServiceUsageError, match=text):
            guard.disable_service(session, "anyplot", SERVICE)
        assert all(method == "GET" for method, _, _ in session.calls)

    def test_state_without_a_state_field_is_treated_as_enabled(self) -> None:
        session = session_for_disable()
        session.gets[f"{API}/{SERVICE_NAME}"] = [FakeResponse(200, {"name": SERVICE_NAME})]
        assert guard.disable_service(session, "anyplot", SERVICE) == "disabled"


# ===== handler =====


def never_called() -> Any:
    raise AssertionError("the session factory must not be called")


class TestHandle:
    def test_below_budget_logs_one_line_and_calls_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        data = event_data(notification(costAmount=2.5))
        record = guard.handle(data, config=config(), session_factory=never_called)
        [line] = log_lines(capsys)
        assert line == record
        assert line["action"] == "none"
        assert line["reason"] == "below_budget"
        assert line["severity"] == "INFO"
        assert (line["budget"], line["cost"], line["amount"], line["currency"]) == (BUDGET, 2.5, 5.0, "CHF")

    def test_the_raw_message_is_never_logged(self, capsys: pytest.CaptureFixture[str]) -> None:
        data = event_data(notification(costAmount=2.5))
        guard.handle(data, config=config(), session_factory=never_called)
        out = capsys.readouterr().out
        assert data["message"]["data"] not in out
        for key in ("costIntervalStart", "budgetAmountType", "billingAccountId", "attributes", "subscription"):
            assert key not in out

    def test_malformed_message_is_acknowledged_not_retried(self, capsys: pytest.CaptureFixture[str]) -> None:
        record = guard.handle(event_data(b"{oops"), config=config(), session_factory=never_called)
        [line] = log_lines(capsys)
        assert line == record
        assert (line["action"], line["reason"], line["severity"]) == ("none", "invalid_json", "WARNING")
        assert "budget" not in line

    def test_dry_run_logs_the_decision_and_calls_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        record = guard.handle(event_data(notification()), config=config(dry_run=True), session_factory=never_called)
        [line] = log_lines(capsys)
        assert line == record
        assert (line["action"], line["reason"], line["dry_run"]) == ("dry_run", "budget_reached", True)
        assert SERVICE in line["message"]

    def test_budget_reached_disables(self, capsys: pytest.CaptureFixture[str]) -> None:
        session = session_for_disable()
        record = guard.handle(event_data(notification()), config=config(), session_factory=lambda: session)
        [line] = log_lines(capsys)
        assert line == record
        assert line["action"] == "disable"
        assert line["results"] == {SERVICE: "disabled"}
        assert line["severity"] == "CRITICAL"

    def test_already_disabled_is_idempotent_and_quieter(self, capsys: pytest.CaptureFixture[str]) -> None:
        session = session_for_disable(initial_state="DISABLED")
        record = guard.handle(event_data(notification()), config=config(), session_factory=lambda: session)
        assert record["results"] == {SERVICE: "already_disabled"}
        assert record["severity"] == "NOTICE"
        assert [method for method, _, _ in session.calls] == ["GET"]
        assert len(log_lines(capsys)) == 1

    def test_pending_operation_is_logged_as_a_disable(self, capsys: pytest.CaptureFixture[str]) -> None:
        running = {"name": "operations/op-1", "done": False}
        session = session_for_disable(post=FakeResponse(200, running))
        session.gets[f"{API}/operations/op-1"] = [FakeResponse(200, running) for _ in range(40)]
        clock = FakeClock()
        record = guard.handle(
            event_data(notification()), config=config(), session_factory=lambda: session, sleep=clock.sleep, clock=clock
        )
        assert record["results"] == {SERVICE: "disable_pending"}
        assert record["severity"] == "CRITICAL"
        assert len(log_lines(capsys)) == 1

    def test_failure_raises_after_trying_every_service(self, capsys: pytest.CaptureFixture[str]) -> None:
        other = "generativelanguage.googleapis.com"
        other_name = f"projects/anyplot/services/{other}"
        session = FakeSession(
            gets={
                f"{API}/{SERVICE_NAME}": [FakeResponse(403, {"error": {"status": "PERMISSION_DENIED"}})],
                f"{API}/{other_name}": [FakeResponse(200, {"state": "ENABLED"})],
            },
            posts={f"{API}/{other_name}:disable": [done_operation()]},
        )
        with pytest.raises(guard.ServiceUsageError, match="PERMISSION_DENIED"):
            guard.handle(
                event_data(notification()), config=config(services=(SERVICE, other)), session_factory=lambda: session
            )
        [line] = log_lines(capsys)
        assert line["action"] == "failed"
        assert line["severity"] == "ERROR"
        assert line["results"] == {SERVICE: "failed", other: "disabled"}
        assert "PERMISSION_DENIED" in line["error"]

    @pytest.mark.parametrize(
        "exc",
        [requests.ConnectionError("connection reset"), google.auth.exceptions.RefreshError("token refresh failed")],
    )
    def test_transport_and_auth_errors_are_retried(self, exc: Exception, capsys: pytest.CaptureFixture[str]) -> None:
        session = mock.Mock(spec=FakeSession)
        session.get.side_effect = exc
        with pytest.raises(guard.ServiceUsageError):
            guard.handle(event_data(notification()), config=config(), session_factory=lambda: session)
        [line] = log_lines(capsys)
        assert line["action"] == "failed"
        assert str(exc) in line["error"]

    def test_missing_credentials_are_retried(self, capsys: pytest.CaptureFixture[str]) -> None:
        def no_credentials() -> Any:
            raise google.auth.exceptions.DefaultCredentialsError("no ADC")

        with pytest.raises(guard.ServiceUsageError, match="credentials: no ADC"):
            guard.handle(event_data(notification()), config=config(), session_factory=no_credentials)
        [line] = log_lines(capsys)
        assert (line["action"], line["results"]) == ("failed", {})

    def test_unexpected_errors_propagate_unchanged(self) -> None:
        session = mock.Mock(spec=FakeSession)
        session.get.side_effect = KeyError("bug")
        with pytest.raises(KeyError):
            guard.handle(event_data(notification()), config=config(), session_factory=lambda: session)


# ===== entry point =====


class TestEntryPoint:
    def test_budget_guard_handles_the_cloud_event_with_the_module_config(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(guard, "CONFIG", config(dry_run=True))
        monkeypatch.setattr(guard, "_authorized_session", never_called)
        cloud_event = types.SimpleNamespace(data=event_data(notification()))
        assert guard.budget_guard(cloud_event) is None
        [line] = log_lines(capsys)
        assert line["action"] == "dry_run"

    def test_authorized_session_uses_adc_with_the_cloud_platform_scope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        credentials = google.auth.credentials.AnonymousCredentials()
        default = mock.Mock(return_value=(credentials, "anyplot"))
        monkeypatch.setattr(guard.google.auth, "default", default)
        session = guard._authorized_session()
        default.assert_called_once_with(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        assert session.credentials is credentials
