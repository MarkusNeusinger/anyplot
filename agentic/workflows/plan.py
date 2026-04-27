#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "pydantic-settings",
#   "python-dotenv",
#   "click",
#   "rich",
# ]
# ///
"""
Standalone planning workflow with automatic task classification.

Phase 1: Classify task (small model) → bug / feature / chore
Phase 2: Generate plan using the matching template

Usage:
    # Automatic classification
    uv run agentic/workflows/plan.py "Fix the 404 error on /api/plots"

    # Skip classifier with explicit type
    uv run agentic/workflows/plan.py "Add CSV export feature" --type feature

    # Pipe to build.py
    uv run agentic/workflows/plan.py "Fix bug" | uv run agentic/workflows/build.py
"""

import json
import os
import re
import sys
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table


# Add the modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from agent import OUTPUT_JSONL, SUMMARY_JSON, AgentPromptRequest, generate_short_id, prompt_claude_code_with_retry
from state import WorkflowState
from template import load_template, render_template


# Template paths (relative to project root)
CLASSIFY_TEMPLATE = "agentic/commands/classify.md"
TEMPLATE_MAP = {
    "bug": "agentic/commands/bug.md",
    "feature": "agentic/commands/feature.md",
    "chore": "agentic/commands/chore.md",
    "refactor": "agentic/commands/refactor.md",
}


def parse_classify_response(output: str) -> dict:
    """Parse classifier JSON response from LLM output."""
    # Try entire output as JSON
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # Find JSON object with "type" field
    match = re.search(r'\{[^}]*"type"\s*:\s*"(bug|feature|chore|refactor)"[^}]*\}', output)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: extract just the type
    type_match = re.search(r'"type"\s*:\s*"(bug|feature|chore|refactor)"', output)
    if type_match:
        return {"type": type_match.group(1), "reason": "extracted from output"}

    raise ValueError(f"Could not parse classifier response: {output}")


