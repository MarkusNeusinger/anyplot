---
name: triage-agent-cases
description: Triage the agent chat's feedback cases (the quick feedback of "Use with my data") in rounds — list the open cases with the bundled read-only list_cases.py, copy each case's files to a private directory with fetch_case.sh, read the transcript, data, plot and config stamp, check origin/main for a fix, classify every case (done with the fixing PR, in_progress with a failure-class tag and a general fix, wont_solve with the reason, promotion to the eval harness), write a private report and a plan file, and only after the owner's OK for the round write status and tags in one snapshotted transaction with apply_triage.py. Use when asked to triage the agent cases, go through the feedback cases, review the agent chat feedback, or "Agent-Cases durchgehen".
---

# Triage the agent chat's feedback cases

A visitor or the owner rates a plot of the agent chat, or the chat itself, and
the BFF stores a **case**: a row in the production table `agent_feedback` and
the files under `gs://anyplot-agent-cases/cases/<case id>/` (`manifest.json`
with the whole bundle, plus `data.csv`, the PNGs and the code when the case
holds them). The row is the source of truth for the triage: `status`, `tags`,
`expected`, `promoted_at`, `superseded_by`. The files expire after 180 days;
the row stays. Background: `docs/reference/api.md` ("Feedback case",
"Feedback triage") and `agents/README.md` ("Sync promoted cases from the
bucket").

There is no schedule. Run a round when the owner asks, usually once a few
cases have collected (owner decision, 2026-11-04).

A case is a transient reproducer, never an archive (owner rule, 2026-10-12):
report, triage with a failure-class tag, generalize into a code check or a
synthetic fixture with invented data, fix the cause, retire the case. A real
case ages with the model and the prompts in its config stamp, so only its
inputs carry over (data shape, bindings, request, expected outcome).

## Rules

- **Read-only until the owner's OK.** Listing, fetching and reading touch
  nothing. The one write is `apply_triage.py --apply`, after the owner has
  approved that round's plan by name, and it snapshots the rows first.
- **No admin token.** Never call `PATCH /debug/agent/cases/{id}` with the
  owner's token. The write goes through `apply_triage.py`, which applies the
  route's own rules (`core.agent_cases.triage_updates`).
- **Users' data stays private.** A case holds a user's messages, data,
  conversation and plot. None of it goes into the repository, a commit, a PR,
  an issue, a Todoist task or a public page. The round directory lies outside
  every git checkout (the scripts refuse a path inside one), the report quotes
  at most a short phrase per case, and examples you write anywhere else use
  invented data.
- **General fixes, not case fixes.** Fix the class at its source: a code check
  over a prompt sentence, one rule in `core/` or `prompts/` that the pipeline
  and the agents share, never a patch that recognizes one dataset (CLAUDE.md:
  structural fix over symptomatic fix).
- **Replays cost money.** A harness run (`agents.evals.matrix`) or a live
  session calls Vertex. Run one only with the owner's OK and a stated budget.
- **Never join telemetry to a case.** The telemetry's session hash is salted
  on purpose; do not join by time either (`docs/reference/agent-telemetry.md`).

## 1 · Set up the round

1. Run `git fetch origin main`. Read the code as it is on `origin/main`, from
   a worktree on it or the main checkout.
2. Make the round directory outside the repository, private:
   `ROUND=~/anyplot-triage/$(date -u +%F)` and
   `mkdir -p "$ROUND" && chmod 700 ~/anyplot-triage "$ROUND"` (`mkdir -m`
   leaves an existing directory's mode as it was).
3. Name the `.env` that holds `DATABASE_URL`. A worktree has none; pass the
   main checkout's with `--env` (the scripts read only that key and never
   print it).

## 2 · List and fetch

```bash
S=.claude/skills/triage-agent-cases
ENV="$(git rev-parse --path-format=absolute --git-common-dir)/../.env"   # the main checkout's .env
uv run python $S/list_cases.py --env "$ENV" --json "$ROUND/cases.json"        # open queue
uv run python $S/list_cases.py --env "$ENV" --all --json "$ROUND/all.json"   # every row: tags in use, superseded cases
bash $S/fetch_case.sh --dest "$ROUND/files" <case id> <case id> ...
```

- `list_cases.py` lists the queue `/debug` opens on: `new` and
  `in_progress`, not superseded, oldest first, in a transaction PostgreSQL
  holds read-only. Flags: `S` superseded, `P` promoted, `E` expected set.
  `--json` writes every column, the users' messages included (mode 0600).
- `fetch_case.sh` copies `cases/<id>/` per case into `$ROUND/files/<id>/`
  (mode 0700); without `--dest` it makes a `mktemp -d` directory. It only
  reads the bucket.

Tell the user the number of open cases and the round directory before you
read them.

## 3 · Read each case

| Where | What it tells you |
|---|---|
| Row: `reaction`, `message`, `result_version`, `pipeline_status`, `attempts` | What the user said about which version, and how the pipeline judged it. `result_version` 0 is a chat case: feedback on a session with no plot on the page. |
| `bundle.transcript` | Every turn; `[action]` lines are the page's buttons. Read the root's claims against the result. |
| `bundle.turns.records` | Per turn (`turn` N is the transcript's N-th user line; a turn refused before the judge has none and shares the next number): every root tool call with its guard verdict, outcome and answer code, and the guards' verdicts (`scope_guard`, `output_guard`, `empty_reply`, `reply_language`, `budget_halt`, `queue`). Read the root cause here instead of inferring it. Never match the record against log or telemetry lines, by sequence or by time: it is no join key. |
| `bundle.versions[0].result` | `status`, `changes`, `residual_defects`, `rounds` (each round's outcome and rubric ids), `shows.texts` (the drawn texts). |
| `bundle.bindings`, `bundle.profile` | The roles as bound, and each column's dtype, range and top values. |
| `bundle.config` | `service_version`, the model, and `prompt_hashes` of the root, the reviewer and each adapter. |
| `bundle.session`, `bundle.snapshot` | Spec, library, locale, plot language and its source; the catalogue library version the session adapted. |
| `data.csv`, `plot-*.png`, `plot.py` | Open the PNGs and read the data yourself; judge the plot as the user saw it. |

Then decide whether `origin/main` already fixes the cause:

1. Search for the case id first. Fixes often cite it:
   `gh search prs "<case id>" --repo MarkusNeusinger/anyplot` and
   `git log origin/main --grep "<case id>"` and
   `grep -rn "<case id>" docs agents CHANGELOG.md`.
2. Compare the stamp with today: `service_version` against
   `pyproject.toml`, and the prompt hashes against a current case or
   `policy.prompt_hash` of today's prompts. A different hash says the prompt
   changed, not that the class is fixed.
3. Read the history of the code the class lives in since the case's
   `created_at`: `git log origin/main --since=<created_at> -- <paths>`, and
   the PR bodies of likely fixes (`gh pr view <n> --json mergedAt,body`). A
   fix counts only when it merged after the case and covers the class; cite
   the PR and the line that shows it.
4. When nothing fixes it, find the root cause with `path:line` on
   `origin/main` and say what the general fix is.

## 4 · Classify

Every open case gets one proposed status, its tags, and a promotion verdict.

| Status | When | What the report names |
|---|---|---|
| `done` | The class is fixed on `origin/main`, or a positive reaction leaves nothing to fix | The fixing PR (merged after the case) and the evidence; for a positive case, that the plot shows no defect |
| `in_progress` | The class needs a general fix that is not on `main` | The class as a tag, the root cause with `path:line`, the fix, and its vehicle: a PR plan, a Todoist task, or a Gemini brief |
| `wont_solve` | Out of scope, working as intended, or a fix the owner has declined | The reason in one sentence |
| `new` | Evidence is missing to decide | What evidence, and how to get it without a replay (or the replay's budget) |

- **Tags** name failure classes as lowercase slugs (`^[a-z0-9-]{1,40}$`, at
  most 10), such as `legend-overlap` or `negative-radius`. Reuse the tags
  already in the table (`list_cases.py --all`) before you coin one. A
  positive case with nothing to fix gets `confirmed`.
- **Superseded cases** follow their successor: triage the newest case of the
  chain (`superseded_by`) and give the older ones the same status. Their
  `seen` state comes from `all.json`, since the open list hides them.
- **Promotion** to the eval harness (`promoted: true`) needs a plot
  (`result_version` ≥ 1) and `data.csv`, and a reason: a class no fixture
  covers, the reaction contradicting the pipeline outcome, or a bug or idea
  with a reproducer (then `expected` is required). A chat case cannot be
  promoted: propose a unit test or a prep or scope fixture with invented data
  instead. Retire a promoted case (`done`) once a test or fixture covers its
  class; the next `sync_cases.py` run removes it from `agents/evals/.cases/`.
- **Who decides.** The statuses and tags of the round are the owner's to
  approve. A new operation, a new gate or a change to what the assistant
  offers is an owner decision; present it with options. A fix inside an
  existing mechanism (an exemption table, a missing field) is routine: name it
  in the plan.

## 5 · Write the report and the plan

Write `$ROUND/report.md` in English, Google style:

1. **Summary**: the number of cases, the proposed statuses, and the one or two
   general fixes that matter most.
2. **Cases**: one entry each, oldest first: id, spec and library, reaction,
   a short quote, the diagnosis, the proposed status, tags and promotion, the
   fixing PR or the proposed fix with `path:line`.
3. **General fixes**: ranked by the number of cases they cover, each with the
   vehicle and *owner decision* or *routine*.
4. **Evidence gaps**: what the bundle could not tell, and what would.

Write `$ROUND/plan.json` in the format below and check it with a dry run,
which only reads:

```bash
uv run python $S/apply_triage.py --env "$ENV" --plan "$ROUND/plan.json"
```

Then give the owner the report path, the headline and the plan's dry-run
lines, and create one Todoist task per owner decision in the **Anyplot**
project (the action and the report path; never a case's content).

### The plan file

```json
{
  "round": "2026-11-04",
  "cases": [
    {
      "id": "20261012T143005Z-1a2b3c4d",
      "seen": {"status": "new", "tags": [], "expected": null, "promoted": false},
      "status": "in_progress",
      "tags": ["legend-overlap"],
      "why": "The legend covers the last bars; gate G7 does not measure legend boxes."
    }
  ]
}
```

- `seen` is every triage field of the row as the round read it (from
  `cases.json`): `status`, `tags`, `expected`, and `promoted` (whether
  `promoted_at` is set). A row that differs in any of them at write time,
  because someone triaged it on `/debug` in between, is refused.
- `status`, `tags`, `promoted` and `expected` mean what they mean in the PATCH
  route; `tags` replaces the whole list; a field left out stays as it is.
- `why` is for the reader and is never written. Keep users' data out of it.

## 6 · Write, after the owner's OK

Only after the owner has approved this round's plan in the session:

```bash
uv run python $S/apply_triage.py --env "$ENV" --plan "$ROUND/plan.json" --apply
uv run python $S/list_cases.py --env "$ENV" --all
```

In one transaction the script locks the rows, checks them against `seen`
and the rules again, writes them all to a new
`~/anyplot-backups/<UTC time>-agent-feedback-triage/rows.json` (it never
writes into an existing directory, and it reads the file back and counts the
rows), sets the changes and commits. A refusal or an error before the commit
changes nothing. The list afterwards shows the new statuses.

The `seen` check guards the script's write only. An edit on `/debug` while
the script holds its locks waits and then overwrites the round's values, so
ask the owner not to triage on `/debug` while a round applies.

To undo a round, write a plan whose fields are the snapshot's values and
whose `seen` is the state now, and apply it the same way. Two values do not
come back that way: `promoted_at` returns as the time of that write, and an
`expected` the round set cannot be cleared, because a plan, like the PATCH
route and `/debug`, only sets an outcome. It matters only while the case is
promoted, so unpromote the case instead.

## 7 · Clean up

Delete the fetched files (`rm -rf "$ROUND/files"`). Keep `report.md`,
`plan.json` and `cases.json` in the round directory; they stay out of every
checkout.

## Gotchas

- **A chat case has no versions.** For `result_version` 0 the bundle holds
  the conversation only, even when the root described a plot. The chat's
  feedback control shows only while the page has no plot, so a root reply
  that says "the plot is ready" in a chat case means no version reached the
  page.
- **A failed round carries no error.** `rounds[].outcome` says
  `render_failed`, but the bundle holds no error line or failed gate id, so a
  first render that failed cannot be attributed from the case alone.
- **The diff runs against today's catalogue.** `/debug`'s diff compares the
  case's code with the current implementation; a regeneration since the
  session changes it (`snapshot_library_version` against
  `catalogue_library_version`).
- **A root rule that failed in the case is a sign for a code check.** When
  the prompt already forbade what the root did, propose a deterministic check
  (`agents/anyplot/plugins/`, `output_guard.py`) rather than more wording.
- **Positive cases count.** A thumbs up is the only evidence that a class
  works; mark it `done` with `confirmed`, do not drop it.
- **A worktree has no `.env`.** The scripts stop with exit code 2 until you
  pass `--env`; they never fall back to a parent directory's file.
