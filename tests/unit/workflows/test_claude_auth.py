"""Claude credential switch (vars.CLAUDE_AUTH), the session summary, and the stops Claude makes.

Every job that runs Claude starts with the same "Resolve Claude credentials"
step. It maps CLAUDE_AUTH (unset or `subscription`, `api`, `oidc`) to a mode,
stops the job on an unknown value or a missing credential instead of falling
back to the subscription, and hands the mode and, for `oidc`, the four
workload identity federation IDs to every Claude step as outputs. Each step
then passes exactly one credential; the action's precedence with several set
is undocumented (an API key or OAuth token silently shadows federation).
Under `oidc`, the runs the federation rule refuses (a pull-request event,
another ref, a job without id-token) use the subscription by design.

After every Claude step, "Claude session summary" writes the cost line and
reads whether Claude stopped the session: a spend or usage limit (the API's
spend limit, spend cap or credit balance, the subscription's usage limit) in
every mode, or refused credentials with api/oidc. The retry is skipped then;
impl-generate parks the pair, impl-review and impl-repair pause the PR
(`ai-review-paused`, `ai-repair-paused`, which the watchdog skips), and
nothing counts as an attempt or a failure verdict. Pair mode resumes the
paused PRs first.

There is no pre-merge smoke for these workflows (claude-code-action refuses
to run on a PR that changes them), so the wiring is pinned here and the
scripts run for real. The pick itself is tested in
tests/unit/automation/scripts/test_regen_pick_pairs.py.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / ".github" / "workflows"
ACTION = "anthropics/claude-code-action@"
RESOLVE = "Resolve Claude credentials"
SUMMARY = "Claude session summary"
STOP = "Stop when Claude stopped the session"
CREDENTIALS = {
    "anthropic_api_key": "${{ steps.claude_auth.outputs.mode == 'api' && secrets.ANTHROPIC_API_KEY || '' }}",
    "claude_code_oauth_token": (
        "${{ steps.claude_auth.outputs.mode == 'subscription' && secrets.CLAUDE_CODE_OAUTH_TOKEN || '' }}"
    ),
    "anthropic_federation_rule_id": "${{ steps.claude_auth.outputs.federation_rule_id }}",
    "anthropic_organization_id": "${{ steps.claude_auth.outputs.organization_id }}",
    "anthropic_service_account_id": "${{ steps.claude_auth.outputs.service_account_id }}",
    "anthropic_workspace_id": "${{ steps.claude_auth.outputs.workspace_id }}",
}
# Inputs that would select another provider or route credentials around the switch.
FOREIGN_INPUTS = {"use_bedrock", "use_vertex", "use_foundry", "claude_env", "anthropic_oidc_audience"}
# The eight workflows (13 steps) that ran Claude on the OAuth token before the switch.
CLAUDE_WORKFLOWS = {
    "daily-regen.yml": 2,
    "impl-generate.yml": 2,
    "impl-repair.yml": 2,
    "spec-create.yml": 2,
    "util-claude.yml": 2,
    "impl-review.yml": 1,
    "report-validate.yml": 1,
    "review-retest.yml": 1,
}
WIF = {
    "WIF_RULE_ID": "fdrl_01abc",
    "WIF_ORG_ID": "00000000-0000-4000-8000-000000000000",
    "WIF_SERVICE_ACCOUNT_ID": "svac_01abc",
    "WIF_WORKSPACE_ID": "wrkspc_01abc",
}


def _load(filename: str) -> dict[str, Any]:
    return yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))


def _claude_jobs() -> list[tuple[str, str, dict[str, Any]]]:
    jobs = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for name, job in (_load(path.name).get("jobs") or {}).items():
            if any(_is_claude(s) for s in job.get("steps") or []):
                jobs.append((path.name, name, job))
    return jobs


def _is_claude(step: dict[str, Any]) -> bool:
    return str(step.get("uses", "")).startswith(ACTION)


def _named(name: str) -> list[dict[str, Any]]:
    return [s for _, _, job in _claude_jobs() for s in job["steps"] if str(s.get("name", "")).startswith(name)]


def _step(filename: str, name: str) -> dict[str, Any]:
    steps = [s for job in _load(filename)["jobs"].values() for s in job.get("steps", [])]
    matches = [s for s in steps if s.get("name") == name]
    assert len(matches) == 1, (filename, name)
    return matches[0]


def _names(filename: str, job: str) -> list[str]:
    return [s.get("name", "") for s in _load(filename)["jobs"][job]["steps"]]


JOBS = _claude_jobs()
IDS = [f"{f}:{j}" for f, j, _ in JOBS]


def test_every_claude_workflow_is_covered():
    found: dict[str, int] = {}
    for filename, _, job in JOBS:
        found[filename] = found.get(filename, 0) + sum(1 for s in job["steps"] if _is_claude(s))
    assert found == CLAUDE_WORKFLOWS


# --- wiring -----------------------------------------------------------------


@pytest.mark.parametrize(("filename", "name", "job"), JOBS, ids=IDS)
def test_each_claude_step_reads_the_resolved_credentials(filename, name, job):
    for step in filter(_is_claude, job["steps"]):
        given = step.get("with") or {}
        assert {k: given.get(k) for k in CREDENTIALS} == CREDENTIALS, (filename, step.get("name"))
        assert not FOREIGN_INPUTS & set(given), (filename, step.get("name"))
        env = step.get("env") or {}
        assert not {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"} & set(env), (filename, step.get("name"))


@pytest.mark.parametrize(("filename", "name", "job"), JOBS, ids=IDS)
def test_the_credentials_are_resolved_before_any_claude_step(filename, name, job):
    steps = job["steps"]
    names = [s.get("name") for s in steps]
    assert names.count(RESOLVE) == 1, (filename, name)
    resolve = steps[names.index(RESOLVE)]
    first_claude = next(i for i, s in enumerate(steps) if _is_claude(s))
    assert names.index(RESOLVE) < first_claude
    assert resolve["id"] == "claude_auth"
    # Unconditional, or gated exactly like the first Claude step (a label
    # event that never reaches Claude must not fail on a misconfigured switch).
    assert resolve.get("if") in (None, steps[first_claude].get("if")), (filename, name)
    assert "continue-on-error" not in resolve


def test_every_resolve_step_is_identical():
    steps = _named(RESOLVE)
    assert len(steps) == len(JOBS) == 8
    reference = {k: v for k, v in steps[0].items() if k != "if"}
    for step in steps[1:]:
        assert {k: v for k, v in step.items() if k != "if"} == reference
    assert reference["env"] == {
        "CLAUDE_AUTH": "${{ vars.CLAUDE_AUTH }}",
        "API_KEY_SET": "${{ secrets.ANTHROPIC_API_KEY != '' }}",
        "OAUTH_TOKEN_SET": "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN != '' }}",
        "WIF_RULE_ID": "${{ vars.CLAUDE_WIF_RULE_ID }}",
        "WIF_ORG_ID": "${{ vars.CLAUDE_WIF_ORG_ID }}",
        "WIF_SERVICE_ACCOUNT_ID": "${{ vars.CLAUDE_WIF_SERVICE_ACCOUNT_ID }}",
        "WIF_WORKSPACE_ID": "${{ vars.CLAUDE_WIF_WORKSPACE_ID }}",
        "EVENT": "${{ github.event_name }}",
        "REF": "${{ github.ref }}",
    }


@pytest.mark.parametrize(("filename", "name", "job"), JOBS, ids=IDS)
def test_id_token_is_where_it_was(filename, name, job):
    """No job gains id-token in this change; review-retest stays without it (oidc routes it to the subscription)."""
    has_id_token = (job.get("permissions") or {}).get("id-token") == "write"
    assert has_id_token is (filename != "review-retest.yml"), (filename, name)


@pytest.mark.parametrize(("filename", "name", "job"), JOBS, ids=IDS)
def test_each_claude_step_is_followed_by_its_session_summary(filename, name, job):
    """Read before the next Claude step: a retry writes the same execution file."""
    steps = job["steps"]
    for i, step in enumerate(steps):
        if not _is_claude(step):
            continue
        sid = step["id"]
        later = steps[i + 1 :]
        summary = next(s for s in later if str(s.get("name", "")).startswith(SUMMARY))
        next_claude = next((j for j, s in enumerate(later) if _is_claude(s)), len(later))
        assert later.index(summary) < next_claude, (filename, step.get("name"))
        assert summary["id"] == f"{sid}_cost"
        assert summary["if"] == (
            f"${{{{ !cancelled() && (steps.{sid}.outcome == 'success' || steps.{sid}.outcome == 'failure') }}}}"
        )
        assert summary["continue-on-error"] is True
        assert summary["env"]["EXECUTION_FILE"] == f"${{{{ steps.{sid}.outputs.execution_file }}}}"
        assert summary["env"]["CLAUDE_AUTH_MODE"] == "${{ steps.claude_auth.outputs.mode }}"


def test_summary_steps_share_one_script_and_unique_labels():
    summaries = _named(SUMMARY)
    labels = [s["env"]["CLAUDE_STEP"] for s in summaries]
    assert len(labels) == len(set(labels)) == sum(CLAUDE_WORKFLOWS.values())
    assert all(" " not in label for label in labels)
    keys = ("SESSION_ERRORS", "LIMIT_PATTERN", "AUTH_PATTERN")
    assert len({(s["run"], *(s["env"][k] for k in keys)) for s in summaries}) == 1
    # The line must not look like Claude Code's own `"total_cost_usd": n`, or
    # collect_week.py's fallback regex would count a session twice.
    assert '"total_cost_usd":' not in summaries[0]["run"]


@pytest.mark.parametrize(("filename", "name", "job"), JOBS, ids=IDS)
def test_a_stop_skips_the_retry_and_fails_the_job(filename, name, job):
    steps = job["steps"]
    names = [s.get("name") for s in steps]
    claude = [s for s in steps if _is_claude(s)]
    if filename == "daily-regen.yml":
        # Two independent pre-flight sessions, no retry: either one stops the dispatch.
        stop = steps[names.index(STOP)]
        assert stop["if"] == (
            "${{ steps.polish_cost.outputs.stopped == 'true' || steps.similarity_cost.outputs.stopped == 'true' }}"
        )
        dispatches = [i for i, n in enumerate(names) if str(n).startswith("Dispatch ")]
        assert len(dispatches) == 2 and min(dispatches) > names.index(STOP) > steps.index(claude[-1])
    elif len(claude) == 1:
        # No retry to skip: the job's own failure path reads the summary.
        assert STOP not in names
        return
    else:
        first, retry = claude
        assert retry["if"].endswith(f" && steps.{first['id']}_cost.outputs.stopped != 'true'")
        stop = steps[names.index(STOP)]
        assert names.index(STOP) > steps.index(retry)
        assert stop["if"] == f"steps.{first['id']}_cost.outputs.stopped == 'true'"
    assert "exit 1" in stop["run"] and "continue-on-error" not in stop


def test_the_api_key_reaches_nothing_but_the_action_input():
    """The key is never put into an env block, a script or another action."""
    allowed = {
        f"anthropic_api_key: {CREDENTIALS['anthropic_api_key']}",
        "API_KEY_SET: ${{ secrets.ANTHROPIC_API_KEY != '' }}",
    }
    for path in WORKFLOWS_DIR.glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if "secrets.ANTHROPIC_API_KEY" in stripped and not stripped.startswith("#"):
                assert stripped in allowed, (path.name, stripped)


def test_no_claude_workflow_runs_on_pull_request_events():
    """A fork PR never reaches a credential: no `pull_request` or `pull_request_target` trigger."""
    for filename in CLAUDE_WORKFLOWS:
        workflow = _load(filename)
        triggers = workflow.get(True) or workflow.get("on") or {}
        assert "pull_request_target" not in triggers, filename
        assert "pull_request" not in triggers, filename


@pytest.mark.parametrize(
    ("filename", "name"),
    [
        ("impl-generate.yml", "Adopt implementation from source ref"),
        ("impl-generate.yml", "Adaptability smoke run (record-only)"),
        ("impl-repair.yml", "Adaptability smoke run (record-only)"),
    ],
)
def test_steps_running_model_written_code_get_no_oidc_request(filename, name):
    """The jobs have id-token; the code they run must not be able to mint a token."""
    first = next(line for line in _step(filename, name)["run"].splitlines() if not line.lstrip().startswith("#"))
    assert first == "unset ACTIONS_ID_TOKEN_REQUEST_URL ACTIONS_ID_TOKEN_REQUEST_TOKEN"


# --- the resolve step, run for real ------------------------------------------


def _resolve(
    tmp_path: Path,
    auth: str | None,
    key_set: bool = False,
    id_token: bool = True,
    oauth_set: bool = True,
    event: str = "schedule",
    ref: str = "refs/heads/main",
    **wif: str,
):
    script = _named(RESOLVE)[0]["run"]
    out, summary = tmp_path / "out", tmp_path / "summary"
    out.write_text("", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_", "WIF_", "ACTIONS_ID_TOKEN"))}
    env |= {
        "API_KEY_SET": "true" if key_set else "false",
        "OAUTH_TOKEN_SET": "true" if oauth_set else "false",
        "EVENT": event,
        "REF": ref,
        "GITHUB_OUTPUT": str(out),
        "GITHUB_STEP_SUMMARY": str(summary),
        **wif,
    }
    if auth is not None:
        env["CLAUDE_AUTH"] = auth
    if id_token:
        env["ACTIONS_ID_TOKEN_REQUEST_URL"] = "https://token.actions.example/"
    result = subprocess.run(["bash", "-e", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True)
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines() if "=" in line)
    return result, outputs, summary.read_text() if summary.exists() else ""


def _inputs(outputs: dict[str, str], key: str, token: str) -> dict[str, str]:
    """The six action inputs as GitHub evaluates CREDENTIALS: `a && b || ''` yields b or ''."""
    mode = outputs.get("mode", "")
    return {
        "anthropic_api_key": key if mode == "api" and key else "",
        "claude_code_oauth_token": token if mode == "subscription" and token else "",
        "anthropic_federation_rule_id": outputs.get("federation_rule_id", ""),
        "anthropic_organization_id": outputs.get("organization_id", ""),
        "anthropic_service_account_id": outputs.get("service_account_id", ""),
        "anthropic_workspace_id": outputs.get("workspace_id", ""),
    }


@pytest.mark.parametrize(
    ("auth", "key_set", "mode", "given"),
    [
        (None, False, "subscription", {"claude_code_oauth_token"}),
        ("", False, "subscription", {"claude_code_oauth_token"}),
        ("Subscription", True, "subscription", {"claude_code_oauth_token"}),
        ("api", True, "api", {"anthropic_api_key"}),
        ("API", True, "api", {"anthropic_api_key"}),
        ("oidc", True, "oidc", {"anthropic_federation_rule_id", "anthropic_organization_id"}),
        ("OIDC", False, "oidc", {"anthropic_federation_rule_id", "anthropic_organization_id"}),
    ],
)
def test_resolve_passes_exactly_one_credential(tmp_path, auth, key_set, mode, given):
    result, outputs, _ = _resolve(tmp_path, auth, key_set, **WIF)
    assert result.returncode == 0, result.stdout + result.stderr
    assert outputs["mode"] == mode and f"Claude credentials: {mode}" in result.stdout
    inputs = _inputs(outputs, "sk-ant-key" if key_set else "", "oauth-token")
    if mode == "oidc":
        # Federation is one credential: rule + organization (+ service account, workspace), no key, no token.
        assert set(given) <= {k for k, v in inputs.items() if v}
        assert not inputs["anthropic_api_key"] and not inputs["claude_code_oauth_token"]
        assert outputs["workspace_id"] == WIF["WIF_WORKSPACE_ID"]
    else:
        assert {k for k, v in inputs.items() if v} == given
        assert not any(k in outputs for k in ("federation_rule_id", "organization_id"))


@pytest.mark.parametrize(
    ("event", "ref", "id_token", "where"),
    [
        # util-claude's review events present the `…:pull_request` subject.
        ("pull_request_review", "refs/pull/7/merge", True, "pull_request_review/refs/pull/7/merge"),
        ("pull_request_review_comment", "refs/pull/7/merge", True, "pull_request_review_comment/refs/pull/7/merge"),
        # A branch smoke: `…:ref:refs/heads/feature/x`.
        ("workflow_dispatch", "refs/heads/feature/x", True, "workflow_dispatch/refs/heads/feature/x"),
        # review-retest: no id-token on purpose.
        ("workflow_dispatch", "refs/heads/main", False, "workflow_dispatch/refs/heads/main (no id-token)"),
    ],
)
def test_oidc_routes_the_runs_federation_refuses_to_the_subscription(tmp_path, event, ref, id_token, where):
    result, outputs, summary = _resolve(tmp_path, "oidc", id_token=id_token, event=event, ref=ref, **WIF)
    assert result.returncode == 0, result.stdout + result.stderr
    assert outputs["mode"] == "subscription" and "federation_rule_id" not in outputs
    assert f"::notice::oidc not available for {where}; using subscription" in result.stdout
    assert f"- oidc not available for {where}; using subscription" in summary
    assert {k for k, v in _inputs(outputs, "", "oauth-token").items() if v} == {"claude_code_oauth_token"}


def test_oidc_routing_fails_fast_without_the_oauth_token(tmp_path):
    result, outputs, _ = _resolve(
        tmp_path, "oidc", oauth_set=False, event="pull_request_review", ref="refs/pull/7/merge"
    )
    assert result.returncode == 1 and "mode" not in outputs
    assert result.stdout.startswith("::error::oidc not available for pull_request_review/refs/pull/7/merge")
    assert "CLAUDE_CODE_OAUTH_TOKEN secret is missing" in result.stdout


@pytest.mark.parametrize(
    ("auth", "key_set", "wif", "why"),
    [
        ("api", False, WIF, "ANTHROPIC_API_KEY secret is missing"),
        ("oidc", True, {**WIF, "WIF_RULE_ID": ""}, "CLAUDE_WIF_RULE_ID is missing"),
        ("oidc", True, {k: v for k, v in WIF.items() if k != "WIF_WORKSPACE_ID"}, "CLAUDE_WIF_WORKSPACE_ID"),
        ("oidc", True, {**WIF, "WIF_ORG_ID": "x\n::warning::y"}, "CLAUDE_WIF_ORG_ID is missing or not an ID"),
        ("apikey", True, WIF, "must be unset, 'subscription', 'api' or 'oidc'"),
        (" api", True, WIF, "must be unset"),
        ("api\n::warning::injected", True, WIF, "must be unset"),
    ],
)
def test_resolve_stops_instead_of_falling_back(tmp_path, auth, key_set, wif, why):
    result, outputs, _ = _resolve(tmp_path, auth, key_set, **wif)
    assert result.returncode == 1
    assert result.stdout.startswith("::error::") and why in result.stdout
    assert "not falling back to the subscription" in result.stdout
    assert "\n::warning::" not in result.stdout
    assert "mode" not in outputs


# --- the session summary, run for real ----------------------------------------


def _summary(tmp_path: Path, execution: list[dict[str, Any]] | None, mode: str = "subscription"):
    step = _named(SUMMARY)[0]
    exec_file = tmp_path / "claude-execution-output.json"
    if execution is not None:
        exec_file.write_text(json.dumps(execution), encoding="utf-8")
    summary, out = tmp_path / "summary", tmp_path / "out"
    env = {
        **os.environ,
        "EXECUTION_FILE": str(exec_file) if execution is not None else "",
        "CLAUDE_AUTH_MODE": mode,
        "CLAUDE_STEP": "impl-review",
        **{k: step["env"][k] for k in ("SESSION_ERRORS", "LIMIT_PATTERN", "AUTH_PATTERN")},
        "GITHUB_STEP_SUMMARY": str(summary),
        "GITHUB_OUTPUT": str(out),
    }
    result = subprocess.run(["bash", "-e", "-c", step["run"]], env=env, capture_output=True, text=True)
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines()) if out.exists() else {}
    return result, summary.read_text() if summary.exists() else "", outputs


INIT = {"type": "system", "subtype": "init", "model": "claude-opus-5-5"}
NOT_STOPPED = {"stopped": "false", "stop_reason": ""}


def _failed(text: str, error: str | None = "invalid_request", status: int = 400) -> list[dict[str, Any]]:
    """A session the API stopped: Claude Code's synthetic error message and an error result."""
    assistant: dict[str, Any] = {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
    if error:
        assistant["error"] = error
    result = {"type": "result", "subtype": "success", "is_error": True, "api_error_status": status}
    return [INIT, assistant, result | {"result": text, "total_cost_usd": 0.41}]


# Fixtures with the texts as the API and Claude Code produce them, by source.
LIMIT_FIXTURES = {
    # A workspace spend limit you set: HTTP 400 invalid_request_error
    # (platform.claude.com/docs/en/api/rate-limits; anthropics/claude-code#40664).
    "workspace spend limit": _failed(
        'API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"You have reached your '
        'specified workspace API usage limits. You will regain access on 2026-12-01 at 00:00 UTC."}}'
    ),
    # An organization spend limit you set (anthropics/claude-code#52077, the raw API error).
    "org spend limit": _failed(
        'Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"You have reached your '
        'specified API usage limits. You will regain access on 2026-05-01 at 00:00 UTC."}}'
    ),
    # The usage tier's monthly cap: HTTP 429 rate_limit_error with an error_code (the same docs page).
    "tier spend cap": _failed(
        'API Error: 429 {"type":"error","error":{"type":"rate_limit_error","message":"You have reached your API usage '
        'limits: your organization has crossed its monthly API usage threshold.","details":{"error_code":'
        '"enforced_spend_limit_reached"}}}',
        error="rate_limit",
        status=429,
    ),
    # Credits: the API's message, and Claude Code's non-interactive and interactive renderings
    # (anthropics/claude-code#99371, #103854).
    "credit, API": _failed(
        "Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or "
        "purchase credits.",
        error="billing_error",
    ),
    "credit, Claude Code result": _failed("Credit balance is too low", error=None),
    "credit, Claude Code interactive": _failed(
        "Credit balance too low · Add funds: https://platform.claude.com/settings/billing", error=None
    ),
    # The SDK's own billing error type on an API retry (SDKAssistantMessageError).
    "billing_error retry": [
        INIT,
        {"type": "system", "subtype": "api_retry", "error": "billing_error", "error_status": 402},
    ],
    # Subscription: Claude Code's usage-limit messages, which start with one of the SDK's
    # USAGE_LIMIT_ERROR_PREFIXES ("the error-path outputs of getLimitReachedText"); the
    # session-limit text as reported in anthropics/claude-code#101965.
    "session limit": _failed("You've hit your session limit · resets 12:30pm", error="rate_limit", status=429),
    "session limit, curly apostrophe": _failed("You’ve hit your session limit · resets 4am (Europe/Berlin)", None),
    "weekly limit": _failed("You've reached your weekly limit · resets Nov 3, 9am", error="rate_limit", status=429),
    "out of extra usage": _failed("You're out of extra usage · resets 12:30pm", error="rate_limit", status=429),
    "org out of usage": _failed("Your org is out of usage · contact your admin", error="rate_limit", status=429),
    "older CLI wording": _failed("Claude AI usage limit reached|1761955200", error=None),
}

# Refused credentials (the API's error types, docs/en/api/errors; the federation's
# fixed `401 Authentication failed`, docs/en/manage-claude/wif-providers/github-actions).
AUTH_FIXTURES = {
    "bad API key": _failed(
        'API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}}',
        error="authentication_failed",
        status=401,
    ),
    "federation refused": _failed(
        'API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"Authentication failed"}}',
        error="authentication_failed",
        status=401,
    ),
    "permission": _failed(
        'API Error: 403 {"type":"error","error":{"type":"permission_error","message":"Your API key does not have '
        'permission to use the specified resource."}}',
        error="unknown",
        status=403,
    ),
    "status only": _failed("Request failed", error=None, status=401),
}

NOT_A_STOP = {
    # A transient rate limit keeps its retry and the infrastructure path it had.
    "per-minute rate limit": _failed(
        'API Error: 429 {"error":{"type":"rate_limit_error","message":"Number of request tokens has exceeded your '
        'per-minute rate limit"}}',
        error="rate_limit",
        status=429,
    ),
    "rate limit, CLI wording": _failed("API Error: Rate limit reached", error="rate_limit", status=429),
    "server error": _failed("API Error: 500 Internal server error", error="server_error", status=500),
    # A usage warning, not a stop (the SDK's USAGE_WARNING_PREFIXES).
    "usage warning": _failed("You've used 95% of your weekly limit", error="unknown", status=500),
    # The session's own text may quote the messages (a doc it read, a review comment): not an error field.
    "quoted by the model": [
        INIT,
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Docs: credit balance is too low"}]}},
    ],
    "quoted by a tool": [
        INIT,
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "You've hit your session limit"}]}},
    ],
    "in a successful result": [
        INIT,
        {"type": "result", "subtype": "success", "is_error": False, "result": "Docs say: Authentication failed"},
    ],
    # A retried billing error the session got past: it ended well, so it never stopped.
    "recovered": [
        INIT,
        {"type": "system", "subtype": "api_retry", "error": "billing_error", "error_status": 402},
        {"type": "result", "subtype": "success", "is_error": False, "result": "done"},
    ],
}


