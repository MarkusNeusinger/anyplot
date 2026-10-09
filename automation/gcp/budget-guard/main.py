"""Vertex AI budget guard: disable Vertex AI when its Cloud Billing budget is reached.

Cloud Billing publishes the status of the budget "anyplot Vertex AI cap" to the
Pub/Sub topic ``vertex-budget-alerts`` several times a day. An Eventarc trigger
delivers each message to this Cloud Run function as a CloudEvent. When the
message belongs to the configured budget and the actual cost has reached the
budget amount, the function disables the configured services (by default only
``aiplatform.googleapis.com``) through the Service Usage API. It never enables
anything: recovery is a manual step (README.md next to this file).

The core is pure and unit-tested: ``decode_pubsub_message`` turns the CloudEvent
data into the notification dict, ``decide`` returns a ``Decision``, and
``disable_service`` talks to the Service Usage API through an injected session.

Retries: a disable that failed or is not confirmed (its operation still running
after 60 seconds) raises, Functions Framework answers 500, and Pub/Sub
redelivers with exponential backoff (Eventarc default: 10 to 600 seconds) until
the trigger subscription's retention runs out; a dead-letter topic on that
subscription keeps what never succeeded. Malformed messages and no-op decisions
return normally, so Pub/Sub acknowledges them: a retry cannot change them. Every
message writes exactly one log line, an unexpected exception included.

Configuration (environment variables, validated at import so a typo fails the
deploy instead of the first real alert):

- ``BUDGET_GUARD_PROJECT``: project whose services are disabled (default ``anyplot``).
- ``BUDGET_GUARD_BUDGET_NAME``: budget display name to act on (default ``anyplot Vertex AI cap``).
- ``BUDGET_GUARD_SERVICES``: comma-separated services (default ``aiplatform.googleapis.com``).
- ``BUDGET_GUARD_DRY_RUN``: ``true`` logs the decision without calling the API (default ``false``).
"""

from __future__ import annotations

import base64
import binascii
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import functions_framework
import google.auth
import google.auth.exceptions
import requests
from google.auth.transport.requests import AuthorizedSession


if TYPE_CHECKING:
    from cloudevents.http import CloudEvent


SERVICE_USAGE_API = "https://serviceusage.googleapis.com/v1"
SCOPES = ("https://www.googleapis.com/auth/cloud-platform",)
HTTP_TIMEOUT_S = 30.0
OPERATION_POLL_INTERVAL_S = 2.0
OPERATION_TIMEOUT_S = 60.0

DEFAULT_PROJECT = "anyplot"
DEFAULT_BUDGET_NAME = "anyplot Vertex AI cap"
DEFAULT_SERVICES = "aiplatform.googleapis.com"

# Explicit, so the brake never depends on a server-side default. SKIP means the
# disable is not refused because the service was used in the last 30 days, which
# it always was when this budget is reached. Dependent services are not
# disabled: if one exists, the call fails loudly and the owner decides.
DISABLE_REQUEST_BODY: dict[str, Any] = {"disableDependentServices": False, "checkIfServiceHasUsage": "SKIP"}

_PROJECT_RE = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]|[0-9]+")
_SERVICE_RE = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)*\.googleapis\.com")
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})
_ERROR_TEXT_LIMIT = 300


class ConfigError(ValueError):
    """An environment variable holds a value the guard refuses to run with."""


class MessageError(ValueError):
    """The CloudEvent does not carry a decodable budget notification."""


class ServiceUsageError(RuntimeError):
    """A Service Usage API call failed; raising it makes Pub/Sub retry."""


# The errors one service's disable can end in. Anything else is a bug and
# propagates unchanged.
GUARD_ERRORS: tuple[type[Exception], ...] = (
    ServiceUsageError,
    requests.RequestException,
    google.auth.exceptions.GoogleAuthError,
)


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> Any: ...


class HttpSession(Protocol):
    def get(self, url: str, **kwargs: Any) -> HttpResponse: ...

    def post(self, url: str, **kwargs: Any) -> HttpResponse: ...