def extract_plan_path(output: str, date_prefix: str) -> str:
    """Extract the plan file path from the planner output.

    Looks for YYMMDD-{name}.md patterns first, falls back to any spec path.
    """
    patterns = [
        # Primary: YYMMDD-name.md (our convention)
        rf"agentic/specs/{date_prefix}-[a-zA-Z0-9_\-]+\.md",
        rf"specs/{date_prefix}-[a-zA-Z0-9_\-]+\.md",
        # Fallback: any file in specs/
        r"agentic/specs/[a-zA-Z0-9_\-]+\.md",
        r"specs/[a-zA-Z0-9_\-]+\.md",
        # With path-like prefixes in output
        r"(?:path|file|created|plan)[:\s]+[`]?(agentic/specs/[a-zA-Z0-9_\-]+\.md)[`]?",
        r"(?:path|file|created|plan)[:\s]+[`]?(specs/[a-zA-Z0-9_\-]+\.md)[`]?",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if match:
            path = match.group(1) if match.groups() else match.group(0)
            # Ensure agentic/ prefix
            if not path.startswith("agentic/"):
                path = "agentic/" + path
            return path

    raise ValueError("Could not find plan file path in planner output")


@click.command()
@click.argument("prompt", required=True)
@click.option(
    "--type",
    "task_type",
    type=click.Choice(["bug", "feature", "chore", "refactor"]),
    default=None,
    help="Skip classifier, use this type directly",
)
@click.option(
    "--model",
    type=click.Choice(["small", "medium", "large"]),
    default="large",
    help="Model tier for planning (default: large)",
)
@click.option(
    "--working-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Working directory (default: current directory)",
)
@click.option(
    "--cli",
    type=click.Choice(["claude", "copilot", "gemini"]),
    default="claude",
    help="CLI tool to use (default: claude)",
)
def main(prompt: str, task_type: str, model: str, working_dir: str, cli: str):
    """Classify a task and generate an implementation plan."""
    # Detect piping: Rich to stderr, JSON state to stdout
    is_piped = not sys.stdout.isatty()
    console = Console(file=sys.stderr if is_piped else None)

    run_id = generate_short_id()
    date_prefix = time.strftime("%y%m%d")

    if not working_dir:
        working_dir = os.getcwd()

    state = WorkflowState(run_id=run_id, prompt=prompt)

    console.print(
        Panel(
            f"[bold blue]Plan Workflow[/bold blue]\n\n"
            f"[cyan]Run ID:[/cyan] {run_id}\n"
            f"[cyan]Date:[/cyan] {date_prefix}\n"
            f"[cyan]CLI:[/cyan] {cli}\n"
            f"[cyan]Model:[/cyan] {model}\n"
            f"[cyan]Prompt:[/cyan] {prompt}",
            title="[bold blue]Plan Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # ── Phase 1: Classify ───────────────────────────────────────────
    if task_type is None:
        classifier_model = "small"  # Always use small model for simple classification
        console.print(Rule(f"[bold yellow]Phase 1: Classification ({classifier_model} model)[/bold yellow]"))
        console.print()

        try:
            classify_template = load_template(CLASSIFY_TEMPLATE, working_dir)
        except FileNotFoundError as e:
            console.print(Panel(str(e), title="[bold red]Template Error[/bold red]", border_style="red"))
            sys.exit(2)

        classify_prompt = render_template(classify_template, {"ARGUMENTS": prompt})

        classify_output_dir = os.path.join(working_dir, f"agentic/runs/{run_id}/classifier")
        os.makedirs(classify_output_dir, exist_ok=True)

        classify_request = AgentPromptRequest(
            prompt=classify_prompt,
            run_id=run_id,
            agent_name="classifier",
            model=classifier_model,
            cli=cli,
            dangerously_skip_permissions=True,
            output_file=os.path.join(classify_output_dir, OUTPUT_JSONL),
            working_dir=working_dir,
        )

        with console.status("[bold yellow]Classifying task...[/bold yellow]"):
            classify_response = prompt_claude_code_with_retry(classify_request, max_retries=2)

        if not classify_response.success:
            console.print(
                Panel(classify_response.output, title="[bold red]Classification Failed[/bold red]", border_style="red")
            )
            sys.exit(1)

        try:
            classification = parse_classify_response(classify_response.output)
            task_type = classification["type"]
            classify_reason = classification.get("reason", "")
        except ValueError as e:
            console.print(Panel(str(e), title="[bold red]Parse Error[/bold red]", border_style="red"))
            sys.exit(1)

        state.update(task_type=task_type, classify_reason=classify_reason)
        console.print(f"  [bold green]Type:[/bold green] {task_type}")
        console.print(f"  [bold green]Reason:[/bold green] {classify_reason}")
        console.print()

        # Save classifier summary
        with open(os.path.join(classify_output_dir, SUMMARY_JSON), "w") as f:
            json.dump(
                {
                    "phase": "classification",
                    "run_id": run_id,
                    "type": task_type,
                    "reason": classify_reason,
                    "raw_output": classify_response.output,
                    "session_id": classify_response.session_id,
                },
                f,
                indent=2,
            )
    else:
        state.update(task_type=task_type)
        console.print(f"[cyan]Skipping classifier, using type:[/cyan] [bold]{task_type}[/bold]\n")

    # ── Phase 2: Plan ───────────────────────────────────────────────
    console.print(Rule(f"[bold yellow]Phase 2: Planning ({task_type}.md)[/bold yellow]"))
    console.print()

    template_path = TEMPLATE_MAP[task_type]

    try:
        plan_template = load_template(template_path, working_dir)
    except FileNotFoundError as e:
        console.print(Panel(str(e), title="[bold red]Template Error[/bold red]", border_style="red"))
        sys.exit(2)

    plan_prompt = render_template(plan_template, {"1": run_id, "2": prompt})

    # Override filename convention: YYMMDD-{name}.md
    filename_override = (
        f"\n\nIMPORTANT - Filename Convention Override:\n"
        f"Create the plan file in `agentic/specs/` with filename: `{date_prefix}-{{descriptive-name}}.md`\n"
        f"Example: `agentic/specs/{date_prefix}-fix-api-timeout.md`\n"
        f"Do NOT use run_id or type prefix in the filename. The date prefix `{date_prefix}` is today's date.\n"
    )
    plan_prompt = filename_override + plan_prompt

    planner_output_dir = os.path.join(working_dir, f"agentic/runs/{run_id}/planner")
    os.makedirs(planner_output_dir, exist_ok=True)

    plan_request = AgentPromptRequest(
        prompt=plan_prompt,
        run_id=run_id,
        agent_name="planner",
        model=model,
        cli=cli,
        dangerously_skip_permissions=True,
        output_file=os.path.join(planner_output_dir, OUTPUT_JSONL),
        working_dir=working_dir,
    )

    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column(style="bold cyan")
    info_table.add_column()
    info_table.add_row("Template", template_path)
    info_table.add_row("Task Type", task_type)
    info_table.add_row("Model", model)
    info_table.add_row("Date Prefix", date_prefix)

    console.print(Panel(info_table, title="[bold blue]Planner Inputs[/bold blue]", border_style="blue"))
    console.print()

    with console.status("[bold yellow]Generating plan...[/bold yellow]"):
        plan_response = prompt_claude_code_with_retry(plan_request)

    if not plan_response.success:
        console.print(
            Panel(
                plan_response.output, title="[bold red]Planning Failed[/bold red]", border_style="red", padding=(1, 2)
            )
        )
        sys.exit(1)

    # Extract plan path from output
    try:
        plan_path = extract_plan_path(plan_response.output, date_prefix)
    except ValueError as e:
        console.print(
            Panel(
                f"[bold red]{str(e)}[/bold red]\n\nPlanner output (first 500 chars):\n{plan_response.output[:500]}",
                title="[bold red]Plan Path Error[/bold red]",
                border_style="red",
            )
        )
        sys.exit(1)

    state.update(plan_file=plan_path)

    console.print(
        Panel(
            plan_response.output,
            title="[bold green]Planning Success[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(f"\n[bold cyan]Plan file:[/bold cyan] {plan_path}")

    # Save planner summary
    with open(os.path.join(planner_output_dir, SUMMARY_JSON), "w") as f:
        json.dump(
            {
                "phase": "planning",
                "run_id": run_id,
                "task_type": task_type,
                "template": template_path,
                "model": model,
                "success": plan_response.success,
                "session_id": plan_response.session_id,
                "plan_path": plan_path,
                "output": plan_response.output,
            },
            f,
            indent=2,
        )

    # Save state
    state.save(working_dir, phase="plan")
    console.print(f"[bold cyan]State saved:[/bold cyan] agentic/runs/{run_id}/state.json")
    console.print(f"\n[dim]Next: uv run agentic/workflows/build.py --run-id {run_id}[/dim]")
    console.print()

    # Output state JSON to stdout for piping (only when piped)
    if is_piped:
        state.to_stdout()


if __name__ == "__main__":
    main()
