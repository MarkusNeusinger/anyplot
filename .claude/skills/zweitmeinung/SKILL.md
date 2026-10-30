---
name: zweitmeinung
description: Get an outside second opinion on the current plan, design or diff from Google Gemini through Vertex AI (4 Argon for second opinions the owner asks for, 3.8 Flash for the check of every code PR Claude opens; read-only tools over the repository), optionally side by side with a Fable subagent, and compare it with your own view. For Claude only; Gemini in agy never runs it. Use when the owner asks for a "Zweitmeinung", a second opinion, a Gemini or Google opinion, or a Fable and Gemini review of a plan, and for the Flash check before Claude opens a PR. Never implements anything by itself.
---

# Zweitmeinung (second opinion)

Goal: an independent critique of the current plan or change from a model family other
than yours, compared honestly with your own view. The skill gathers and compares
opinions; it never implements a suggestion on its own. The owner decides.

This skill is for Claude. Gemini in the owner's agy session sees it through
`.agents/skills/` but never runs it: it would be asking itself.

**Never run `agy` from Claude.** Google's Antigravity FAQ, and a forum reply of 2026-10-16
not marked as Google staff (discuss.ai.google.dev/t/189905), say that running the Antigravity CLI from a third-party
coding agent such as Claude Code under a consumer login (the owner's Google AI Ultra)
breaks the terms and can get the account suspended, even with the unmodified binary and
no token access. The Gemini part therefore runs through `gemini_review.py` in this
directory: Gemini on Vertex AI in project `anyplot`, location `global` (the owner's choice
on 2026-10-21; the site's own agents stay on `eu`), billed to the anyplot billing account,
where the Google AI Ultra Cloud credit ($100 a month) applies. Implementation work for
Gemini goes through briefs the owner works in his own interactive agy session
(`/gemini-task`).

## 1. Check the setup

```bash
GR="env -u GOOGLE_GENAI_USE_ENTERPRISE -u GOOGLE_GENAI_USE_VERTEXAI uv run -q --no-project --with google-genai==2.29.0 python -I $(git rev-parse --show-toplevel)/.claude/skills/zweitmeinung/gemini_review.py"
$GR check
```

- It uses the local Google Cloud login (ADC, `gcloud auth application-default login`), so
  it runs on the owner's machine, not in a cloud session. Never print or copy credentials;
  the script handles them and Gemini never sees them.
- `not reachable`: show the owner the reason line and continue with Fable alone. Do not
  fall back silently to another model.

## 2. Who reviews

**The owner's standing rules (2026-10-15, 2026-10-21, 2026-10-22 and 2026-10-28):**

- **The owner asks for a "Zweitmeinung" or a second opinion:** Fable and Gemini 4 Argon
  (`gemini-4-argon`, the default, thinking `high`: the owner wants it to think), both in
  parallel. Only when he asks (owner, 2026-10-28): a plan does not get one by default, so
  offer it for a large plan instead of running it.
- **Every code PR Claude opens, before it opens** (`/open-pr` section 1 names the
  exceptions: docs, instruction files, changelog fragments, `plots/`, under about 20
  lines, Dependabot; nobody asks): Gemini
  3.8 Flash alone (`--model gemini-3.8-flash`; Flex PayGo turns on by itself, half
  price), so that Copilot's one round finds nothing. Flash is on probation, see step 4.
  Fable joins only for high-risk changes (security, prod data, sandbox, privacy,
  credentials) or when Gemini reports something serious.
- **A diff Gemini wrote** (`/gemini-task`): a Gemini review never counts as the
  independent review of Gemini's work. A fresh Opus subagent reviews the diff from the
  acceptance criteria alone. Fable for high risk.
- Copilot reviews every PR last, whatever ran before.

Only when the owner names other models, or explicitly asks to choose, propose 2–3 Gemini
models with AskUserQuestion, recommended option first (`--model <id>`). Never a Claude
model: the point is a foreign opinion, and Fable covers the Claude side.

## 3. Build the briefing

Gemini has five read-only tools and uses them on its own:

- `list_files`, `read_file`, `read_files` (up to 10 files in one call), `search`: the
  files git tracks in `--root` (a worktree of the code under review), plus everything in
  `--data` as `data/...`. Untracked files (`.env`, local settings), symlinks leading
  outside, and secret-looking names in `--data` never appear.
- `http_get`: GET on `https://api.anyplot.ai` only (no `/debug`, no `/mcp`, no
  redirects).

Each tool turn re-sends the whole conversation and is paid again, so whatever Gemini will
certainly need goes into the first prompt: `--diff-base <ref>` inlines the diff and the
changed files (lock files, binary files and files over 60 KB are left to the tools), and
`--attach` adds further files from `--root` or `--data`. The briefing then names what to
check rather than pasting everything. Write it into a private temp directory
(`D=$(mktemp -d)`, `$D/briefing.md`), in English:

- **Context:** what the system is, in 3–6 lines.
- **The plan or change** to review, compact (decisions the owner already took are marked
  as such; the reviewer may still challenge them, but must say so). For a diff: say that
  it and the changed files follow the briefing.
- **Where to look:** the paths and live endpoints the critique centres on.
- **Questions:** the specific points you want challenged.
- **Requested output:** verdict (sound / sound with changes / rethink); findings ranked by
  severity with `path:line` evidence and a concrete fix; what it would do differently;
  claims it could not verify marked as such. Plain text, under about 1,000 words.

Other prefetched material goes into `$D/data/`: files from outside the repository,
read-only SELECT results, build logs, PR threads; `--attach` the parts Gemini will
certainly read. Strip personal data (feedback messages, emails, IP hashes) and never put
a secret there; the script refuses obvious secret file names in `--data`, but the content
is your responsibility.

Gemini's safety filter refuses prompts that read like attacks (finding or using tokens,
probing isolation); the script then exits 3 with a `block_reason`. Rephrase as a review
question; for real security probing use Fable.

## 4. Run the second opinion

For a change under review, point `--root` at a throwaway detached worktree of its head.
Flex gets 5 minutes per run. Once its turns add up to that, or one times out or meets a 429
or 5xx, the rest of the run goes online (`flex_fallback` in the summary, the wait per turn
in `per_turn_seconds`). Run the review in the background:

```bash
mkdir -p "$D/data"
W="$D/wt" && git fetch -q origin && git worktree add -q --detach "$W" <ref>
$GR [--model gemini-3.8-flash] review --briefing "$D/briefing.md" --root "$W" --diff-base origin/main \
  --data "$D/data" --out "$D/gemini.md" > "$D/gemini.json"
echo "exit=$?"
git worktree remove --force "$W"
```

`--model` goes before `review`. For a plan without code changes, `--root` is a worktree
of `origin/main`, or the current branch's worktree, which the tools only read.

- **Exit 0:** read `$D/gemini.md`. `$D/gemini.json` holds turns, tool calls, token counts
  (also per turn, to see the cache hit rate), `traffic_type` (`ON_DEMAND_FLEX` confirms
  Flex) and `est_cost_usd` at Vertex list price for `global`, per 1M tokens: Argon $4 /
  $20 / cached $0.20; Flash $1.50 / $7.50 / $0.15, and half of that when every turn ran
  on Flex.
- **Exit 2:** setup or input problem; the message says which. **Exit 3:** blocked, or no
  answer (the model kept calling tools after the budget). **Exit 4:** the answer stopped
  early (`finish_reason`); use what is there and say so.
- **Bounds:** 8 tool turns and 600k input tokens summed over all turns (`--max-turns`,
  `--max-input-tokens`). Then the tool responses tell Gemini to answer from what it has
  (`stopped_by`), and two more tool calls at most are refused before the run ends.
- **Cost, measured on 2026-10-21 and 2026-10-22:** Flash $0.07–0.28 per review, mostly
  thinking; Argon $0.57–1.16. The owner's account merges about 8 PRs a day, so routine
  reviews must stay cheap.
- **Flash is on probation.** The owner's decision on 2026-10-22: measure it on real PRs,
  with no extra test runs. On every PR Flash reviewed, once Copilot's review is in, add
  `copilot_findings` (the real ones) and `matched_copilot` (how many of those Flash also
  had) to that run's ledger line. Since 2026-10-28 Flash runs before the PR opens and its
  findings are fixed first, so `copilot_findings` counts what Copilot still raises after a
  Flash pass, and `flash_fixed` how many Flash findings were fixed before the PR opened.
  After about 10 PRs, report the balance to the owner.
- **Ledger:** append one JSON line to `~/.claude/team-ledger.jsonl`: `date`, `repo`,
  `task`, `lane` (`gemini-review` or `fable-review`), `model`, `gemini_tokens` (prompt +
  output + thoughts), `est_cost_usd`, `claude_tokens`, `findings` (count),
  `true_positives` (findings you verified).

Fable (when step 2 calls for it): spawn a subagent with `model: "fable"` and the same
briefing. It may also read the repository read-only, in a detached worktree it removes
afterwards. Run it in parallel with the Gemini call, and note its token use from the
completion notification for the ledger.

## 5. Report

Summarise each opinion in a few bullets, then compare:

| Point | You | Gemini | Fable |
|---|---|---|---|

- **Agree:** what all sides see the same way.
- **Disagree:** where they differ, and why you think so. Verify claims against the code
  before you accept them; drop what you cannot substantiate.
- **What I would adopt:** concrete changes, ranked, each with its reason.
- **Open decisions for the owner:** phrased as option questions (AskUserQuestion), with
  your recommendation first.

Write the report in the owner's language. Nothing is implemented automatically; changes
only follow the owner's decision. If the work later goes into a PR, the Copilot review
there is the third, independent check; do not skip it because a second opinion exists.
