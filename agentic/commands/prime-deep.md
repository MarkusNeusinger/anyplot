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

## Tools

### Code navigation (prefer targeted lookups over brute-force scanning)

Use the built-in Glob/Grep/Read tools for code navigation — targeted searches beat reading whole directories.

- Read — read a file to understand it before diving deeper. For a quick structural overview (classes, functions, variables), Grep the file for `class |def ` declarations.
- Grep for a symbol's definition (e.g. `class MyClass`, `def my_method`) — find where it's defined across the codebase. Use context flags (`-A`/`-B`/`-C`) to see signatures and docstrings.
- Grep for a symbol's name — find all usages (who calls this function? who imports this class?). Essential for understanding impact of changes.
- Glob — locate files by pattern (e.g. `core/database/**`, `**/*.tsx`) when you know the shape of the path but not the exact file.

### Editing

For code edits, use the built-in tools:

- Edit — exact string replacement in a file (e.g. replace a function/class body, insert code relative to a symbol)
- Write — create a new file or fully rewrite an existing one
- Grep — regex search across the codebase (fast, flexible)
