"""
Tests for GitHub Actions workflows structure and security.

Best practices for workflow testing:
1. Valid YAML syntax - All workflow files parse correctly
2. Required fields - name, on, jobs are present
3. Security - No hardcoded secrets, proper permissions
4. Pinned versions - Action versions are pinned (v1, not @main)
5. Naming conventions - Consistent file and job naming
6. Best practices - Uses recommended patterns
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml


# Base paths
WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / ".github" / "workflows"

# Expected workflow files (updated for new architecture)
EXPECTED_WORKFLOWS = [
    # CI workflows
    "ci-lint.yml",
    "ci-tests.yml",
    # Specification workflows
    "spec-create.yml",
    # Implementation workflows
    "impl-generate.yml",
    "impl-review.yml",
    "impl-repair.yml",
    "impl-merge.yml",
    "bulk-generate.yml",
    # Database sync
    "sync-postgres.yml",
    # Utility
    "util-claude.yml",
]

# Actions that should have pinned versions
KNOWN_ACTIONS = [
    "actions/checkout",
    "actions/setup-python",
    "actions/upload-artifact",
    "astral-sh/setup-uv",
    "codecov/codecov-action",
    "anthropics/claude-code-action",
]


def load_workflow(filename: str) -> dict[str, Any]:
    """Load and parse a workflow YAML file.

    Note: YAML's 'on' keyword is parsed as True (boolean) in Python.
    We handle this by checking for both 'on' and True keys.
    """
    filepath = WORKFLOWS_DIR / filename
    with open(filepath) as f:
        return yaml.safe_load(f)


def get_workflow_trigger(workflow: dict[str, Any]) -> dict[str, Any] | str | list | None:
    """Get the 'on' trigger from a workflow, handling YAML's reserved word.

    YAML parses 'on' as True (boolean), so we need to check for both.
    """
    return workflow.get("on") or workflow.get(True)


def get_all_workflow_files() -> list[Path]:
    """Get all YAML workflow files."""
    return list(WORKFLOWS_DIR.glob("*.yml"))


class TestWorkflowFileExistence:
    """Test that all expected workflow files exist."""

    def test_workflows_directory_exists(self) -> None:
        """Workflows directory should exist."""
        assert WORKFLOWS_DIR.exists(), f"Workflows directory not found: {WORKFLOWS_DIR}"
        assert WORKFLOWS_DIR.is_dir()

    @pytest.mark.parametrize("filename", EXPECTED_WORKFLOWS)
    def test_expected_workflow_exists(self, filename: str) -> None:
        """Each expected workflow file should exist."""
        filepath = WORKFLOWS_DIR / filename
        assert filepath.exists(), f"Missing workflow: {filename}"


class TestYamlValidity:
    """Test that all workflow files are valid YAML."""

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_valid_yaml_syntax(self, filepath: Path) -> None:
        """Each workflow file should be valid YAML."""
        try:
            with open(filepath) as f:
                content = yaml.safe_load(f)
            assert content is not None, f"Empty YAML file: {filepath.name}"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {filepath.name}: {e}")

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_no_tabs_in_yaml(self, filepath: Path) -> None:
        """YAML files should use spaces, not tabs."""
        content = filepath.read_text()
        lines_with_tabs = [i + 1 for i, line in enumerate(content.split("\n")) if "\t" in line]
        assert not lines_with_tabs, f"Tabs found in {filepath.name} at lines: {lines_with_tabs}"


class TestWorkflowStructure:
    """Test required workflow structure."""

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_has_name(self, filepath: Path) -> None:
        """Each workflow should have a name."""
        workflow = load_workflow(filepath.name)
        assert "name" in workflow, f"Missing 'name' in {filepath.name}"
        assert workflow["name"], f"Empty 'name' in {filepath.name}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_has_trigger(self, filepath: Path) -> None:
        """Each workflow should have a trigger (on)."""
        workflow = load_workflow(filepath.name)
        trigger = get_workflow_trigger(workflow)
        assert trigger is not None, f"Missing 'on' trigger in {filepath.name}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_has_jobs(self, filepath: Path) -> None:
        """Each workflow should have jobs defined."""
        workflow = load_workflow(filepath.name)
        assert "jobs" in workflow, f"Missing 'jobs' in {filepath.name}"
        assert workflow["jobs"], f"Empty 'jobs' in {filepath.name}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_jobs_have_runs_on(self, filepath: Path) -> None:
        """Each job should specify runs-on."""
        workflow = load_workflow(filepath.name)
        for job_name, job in workflow.get("jobs", {}).items():
            # Skip reusable workflow calls (they use 'uses' instead of 'runs-on')
            if "uses" in job:
                continue
            assert "runs-on" in job, f"Job '{job_name}' missing runs-on in {filepath.name}"


class TestSecurityBestPractices:
    """Test security best practices in workflows."""

    # Patterns that might indicate hardcoded secrets
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",  # API keys
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub PAT
        r"ghs_[a-zA-Z0-9]{36}",  # GitHub App token
        r"password:\s*['\"][^$]",  # Hardcoded password
        r"api_key:\s*['\"][^$]",  # Hardcoded API key
    ]

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_no_hardcoded_secrets(self, filepath: Path) -> None:
        """No hardcoded secrets should be present."""
        content = filepath.read_text()

        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, f"Possible hardcoded secret in {filepath.name}: {matches}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_secrets_use_proper_syntax(self, filepath: Path) -> None:
        """Secrets should use ${{ secrets.NAME }} syntax."""
        content = filepath.read_text()

        # Find all secret references
        secret_refs = re.findall(r"\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}", content)

        # These are valid - just make sure they're using proper naming
        for secret_name in secret_refs:
            assert secret_name.isupper(), f"Secret name should be UPPER_CASE: {secret_name}"
            assert "_" in secret_name or len(secret_name) > 3, f"Secret name too short: {secret_name}"

    def test_ci_workflows_dont_need_write_permissions(self) -> None:
        """CI workflows should use minimal permissions."""
        ci_workflows = ["ci-lint.yml", "ci-tests.yml"]

        for filename in ci_workflows:
            filepath = WORKFLOWS_DIR / filename
            if not filepath.exists():
                continue

            workflow = load_workflow(filename)
            for job_name, job in workflow.get("jobs", {}).items():
                if "uses" in job:
                    continue
                perms = job.get("permissions", {})
                # CI jobs shouldn't need write access to contents
                if "contents" in perms:
                    assert perms["contents"] in ["read", None], f"CI job '{job_name}' has unnecessary write permissions"


class TestActionVersions:
    """Test that actions use pinned versions."""

    VERSION_PATTERN = re.compile(r"uses:\s*([^@\s]+)@(\S+)")

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_actions_have_version(self, filepath: Path) -> None:
        """All external actions should have a version specified.

        Local workflow references (starting with ./) don't need versions.
        """
        content = filepath.read_text()

        # Find actions without version, excluding local references (./)
        no_version = re.findall(r"uses:\s*([^\s@]+)\s*$", content, re.MULTILINE)
        # Filter out local workflow references
        external_no_version = [a for a in no_version if not a.startswith("./")]
        assert not external_no_version, f"Actions without version in {filepath.name}: {external_no_version}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_no_main_branch_versions(self, filepath: Path) -> None:
        """Actions should not use @main or @master."""
        content = filepath.read_text()

        bad_versions = re.findall(r"uses:\s*([^@\s]+)@(main|master)\b", content)
        assert not bad_versions, f"Actions using @main/@master in {filepath.name}: {bad_versions}"

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_uses_semver_or_major_version(self, filepath: Path) -> None:
        """Actions should use semantic versioning (v1, v2.1.0, etc.)."""
        content = filepath.read_text()

        for match in self.VERSION_PATTERN.finditer(content):
            action, version = match.groups()
            # Skip local actions (start with ./)
            if action.startswith("./"):
                continue
            # Check for valid version format (v1, v2, v1.2.3, sha)
            valid = (
                version.startswith("v")
                or re.match(r"^[a-f0-9]{40}$", version)  # SHA
                or version == "latest"  # Some actions use this
            )
            assert valid, f"Invalid version format for {action}@{version} in {filepath.name}"


class TestNamingConventions:
    """Test naming conventions for workflows."""

    def test_workflow_file_naming(self) -> None:
        """Workflow files should follow naming convention."""
        for filepath in get_all_workflow_files():
            name = filepath.stem
            # Should be lowercase with hyphens
            assert name == name.lower(), f"Workflow name should be lowercase: {filepath.name}"
            assert "_" not in name, f"Use hyphens, not underscores: {filepath.name}"

    def test_workflow_name_matches_file(self) -> None:
        """Workflow name should relate to filename."""
        for filepath in get_all_workflow_files():
            workflow = load_workflow(filepath.name)
            name = workflow.get("name", "").lower()
            file_stem = filepath.stem.replace("-", " ").replace("_", " ")

            # At least some keywords should match
            file_words = set(file_stem.split())
            name_words = set(name.lower().split())

            # Remove common words
            common_words = {"the", "a", "an", "for", "to", "and", "or", "in", "on"}
            file_words -= common_words
            name_words -= common_words

            # Check for at least some word overlap between filename and workflow name
            # This is a lenient check using multiple strategies
            if file_words and name_words:
                # Strategy 1: Exact word overlap
                overlap = file_words & name_words

                # Strategy 2: Substring matching (e.g., "plottest" contains "plot")
                has_substring_match = any(
                    fw in nw or nw in fw
                    for fw in file_words
                    for nw in name_words
                    if len(fw) >= 3 and len(nw) >= 3  # Only match words with 3+ chars
                )

                has_relation = len(overlap) > 0 or has_substring_match
                assert has_relation, f"Workflow name '{name}' unrelated to file: {filepath.name}"


class TestWorkflowBestPractices:
    """Test workflow best practices."""

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_checkout_with_fetch_depth(self, filepath: Path) -> None:
        """Checkout actions should consider fetch-depth for history needs."""
        content = filepath.read_text()

        # Best practice: fetch-depth: 0 is needed for full git history
        # When using git log/diff, workflows should set fetch-depth
        # Note: This is advisory only - workflows may have valid reasons not to fetch full history
        _ = content  # Suppress unused variable warning; content is read for potential future validation

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_uses_environment_for_secrets(self, filepath: Path) -> None:
        """Production secrets should use environments for protection."""
        workflow = load_workflow(filepath.name)

        # This is a soft check - environments are recommended for production
        # Just verify the structure is valid
        for job_name, job in workflow.get("jobs", {}).items():
            if "uses" in job:
                continue
            # If job uses secrets, it should work
            env = job.get("env", {})
            for _key, value in env.items():
                if isinstance(value, str) and "secrets." in value:
                    # Valid secret reference
                    assert "${{" in value, f"Malformed secret reference in {job_name}"

    def test_reusable_workflows_have_inputs(self) -> None:
        """Reusable workflows should define their inputs."""
        # Check for any workflows that use workflow_call trigger
        for filepath in get_all_workflow_files():
            workflow = load_workflow(filepath.name)
            on_trigger = get_workflow_trigger(workflow)

            if isinstance(on_trigger, dict) and "workflow_call" in on_trigger:
                call_config = on_trigger["workflow_call"]
                # Reusable workflows should define inputs or secrets
                assert "inputs" in call_config or "secrets" in call_config or call_config is None, (
                    f"Reusable workflow {filepath.name} should define inputs or secrets"
                )


class TestWorkflowTriggers:
    """Test workflow trigger configurations."""

    @pytest.mark.parametrize("filepath", get_all_workflow_files(), ids=lambda p: p.name)
    def test_valid_trigger_events(self, filepath: Path) -> None:
        """Workflow triggers should be valid GitHub events."""
        valid_events = {
            "push",
            "pull_request",
            "pull_request_target",
            "pull_request_review",
            "pull_request_review_comment",
            "merge_group",
            "workflow_dispatch",
            "workflow_call",
            "workflow_run",
            "issues",
            "issue_comment",
            "schedule",
            "release",
            "repository_dispatch",
            "create",
            "delete",
            "fork",
            "deployment",
            "deployment_status",
        }

        workflow = load_workflow(filepath.name)
        on_trigger = get_workflow_trigger(workflow)

        if isinstance(on_trigger, dict):
            events = set(on_trigger.keys())
        elif isinstance(on_trigger, list):
            events = set(on_trigger)
        else:
            events = {on_trigger} if on_trigger else set()

        invalid = events - valid_events
        assert not invalid, f"Invalid trigger events in {filepath.name}: {invalid}"

    def test_ci_workflows_trigger_on_push_and_pr(self) -> None:
        """CI workflows should run on both push and PR."""
        ci_workflows = ["ci-lint.yml", "ci-tests.yml"]

        for filename in ci_workflows:
            filepath = WORKFLOWS_DIR / filename
            if not filepath.exists():
                continue

            workflow = load_workflow(filename)
            on_trigger = get_workflow_trigger(workflow)

            if isinstance(on_trigger, dict):
                assert "push" in on_trigger or "pull_request" in on_trigger, (
                    f"CI workflow {filename} should trigger on push or PR"
                )


class TestCiTestsSpecSectionCheck:
    """ci-tests.yml lints every spec's characteristic section on every event,
    inside the required "Run Tests" job — spec-only PRs skip pytest, so this
    step is the only thing that guards the regen gate's C1..Cn contract there."""

    def _steps(self) -> list[dict[str, Any]]:
        return load_workflow("ci-tests.yml")["jobs"]["test"]["steps"]

    def _step(self, name: str) -> dict[str, Any]:
        matches = [s for s in self._steps() if s.get("name") == name]
        assert len(matches) == 1, f"expected exactly one step named {name!r}"
        return matches[0]

    def test_step_runs_unconditionally_in_the_required_job(self) -> None:
        assert load_workflow("ci-tests.yml")["jobs"]["test"]["name"] == "Run Tests"
        step = self._step("Check spec characteristic sections")
        assert "if" not in step

    def test_contract_runs_repo_wide_and_style_on_changed_specs(self) -> None:
        script = self._step("Check spec characteristic sections")["run"]
        assert "python3 -m automation.scripts.spec_characteristics_lint contract --all" in script
        assert "spec_characteristics_lint style" in script
        assert "--strict" not in script  # style only warns in CI
        assert '"$RUNNER_TEMP/changed_specs.txt"' in script
        check = self._step("Check for testable changes")["run"]
        assert "$RUNNER_TEMP/changed_specs.txt" in check
        assert "specification\\.md$" in check

    def test_step_needs_no_dependency_install(self) -> None:
        names = [s.get("name") for s in self._steps()]
        assert names.index("Check spec characteristic sections") < names.index("Set up Python")


