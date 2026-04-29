# Regen Oldest Spec

> Picks the oldest non-recently-updated spec and regenerates all its library implementations locally — same flow as
> `/update`, but unattended and without dispatching the Cloud AI review. PRs are auto-approved (or marked
> `quality-poor`) based on the local quality score, so `impl-merge.yml` handles the rest. Works identically with the
> default Claude Code config (Sonnet) and with a locally-configured model — the skill makes no model assumptions.

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **regen-lead**. Your job is to:

1. Pick the single oldest spec by latest implementation `updated` timestamp.
2. Coordinate per-library updater agents (same mechanics as `/update`).
3. Ship per-library PRs **without** triggering the Cloud AI review — instead label PRs directly so
   `impl-merge.yml` auto-merges (score ≥ 50) or leaves them open for manual review (score < 50).

**Prerequisite:** This command uses agent teams (experimental). Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
in your environment or Claude Code settings.

**Model-agnostic by design:** The skill never inspects or sets the LLM endpoint. Whatever Claude Code is currently
configured for (Anthropic Sonnet by default, or any local OpenAI/Anthropic-compatible endpoint via `ANTHROPIC_BASE_URL`
+ `ANTHROPIC_AUTH_TOKEN`) is what spawned sub-agents will use.

---

### Phase 1: Pick the oldest spec

Run this Python snippet to find the spec whose newest per-library `updated` timestamp is the oldest. Specs without any
metadata are treated as "ancient" and picked first.

```bash
SPEC_INFO=$(uv run python -c "
from datetime import datetime, timezone
from pathlib import Path
import yaml

candidates = []
for spec_dir in sorted(Path('plots').iterdir()):
    if not spec_dir.is_dir() or spec_dir.name.startswith('.'):
        continue
    meta_dir = spec_dir / 'metadata' / 'python'
    if not meta_dir.is_dir():
        continue
    latest = None
    for yf in meta_dir.glob('*.yaml'):
        try:
            d = yaml.safe_load(yf.read_text(encoding='utf-8')) or {}
        except Exception:
            continue
        u = d.get('updated') or d.get('created')
        if u and (latest is None or str(u) > str(latest)):
            latest = u
    if latest is None:
        candidates.append((datetime.min.replace(tzinfo=timezone.utc), spec_dir.name))
        continue
    try:
        dt = datetime.fromisoformat(str(latest).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        candidates.append((dt, spec_dir.name))
    except Exception:
        continue
candidates.sort()
if candidates:
    dt, name = candidates[0]
    print(f'{name}\t{dt.isoformat()}')
")

SPEC_ID=$(echo "$SPEC_INFO" | cut -f1)
SPEC_LATEST=$(echo "$SPEC_INFO" | cut -f2)
```

If `SPEC_ID` is empty, abort with a clear message — the repo has no eligible specs.

**Discover existing libraries:** Scan `plots/$SPEC_ID/implementations/python/` for `*.py` files (excluding
`__init__.py`) — these are the libraries to regenerate. If the directory is empty, abort.

**Confirm with user:**

```
Oldest spec: {SPEC_ID}
Latest implementation update: {SPEC_LATEST}
Libraries to regenerate: {comma-separated list}

Proceed? (y/n)
```

Wait for explicit `y` / `yes` / `ja` / `passt`. Anything else aborts.

---

### Phase 2: Spawn per-library agents

Mirror Phase 3 of `/update` (`agentic/commands/update.md`). Read that file once and follow the same agent-spawning
mechanics:

1. **Read the spec:** `plots/{SPEC_ID}/specification.md` and `plots/{SPEC_ID}/specification.yaml` to extract
   `{SPEC_TITLE}` and the primary `{PLOT_TYPE}` tag.
2. **Create team:** `TeamCreate` with name `regen-{SPEC_ID}`.
3. **For each library**, create a task via `TaskCreate`:
   - Subject: `Regen {library} implementation for {SPEC_ID}`
   - Description: `Unattended regeneration — no specific user request. Perform a comprehensive review and improve.`
4. **Spawn one `general-purpose` agent per library** via the `Agent` tool with:
   - `team_name`: `regen-{SPEC_ID}`
   - `name`: `{library}`
   - `subagent_type`: `general-purpose`
   - `model`: `opus`
   - **Prompt:** Use the exact `Library Agent Prompt` from `agentic/commands/update.md` (the section starting at
     `## Library Agent Prompt`). Fill `{SPEC_ID}`, `{LIBRARY}`, `{CONTEXT7_LIBRARY}`, `{PLOT_TYPE}`, `{SPEC_TITLE}` as
     in `/update`. For `{DESCRIPTION}`, pass:
     `No specific user request — perform a comprehensive review across all dimensions (code quality, data choice,
     visual design, spec compliance, library feature usage, transferability) and improve where genuinely needed. If you
     find nothing meaningful to improve, report "no improvements needed" and leave the code unchanged.`

   The library agent's Phase 7 (local quality scoring + up-to-2-iteration repair) runs unchanged — that's the local
   substitute for the Cloud `impl-review.yml`/`impl-repair.yml` chain.
