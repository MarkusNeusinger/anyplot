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

- Run `check_onboarding_performed`
- Run `list_memories` and read relevant ones

### JetBrains Tools (prefer over brute-force scanning)

Use Serena's JetBrains-backed tools for code navigation — they provide semantic understanding
that grep/glob cannot:

- `jet_brains_get_symbols_overview` — get top-level symbols in a file (classes, functions, variables). Use with `depth: 1` to also see methods of classes. Start here to understand a file before diving deeper.
- `jet_brains_find_symbol` — search for a symbol by name across the codebase. Supports name path patterns like `MyClass/my_method`. Use `include_body: true` to read source code, `include_info: true` for docstrings/signatures.
- `jet_brains_find_referencing_symbols` — find all usages of a symbol (who calls this function? who imports this class?). Essential for understanding impact of changes.
- `jet_brains_find_declaration` — jump to where a symbol is defined.
- `jet_brains_find_implementations` — find implementations of an interface/abstract class.
- `jet_brains_type_hierarchy` — understand class inheritance chains.

### Editing via Serena

For structural edits, prefer Serena's symbol-aware tools over raw text replacement:

- `replace_symbol_body` — replace an entire function/class body
- `insert_after_symbol` / `insert_before_symbol` — add code relative to a symbol
- `search_for_pattern` — regex search across the codebase (fast, flexible)