def test_summary_reads_cost_and_model(tmp_path):
    execution = [INIT, {"type": "assistant"}, {"type": "result", "subtype": "success", "total_cost_usd": 0.2931}]
    result, summary, outputs = _summary(tmp_path, execution, mode="oidc")
    assert result.returncode == 0
    assert summary == "- `claude-cost step=impl-review auth=oidc model=claude-opus-5-5 total_cost_usd=0.2931`\n"
    assert outputs == NOT_STOPPED


@pytest.mark.parametrize("execution", [None, [], [{"type": "assistant"}], [{"type": "result"}]])
def test_summary_never_fails_without_a_cost(tmp_path, execution):
    result, summary, outputs = _summary(tmp_path, execution)
    assert result.returncode == 0
    assert "auth=subscription model=n/a total_cost_usd=n/a" in summary
    assert outputs == NOT_STOPPED


@pytest.mark.parametrize("case", sorted(LIMIT_FIXTURES))
@pytest.mark.parametrize("mode", ["subscription", "oidc", "api"])
def test_summary_detects_a_spend_or_usage_limit(tmp_path, case, mode):
    result, summary, outputs = _summary(tmp_path, LIMIT_FIXTURES[case], mode)
    assert result.returncode == 0
    assert outputs == {"stopped": "true", "stop_reason": "limit"}, case
    assert f"::error::Claude spend/usage limit reached (auth={mode}) in impl-review" in result.stdout
    assert f"- **Claude spend/usage limit reached (auth={mode})** in `impl-review`" in summary