@dataclass(frozen=True)
class Config:
    project: str
    budget_name: str
    services: tuple[str, ...]
    dry_run: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Config:
        project = env.get("BUDGET_GUARD_PROJECT", DEFAULT_PROJECT).strip()
        if not _PROJECT_RE.fullmatch(project):
            raise ConfigError(f"BUDGET_GUARD_PROJECT is not a project ID or number: {project!r}")
        budget_name = env.get("BUDGET_GUARD_BUDGET_NAME", DEFAULT_BUDGET_NAME).strip()
        if not budget_name:
            raise ConfigError("BUDGET_GUARD_BUDGET_NAME is empty")
        raw_services = env.get("BUDGET_GUARD_SERVICES", DEFAULT_SERVICES)
        services = tuple(dict.fromkeys(s.strip() for s in raw_services.split(",") if s.strip()))
        if not services:
            raise ConfigError("BUDGET_GUARD_SERVICES names no service")
        invalid = [s for s in services if not _SERVICE_RE.fullmatch(s)]
        if invalid:
            raise ConfigError(f"BUDGET_GUARD_SERVICES has invalid service names: {invalid!r}")
        dry_run_raw = env.get("BUDGET_GUARD_DRY_RUN", "false").strip().lower()
        if dry_run_raw in _TRUE_VALUES:
            dry_run = True
        elif dry_run_raw in _FALSE_VALUES:
            dry_run = False
        else:
            raise ConfigError(f"BUDGET_GUARD_DRY_RUN must be true or false, got {dry_run_raw!r}")
        return cls(project=project, budget_name=budget_name, services=services, dry_run=dry_run)


@dataclass(frozen=True)
class Decision:
    disable: bool
    reason: str
    budget: str | None = None
    cost: float | None = None
    amount: float | None = None
    currency: str | None = None


def decode_pubsub_message(event_data: Any) -> dict[str, Any]:
    """Return the budget notification carried by an Eventarc Pub/Sub CloudEvent's data.

    The data is ``{"message": {"data": "<base64 JSON>", "attributes": {...}, ...}, ...}``.
    Raises ``MessageError`` (its text is a short reason code) for anything else.
    """
    if not isinstance(event_data, Mapping):
        raise MessageError("event_without_data")
    message = event_data.get("message")
    if not isinstance(message, Mapping):
        raise MessageError("event_without_message")
    data = message.get("data")
    if not isinstance(data, str | bytes) or not data:
        raise MessageError("message_without_data")
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise MessageError("invalid_base64") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MessageError("invalid_json") from exc
    if not isinstance(payload, dict):
        raise MessageError("payload_not_object")
    return payload


def _finite_number(value: Any) -> float | None:
    """The value as a finite float, or None. JSON booleans are not amounts."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        number = float(value)
    except OverflowError:
        # A JSON integer beyond the float range (such as 10**400) parses as int.
        return None
    return number if math.isfinite(number) else None


def decide(message: Mapping[str, Any], *, budget_name: str) -> Decision:
    """Decide whether a budget notification means "disable the services now".

    Disable only when ``budgetDisplayName`` equals ``budget_name`` and
    ``costAmount >= budgetAmount``. Threshold keys (``alertThresholdExceeded``,
    ``forecastThresholdExceeded``) and ``currencyCode`` do not take part: both
    amounts are in the budget's currency, and a forecast never cuts anything off.
    Every other message is a no-op with a reason.
    """
    budget = message.get("budgetDisplayName")
    if not isinstance(budget, str):
        return Decision(disable=False, reason="missing_budget_name")
    currency_value = message.get("currencyCode")
    currency = currency_value if isinstance(currency_value, str) else None
    if budget != budget_name:
        return Decision(disable=False, reason="other_budget", budget=budget, currency=currency)
    cost = _finite_number(message.get("costAmount"))
    amount = _finite_number(message.get("budgetAmount"))
    if cost is None:
        return Decision(disable=False, reason="invalid_cost_amount", budget=budget, amount=amount, currency=currency)
    if amount is None or amount <= 0:
        return Decision(disable=False, reason="invalid_budget_amount", budget=budget, cost=cost, currency=currency)
    if cost < amount:
        return Decision(
            disable=False, reason="below_budget", budget=budget, cost=cost, amount=amount, currency=currency
        )
    return Decision(disable=True, reason="budget_reached", budget=budget, cost=cost, amount=amount, currency=currency)


def _error_text(response: HttpResponse) -> str:
    """HTTP status plus the API's error status and message, shortened, for the log."""
    detail = ""
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, Mapping) and isinstance(body.get("error"), Mapping):
        error = body["error"]
        detail = f" {error.get('status', '')}: {error.get('message', '')}".rstrip(": ")
    return f"HTTP {response.status_code}{detail}"[:_ERROR_TEXT_LIMIT]


