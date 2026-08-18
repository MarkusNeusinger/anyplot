---
name: write-docs
description: Editing contract for the documentation — where a new doc goes (docs/ vs agentic/docs/), keeping docs/index.md and the CLAUDE.md/copilot-instructions pair in sync, the cross-file sync duties (changelog rule triple, plausible events, contributing), and formatting standards. Use when asked to write, add, update, restructure, or format documentation.
---

# Write or update the docs

`docs/` is plain Markdown, read on GitHub — no build step; this skill
is the editing contract. All docs are **English** (CLAUDE.md language
rule).

## Where a new doc goes

```
docs/
├── index.md          # the index — every doc is listed here
├── contributing.md   # user-facing: how to propose plots, improve specs
├── development.md    # local setup, testing, code quality
├── concepts/         # philosophy, design decisions, roadmaps (vision, library-expansion)
├── workflows/        # how the GitHub Actions automation works
└── reference/        # technical lookup: api, database, mcp, repository, style-guide, tagging-system, plausible, seo, performance
agentic/docs/         # agent-workflow internals (project-guide.md) — for AI agents, not end users
```

Decision: end-user/contributor-facing → `docs/` (pick the layer
above); pipeline/agent internals → `agentic/docs/`; prompt-shaped
content → `prompts/` (not documentation).

Checklist for adding, renaming, or removing a doc:

1. Pick the layer (above).
2. **Update `docs/index.md` in ALL its surfaces**: the structure
   tree AND the layer's prose section — plus a Quick Links row when
   readers would look the doc up there. Drift check:
   `find docs -maxdepth 2 -name '*.md' | sort` vs. the index —
   deeper artifact directories (`reference/og-samples/`,
   `reference/palette-variants/`) hold working reports and stay
   unindexed by design.
3. A doc describing a partially built system opens with a status line
   under its H1 — `> **Status (YYYY-MM-DD):** what exists, what is
   still planned.` Absolute dates only; bump the date whenever you
   touch the status. (No retrofit duty for existing docs.)

## Sync duties (the part everyone forgets)

- **`CLAUDE.md` ↔ `.github/copilot-instructions.md`**: shared rules
  live in both; changing one checks the other in the same commit.
  Drift check: `git diff main -- CLAUDE.md .github/copilot-instructions.md`
- **The changelog rule is TRIPLED**: `CLAUDE.md` ↔
  `.github/copilot-instructions.md` ↔
  `agentic/commands/pull_request.md` — change all three together.
- Analytics events → `docs/reference/plausible.md`; API endpoints →
  `docs/reference/api.md`; workflow behavior → `docs/workflows/`;
  user-facing changes → `docs/contributing.md` (the CLAUDE.md
  documentation rule).
- **When a concept, path, or term changes, sweep the whole doc
  surface for the old form** — don't rely on remembering which docs
  cite it:

  ```bash
  grep -rn '<old term or path>' docs/ agentic/docs/ CLAUDE.md .github/copilot-instructions.md README.md
  ```

## Formatting

- Actually FIX formatting issues while editing (headings, lists, code
  blocks, structure) — don't just analyze them (CLAUDE.md rule).
- Absolute dates only (2026-08-17), never "currently"/"recently" —
  relative dates rot.
- Keep-a-Changelog style stays in `CHANGELOG.md`; docs don't
  duplicate changelog content.

## Gotchas

- `docs/index.md` has THREE surfaces to keep aligned: the Quick Links
  table, the structure tree, and the per-layer sections — a new doc
  that misses one is findable in some views and an orphan in others.
- `agentic/docs/project-guide.md` is the deep-dive that CLAUDE.md
  points at — structural project changes (new top-level dirs, new
  pipelines) update it, not CLAUDE.md, which stays rules-only.
