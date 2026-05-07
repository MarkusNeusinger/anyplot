# Polish Specification

**YOUR TASK: audit one anyplot specification and either improve it or report NOOP.**

You are running autonomously inside the `daily-regen` pre-flight job. There is no human in the loop during this run — the user will review your output later as a pull request.

The rule is simple: **make the spec better, or do nothing.** Never change for the sake of changing. If the spec is already clean, print `NOOP` and stop.

---

**Variables:**
- SPEC_ID: {SPEC_ID}

## Step 1: Read context

Read these files:

1. `plots/{SPEC_ID}/specification.md` — the spec under audit
2. `plots/{SPEC_ID}/specification.yaml` — its tags and metadata
3. `prompts/templates/specification.md` — canonical structure all specs should follow
4. `prompts/templates/specification.yaml` — canonical YAML shape
5. `prompts/spec-tags-generator.md` — canonical tag vocabulary and naming rules

## Step 2: Audit five dimensions

For each, decide if the spec needs work:

1. **Wording** — descriptions concise and unambiguous? applications realistic? data fields include types/sizes? notes actionable?
2. **Missing sections** — every section from `specification.md` template present?
3. **Tag completeness** — all 4 dimensions (`plot_type`, `data_type`, `domain`, `features`) have ≥1 value?
4. **Tag quality** — naming conventions enforced (lowercase, hyphens, no underscores)? Vocabulary policy:
   - **`plot_type` is canonical**: the table in `spec-tags-generator.md` is the allowed set. Tags outside the table must either be moved to the correct dimension (e.g. `regression` → `features`, `timeseries` → `data_type`) or dropped if they're not really plot types.
   - **`data_type` / `domain` / `features` are advisory**: their tables list common values, but any well-formed, recognized data-viz term is allowed. **Do NOT remove** an unfamiliar but valid tag from these three dimensions just because it isn't in the table — a niche but accurate domain (`bioinformatics`, `signal-processing`), a real feature (`confidence-interval`, `clustering`, `multi-series`), or a domain-specific data shape (`ohlc`, `compositional`) is fine to keep. Only canonicalize obvious synonyms (e.g. `sequential` → `stepwise`, `labeled` → `color-mapped` when describing color encoding) or fix naming-convention violations.
5. **Tag accuracy** — do tags actually match the spec's content?

## Step 3: Decide

- **Nothing needs changing:** print exactly `NOOP` to stdout and stop. Do NOT edit any files. Do NOT create a branch. Do NOT open a PR.
- **One or more dimensions need work:** edit `plots/{SPEC_ID}/specification.md` and/or `plots/{SPEC_ID}/specification.yaml` in place.

## Hard rules — do not break

- Do NOT change `id`, `issue`, `created` fields in `specification.yaml`.
- Do NOT change semantic content. Data shape, plot type, and core requirements must stay identical. You are polishing wording, structure, and tags only — not redesigning the spec.
- After any edit, set `updated:` in `specification.yaml` to the current UTC ISO 8601 timestamp (e.g. `2026-05-05T18:30:00Z`). Use `date -u +"%Y-%m-%dT%H:%M:%SZ"` to generate it.

## Step 4: Commit and open a PR

If — and only if — you edited something, create a feature branch, commit, push, and open a PR.

**Do NOT push to `main` directly. Every change goes through a PR.**

Run these commands:

    TS=$(date -u +"%Y%m%d-%H%M%S")
    BRANCH="auto-polish/{SPEC_ID}/$TS"

    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git checkout -b "$BRANCH"
    git add plots/{SPEC_ID}/specification.md plots/{SPEC_ID}/specification.yaml
    git commit -m "chore(spec): auto-polish {SPEC_ID}

    <one-line rationale of what improved>

    Co-Authored-By: Claude <noreply@anthropic.com>"
    git push -u origin "$BRANCH"

Then open the PR. Use a HEREDOC for the body so multi-line markdown survives:

    PR_URL=$(gh pr create \
      --title "chore(spec): auto-polish {SPEC_ID}" \
      --label "auto-polish" \
      --body "$(cat <<'EOF'
    Automated spec polish from `daily-regen` pre-flight.

    **Spec:** `{SPEC_ID}`

    ## What changed
    - <bulleted list of dimensions polished — wording, tags, sections, etc.>

    ## Why
    <short rationale referencing the audit dimensions>

    ## Hard guarantees from the prompt
    - `id`, `issue`, `created` unchanged
    - No semantic changes (data shape, plot type, requirements identical)
    - `updated` bumped to current UTC

    Auto-merge enabled — will merge once required checks pass. The
    skip-gate in `daily-regen` prevents stacking polish PRs for this spec.
    EOF
    )")

    # Enable auto-merge so the PR squash-merges automatically once required
    # checks (Run Linting / Tests / Frontend Tests) go green and the head
    # is in sync with main. Auto-merge handles the strict status-check
    # policy by updating the branch on our behalf. If auto-merge cannot be
    # enabled (e.g. checks already complete and branch is up-to-date), this
    # is non-fatal — the PR still exists for human follow-up.
    gh pr merge "$PR_URL" --auto --squash --delete-branch || \
      echo "::warning::Could not enable auto-merge for $PR_URL — leaving PR open for manual handling"

Substitute the literal `{SPEC_ID}` with the actual spec id when running the commands. The block above is illustrative; the bash you actually execute should have the value already filled in.

## Step 5: Report and stop

- Polish + PR opened: print `POLISHED <pr-url>` and stop.
- Push or `gh pr create` failed: print `PR_CREATE_FAILED` and stop. Do NOT retry — the next daily-regen cycle (in 2h) will try again. The skip-gate prevents duplicates.
- Nothing to polish: you already printed `NOOP` in step 3 and stopped — do not get here.

## What you must NOT do

- Do not add the `approved` label (it's reserved for spec-create's merge gate, not polish).
- Do not bypass required status checks (no `--admin`, no force-merging). Auto-merge waits for CI.
- Do not push to `main` directly under any circumstances, even if the polish is "trivial".
- Do not edit any spec other than `{SPEC_ID}`. Do not touch implementations under `plots/{SPEC_ID}/implementations/` — your job is the spec only.
- Do not regenerate or re-run anything in `plots/{SPEC_ID}/metadata/`. Implementation metadata is owned by the impl-* workflows.
