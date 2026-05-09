#!/usr/bin/env python3
"""
CLI wrapper for workflow utilities.

Provides command-line interface for workflow_utils and label_manager
functions, designed for use in GitHub Actions workflows.

Usage in workflows:
    uv run python -m automation.scripts.workflow_cli extract-branch auto/scatter-basic/matplotlib
    uv run python -m automation.scripts.workflow_cli extract-sub-issue "Sub-Issue: #42"
    uv run python -m automation.scripts.workflow_cli get-attempt-count "ai-attempt-1,ai-attempt-2"
    uv run python -m automation.scripts.workflow_cli status-transition "generating,testing" reviewing
"""

from __future__ import annotations

import argparse
import json
import sys

from automation.scripts.label_manager import get_quality_label, get_status_transition
from automation.scripts.workflow_utils import (
    extract_branch_info,
    extract_parent_issue,
    extract_sub_issue,
    get_attempt_count,
)


def cmd_extract_branch(args: argparse.Namespace) -> int:
    """Extract info from auto branch name."""
    info = extract_branch_info(args.branch)
    if info is None:
        print("null")
        return 1

    result = {"spec_id": info.spec_id, "library": info.library, "is_auto_branch": info.is_auto_branch}
    print(json.dumps(result))
    return 0


def cmd_extract_sub_issue(args: argparse.Namespace) -> int:
    """Extract sub-issue number from PR body."""
    issue_num = extract_sub_issue(args.pr_body)
    if issue_num is None:
        print("")
        return 1
    print(issue_num)
    return 0


def cmd_extract_parent_issue(args: argparse.Namespace) -> int:
    """Extract parent issue number."""
    issue_num = extract_parent_issue(args.pr_body, args.issue_body)
    if issue_num is None:
        print("")
        return 1
    print(issue_num)
    return 0


def cmd_get_attempt_count(args: argparse.Namespace) -> int:
    """Get attempt count from labels."""
    labels = args.labels.split(",") if args.labels else []
    count = get_attempt_count(labels)
    print(count)
    return 0


def cmd_status_transition(args: argparse.Namespace) -> int:
    """Calculate label changes for status transition."""
    current_labels = args.current_labels.split(",") if args.current_labels else []
    change = get_status_transition(current_labels, args.to_status)

    # Output gh CLI arguments
    if not change.is_empty():
        print(change.to_gh_args())
    return 0


def cmd_quality_label(args: argparse.Namespace) -> int:
    """Get quality label for score."""
    label = get_quality_label(args.score)
    print(label)
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Workflow utility CLI", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract-branch
    p = subparsers.add_parser("extract-branch", help="Extract info from auto branch")
    p.add_argument("branch", help="Branch name (e.g., auto/scatter-basic/matplotlib)")
    p.set_defaults(func=cmd_extract_branch)

    # extract-sub-issue
    p = subparsers.add_parser("extract-sub-issue", help="Extract sub-issue from PR body")
    p.add_argument("pr_body", help="PR body text")
    p.set_defaults(func=cmd_extract_sub_issue)

    # extract-parent-issue
    p = subparsers.add_parser("extract-parent-issue", help="Extract parent issue from PR/issue body")
    p.add_argument("pr_body", help="PR body text")
    p.add_argument("--issue-body", default=None, help="Issue body as fallback")
    p.set_defaults(func=cmd_extract_parent_issue)

    # get-attempt-count
    p = subparsers.add_parser("get-attempt-count", help="Get attempt count from labels")
    p.add_argument("labels", help="Comma-separated list of labels")
    p.set_defaults(func=cmd_get_attempt_count)

    # status-transition
    p = subparsers.add_parser("status-transition", help="Calculate label changes for status transition")
    p.add_argument("current_labels", help="Comma-separated current labels")
    p.add_argument("to_status", help="Target status")
    p.set_defaults(func=cmd_status_transition)

    # quality-label
    p = subparsers.add_parser("quality-label", help="Get quality label for score")
    p.add_argument("score", type=int, help="Quality score (0-100)")
    p.set_defaults(func=cmd_quality_label)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
