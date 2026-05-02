# Prime (Deep)

> Full project orientation. Use when starting architecture work, refactors, or when unsure about the codebase. For quick starts, use `/prime` instead.

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
The canonical, MCP-registered prefix is `mcp__serena__*` (matches `.claude/settings.json`).

- `mcp__serena__get_symbols_overview` — get top-level symbols in a file (classes, functions, variables). Use with `depth: 1` to also see methods of classes. Start here to understand a file before diving deeper.
- `mcp__serena__find_symbol` — search for a symbol by name across the codebase. Supports name-path patterns like `MyClass/my_method`. Use `include_body: true` to read source code, `include_info: true` for docstrings/signatures.
- `mcp__serena__find_referencing_symbols` — find all usages of a symbol (who calls this function? who imports this class?). Essential for understanding impact of changes.
- `mcp__serena__find_declaration` — jump to where a symbol is defined.
- `mcp__serena__find_implementations` — find implementations of an interface/abstract class.
- `mcp__serena__type_hierarchy` — understand class inheritance chains.

### Editing via Serena

For structural edits, prefer Serena's symbol-aware tools over raw text replacement:

- `mcp__serena__replace_symbol_body` — replace an entire function/class body
- `mcp__serena__insert_after_symbol` / `mcp__serena__insert_before_symbol` — add code relative to a symbol
- `mcp__serena__search_for_pattern` — regex search across the codebase (fast, flexible)