@pytest.mark.parametrize("case", sorted(AUTH_FIXTURES))
@pytest.mark.parametrize("mode", ["oidc", "api"])
def test_summary_detects_refused_credentials_with_api_and_oidc(tmp_path, case, mode):
    result, summary, outputs = _summary(tmp_path, AUTH_FIXTURES[case], mode)
    assert outputs == {"stopped": "true", "stop_reason": "auth"}, case
    assert f"::error::Claude credentials refused (auth={mode}) in impl-review" in result.stdout
    assert f"- **Claude credentials refused (auth={mode})** in `impl-review`" in summary


@pytest.mark.parametrize("case", sorted(AUTH_FIXTURES))
def test_the_subscription_keeps_its_handling_of_refused_credentials(tmp_path, case):
    assert _summary(tmp_path, AUTH_FIXTURES[case], "subscription")[2] == NOT_STOPPED


def test_a_limit_wins_over_its_status_code(tmp_path):
    """A 403 with a usage-limit message is a limit, not refused credentials."""
    execution = _failed("You've hit your session limit · resets 12:30pm", error="rate_limit", status=403)
    assert _summary(tmp_path, execution, "oidc")[2] == {"stopped": "true", "stop_reason": "limit"}


@pytest.mark.parametrize("case", sorted(NOT_A_STOP))
@pytest.mark.parametrize("mode", ["subscription", "api"])
def test_summary_ignores_everything_else(tmp_path, case, mode):
    result, summary, outputs = _summary(tmp_path, NOT_A_STOP[case], mode)
    assert outputs == NOT_STOPPED, case
    assert "limit reached" not in summary and "refused" not in summary