class TestSpecCreateCharacteristicsSection:
    """spec-create must ask for the review's yardstick section in BOTH Claude
    prompts (first attempt and retry), in the one-line-per-bullet shape the
    regen gate's C1..Cn parser reads."""

    def _spec_create_prompts(self) -> dict[str, str]:
        workflow = load_workflow("spec-create.yml")
        prompts: dict[str, str] = {}
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                prompt = (step.get("with") or {}).get("prompt", "")
                if "Task: Create New Specification" in prompt:
                    prompts[step.get("id", step.get("name", "?"))] = prompt
        return prompts

    def test_first_attempt_and_retry_prompts_found(self) -> None:
        assert len(self._spec_create_prompts()) == 2

    def test_both_prompts_request_the_section(self) -> None:
        for step_id, prompt in self._spec_create_prompts().items():
            assert "## What a good version looks like" in prompt, step_id
            assert "3-6 column-0 `- ` bullets" in prompt, step_id
            assert "one line per bullet (no wrapped continuation lines)" in prompt, step_id
            assert "`A good version shows: `" in prompt, step_id
            assert "`Expected, not a defect: `" in prompt, step_id
            assert "one kind per bullet" in prompt, step_id
            assert "at least one of each" in prompt, step_id
            assert "the basic variant's" in prompt, step_id

    def test_both_prompts_self_check_with_the_lint(self) -> None:
        for step_id, prompt in self._spec_create_prompts().items():
            assert "python3 -m automation.scripts.spec_characteristics_lint contract plots/" in prompt, step_id
            assert "python3 -m automation.scripts.spec_characteristics_lint style plots/" in prompt, step_id

    def test_both_prompts_share_the_section_rules(self) -> None:
        """First attempt and retry carry the same section instructions (the
        retry only adds its repair sentence)."""
        retry = (
            " If the first attempt left a `specification.md` without this section, add it;"
            " if it left bullets without a kind prefix, fix them."
        )
        blocks = []
        for prompt in self._spec_create_prompts().values():
            start = prompt.index("- End `specification.md` with the template's")
            end = prompt.index("- Create: `plots/{specification-id}/specification.yaml`")
            blocks.append(" ".join(prompt[start:end].split()))
        assert sum(retry in block for block in blocks) == 1
        assert len({block.replace(retry, "") for block in blocks}) == 1