5. **Assign each task** to its agent immediately via `TaskUpdate` with `owner: "{library}"`.

All agents run in parallel.

**Skip these phases from `/update`:**
- Phase 2 (Spec Optimization) — `/regen` is unattended.
- Phase 4 / 5 (Collect-Present-Iterate with user feedback) — go directly to shipping once all agents report
  `STATUS: done` or `STATUS: conflict`. Conflicts are logged but do not block: if an agent reports a conflict, **skip
  that library** (don't ship it) and continue with the others.

---

### Phase 3: Ship (modified `/update` Phase 6)

For shipping, follow `/update`'s Phase 6 in `agentic/commands/update.md` — sub-phases **6a, 6b, 6c, 6d, 6e, 6f, 6g
Step 1**.

**6g Step 1 override:** in the per-library worktree block, when creating the PR replace `/update`'s review-trigger:

```bash
# /update.md does this (Cloud AI review):
gh api repos/{owner}/{repo}/dispatches \
  -f event_type=review-pr \
  -f 'client_payload[pr_number]='"$PR_NUMBER"
```

**…with this label-based dispatch (no Cloud AI call):**

```bash
PR_NUMBER=$(gh pr view --json number -q '.number')
SCORE={score reported by the library agent in its STATUS: done message}

# Always tag the PR with its locally-computed quality score.
gh pr edit "$PR_NUMBER" --add-label "quality:${SCORE}"

if [ "$SCORE" -ge 50 ]; then
  # Auto-approve → impl-merge.yml triggers → squash-merge + GCS staging→prod + impl:{lib}:done.
  gh pr edit "$PR_NUMBER" --add-label "ai-approved"
  echo "::notice::PR #$PR_NUMBER ai-approved (score=$SCORE)"
else
  # Score too low for auto-merge — flag for manual review.
  gh pr edit "$PR_NUMBER" --add-label "quality-poor"
  echo "::warning::PR #$PR_NUMBER flagged quality-poor (score=$SCORE) — left open for manual review"
fi
```

The PR body itself already includes the score and category breakdown (set by `/update` Phase 6g Step 1's `gh pr create`
template).

**6g Step 2** (cleanup worktrees) and **Phase 7a** (shut down team, `TeamDelete`, remove `.update-preview/`) run
unchanged.

---

### Phase 4: Brief monitor

Print a one-shot status table — no polling loop. The CI does the rest.

Wait 60 seconds (so `impl-merge.yml` has time to start), then for each PR:

```bash
gh pr view "$PR_NUMBER" --json number,state,mergedAt,labels \
  --jq '[.number, .state, (.mergedAt // "—"), ([.labels[].name] | join(","))] | @tsv'
```

Render a table:

```
| Library      | PR    | State | Merged | Labels                              |
|--------------|-------|-------|--------|-------------------------------------|
| matplotlib   | #1234 | MERGED| 14:02Z | quality:88, ai-approved             |
| seaborn      | #1235 | OPEN  | —      | quality:42, quality-poor            |
| ...                                                                          |
```

Tell the user:
- Which PRs auto-merged (success).
- Which are `quality-poor` (need manual review).
- That **no Cloud AI review/repair was triggered** — verifiable via:
  ```bash
  gh run list --workflow=impl-review.yml --limit 5
  gh run list --workflow=impl-repair.yml --limit 5
  ```
  (no new runs for this `SPEC_ID` should appear).

Then exit. The user can re-run `/regen` later to pick the next-oldest spec.

---

## Notes

- **Token cost:** All Claude Code calls (lead + agents) hit whatever endpoint Claude Code is configured for. With the
  default config that's Anthropic Sonnet (useful for end-to-end testing). With a local model configured via
  `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`, cost is effectively zero. **No code path differs between modes.**
- **Cloud workflows skipped:** `impl-review.yml` and `impl-repair.yml` only trigger on explicit dispatch (see
  `.github/workflows/impl-review.yml` triggers — `workflow_dispatch` + `repository_dispatch types: [review-pr]`).
  Skipping the dispatch in Phase 3 is sufficient to bypass them entirely.
- **Cloud workflows still active:** `impl-merge.yml` triggers on the `ai-approved` label, so it still squash-merges,
  promotes GCS staging → production, sets `impl:{library}:done` on the parent issue, and triggers `sync-postgres.yml`.
  This is intentional — we want those side effects.
- **Failure modes:**
  - Agent reports `STATUS: conflict` → skip that library, continue with the others.
  - Library agent crashes (script error, lint failure after 3 retries) → the `/update` agent prompt already handles
    this; library is reported as a failure and skipped.
  - `gh` not authenticated or GCS creds missing → Phase 3 fails fast in the first worktree's push step.
- **Re-run safe:** Running `/regen` twice in a row picks a different spec the second time (the freshly merged one is
  no longer oldest).

## Usage

```
/regen
```

No arguments. Always picks the single oldest spec.