# --- the failure paths after a stop -------------------------------------------


# Logs every call as one JSON line; `pr view` answers with $GH_LABELS.
FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "view"]:
    print(os.environ.get("GH_LABELS", ""))
"""


def _run(tmp_path: Path, script: str, **env: str) -> tuple[subprocess.CompletedProcess, list]:
    for expr, value in {
        "${{ github.repository }}": "owner/repo",
        "${{ github.run_id }}": "1",
        "${{ matrix.spec_id }}": "spec-a",
    }.items():
        script = script.replace(expr, value)
    assert "${{" not in script
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, body in {"gh": FAKE_GH, "sleep": "#!/bin/sh\nexit 0\n"}.items():
        (bin_dir / name).write_text(body, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
    log = tmp_path / "gh.log"
    base = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={**base, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "GH_LOG": str(log), **env},
        capture_output=True,
        text=True,
    )
    calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    return result, calls


def _run_step(tmp_path: Path, filename: str, name: str, **env: str):
    return _run(tmp_path, _step(filename, name)["run"], **env)


def _bodies(calls: list[list[str]]) -> list[str]:
    return [c[c.index("--body") + 1] for c in calls if "--body" in c]


GENERATION_ENV = {
    "SPEC_ID": "spec-a",
    "LIBRARY": "plotly",
    "ISSUE": "42",
    "MODEL": "sonnet",
    "CHANGE_REQUEST": "",
    "CAMPAIGN_WINDOW_H": "12",
    "INFRA_WINDOW_CAP": "5",
    "CLAUDE_RETRY_OUTCOME": "skipped",
    "CLAUDE_EXEC_FILE": "",
    "CLAUDE_STOPPED": "true",
    "LANGUAGE": "python",
    "EXT": ".py",
    "REGEN_GATE": "true",
    "SOURCE_REF": "",
    "SOURCE_MODEL": "",
    "ADOPT_CAUSE": "",
    "TRIGGER_REF": "main",
    "RUN_URL": "https://github.com/owner/repo/actions/runs/1",
}


@pytest.mark.parametrize(
    ("mode", "reason", "why"),
    [
        ("subscription", "limit", "Claude spend/usage limit reached"),
        ("oidc", "limit", "Claude spend/usage limit reached"),
        ("oidc", "auth", "Claude credentials refused"),
    ],
)
@pytest.mark.parametrize(("regen_label", "live"), [("regen", True), ("", False)])
def test_a_stopped_generation_is_parked(tmp_path, regen_label, live, mode, reason, why):
    """A first implementation too: no retry, no counted attempt, never `impl:<lib>:failed`."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    env = GENERATION_ENV | {"CLAUDE_MODE": mode, "STOP_REASON": reason, "REGEN_LABEL": regen_label}
    result, calls = _run_step(tmp_path, "impl-generate.yml", "Handle generation failure", **env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"::error::{why} (auth={mode})" in result.stdout
    assert not [c for c in calls if c[:2] == ["workflow", "run"]]  # no auto-retry
    edits = [c[3:5] for c in calls if c[:2] == ["issue", "edit"]]
    assert ["--remove-label", "impl:plotly:pending"] in edits and ["--remove-label", "generate:plotly"] in edits
    assert (["--add-label", "impl:plotly:done"] in edits) is live
    assert not any("impl:plotly:failed" in c for c in edits)  # never a capability verdict
    assert not [c for c in calls if c[:2] == ["api", "--paginate"]]  # the attempt budget is not even read
    (body,) = _bodies(calls)
    # Its own marker: neither the 3-attempt cap nor daily-regen's attempt window counts it.
    assert "<!-- impl-paused-claude:spec-a:plotly -->" in body and why in body
    assert "<!-- impl-fail:" not in body and "impl-fail-cause:infra" not in body


@pytest.mark.parametrize(("reason", "why"), [("limit", "spend/usage limit"), ("auth", "credentials refused")])
def test_a_stopped_repair_is_paused_and_keeps_its_retry(tmp_path, reason, why):
    result, calls = _run_step(
        tmp_path,
        "impl-repair.yml",
        "Handle repair failure",
        PR_NUM="7",
        SPEC_ID="spec-a",
        LIBRARY="plotly",
        ATTEMPT="2",
        MODEL="sonnet",
        REPOSITORY="owner/repo",
        RUN_ID="1",
        CLAUDE_STOPPED="true",
        STOP_REASON=reason,
        CLAUDE_MODE="oidc",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert why in result.stdout
    assert ["pr", "edit", "7", "--add-label", "ai-rejected"] in calls
    assert ["pr", "edit", "7", "--add-label", "ai-repair-paused"] in calls
    assert any(c[:3] == ["label", "create", "ai-repair-paused"] for c in calls)
    assert not [c for c in calls if c[:2] == ["workflow", "run"]]
    assert not [c for c in calls if c[:1] == ["api"]]  # the retry budget is not even read
    (body,) = _bodies(calls)
    assert "<!-- repair-paused-claude:spec-a:plotly:attempt-2 -->" in body
    assert "<!-- repair-retry:" not in body


@pytest.mark.parametrize(("reason", "why"), [("limit", "spend/usage limit"), ("auth", "credentials refused")])
def test_a_stopped_review_is_paused_without_spending_the_retry(tmp_path, reason, why):
    result, calls = _run_step(
        tmp_path,
        "impl-review.yml",
        "Validate review output",
        PR_NUM="7",
        SPEC_ID="spec-a",
        LIBRARY="plotly",
        REPOSITORY="owner/repo",
        RUN_ID="1",
        MODEL="sonnet",
        REVIEW_MODEL_ALIAS="opus",
        CLAUDE_STOPPED="true",
        STOP_REASON=reason,
        CLAUDE_MODE="oidc",
    )
    assert result.returncode == 1  # no verdict: the run is red
    assert why in result.stdout
    assert ["pr", "edit", "7", "--add-label", "ai-review-paused"] in calls
    assert not [c for c in calls if "ai-review-failed" in c]  # the watchdog's label stays off
    assert any(c[:3] == ["label", "create", "ai-review-paused"] for c in calls)
    assert not [c for c in calls if c[:2] == ["api", "repos/owner/repo/dispatches"]]  # no re-review
    assert not [c for c in calls if c[:2] == ["api", "--paginate"]]
    (body,) = _bodies(calls)
    assert "<!-- review-paused-claude:spec-a:plotly -->" in body
    assert "<!-- review-retry:" not in body


@pytest.mark.parametrize(
    ("filename", "name"),
    [
        ("impl-generate.yml", "Handle generation failure"),
        ("impl-repair.yml", "Handle repair failure"),
        ("impl-review.yml", "Validate review output"),
    ],
)
def test_failure_paths_read_the_stop(filename, name):
    env = _step(filename, name)["env"]
    assert env["CLAUDE_MODE"] == "${{ steps.claude_auth.outputs.mode }}"
    if filename == "impl-review.yml":
        assert env["CLAUDE_STOPPED"] == "${{ steps.review_cost.outputs.stopped }}"
        assert env["STOP_REASON"] == "${{ steps.review_cost.outputs.stop_reason }}"
    else:
        assert env["CLAUDE_STOPPED"] == (
            "${{ steps.claude_cost.outputs.stopped == 'true' || steps.claude_retry_cost.outputs.stopped == 'true' }}"
        )
        assert env["STOP_REASON"] == (
            "${{ steps.claude_cost.outputs.stop_reason || steps.claude_retry_cost.outputs.stop_reason }}"
        )


def test_generation_park_comes_before_any_attempt_counting():
    """The park exits before the infra/agent split reads or writes a single impl-fail marker."""
    script = _step("impl-generate.yml", "Handle generation failure")["run"]
    park = script.index('if [ "${CLAUDE_STOPPED}" = "true" ]; then')
    assert park < script.index('INFRA_CAUSE=""') < script.index('MARKER="<!-- impl-fail:')


def test_a_stopped_review_gives_no_score_verdict_or_gate_decision():
    """Even when it wrote quality_score.txt before the stop: Extract skips, Validate takes the paused path."""
    extract = _step("impl-review.yml", "Extract quality score")
    assert extract["if"] == "steps.review.conclusion == 'success' && steps.review_cost.outputs.stopped != 'true'"
    # With Extract skipped, has_output is '' — Validate runs, every scored step does not.
    validate = _step("impl-review.yml", "Validate review output")
    assert validate["if"] == "steps.review.conclusion == 'success' && steps.score.outputs.has_output != 'true'"
    names = _names("impl-review.yml", "review")
    assert names.index("Claude session summary") < names.index("Extract quality score")
    assert names.index("Extract quality score") < names.index("Validate review output")


@pytest.mark.parametrize(("labels", "removed"), [("ai-review-paused\nquality:80", True), ("quality:80", False)])
def test_a_resumed_review_clears_its_pause(tmp_path, labels, removed):
    names = _names("impl-review.yml", "review")
    assert names.index("Clear the ai-review-paused label") < names.index("Run AI Quality Review")
    result, calls = _run_step(
        tmp_path, "impl-review.yml", "Clear the ai-review-paused label", PR_NUM="7", GH_LABELS=labels
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (["pr", "edit", "7", "--remove-label", "ai-review-paused"] in calls) is removed


def test_a_resumed_repair_clears_its_pause():
    script = _step("impl-repair.yml", "Remove ai-rejected label")["run"]
    assert '--remove-label "ai-repair-paused"' in script
    names = _names("impl-repair.yml", "repair")
    assert names.index("Remove ai-rejected label") < names.index("Run Claude Code to repair implementation")


# --- the watchdog skips paused PRs ----------------------------------------------


# `pr list` answers with $GH_PRS_JSON, `issue list` with nothing; every `api`
# call fails, which the scan reads as "daily-regen state unknown".
FAKE_GH_WATCHDOG = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "list"]:
    print(os.environ["GH_PRS_JSON"])
elif sys.argv[1:3] == ["issue", "list"]:
    print("[]")
elif sys.argv[1:2] == ["api"]:
    sys.exit(1)
"""


@pytest.mark.parametrize(
    "labels",
    [
        ["ai-review-paused", "ai-review-failed"],  # Case 1 would re-dispatch the review
        ["ai-repair-paused", "ai-rejected", "ai-attempt-2", "quality:70"],  # Case 2b would re-dispatch the repair
    ],
)
def test_the_watchdog_skips_paused_prs(tmp_path, labels):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH_WATCHDOG, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    prs = [
        {
            "number": 7,
            "labels": [{"name": n} for n in labels],
            "headRefName": "implementation/spec-a/plotly",
            "updatedAt": "2026-01-01T00:00:00Z",
        }
    ]
    log = tmp_path / "gh.log"
    script = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]
    base = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={
            **base,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "GH_LOG": str(log),
            "GH_TOKEN": "unused",
            "GH_REPO": "owner/repo",
            "GH_PRS_JSON": json.dumps(prs),
            "STALE_HOURS": "4",
            "DRY_RUN": "false",
            "REGEN_PAIRS": "",
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert "PR #7: paused" in result.stdout
    assert not [c for c in calls if c[:2] == ["workflow", "run"]]
    assert not [c for c in calls if c[:2] == ["pr", "edit"]]


# --- daily-regen modes ------------------------------------------------------


def _daily_step(name: str) -> dict[str, Any]:
    return _step("daily-regen.yml", name)


@pytest.mark.parametrize(
    ("pairs", "override", "rc", "mode"),
    [
        ("", "", 0, "spec"),
        ("", "scatter-basic", 0, "spec"),
        ("5", "scatter-basic", 0, "spec"),
        ("5", "", 0, "pairs"),
        ("12", "", 0, "pairs"),
        ("0", "", 1, None),
        ("-3", "", 1, None),
        ("five", "", 1, None),
        (" 5", "", 1, None),
    ],
)
def test_daily_regen_mode(tmp_path, pairs, override, rc, mode):
    out = tmp_path / "out"
    env = {**os.environ, "PAIRS": pairs, "SPEC_OVERRIDE": override, "GITHUB_OUTPUT": str(out)}
    result = subprocess.run(
        ["bash", "-e", "-c", _daily_step("Resolve regen mode")["run"]], env=env, capture_output=True, text=True
    )
    assert result.returncode == rc, result.stdout + result.stderr
    if mode:
        assert f"mode={mode}" in out.read_text()
        assert (f"pairs={pairs}" in out.read_text()) is (mode == "pairs")


def test_daily_regen_mode_sources():
    """The variable drives only the schedule; a manual run keeps its inputs."""
    workflow = _load("daily-regen.yml")
    env = _daily_step("Resolve regen mode")["env"]
    assert env["PAIRS"] == "${{ github.event_name == 'schedule' && vars.REGEN_PAIRS_PER_DAY || inputs.pairs }}"
    inputs = (workflow.get(True) or workflow["on"])["workflow_dispatch"]["inputs"]
    assert inputs["pairs"]["default"] == "" and inputs["attempt_window_days"]["default"] == ""
    assert {"specification_id", "model", "count", "min_age_hours", "dry_run"} <= set(inputs)
    assert _daily_step("Pick oldest spec(s) (or use override)")["if"] == "steps.mode.outputs.mode == 'spec'"
    pick = _daily_step("Pick oldest pairs (pair mode)")
    assert pick["if"] == "steps.mode.outputs.mode == 'pairs'"
    assert pick["env"]["ATTEMPT_WINDOW_DAYS"] == (
        "${{ inputs.attempt_window_days || vars.REGEN_ATTEMPT_WINDOW_DAYS || '30' }}"
    )
    assert '--attempt-window-days "$ATTEMPT_WINDOW_DAYS"' in pick["run"]
    outputs = workflow["jobs"]["pick"]["outputs"]
    assert outputs["specs_json"] == "${{ steps.pick.outputs.specs_json || steps.pick_pairs.outputs.specs_json }}"
    assert outputs["resume_json"] == "${{ steps.pick_pairs.outputs.resume_json }}"
    assert outputs["resume_count"] == "${{ steps.pick_pairs.outputs.resume_count }}"


def test_spec_mode_steps_are_gated_off_in_pair_mode():
    assert (
        "needs.pick.outputs.mode != 'pairs'" in _daily_step("Spec polish (autonomous, opens PR with auto-merge)")["if"]
    )
    assert _daily_step("Dispatch bulk-generate with change_requests")["if"] == (
        "${{ !inputs.dry_run && needs.pick.outputs.mode != 'pairs' }}"
    )
    assert _daily_step("Dispatch impl-generate for each picked pair (pair mode)")["if"] == (
        "${{ !inputs.dry_run && needs.pick.outputs.mode == 'pairs' }}"
    )
    # The similarity audit runs in both modes.
    assert "if" not in _daily_step("Cross-library similarity audit")


FAKE_DISPATCH_GH = """#!/bin/sh
printf '%s\\n' "$@" >> "$GH_LOG"
echo "--END--" >> "$GH_LOG"
"""
FAKE_YQ = """#!/bin/sh
sed -n 's/^issue: //p' "$2"
"""


def _calls(log: Path) -> list[list[str]]:
    calls, current = [], []
    for line in log.read_text().splitlines() if log.exists() else []:
        if line == "--END--":
            calls.append(current)
            current = []
        else:
            current.append(line)
    return calls


def _dispatch_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in {
        "gh": FAKE_DISPATCH_GH,
        "yq": FAKE_YQ,
        "sleep": '#!/bin/sh\necho "slept $1" >> "$GH_LOG.sleep"\n',
    }.items():
        (bin_dir / name).write_text(body, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
    return bin_dir


def test_pair_dispatch_mirrors_bulk_generate(tmp_path):
    bin_dir = _dispatch_bin(tmp_path)
    (tmp_path / "plots" / "a-spec").mkdir(parents=True)
    (tmp_path / "plots" / "a-spec" / "specification.yaml").write_text("issue: 42\n", encoding="utf-8")
    pairs = [
        {"spec": "b-spec", "library": "plotly"},
        {"spec": "a-spec", "library": "altair"},
        {"spec": "a-spec", "library": "plotly"},
    ]
    step = _daily_step("Dispatch impl-generate for each picked pair (pair mode)")
    script = step["run"].replace("${{ github.repository }}", "owner/repo")
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "SPEC_ID": "a-spec",
        "MODEL": "auto",
        "CHANGE_REQUESTS": json.dumps({"plotly": "Use a horizontal layout"}),
        "PAIRS_JSON": json.dumps(pairs),
        "PACE_SECONDS": "180",
    }
    result = subprocess.run(["bash", "-e", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    def dispatch(library: str, hint: str) -> list[str]:
        fields = {
            "specification_id": "a-spec",
            "library": library,
            "model": "auto",
            "change_request": hint,
            "regen_gate": "true",
            "source_ref": "",
            "source_model": "",
            "issue_number": "42",
        }
        args = ["workflow", "run", "impl-generate.yml", "--repo", "owner/repo"]
        for key, value in fields.items():
            args += ["-f", f"{key}={value}"]
        return args

    # bulk-generate's arguments, pair by pair, with the library's own hint.
    assert _calls(tmp_path / "gh.log") == [dispatch("altair", ""), dispatch("plotly", "Use a horizontal layout")]
    # b-spec/plotly is the run's first dispatch (another matrix entry): both of
    # this entry's dispatches wait the pace first.
    assert (tmp_path / "gh.log.sleep").read_text().splitlines() == ["slept 180", "slept 180"]
    assert (
        step["env"]["PACE_SECONDS"] == "${{ (inputs.model == 'sonnet' || inputs.model == 'haiku') && '120' || '180' }}"
    )


def test_paused_prs_are_resumed_first(tmp_path):
    job = _load("daily-regen.yml")["jobs"]["resume-paused"]
    assert job["needs"] == "pick"
    assert job["if"] == (
        "${{ needs.pick.outputs.mode == 'pairs' && needs.pick.outputs.resume_count != '0' "
        "&& needs.pick.outputs.resume_count != '' && !inputs.dry_run }}"
    )
    assert job["permissions"] == {"contents": "read", "actions": "write"}
    bin_dir = _dispatch_bin(tmp_path)
    resume = [
        {"pr": 7, "kind": "review", "spec": "a-spec", "library": "plotly", "attempt": 1},
        {"pr": 8, "kind": "repair", "spec": "b-spec", "library": "altair", "attempt": 2},
    ]
    script = _daily_step("Re-dispatch paused reviews and repairs")["run"].replace(
        "${{ github.repository }}", "owner/repo"
    )
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "RESUME_JSON": json.dumps(resume),
        "PACE_SECONDS": "180",
    }
    result = subprocess.run(["bash", "-e", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _calls(tmp_path / "gh.log") == [
        ["workflow", "run", "impl-review.yml", "-f", "pr_number=7", "--repo", "owner/repo"],
        [
            "workflow",
            "run",
            "impl-repair.yml",
            "-f",
            "pr_number=8",
            "-f",
            "specification_id=b-spec",
            "-f",
            "library=altair",
            "-f",
            "attempt=2",
            "--repo",
            "owner/repo",
        ],
    ]
    assert (tmp_path / "gh.log.sleep").read_text().splitlines() == ["slept 180"]


def test_watchdog_rescue_forwards_the_pair_count():
    scan = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")
    assert scan["env"]["REGEN_PAIRS"] == "${{ vars.REGEN_PAIRS_PER_DAY }}"
    assert 'daily-regen.yml ${REGEN_PAIRS:+-f "pairs=$REGEN_PAIRS"} || true' in scan["run"]
