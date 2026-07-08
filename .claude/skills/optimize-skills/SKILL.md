---
name: optimize-skills
description: Mine past Claude Code session transcripts for recurring friction — problems the user had to find manually, corrections, repeated tool errors, hand-rolled loops — and turn the patterns into skill gotchas, memory entries, or CLAUDE.md rules. Use when asked to optimize the skills, run a retro, review past sessions, or find recurring problems.
---

# Session retro: mine friction, improve the loops

Past sessions are data. This skill extracts friction signals from the
transcript JSONL files and converts recurring patterns into fixes in
the right place: a gotcha in an existing skill, a memory entry, a
CLAUDE.md rule, or a new skill/command proposal. Transcripts live
under `~/.claude/projects/<slug>/`, where the slug is the absolute
repo path with `/` replaced by `-` — derive it from the working
directory instead of hardcoding a machine-specific path. The files
are megabytes — **never read them raw**, always extract with jq.

## 1 · Extract (per transcript)

```bash
ls -S ~/.claude/projects/$(pwd | tr '/' '-')/*.jsonl
```

Four extractors, each verified against real transcripts. `FILE` is
one transcript path:

**User texts** — the user's own words: bug reports the assistant
missed, corrections, re-instructions:

```bash
jq -r 'select(.type=="user") | .message.content | if type=="string" then . elif type=="array" then (map(select(.type=="text") | .text) | join(" ")) else empty end' FILE | grep -v '^$' | grep -v '^<' | head -80
```

**Tool errors**, deduplicated by class:

```bash
jq -r 'select(.type=="user") | .message.content[]? | select(type=="object" and .type=="tool_result" and .is_error==true) | .content | if type=="string" then . elif type=="array" then (map(.text? // empty) | join(" ")) else empty end' FILE | cut -c1-200 | sort | uniq -c | sort -rn | head -20
```

**Interruptions** (user broke in mid-action — scoped to user entries,
see Gotchas):

```bash
jq -r 'select(.type=="user") | .message.content | if type=="string" then . else empty end' FILE | grep -c 'Request interrupted by user'
```

**Command repetition** (hand-rolled loops a skill should own):

```bash
jq -r 'select(.type=="assistant") | .message.content[]? | select(type=="object" and .type=="tool_use" and .name=="Bash") | .input.command' FILE | awk '{print $1, $2}' | sort | uniq -c | sort -rn | head -10
```

## 2 · Judge into categories

- **undetected-problem** — the user reports something broken that the
  assistant did not catch itself (found via manual testing, the live
  site, a screenshot). The most valuable signal: each one means a
  verification loop has a hole.
- **user-correction** — the user redirects („nein", „nicht so",
  switching tool/approach).
- **recurring-tool-error** — same error class ≥ 3× (permission
  denials, missing flags, `/api`-prefix 404s, wrong package manager).
- **manual-repetition** — the same command sequence run many times
  (dozens of `gh run list` / `gh pr checks` cycles = the loop belongs
  in a skill or command).
- **workflow-friction** — anything else that cost a round trip
  (blocked sleeps, stalled background waits, harness denials).

Ignore: routine output, system reminders, skill/command texts pasted
into user messages, one-off typos, and the **expected** chatter of
pipeline babysitting (bulk-generate monitoring output is high-volume
by design — only its *failures* and hand-rolled polling loops count
as friction).

## 3 · Scale: fan out for many sessions

For 1–2 transcripts, run the extractors inline. For more, use a
Workflow: one mining agent per transcript (each runs the §1
extractors and returns structured findings), then a single synthesis
agent that clusters across sessions, ranks by `sessions × frequency`,
and — **after reading the current skill files** — proposes only fixes
that aren't already documented.

## 4 · Convert patterns into fixes

Route each accepted pattern to where it prevents the recurrence:

- behaviour during verification/shipping → a **gotcha/step in the
  matching `.claude/skills/` skill** (`verify-*`, `open-pr`)
- repeatable multi-step procedures → an **`agentic/commands/*.md`
  command** (edit there, never in `.claude/commands/` — it's a
  symlink)
- environment/infra knowledge → a **memory entry** under
  `~/.claude/projects/<slug>/memory/` (update existing files before
  creating new ones; keep the MEMORY.md index in sync)
- session-spanning working rules → **CLAUDE.md** (duplicate into
  `.github/copilot-instructions.md` only if it's a repo/domain rule
  the reviewer bot needs, not a Claude-harness rule — and honor the
  declared sync duties between the two)

Apply small, low-risk fixes (gotchas, memory) directly and list them;
anything touching settings, hooks, workflows, or new repo code is a
recommendation for the user, not a unilateral change. Repo-file
changes ship as a normal PR through `/open-pr` (changelog entry
included).

## Gotchas

- **Workflow `args` can arrive undefined** — inline the transcript
  file list in the script body instead of passing it via `args`.
- **`.message.content` is string OR array** depending on entry type —
  both extractor branches are needed, otherwise jq silently drops
  half the messages.
- **User-text extraction picks up pasted skill instructions** and
  command output; the `grep -v '^<'` filter drops system-reminder
  blocks, the rest needs judgment in §2.
- **Transcripts may contain secrets** (env output, tokens). Findings
  quote error *classes*, never raw transcript lines with values, and
  nothing from a transcript gets committed verbatim.
- **The current session is in the list** — including it is fine (its
  friction is the freshest), but its file keeps growing while you
  mine; frequencies for it are a snapshot.
- **A raw `grep -c` for interruptions false-positives** when the
  transcript embeds skill/command text containing the phrase (this
  SKILL.md being read or written mid-session once produced 4 phantom
  interruptions) — hence the jq-scoped extractor above; verify
  nonzero counts against entry context.
- **Transcript retention is limited** (old sessions are cleaned up) —
  run this regularly (e.g. a weekly/monthly cadence) or the friction
  history evaporates before it's mined.

## Troubleshooting

- jq prints nothing for a file that clearly has content → you are
  filtering on the wrong `.type`; inspect first:
  `jq -r '.type' FILE | sort | uniq -c`.