def _json_object(response: HttpResponse, what: str) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise ServiceUsageError(f"{what}: response is not JSON") from exc
    if not isinstance(body, dict):
        raise ServiceUsageError(f"{what}: response is not a JSON object")
    return body


def _service_state(session: HttpSession, name: str) -> str:
    """The service's state: ``ENABLED``, ``DISABLED`` or ``STATE_UNSPECIFIED``."""
    response = session.get(f"{SERVICE_USAGE_API}/{name}", timeout=HTTP_TIMEOUT_S)
    if response.status_code != 200:
        raise ServiceUsageError(f"get {name}: {_error_text(response)}")
    state = _json_object(response, f"get {name}").get("state")
    return state if isinstance(state, str) else "STATE_UNSPECIFIED"


def _wait_for_operation(
    session: HttpSession,
    operation: dict[str, Any],
    *,
    sleep: Callable[[float], None],
    clock: Callable[[], float],
    timeout_s: float,
) -> bool:
    """Poll a long-running operation. True when it finished, False when still running at the deadline."""
    deadline = clock() + timeout_s
    while True:
        if operation.get("done"):
            error = operation.get("error")
            if error:
                message = error.get("message", "") if isinstance(error, Mapping) else str(error)
                raise ServiceUsageError(f"operation failed: {message}"[:_ERROR_TEXT_LIMIT])
            return True
        name = operation.get("name")
        if not isinstance(name, str) or not name:
            raise ServiceUsageError("operation is still running and has no name to poll")
        if clock() >= deadline:
            return False
        sleep(OPERATION_POLL_INTERVAL_S)
        response = session.get(f"{SERVICE_USAGE_API}/{name}", timeout=HTTP_TIMEOUT_S)
        if response.status_code != 200:
            raise ServiceUsageError(f"get {name}: {_error_text(response)}")
        operation = _json_object(response, f"get {name}")


def disable_service(
    session: HttpSession,
    project: str,
    service: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    timeout_s: float = OPERATION_TIMEOUT_S,
) -> str:
    """Disable one service, idempotently. Never enables anything.

    Returns ``already_disabled``, ``disabled``, or ``disable_pending`` (the
    operation was accepted but had not finished within ``timeout_s``; the
    handler treats that as unconfirmed and raises, so the redelivered message
    reads the state again). Raises ``ServiceUsageError`` or a ``requests`` error
    on failure.
    """
    name = f"projects/{project}/services/{service}"
    if _service_state(session, name) == "DISABLED":
        return "already_disabled"
    response = session.post(f"{SERVICE_USAGE_API}/{name}:disable", json=DISABLE_REQUEST_BODY, timeout=HTTP_TIMEOUT_S)
    if response.status_code != 200:
        # Disabling a service that is not enabled answers FAILED_PRECONDITION. A
        # redelivered message can race this one, so read the state again before
        # calling it a failure.
        if _service_state(session, name) == "DISABLED":
            return "already_disabled"
        raise ServiceUsageError(f"disable {service}: {_error_text(response)}")
    operation = _json_object(response, f"disable {service}")
    finished = _wait_for_operation(session, operation, sleep=sleep, clock=clock, timeout_s=timeout_s)
    return "disabled" if finished else "disable_pending"


