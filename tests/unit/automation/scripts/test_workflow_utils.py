"""Tests for automation.scripts.workflow_utils module."""

from automation.scripts.workflow_utils import (
    VALID_LIBRARIES,
    BranchInfo,
    extract_branch_info,
    extract_issue_reference,
    extract_parent_issue,
    extract_sub_issue,
    get_attempt_count,
    is_valid_library,
)


class TestExtractBranchInfo:
    """Tests for extract_branch_info function."""

    def test_valid_auto_branch(self):
        result = extract_branch_info("auto/scatter-basic/matplotlib")
        assert result == BranchInfo(spec_id="scatter-basic", library="matplotlib", is_auto_branch=True)

    def test_valid_auto_branch_complex_spec_id(self):
        result = extract_branch_info("auto/heatmap-correlation-annotated/seaborn")
        assert result.spec_id == "heatmap-correlation-annotated"
        assert result.library == "seaborn"

    def test_non_auto_branch_returns_none(self):
        assert extract_branch_info("feature/new-feature") is None
        assert extract_branch_info("main") is None
        assert extract_branch_info("develop") is None

    def test_malformed_auto_branch_returns_none(self):
        # Too few parts
        assert extract_branch_info("auto/scatter-basic") is None
        # Too many parts
        assert extract_branch_info("auto/scatter/basic/matplotlib/extra") is None

    def test_empty_or_none_returns_none(self):
        assert extract_branch_info("") is None
        assert extract_branch_info(None) is None


class TestExtractSubIssue:
    """Tests for extract_sub_issue function."""

    def test_standard_format(self):
        pr_body = "**Sub-Issue:** #42\nSome description"
        assert extract_sub_issue(pr_body) == 42

    def test_without_hash(self):
        pr_body = "Sub-Issue: 123"
        assert extract_sub_issue(pr_body) == 123

    def test_markdown_bold_format(self):
        pr_body = "**Sub-Issue:** #99"
        assert extract_sub_issue(pr_body) == 99

    def test_case_insensitive(self):
        pr_body = "sub-issue: #50"
        assert extract_sub_issue(pr_body) == 50

    def test_not_found(self):
        assert extract_sub_issue("No sub-issue reference") is None
        assert extract_sub_issue("Issue: #42") is None

    def test_empty_or_none(self):
        assert extract_sub_issue("") is None
        assert extract_sub_issue(None) is None


class TestExtractParentIssue:
    """Tests for extract_parent_issue function."""

    def test_from_pr_body(self):
        pr_body = "**Parent Issue:** #100"
        assert extract_parent_issue(pr_body) == 100

    def test_fallback_to_issue_body(self):
        pr_body = "No parent here"
        issue_body = "Parent Issue: #50"
        assert extract_parent_issue(pr_body, issue_body) == 50

    def test_pr_body_takes_precedence(self):
        pr_body = "Parent Issue: #100"
        issue_body = "Parent Issue: #50"
        assert extract_parent_issue(pr_body, issue_body) == 100

    def test_not_found_in_either(self):
        assert extract_parent_issue("No parent", "Also no parent") is None
        assert extract_parent_issue("No parent") is None


class TestGetAttemptCount:
    """Tests for get_attempt_count function."""

    def test_no_attempt_labels(self):
        labels = ["library:matplotlib", "generating"]
        assert get_attempt_count(labels) == 0

    def test_single_attempt_label(self):
        assert get_attempt_count(["ai-attempt-1", "library:matplotlib"]) == 1
        assert get_attempt_count(["ai-attempt-2"]) == 2
        assert get_attempt_count(["ai-attempt-3", "testing"]) == 3

    def test_multiple_attempt_labels_returns_max(self):
        # Shouldn't happen normally, but handle gracefully
        labels = ["ai-attempt-1", "ai-attempt-2"]
        assert get_attempt_count(labels) == 2

    def test_empty_labels(self):
        assert get_attempt_count([]) == 0
        assert get_attempt_count(None) == 0


class TestExtractIssueReference:
    """Tests for extract_issue_reference function."""

    def test_single_reference(self):
        assert extract_issue_reference("Closes #42") == 42

    def test_multiple_references_returns_first(self):
        assert extract_issue_reference("Closes #42 and relates to #100") == 42

    def test_no_reference(self):
        assert extract_issue_reference("No issues here") is None

    def test_empty_or_none(self):
        assert extract_issue_reference("") is None
        assert extract_issue_reference(None) is None


class TestIsValidLibrary:
    """Tests for is_valid_library function."""

    def test_valid_libraries(self):
        for lib in VALID_LIBRARIES:
            assert is_valid_library(lib) is True

    def test_case_insensitive(self):
        assert is_valid_library("MATPLOTLIB") is True
        assert is_valid_library("Seaborn") is True

    def test_invalid_libraries(self):
        assert is_valid_library("pandas") is False
        assert is_valid_library("numpy") is False
        assert is_valid_library("") is False
