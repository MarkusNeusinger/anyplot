# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For detailed project documentation (architecture, commands, workflows, etc.), see [agentic/docs/project-guide.md](agentic/docs/project-guide.md).

## Important Rules

- **Branch-scoped commit/push policy**:
  - **On `main`**: NEVER commit or push directly. Always work on a feature branch.
  - **On a feature branch**: Claude MAY run `git commit`, `git push`, and `gh pr create` when the work warrants it. Still respect the project's automated pipelines (see "CRITICAL: Mandatory Workflow" below) — e.g. don't manually merge spec/impl PRs.
  - Confirm before destructive or hard-to-reverse operations (force-push, reset --hard, branch deletion) regardless of branch.
- **GitHub Actions workflows ARE allowed to commit/push** - When running as part of `spec-*.yml` or `impl-*.yml` workflows, creating branches, commits, and PRs is expected and required.
- **Always write in English** - All output text (code comments, commit messages, PR descriptions, issue comments, documentation) must be in English, even if the user writes in another language.
- **Update documentation when making changes** - When adding new features, events, or modifying behavior, always check if related documentation needs updating (e.g., `docs/reference/plausible.md` for analytics events, `docs/workflows/` for workflow changes, `docs/contributing.md` for user-facing changes).

## MCP Tools (Serena & Context7)

**Serena** - Prefer for Python/TypeScript code navigation and editing:
- `jet_brains_find_symbol` / `jet_brains_get_symbols_overview` - Find classes, functions, methods
- `jet_brains_find_referencing_symbols` - Find all usages of a symbol
- `replace_symbol_body` / `insert_after_symbol` - Edit entire functions/classes
- `replace_content` (regex) - Small inline edits
- `search_for_pattern` / `list_dir` / `find_file` - Non-code files, directory exploration

**Context7** - Use for up-to-date library documentation:
- `resolve-library-id` -> `query-docs` - Get current API docs, code examples
- Use when working with external libraries (matplotlib, FastAPI, SQLAlchemy, React, etc.)

**When to use:**
- Serena: Understanding codebase structure, refactoring, finding usages, editing code
- Context7: Checking correct API usage, finding library-specific patterns, debugging library issues

## Development Workflow

- **Verify working directory** - Always verify the correct working directory before running commands (especially frontend dev servers, package managers). Use `pwd` before executing build/serve commands.
- **Keep plans simple** - Do not over-scope by adding extra modes, elaborate multi-step processes, or spawning teams when a direct approach is requested. Ask for clarification before expanding scope. Only do exactly what was asked.
- **Proper lint fixes only** - Always apply proper fixes for lint/code quality issues. Never use disable comments (`eslint-disable`, `noqa`, etc.) unless explicitly approved by the user.
- **Fix formatting when editing docs** - When formatting or improving markdown files, actually fix formatting issues (headings, lists, code blocks, structure) — don't just analyze the content.

## Package Management

- **Frontend**: Use `yarn` (not npm). Run `cd app && yarn` for installs, `cd app && yarn dev` for dev server.
- **Backend**: Python dependencies managed via `pyproject.toml`. For transitive dependencies, update the lock file directly — do not add constraints to `pyproject.toml`.
- **Scripts**: Use `uv run` for running Python scripts.

## Claude Code Configuration

- **Commands directory**: Commands live in `agentic/commands/` (agent-agnostic). A symlink `.claude/commands/ → ../agentic/commands/` ensures Claude Code slash-command resolution works. Do not create commands directly in `.claude/commands/`.

## CRITICAL: Mandatory Workflow for New Specs and Implementations

**NEVER bypass the automated workflow!** All specifications and implementations MUST go through the GitHub Actions pipeline.

### Creating New Specifications - CORRECT Process

```
1. Create GitHub Issue with descriptive title (NO spec-id in title!)
   OK: "Annotated Scatter Plot with Text Labels"
   BAD: "[scatter-annotated] Annotated Scatter Plot"  <- WRONG: Don't include spec-id

2. Add `spec-request` label to the issue

3. WAIT for spec-create.yml to:
   - Analyze the request
   - Check for duplicates (will close if duplicate exists)
   - Assign a unique spec-id
   - Generate tags automatically
   - Create PR with specification.md and specification.yaml

4. Add `approved` label to the ISSUE (not the PR!)
   - This triggers the merge job in spec-create.yml

5. WAIT for automatic merge and `spec-ready` label
```

### Generating Implementations - CORRECT Process

```
1. After spec has `spec-ready` label, trigger bulk-generate:
   gh workflow run bulk-generate.yml -f specification_id=<spec-id> -f library=all

2. WAIT for the full pipeline to complete:
   impl-generate -> impl-review -> (impl-repair if needed) -> impl-merge

3. DO NOT manually merge PRs!
   - impl-merge.yml handles merging, metadata creation, and GCS promotion
   - Manual merging breaks: quality_score, review data, GCS images
```

### What You Must NEVER Do

| DON'T | DO INSTEAD |
|-------|------------|
| Manually create `plots/{spec-id}/` directories | Let `spec-create.yml` create them |
| Manually write `specification.md` files | Let `spec-create.yml` generate them |
| Include `[spec-id]` in issue title | Use descriptive title only |
| Add `approved` label to PRs | Add `approved` label to ISSUES |
| Run `gh pr merge` on implementation PRs | Let `impl-merge.yml` handle it |
| Manually create `metadata/*.yaml` files | Let `impl-merge.yml` create them |
| Upload images to GCS manually | Let workflows handle GCS |

### Why This Matters

Manual intervention causes:
- `quality_score: null` in metadata (no AI review)
- Missing preview images in GCS production folder
- No `impl:{library}:done` labels on issues
- Broken database sync (missing review data)
- Issues staying open when complete

### Batch Creation Example

```bash
# Step 1: Create 5 issues (NO spec-id in title!)
for title in "Radar Chart" "Treemap" "Sunburst Chart" "Sankey Diagram" "Chord Diagram"; do
  gh issue create --title "$title" --label "spec-request" --body "New plot type request"
done

# Step 2: Wait for spec-create to process each issue
# Check: gh issue list --label "spec-request" --state open

# Step 3: Add approved labels to ISSUES (after reviewing spec PRs)
# gh api repos/OWNER/REPO/issues/NUMBER/labels -f labels[]=approved

# Step 4: Wait for specs to merge and get spec-ready label

# Step 5: Trigger bulk-generate for each spec
# gh workflow run bulk-generate.yml -f specification_id=<spec-id> -f library=all

# Step 6: Monitor - DO NOT manually merge!
# gh run list --workflow=impl-generate.yml
# gh run list --workflow=impl-review.yml
# gh run list --workflow=impl-merge.yml
```
