# The Agentic Layer

The Agentic Layer is a "ring" of code, scripts, and assets that sits around your application code. Its purpose is to
encode your engineering expertise so that AI agents can operate your codebase autonomously.

## Structure

```
agentic/
├── commands/       # Prompt templates (chore.md, implement.md, commit.md, pull_request.md, ...)
├── workflows/      # Executable workflows (uv run)
│   └── modules/    # Shared Python modules (agent.py, state.py)
├── specs/          # Generated plans and specifications
├── context/        # Feature documentation (what was done)
├── docs/           # Static project documentation
└── runs/           # Execution output (in .gitignore)
```

## Usage

```bash
# Plan + Build
uv run agentic/workflows/plan_build.py "your task description"

# Plan + Build + Test (with auto-fix)
uv run agentic/workflows/plan_build_test.py "fix the 404 bug"

# Plan + Build + Test + Review
uv run agentic/workflows/plan_build_test_review.py "add dark mode toggle"

# Full pipeline: Plan + Build + Test + Review + Document
uv run agentic/workflows/plan_build_test_review_document.py "add dark mode toggle"

# Complete pipeline: Plan + Build + Test + Review + Document + Ship
uv run agentic/workflows/plan_build_test_review_document_ship.py "Add CSV export to API endpoints"

# Composable individual phases
uv run agentic/workflows/plan.py "fix bug" --type bug
uv run agentic/workflows/build.py --run-id abc12345
uv run agentic/workflows/test.py --run-id abc12345
uv run agentic/workflows/review.py --run-id abc12345
uv run agentic/workflows/document.py --run-id abc12345
uv run agentic/workflows/ship.py --run-id abc12345

# Quick patch (no planning, direct implementation)
uv run agentic/workflows/patch.py "fix the typo in README.md"

# Patch with test + review
uv run agentic/workflows/patch.py "fix the 404 error" --test --review

# Ad-hoc prompt execution
uv run agentic/workflows/prompt.py "your ad-hoc prompt"

# Piping between phases
uv run agentic/workflows/plan.py "fix bug" | uv run agentic/workflows/build.py

# Options
--model [small|medium|large]   # Default: large
--cli [claude|copilot|gemini]  # Default: claude
--working-dir PATH             # Default: current directory
```

## Model Tiers

Model tiers abstract away CLI-specific model names, allowing the same command to work across different AI tools.

| Tier | Purpose | Claude | Copilot | Gemini |
|------|---------|--------|---------|--------|
| small | Fast/cheap tasks | haiku | gpt-4o-mini | gemini-2.0-flash |
| medium | Balanced tasks | sonnet | gpt-4o | gemini-2.0-flash-thinking |
| large | Complex tasks | opus | o1 | gemini-2.5-pro |

### Override Mappings

Override the default model for any tier via environment variables:

```bash
# Use a specific Claude model for the "large" tier
CLI_MODEL_CLAUDE_LARGE=claude-opus-4-7

# Use a different Copilot model for the "medium" tier
CLI_MODEL_COPILOT_MEDIUM=gpt-4-turbo
```