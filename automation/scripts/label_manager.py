"""
Label management utilities for GitHub Issues and PRs.

Provides consistent label operations across workflows.
Labels are managed via gh CLI in workflows, but this module
provides the logic for label transitions and conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import (
    QUALITY_LABELS,
    QUALITY_THRESHOLD_EXCELLENT,
    QUALITY_THRESHOLD_GOOD,
    QUALITY_THRESHOLD_NEEDS_WORK,
    STATUS_LABELS,
)
from core.constants import get_library_label as _get_library_label


@dataclass
class LabelChange:
    """Represents a set of label changes to apply."""

    add: list[str]
    remove: list[str]

    def to_gh_args(self) -> str:
        """
        Generate gh CLI arguments for label changes.

        Returns:
            String with --add-label and --remove-label arguments

        Examples:
            >>> change = LabelChange(add=['testing'], remove=['generating'])
            >>> change.to_gh_args()
            '--remove-label "generating" --add-label "testing"'
        """
        args = []

        for label in self.remove:
            args.append(f'--remove-label "{label}"')

        for label in self.add:
            args.append(f'--add-label "{label}"')

        return " ".join(args)

    def is_empty(self) -> bool:
        """Check if there are no changes to apply."""
        return not self.add and not self.remove


def get_status_transition(current_labels: list[str], to_status: str) -> LabelChange:
    """
    Calculate label changes for a status transition.

    Removes any existing status labels and adds the new one.

    Args:
        current_labels: Current labels on the issue/PR
        to_status: Target status label

    Returns:
        LabelChange with labels to add/remove

    Examples:
        >>> get_status_transition(['generating', 'library:matplotlib'], 'testing')
        LabelChange(add=['testing'], remove=['generating'])

        >>> get_status_transition(['reviewing', 'ai-attempt-1'], 'ai-approved')
        LabelChange(add=['ai-approved'], remove=['reviewing'])
    """
    to_remove = []
    current_set = set(current_labels)

    # Remove any existing status labels
    for label in STATUS_LABELS:
        if label in current_set and label != to_status:
            to_remove.append(label)

    # Only add if not already present
    to_add = [to_status] if to_status not in current_set else []

    return LabelChange(add=to_add, remove=to_remove)


def get_quality_label(score: int) -> str:
    """
    Get quality label based on score.

    Args:
        score: Quality score (0-100)

    Returns:
        Quality label string

    Examples:
        >>> get_quality_label(95)
        'quality:excellent'

        >>> get_quality_label(87)
        'quality:good'

        >>> get_quality_label(78)
        'quality:needs-work'

        >>> get_quality_label(60)
        'quality:poor'
    """
    if score >= QUALITY_THRESHOLD_EXCELLENT:
        return "quality:excellent"
    elif score >= QUALITY_THRESHOLD_GOOD:
        return "quality:good"
    elif score >= QUALITY_THRESHOLD_NEEDS_WORK:
        return "quality:needs-work"
    else:
        return "quality:poor"


def get_quality_transition(current_labels: list[str], score: int) -> LabelChange:
    """
    Calculate label changes for quality score update.

    Args:
        current_labels: Current labels on the issue/PR
        score: New quality score

    Returns:
        LabelChange with quality label to add/remove
    """
    new_label = get_quality_label(score)
    current_set = set(current_labels)

    to_remove = []
    for label in QUALITY_LABELS:
        if label in current_set and label != new_label:
            to_remove.append(label)

    to_add = [new_label] if new_label not in current_set else []

    return LabelChange(add=to_add, remove=to_remove)


def get_attempt_label(attempt: int) -> str | None:
    """
    Get attempt label for attempt number.

    Args:
        attempt: Attempt number (1-3)

    Returns:
        Attempt label or None if invalid

    Examples:
        >>> get_attempt_label(2)
        'ai-attempt-2'

        >>> get_attempt_label(4)
        None
    """
    if 1 <= attempt <= 3:
        return f"ai-attempt-{attempt}"
    return None


def get_library_label(library: str) -> str:
    """
    Get library label for a library name.

    Args:
        library: Library name

    Returns:
        Library label

    Examples:
        >>> get_library_label('matplotlib')
        'library:matplotlib'
    """
    return _get_library_label(library)


def is_approved(labels: list[str]) -> bool:
    """
    Check if labels indicate AI approval.

    Args:
        labels: List of label names

    Returns:
        True if ai-approved label is present

    Examples:
        >>> is_approved(['ai-approved', 'library:matplotlib'])
        True

        >>> is_approved(['reviewing', 'library:matplotlib'])
        False
    """
    return "ai-approved" in labels


def is_rejected(labels: list[str]) -> bool:
    """
    Check if labels indicate AI rejection.

    Args:
        labels: List of label names

    Returns:
        True if ai-rejected label is present
    """
    return "ai-rejected" in labels


def get_current_status(labels: list[str]) -> str | None:
    """
    Get current status from labels.

    Args:
        labels: List of label names

    Returns:
        Current status label or None

    Examples:
        >>> get_current_status(['generating', 'library:matplotlib'])
        'generating'

        >>> get_current_status(['library:matplotlib'])
        None
    """
    label_set = set(labels)
    for status in STATUS_LABELS:
        if status in label_set:
            return status
    return None


def build_gh_issue_edit_command(issue_number: int | str, label_change: LabelChange) -> str:
    """
    Build gh issue edit command for label changes.

    Args:
        issue_number: Issue or PR number
        label_change: Label changes to apply

    Returns:
        Complete gh command string

    Examples:
        >>> change = LabelChange(add=['testing'], remove=['generating'])
        >>> build_gh_issue_edit_command(42, change)
        'gh issue edit 42 --remove-label "generating" --add-label "testing"'
    """
    if label_change.is_empty():
        return ""

    return f"gh issue edit {issue_number} {label_change.to_gh_args()}"


def build_gh_pr_edit_command(pr_number: int | str, label_change: LabelChange) -> str:
    """
    Build gh pr edit command for label changes.

    Args:
        pr_number: PR number
        label_change: Label changes to apply

    Returns:
        Complete gh command string
    """
    if label_change.is_empty():
        return ""

    return f"gh pr edit {pr_number} {label_change.to_gh_args()}"
