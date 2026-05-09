"""
Workflow utility functions for GitHub Actions.

These functions extract and parse information from branches, PR bodies,
and issue labels. Used across multiple workflows for consistent parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.constants import SUPPORTED_LIBRARIES
from core.constants import is_valid_library as _is_valid_library


@dataclass
class BranchInfo:
    """Information extracted from an auto-generated branch name."""

    spec_id: str
    library: str
    is_auto_branch: bool = True


def extract_branch_info(branch: str) -> BranchInfo | None:
    """
    Extract spec_id and library from 'auto/{spec-id}/{library}' branch.

    Args:
        branch: Branch name (e.g., 'auto/scatter-basic/matplotlib')

    Returns:
        BranchInfo with spec_id and library, or None if not an auto branch

    Examples:
        >>> extract_branch_info('auto/scatter-basic/matplotlib')
        BranchInfo(spec_id='scatter-basic', library='matplotlib', is_auto_branch=True)

        >>> extract_branch_info('feature/new-feature')
        None
    """
    if not branch or not branch.startswith("auto/"):
        return None

    parts = branch.split("/")
    if len(parts) != 3:
        return None

    return BranchInfo(spec_id=parts[1], library=parts[2])


def extract_sub_issue(pr_body: str) -> int | None:
    """
    Extract sub-issue number from PR body.

    Looks for pattern: 'Sub-Issue: #123' or 'Sub-Issue: 123'

    Args:
        pr_body: The PR body text

    Returns:
        Sub-issue number or None if not found

    Examples:
        >>> extract_sub_issue('**Sub-Issue:** #42\\nSome text')
        42

        >>> extract_sub_issue('No sub-issue here')
        None
    """
    if not pr_body:
        return None

    # Match "Sub-Issue: #123" or "Sub-Issue:** #123" (markdown bold)
    match = re.search(r"Sub-Issue:?\*?\*?\s*#?(\d+)", pr_body, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def extract_parent_issue(pr_body: str, issue_body: str | None = None) -> int | None:
    """
    Extract parent issue number with fallback logic.

    First checks PR body for 'Parent Issue: #123', then falls back to
    issue body if provided.

    Args:
        pr_body: The PR body text
        issue_body: Optional issue body as fallback

    Returns:
        Parent issue number or None if not found

    Examples:
        >>> extract_parent_issue('**Parent Issue:** #100')
        100

        >>> extract_parent_issue('No parent', 'Parent Issue: #50')
        50
    """
    # Pattern matches "Parent Issue: #123" or "Parent Issue:** #123"
    pattern = r"Parent Issue:?\*?\*?\s*#?(\d+)"

    if pr_body:
        match = re.search(pattern, pr_body, re.IGNORECASE)
        if match:
            return int(match.group(1))

    if issue_body:
        match = re.search(pattern, issue_body, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def get_attempt_count(labels: list[str]) -> int:
    """
    Count current attempt from ai-attempt-X labels.

    Args:
        labels: List of label names on the PR/issue

    Returns:
        Current attempt number (0 if no attempt labels found)

    Examples:
        >>> get_attempt_count(['ai-attempt-2', 'library:matplotlib'])
        2

        >>> get_attempt_count(['library:seaborn', 'generating'])
        0
    """
    if not labels:
        return 0

    max_attempt = 0
    for label in labels:
        match = re.match(r"ai-attempt-(\d+)", label)
        if match:
            attempt = int(match.group(1))
            max_attempt = max(max_attempt, attempt)

    return max_attempt


def extract_issue_reference(text: str) -> int | None:
    """
    Extract first issue/PR number from text.

    Looks for '#123' pattern and returns the number.

    Args:
        text: Text that may contain issue references

    Returns:
        First issue number found, or None

    Examples:
        >>> extract_issue_reference('Closes #42 and relates to #100')
        42

        >>> extract_issue_reference('No issues here')
        None
    """
    if not text:
        return None

    match = re.search(r"#(\d+)", text)
    if match:
        return int(match.group(1))

    return None


# Valid libraries for validation (re-exported from core.constants)
VALID_LIBRARIES = SUPPORTED_LIBRARIES


def is_valid_library(library: str) -> bool:
    """
    Check if a library name is one of the supported libraries.

    Args:
        library: Library name to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_library('matplotlib')
        True

        >>> is_valid_library('pandas')
        False
    """
    return _is_valid_library(library)
