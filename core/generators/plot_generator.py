#!/usr/bin/env python3
"""
Plot Code Generator

Generates plot implementations from specifications using Claude with versioned rules.
"""

import ast
import logging
import os
import sys
import time
from pathlib import Path
from typing import Callable, Literal, TypeVar

import anthropic
from anthropic import APIConnectionError, APIError, RateLimitError

from core.config import settings


logger = logging.getLogger(__name__)


LibraryType = Literal[
    "matplotlib", "seaborn", "plotly", "bokeh", "altair", "plotnine", "pygal", "highcharts", "letsplot"
]


def extract_and_validate_code(response_text: str) -> str:
    """
    Extract Python code from Claude response and validate syntax.

    Args:
        response_text: Raw response from Claude API

    Returns:
        Validated Python code

    Raises:
        ValueError: If code cannot be extracted or has syntax errors
    """
    code = response_text.strip()

    # Extract code if wrapped in markdown
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    if not code:
        raise ValueError("No code could be extracted from response")

    # Validate Python syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Generated code has syntax errors: {e}") from e

    return code


T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T], max_retries: int = 3, initial_delay: float = 2.0, backoff_factor: float = 2.0
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except (RateLimitError, APIConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    "API error: %s. Retrying in %ss... (attempt %d/%d)",
                    type(e).__name__,
                    delay,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error("Max retries (%d) exceeded", max_retries)
                raise
        except APIError as e:
            # For other API errors, don't retry
            logger.error("API error: %s", e)
            raise

    # Should never reach here, but for type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry loop exit")


def load_spec(spec_id: str) -> str:
    """Load specification from specs/ directory"""
    spec_path = Path(f"specs/{spec_id}.md")
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    content = spec_path.read_text()

    # Check spec version
    import re

    version_match = re.search(r"\*\*Spec Version:\*\*\s+(\d+\.\d+\.\d+)", content)
    if version_match:
        spec_version = version_match.group(1)
        logger.info("Spec version: %s", spec_version)
    else:
        logger.warning("Spec has no version marker. Consider upgrading with upgrade_specs.py")

    return content


def load_generation_rules(version: str = "v1.0.0-draft") -> str:
    """Load code generation rules"""
    rules_path = Path(f"rules/generation/{version}/code-generation-rules.md")
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules not found: {rules_path}")
    return rules_path.read_text()


def load_quality_criteria(version: str = "v1.0.0-draft") -> str:
    """Load quality criteria for self-review"""
    criteria_path = Path(f"rules/generation/{version}/quality-criteria.md")
    if not criteria_path.exists():
        raise FileNotFoundError(f"Quality criteria not found: {criteria_path}")
    return criteria_path.read_text()


def load_self_review_checklist(version: str = "v1.0.0-draft") -> str:
    """Load self-review checklist"""
    checklist_path = Path(f"rules/generation/{version}/self-review-checklist.md")
    if not checklist_path.exists():
        raise FileNotFoundError(f"Self-review checklist not found: {checklist_path}")
    return checklist_path.read_text()


def generate_code(
    spec_id: str,
    library: LibraryType,
    variant: str = "default",
    rules_version: str = "v1.0.0-draft",
    max_attempts: int = 3,
) -> dict:
    """
    Generate plot implementation code using Claude

    Args:
        spec_id: Specification ID (e.g., "scatter-basic-001")
        library: Target library (matplotlib, seaborn, etc.)
        variant: Implementation variant (default, style variant, etc.)
        rules_version: Version of generation rules to use
        max_attempts: Maximum number of self-review attempts

    Returns:
        dict with 'code', 'file_path', 'attempt_count', 'passed_review'
    """
    # Load inputs
    spec_content = load_spec(spec_id)
    generation_rules = load_generation_rules(rules_version)
    quality_criteria = load_quality_criteria(rules_version)
    self_review = load_self_review_checklist(rules_version)

    # Initialize Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    # timeout caps a single request; max_retries=0 disables SDK-side retry so
    # transient errors flow through retry_with_backoff (the outer handler).
    client = anthropic.Anthropic(api_key=api_key, timeout=300.0, max_retries=0)

    # Determine output path
    # Format: plots/{library}/{plot_type}/{spec_id}/{variant}.py
    spec_type = spec_id.split("-")[0]  # e.g., "scatter" from "scatter-basic-001"

    # Library-specific plot type mapping
    plot_type_map = {
        "matplotlib": {"scatter": "scatter", "bar": "bar", "line": "line", "heatmap": "imshow"},
        "seaborn": {"scatter": "scatterplot", "bar": "barplot", "line": "lineplot", "heatmap": "heatmap"},
        "plotly": {"scatter": "scatter", "bar": "bar", "line": "line", "heatmap": "heatmap"},
    }

    plot_type = plot_type_map.get(library, {}).get(spec_type, spec_type)
    file_path = Path(f"plots/{library}/{plot_type}/{spec_id}/{variant}.py")

    # Self-review loop
    code = ""  # Will be set in loop
    review_feedback = ""  # Will be set in loop
    for attempt in range(1, max_attempts + 1):
        logger.info("Attempt %d/%d for %s/%s/%s", attempt, max_attempts, spec_id, library, variant)

        # Build prompt
        if attempt == 1:
            prompt = f"""You are an expert Python data visualization developer.

# Task
Generate a production-ready implementation of this plot specification for {library}.

# Specification
{spec_content}

# Generation Rules (Version: {rules_version})
{generation_rules}

# Quality Criteria
{quality_criteria}

# Requirements
1. Follow the generation rules exactly
2. Implement all data requirements and optional parameters from the spec
3. Meet all quality criteria listed in the spec
4. Use type hints (Python 3.10+ syntax)
5. Include comprehensive docstring
6. Add input validation
7. Make the code deterministic (use fixed random seeds if needed)
8. Add a standalone execution block for testing

# Output Format
Provide ONLY the Python code, no explanations. The code should be production-ready.

# Target
- Library: {library}
- Variant: {variant}
- Python: 3.10+
- File: {file_path}

Generate the implementation now:"""
        else:
            # For subsequent attempts, include the previous code and ask for improvements
            prompt = f"""Your previous implementation needs improvements. Please revise based on the feedback below.

# Previous Code
```python
{code}
```

# Self-Review Feedback
{review_feedback}

# Requirements
1. Fix all issues identified in the feedback
2. Ensure all quality criteria are met
3. Maintain the same structure and function signature

Generate the improved implementation:"""

        # Call Claude with retry logic
        current_prompt = prompt  # Capture for lambda
        response = retry_with_backoff(
            lambda p=current_prompt: client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_max_tokens,
                messages=[{"role": "user", "content": p}],
            )
        )

        # Extract and validate code
        try:
            code = extract_and_validate_code(response.content[0].text)
        except ValueError as e:
            logger.error("Code extraction/validation failed: %s", e)
            if attempt < max_attempts:
                logger.info("Retrying... (%d/%d)", attempt + 1, max_attempts)
                continue
            raise

        # Self-review
        logger.info("Running self-review...")
        review_prompt = f"""Review this generated plot implementation against the specification and quality criteria.

# Specification
{spec_content}

# Generated Code
```python
{code}
```

# Self-Review Checklist
{self_review}

# Task
Go through the self-review checklist and verify each item. For each item, respond with:
- ✅ PASS: [brief reason]
- ❌ FAIL: [specific issue and how to fix]

After reviewing all items, provide:
- Overall verdict: PASS or FAIL
- If FAIL: Specific improvements needed

Format your response as:
## Review Results
[checklist items with ✅/❌]

## Verdict
[PASS or FAIL]

## Improvements Needed (if FAIL)
[specific actionable items]
"""

        current_review_prompt = review_prompt  # Capture for lambda
        review_response = retry_with_backoff(
            lambda p=current_review_prompt: client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_review_max_tokens,
                messages=[{"role": "user", "content": p}],
            )
        )

        review_feedback = review_response.content[0].text

        # Check if passed
        if "## Verdict\nPASS" in review_feedback or "Verdict: PASS" in review_feedback:
            logger.info("Self-review passed on attempt %d", attempt)
            return {
                "code": code,
                "file_path": str(file_path),
                "attempt_count": attempt,
                "passed_review": True,
                "review_feedback": review_feedback,
            }
        else:
            logger.warning("Self-review failed on attempt %d", attempt)
            if attempt < max_attempts:
                logger.info("Regenerating with feedback...")
            else:
                logger.warning("Max attempts reached. Returning best effort code.")

    # Max attempts reached without passing
    return {
        "code": code,
        "file_path": str(file_path),
        "attempt_count": max_attempts,
        "passed_review": False,
        "review_feedback": review_feedback,
    }


