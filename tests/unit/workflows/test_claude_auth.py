"""Claude credential switch (vars.CLAUDE_AUTH) and the per-session cost line.

Every claude-code-action step passes exactly one non-empty credential: the
subscription's CLAUDE_CODE_OAUTH_TOKEN unless CLAUDE_AUTH is `api`, then
ANTHROPIC_API_KEY. The action's precedence with both set is undocumented, so
the other input is always the empty string. Every job that runs Claude starts
with the same check step, which stops on an unknown value or on `api` without
the key instead of falling back to the subscription, and every Claude step is
followed by the same cost step. There is no pre-merge smoke for these
workflows (claude-code-action refuses to run on a PR that changes them), so
the wiring is pinned here and the check step runs for real.

Also here: daily-regen's mode switch (REGEN_PAIRS_PER_DAY / the `pairs`
input), its pair dispatch and the watchdog's rescue, which forwards the pair
count. The pick itself is tested in tests/unit/automation/scripts/
test_regen_pick_pairs.py.
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
API_KEY = "${{ vars.CLAUDE_AUTH == 'api' && secrets.ANTHROPIC_API_KEY || '' }}"
OAUTH = "${{ vars.CLAUDE_AUTH != 'api' && secrets.CLAUDE_CODE_OAUTH_TOKEN || '' }}"
AUTH_MODE = "${{ vars.CLAUDE_AUTH == 'api' && 'api' || 'subscription' }}"
CHECK = "Check Claude credentials"
COST = "Claude cost to the job summary"
# Inputs that would select another credential or provider.
OTHER_CREDENTIALS = {
    "anthropic_federation_rule_id",
    "anthropic_organization_id",
    "anthropic_service_account_id",
    "anthropic_workspace_id",
    "use_bedrock",
    "use_vertex",
    "use_foundry",
    "claude_env",
}
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


def _load(filename: str) -> dict[str, Any]:
    return yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))


def _claude_jobs() -> list[tuple[str, str, list[dict[str, Any]]]]:
    jobs = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for name, job in (_load(path.name).get("jobs") or {}).items():
            steps = job.get("steps") or []
            if any(str(s.get("uses", "")).startswith(ACTION) for s in steps):
                jobs.append((path.name, name, steps))
    return jobs


def _is_claude(step: dict[str, Any]) -> bool:
    return str(step.get("uses", "")).startswith(ACTION)


def _check_steps() -> list[dict[str, Any]]:
    return [s for _, _, steps in _claude_jobs() for s in steps if s.get("name") == CHECK]


def test_every_claude_workflow_is_covered():
    found: dict[str, int] = {}
    for filename, _, steps in _claude_jobs():
        found[filename] = found.get(filename, 0) + sum(1 for s in steps if _is_claude(s))
    assert found == CLAUDE_WORKFLOWS


@pytest.mark.parametrize(("filename", "job", "steps"), _claude_jobs(), ids=lambda v: v if isinstance(v, str) else "")
def test_each_claude_step_passes_exactly_the_switched_credentials(filename, job, steps):
    for step in filter(_is_claude, steps):
        given = step.get("with") or {}
        assert given.get("anthropic_api_key") == API_KEY, (filename, step.get("name"))
        assert given.get("claude_code_oauth_token") == OAUTH, (filename, step.get("name"))
        assert not OTHER_CREDENTIALS & set(given), (filename, step.get("name"))
        env = step.get("env") or {}
        assert not {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"} & set(env), (filename, step.get("name"))


@pytest.mark.parametrize(("filename", "job", "steps"), _claude_jobs(), ids=lambda v: v if isinstance(v, str) else "")
def test_the_check_runs_before_any_claude_step(filename, job, steps):
    names = [s.get("name") for s in steps]
    assert names.count(CHECK) == 1, (filename, job)
    check = steps[names.index(CHECK)]
    first_claude = next(i for i, s in enumerate(steps) if _is_claude(s))
    assert names.index(CHECK) < first_claude
    # Unconditional, or gated exactly like the first Claude step (a label
    # event that never reaches Claude must not fail on a misconfigured switch).
    assert check.get("if") in (None, steps[first_claude].get("if")), (filename, job)
    assert "continue-on-error" not in check


def test_every_check_step_is_identical():
    checks = _check_steps()
    assert len(checks) == len(_claude_jobs()) == 8
    reference = {k: v for k, v in checks[0].items() if k != "if"}
    for check in checks[1:]:
        assert {k: v for k, v in check.items() if k != "if"} == reference
    assert reference["env"] == {
        "CLAUDE_AUTH": "${{ vars.CLAUDE_AUTH }}",
        "API_KEY_SET": "${{ secrets.ANTHROPIC_API_KEY != '' }}",
    }


@pytest.mark.parametrize(("filename", "job", "steps"), _claude_jobs(), ids=lambda v: v if isinstance(v, str) else "")
def test_each_claude_step_is_followed_by_its_cost_step(filename, job, steps):
    """Read before the next Claude step: a retry writes the same execution file."""
    for i, step in enumerate(steps):
        if not _is_claude(step):
            continue
        sid = step["id"]
        later = steps[i + 1 :]
        cost = next(s for s in later if str(s.get("name", "")).startswith(COST))
        next_claude = next((j for j, s in enumerate(later) if _is_claude(s)), len(later))
        assert later.index(cost) < next_claude, (filename, step.get("name"))
        assert cost["if"] == (
            f"${{{{ !cancelled() && (steps.{sid}.outcome == 'success' || steps.{sid}.outcome == 'failure') }}}}"
        )
        assert cost["continue-on-error"] is True
        assert cost["env"]["EXECUTION_FILE"] == f"${{{{ steps.{sid}.outputs.execution_file }}}}"
        assert cost["env"]["CLAUDE_AUTH_MODE"] == AUTH_MODE


def test_cost_steps_share_one_script_and_unique_labels():
    costs = [s for _, _, steps in _claude_jobs() for s in steps if s.get("name", "").startswith(COST)]
    labels = [s["env"]["CLAUDE_STEP"] for s in costs]
    assert len(labels) == len(set(labels)) == sum(CLAUDE_WORKFLOWS.values())
    assert all(" " not in label for label in labels)
    assert len({s["run"] for s in costs}) == 1
    # The line must not look like Claude Code's own `"total_cost_usd": n`, or
    # collect_week.py's fallback regex would count a session twice.
    assert '"total_cost_usd":' not in costs[0]["run"]


def _run_cost(tmp_path: Path, execution: list[dict[str, Any]] | None, mode: str = "subscription") -> tuple[int, str]:
    script = next(s for _, _, steps in _claude_jobs() for s in steps if s.get("name", "").startswith(COST))["run"]
    exec_file = tmp_path / "claude-execution-output.json"
    if execution is not None:
        exec_file.write_text(json.dumps(execution), encoding="utf-8")
    summary = tmp_path / "summary"
    env = {
        **os.environ,
        "EXECUTION_FILE": str(exec_file) if execution is not None else "",
        "CLAUDE_AUTH_MODE": mode,
        "CLAUDE_STEP": "impl-generate",
        "GITHUB_STEP_SUMMARY": str(summary),
    }
    result = subprocess.run(["bash", "-e", "-c", script], env=env, capture_output=True, text=True)
    return result.returncode, summary.read_text() if summary.exists() else ""


def test_cost_step_reads_the_result_message(tmp_path):
    execution = [
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
        {"type": "assistant"},
        {"type": "result", "subtype": "success", "total_cost_usd": 0.2931},
    ]
    rc, summary = _run_cost(tmp_path, execution, mode="api")
    assert rc == 0
    assert summary == "- `claude-cost step=impl-generate auth=api model=claude-sonnet-5-5 total_cost_usd=0.2931`\n"


@pytest.mark.parametrize("execution", [None, [], [{"type": "assistant"}], [{"type": "result"}]])
def test_cost_step_never_fails_without_a_cost(tmp_path, execution):
    rc, summary = _run_cost(tmp_path, execution)
    assert rc == 0
    assert "auth=subscription model=n/a total_cost_usd=n/a" in summary


def test_the_api_key_reaches_nothing_but_the_action_input():
    """The key is never put into an env block, a script or another action."""
    for path in WORKFLOWS_DIR.glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "ANTHROPIC_API_KEY" not in line or line.lstrip().startswith("#"):
                continue
            stripped = line.strip()
            assert (
                stripped in {f"anthropic_api_key: {API_KEY}", "API_KEY_SET: ${{ secrets.ANTHROPIC_API_KEY != '' }}"}
                or "secrets.ANTHROPIC_API_KEY" not in stripped
            ), (path.name, stripped)


def test_no_pull_request_target_workflow_runs_claude():
    """A fork PR never reaches either credential (no secrets on `pull_request`)."""
    for filename in CLAUDE_WORKFLOWS:
        triggers = _load(filename).get(True) or _load(filename).get("on")
        assert "pull_request_target" not in (triggers or {}), filename
        assert "pull_request" not in (triggers or {}), filename


# --- the check step, run for real ------------------------------------------


def _run_check(tmp_path: Path, auth: str | None, key_set: bool) -> subprocess.CompletedProcess:
    script = _check_steps()[0]["run"]
    env = {k: v for k, v in os.environ.items() if k not in {"CLAUDE_AUTH", "API_KEY_SET"}}
    env["API_KEY_SET"] = "true" if key_set else "false"
    if auth is not None:
        env["CLAUDE_AUTH"] = auth
    return subprocess.run(["bash", "-e", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True)


def _expression(auth: str, key: str, token: str) -> tuple[str, str]:
    """The two inputs as GitHub evaluates them: `==` ignores case, `a && b || ''` yields b or ''."""
    is_api = auth.casefold() == "api"
    return (key if is_api and key else "", token if not is_api and token else "")


@pytest.mark.parametrize(
    ("auth", "key_set", "ok", "mode"),
    [
        (None, False, True, "subscription"),
        ("", False, True, "subscription"),
        ("subscription", False, True, "subscription"),
        ("Subscription", True, True, "subscription"),
        ("api", True, True, "api"),
        ("API", True, True, "api"),
        ("api", False, False, None),
        ("apikey", True, False, None),
        (" api", True, False, None),
        ("api\n::warning::injected", True, False, None),
    ],
)
def test_check_step(tmp_path, auth, key_set, ok, mode):
    result = _run_check(tmp_path, auth, key_set)
    assert (result.returncode == 0) is ok, result.stdout + result.stderr
    if ok:
        assert f"Claude credentials: {mode}" in result.stdout
        # Whatever the check lets through, the step gets exactly one credential, the right one.
        key, token = _expression(auth or "", "sk-ant-key" if key_set else "", "oauth-token")
        assert bool(key) != bool(token)
        assert bool(key) is (mode == "api")
    else:
        assert result.stdout.startswith("::error::")
        assert "\n::warning::" not in result.stdout


# --- daily-regen modes ------------------------------------------------------


def _daily_step(name: str) -> dict[str, Any]:
    steps = [s for job in _load("daily-regen.yml")["jobs"].values() for s in job.get("steps", [])]
    return next(s for s in steps if s.get("name") == name)


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
    assert inputs["pairs"]["default"] == ""
    assert {"specification_id", "model", "count", "min_age_hours", "dry_run"} <= set(inputs)
    assert _daily_step("Pick oldest spec(s) (or use override)")["if"] == "steps.mode.outputs.mode == 'spec'"
    assert _daily_step("Pick oldest pairs (pair mode)")["if"] == "steps.mode.outputs.mode == 'pairs'"
    outputs = workflow["jobs"]["pick"]["outputs"]
    assert outputs["specs_json"] == "${{ steps.pick.outputs.specs_json || steps.pick_pairs.outputs.specs_json }}"


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


FAKE_GH = """#!/bin/sh
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


def test_pair_dispatch_mirrors_bulk_generate(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in {
        "gh": FAKE_GH,
        "yq": FAKE_YQ,
        "sleep": '#!/bin/sh\necho "slept $1" >> "$GH_LOG.sleep"\n',
    }.items():
        (bin_dir / name).write_text(body, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
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


def test_watchdog_rescue_forwards_the_pair_count():
    steps = [s for job in _load("watchdog-stuck-jobs.yml")["jobs"].values() for s in job.get("steps", [])]
    scan = next(s for s in steps if s.get("name") == "Scan and dispatch")
    assert scan["env"]["REGEN_PAIRS"] == "${{ vars.REGEN_PAIRS_PER_DAY }}"
    assert 'daily-regen.yml ${REGEN_PAIRS:+-f "pairs=$REGEN_PAIRS"} || true' in scan["run"]
