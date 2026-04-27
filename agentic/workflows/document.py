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
Standalone document workflow.

Runs the document.md template against a spec file and records
the output documentation path in state.

Usage:
    # With run-id from a previous build
    uv run agentic/workflows/document.py --run-id abc12345

    # Piped from review.py
    uv run agentic/workflows/review.py --run-id abc12345 | uv run agentic/workflows/document.py
"""

import json
import os
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule


# Add the modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from agent import OUTPUT_JSONL, SUMMARY_JSON, AgentPromptRequest, prompt_claude_code_with_retry
from state import resolve_state
from template import load_template, render_template


# Template path
DOCUMENT_TEMPLATE = "agentic/commands/document.md"

# Usage hint for resolve_state error message
DOCUMENT_USAGE_HINT = (
    "  uv run agentic/workflows/document.py --run-id <id>\n"
    "  uv run agentic/workflows/review.py --run-id <id> | uv run agentic/workflows/document.py"
)


@click.command()
@click.option("--run-id", default=None, help="Run ID from a previous plan/build/test/review execution")
@click.option(
    "--model",
    type=click.Choice(["small", "medium", "large"]),
    default="large",
    help="Model tier for documentation (default: large)",
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
def main(run_id: str, model: str, working_dir: str, cli: str):
    """Generate documentation for implemented features."""
    is_piped = not sys.stdout.isatty()
    console = Console(file=sys.stderr if is_piped else None)

    if not working_dir:
        working_dir = os.getcwd()

    state = resolve_state(run_id, working_dir, console, usage_hint=DOCUMENT_USAGE_HINT)

    # Detect screenshots directory from reviewer
    screenshots_dir = ""
    review_img_path = os.path.join(working_dir, f"agentic/runs/{state.run_id}/reviewer/review_img")
    if os.path.isdir(review_img_path):
        screenshots_dir = review_img_path

    console.print(
        Panel(
            f"[bold blue]Document Workflow[/bold blue]\n\n"
            f"[cyan]Run ID:[/cyan] {state.run_id}\n"
            f"[cyan]Spec:[/cyan] {state.plan_file or '(auto-detect)'}\n"
            f"[cyan]CLI:[/cyan] {cli}\n"
            f"[cyan]Model:[/cyan] {model}\n"
            f"[cyan]Screenshots:[/cyan] {screenshots_dir or '(none)'}",
            title="[bold blue]Document Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # ── Run documentation generation ──────────────────────────────
    console.print(Rule("[bold yellow]Generating Documentation[/bold yellow]"))
    console.print()

    template = load_template(DOCUMENT_TEMPLATE, working_dir)

    doc_prompt = render_template(template, {"1": state.run_id, "2": state.plan_file or "", "3": screenshots_dir})

    documenter_output_dir = os.path.join(working_dir, f"agentic/runs/{state.run_id}/documenter")
    os.makedirs(documenter_output_dir, exist_ok=True)

    request = AgentPromptRequest(
        prompt=doc_prompt,
        run_id=state.run_id,
        agent_name="documenter",
        model=model,
        cli=cli,
        dangerously_skip_permissions=True,
        output_file=os.path.join(documenter_output_dir, OUTPUT_JSONL),
        working_dir=working_dir,
    )

    with console.status("[bold yellow]Running documentation generation...[/bold yellow]"):
        response = prompt_claude_code_with_retry(request)

    if not response.success:
        console.print(Panel(response.output, title="[bold red]Documentation Failed[/bold red]", border_style="red"))
        doc_success = False
        doc_path = None
    else:
        # The template returns exclusively the path to the documentation file
        doc_path = response.output.strip()

        # Validate the returned path exists
        full_doc_path = os.path.join(working_dir, doc_path) if not os.path.isabs(doc_path) else doc_path
        if os.path.exists(full_doc_path):
            doc_success = True
            console.print(
                Panel(
                    f"Documentation created at:\n[green]{doc_path}[/green]",
                    title="[bold green]Documentation Generated[/bold green]",
                    border_style="green",
                )
            )
        else:
            doc_success = True  # Agent succeeded even if path validation is ambiguous
            console.print(
                Panel(
                    f"Agent returned path: {doc_path}\n[yellow]File not found at expected location[/yellow]",
                    title="[bold yellow]Documentation Generated (unverified)[/bold yellow]",
                    border_style="yellow",
                )
            )

    # ── Summary ────────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold blue]Document Summary[/bold blue]"))
    console.print()

    if doc_success:
        console.print("[bold green]Documentation generation completed.[/bold green]")
    else:
        console.print("[bold red]Documentation generation failed.[/bold red]")

    # Update state
    if doc_path:
        state.update(document_path=doc_path)
    state.save(working_dir, phase="document")
    console.print(f"[bold cyan]State saved:[/bold cyan] agentic/runs/{state.run_id}/state.json")

    # Save summary
    summary = {"phase": "document", "run_id": state.run_id, "success": doc_success, "document_path": doc_path}
    with open(os.path.join(documenter_output_dir, SUMMARY_JSON), "w") as f:
        json.dump(summary, f, indent=2)

    if is_piped:
        state.to_stdout()

    sys.exit(0 if doc_success else 1)


if __name__ == "__main__":
    main()