def save_implementation(result: dict) -> Path:
    """Save generated code to file"""
    file_path = Path(result["file_path"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(result["code"])
    logger.info("Saved to: %s", file_path)
    return file_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Generate plot implementation from spec")
    parser.add_argument("spec_id", help="Specification ID (e.g., scatter-basic-001)")
    parser.add_argument(
        "library", choices=["matplotlib", "seaborn", "plotly", "bokeh", "altair"], help="Target library"
    )
    parser.add_argument("--variant", default="default", help="Variant name (default: default)")
    parser.add_argument("--rules-version", default="v1.0.0-draft", help="Rules version")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max self-review attempts")

    args = parser.parse_args()

    try:
        result = generate_code(
            spec_id=args.spec_id,
            library=args.library,
            variant=args.variant,
            rules_version=args.rules_version,
            max_attempts=args.max_attempts,
        )

        # Save code
        file_path = save_implementation(result)

        logger.info(
            "Generation complete: spec=%s library=%s variant=%s file=%s attempts=%d review=%s",
            args.spec_id,
            args.library,
            args.variant,
            file_path,
            result["attempt_count"],
            "PASSED" if result["passed_review"] else "FAILED",
        )

        sys.exit(0 if result["passed_review"] else 1)

    except Exception:
        # logger.exception preserves the traceback so CLI failures are debuggable.
        logger.exception("Generation failed")
        sys.exit(1)