def _disable_services(
    config: Config,
    session_factory: Callable[[], HttpSession],
    results: dict[str, str],
    *,
    sleep: Callable[[float], None],
    clock: Callable[[], float],
) -> list[str]:
    """Disable every configured service, filling ``results``; return what is not confirmed.

    Expected failures (``GUARD_ERRORS``) and an operation still running at the
    deadline are collected, so every service gets its attempt. Anything else is
    a bug and propagates.
    """
    try:
        session = session_factory()
    except GUARD_ERRORS as exc:
        return [f"credentials: {exc}"[:_ERROR_TEXT_LIMIT]]
    errors: list[str] = []
    for service in config.services:
        try:
            results[service] = disable_service(session, config.project, service, sleep=sleep, clock=clock)
        except GUARD_ERRORS as exc:
            results[service] = "failed"
            errors.append(f"{service}: {exc}"[:_ERROR_TEXT_LIMIT])
        else:
            if results[service] == "disable_pending":
                errors.append(f"{service}: disable operation still running after {OPERATION_TIMEOUT_S:.0f} s")
    return errors


def _log(record: Mapping[str, Any]) -> None:
    """One structured line; Cloud Logging reads ``severity`` and ``message`` from it."""
    print(json.dumps(record, sort_keys=True), file=sys.stdout, flush=True)


def handle(
    event_data: Any,
    *,
    config: Config,
    session_factory: Callable[[], HttpSession],
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Process one CloudEvent's data, log one line, and return that line's record.

    Raises ``ServiceUsageError`` when a disable failed, so Pub/Sub retries. The
    raw message is never logged, only the fields named in the record.
    """
    record: dict[str, Any] = {
        "component": "vertex-budget-guard",
        "project": config.project,
        "services": list(config.services),
        "dry_run": config.dry_run,
    }
    try:
        message = decode_pubsub_message(event_data)
    except MessageError as exc:
        record.update(action="none", reason=str(exc), severity="WARNING")
        record["message"] = f"budget guard: ignored a message ({exc})"
        _log(record)
        return record

    decision = decide(message, budget_name=config.budget_name)
    record.update(
        budget=decision.budget,
        cost=decision.cost,
        amount=decision.amount,
        currency=decision.currency,
        reason=decision.reason,
    )
    if not decision.disable:
        record.update(action="none", severity="INFO", message=f"budget guard: no action ({decision.reason})")
        _log(record)
        return record
    if config.dry_run:
        record.update(
            action="dry_run",
            severity="WARNING",
            message=f"budget guard: dry run, would disable {', '.join(config.services)}",
        )
        _log(record)
        return record

    results: dict[str, str] = {}
    record["results"] = results
    try:
        errors = _disable_services(config, session_factory, results, sleep=sleep, clock=clock)
    except Exception as exc:
        # A bug, not an expected failure: write the one line anyway, then re-raise unchanged.
        record.update(
            action="failed", severity="ERROR", error=f"unexpected {type(exc).__name__}: {exc}"[:_ERROR_TEXT_LIMIT]
        )
        record["message"] = "budget guard: unexpected error, Pub/Sub will retry"
        _log(record)
        raise

    if errors:
        record.update(action="failed", severity="ERROR", error="; ".join(errors))
        record["message"] = "budget guard: disable not confirmed, Pub/Sub will retry"
        _log(record)
        raise ServiceUsageError(record["error"])
    newly_disabled = any(result == "disabled" for result in results.values())
    record.update(action="disable", severity="CRITICAL" if newly_disabled else "NOTICE")
    record["message"] = "budget guard: " + ", ".join(f"{service} {result}" for service, result in results.items())
    _log(record)
    return record


def _authorized_session() -> HttpSession:
    """A session authenticated with the runtime service account (Application Default Credentials)."""
    credentials, _ = google.auth.default(scopes=list(SCOPES))
    session: HttpSession = AuthorizedSession(credentials)
    return session


# Read once at import: an invalid value stops the container from starting, so
# the deploy fails instead of the first real alert.
CONFIG = Config.from_env(os.environ)


@functions_framework.cloud_event
def budget_guard(cloud_event: CloudEvent) -> None:
    """Entry point (``--function budget_guard``) for the Eventarc Pub/Sub trigger."""
    handle(cloud_event.data, config=CONFIG, session_factory=_authorized_session)
