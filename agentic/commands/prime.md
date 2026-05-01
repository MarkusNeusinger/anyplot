# Prime

> Execute the following sections to understand the codebase then summarize your understanding.

## Run

```bash
# Current state: branch, uncommitted changes, stashes
git status --short --branch

# Recent activity: what's been worked on
git log --oneline --graph -15

# Open PRs: what's in flight
gh pr list --limit 10 2>/dev/null || echo "(gh CLI not available)"
```

## Read

@agentic/docs/project-guide.md
@agentic/commands/context.md
@docs/concepts/vision.md
@pyproject.toml

## Serena

- Run `mcp__serena__check_onboarding_performed`
- Run `mcp__serena__list_memories` and read relevant ones

### Serena MCP tools (prefer over brute-force scanning)

Use Serena's symbol-aware tools for code navigation — they provide semantic understanding that grep/glob cannot.
The canonical, MCP-registered prefix is `mcp__serena__*` (matches `.claude/settings.json`). Older repo docs may
still mention `jet_brains_*` aliases — treat them as the same tools and prefer the `mcp__serena__*` form below.

- `mcp__serena__get_symbols_overview` — top-level symbols in a file (classes, functions, variables). Use `depth: 1`
  to also see methods of classes. Start here before diving deeper.
- `mcp__serena__find_symbol` — search for a symbol by name across the codebase. Supports name-path patterns like
  `MyClass/my_method`. Use `include_body: true` to read source code, `include_info: true` for signatures.
- `mcp__serena__find_referencing_symbols` — find all usages of a symbol (who calls this function? who imports this
  class?). Essential for understanding the impact of changes.

### Editing via Serena

For structural edits, prefer Serena's symbol-aware tools over raw text replacement:

- `mcp__serena__replace_symbol_body` — replace an entire function/class body
- `mcp__serena__insert_after_symbol` / `mcp__serena__insert_before_symbol` — add code relative to a symbol
- `mcp__serena__search_for_pattern` — regex search across the codebase (fast, flexible)
