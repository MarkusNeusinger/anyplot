# Prime

> Lightweight orientation for everyday work. For deep architecture context, use `/prime-deep`. CLAUDE.md is auto-loaded — critical rules are already in context.

## Run

```bash
git status --short --branch
git log --oneline -5
gh pr list --limit 5 2>/dev/null || echo "(gh CLI not available)"
```

## Tools

- Use the built-in Glob/Grep/Read/Edit tools for code navigation and edits:
  - Read a file, or Grep for `class |def ` declarations — structural overview and symbol lookup
  - Grep for a symbol name to find its usages/call sites — impact analysis before edits
  - Edit / Write — code edits
- See `/prime-deep` for the full tool catalog.

## What this project is

**anyplot**: AI-powered platform that generates Python data-viz examples for 9 libraries (matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot). Spec-driven: every plot starts as a library-agnostic Markdown spec, then AI generates implementations per library.

## Where things live

- `plots/{spec-id}/` — spec + per-library metadata + implementations (one dir per plot)
- `core/` — shared business logic (DB, repositories, config)
- `api/` — FastAPI backend
- `app/` — React frontend (Vite + TS + MUI)
- `agentic/` — AI workflow layer (commands in `agentic/commands/`, docs in `agentic/docs/`)
- `prompts/` — AI prompts for generation/review/tagging
- `automation/` — CI/CD helper scripts
- `.github/workflows/` — GitHub Actions pipelines

Stack: Python 3.13+ (uv), PostgreSQL, GCP (Cloud Run + Cloud SQL + GCS).

## GitHub pipeline (don't bypass it)

**New spec:**
1. Create issue (descriptive title, no spec-id) + add `spec-request` label
2. `spec-create.yml` runs → opens PR
3. Add `approved` label to the **issue** (not PR) → auto-merges → `spec-ready`

**Generate implementations:**
1. `gh workflow run bulk-generate.yml -f specification_id=<id> -f library=all`
2. Pipeline: `impl-generate` → `impl-review` → (`impl-repair` if needed) → `impl-merge`
3. **Never manually merge impl PRs** — `impl-merge.yml` handles metadata + GCS promotion

## Need more?

- `/prime-deep` — full architecture, metadata schemas, all workflows, deployment
- `agentic/docs/project-guide.md` — comprehensive reference
- `docs/` — contributing, workflows, API, DB schema
