# Agent operations

This document says which model or agent does which kind of work in this
repository: the main session, subagents, the Gemini lane, the check before a
code PR opens, and second opinions. `CLAUDE.md` makes it binding under "Pick
the agent by the work": read it before you start a subagent or hand work to
another model. If this document and `CLAUDE.md` ever disagree, `CLAUDE.md` is
the rule.

The history behind each lane, with the incidents and numbers that shaped it,
is in [`.claude/guardrails.md`](../../.claude/guardrails.md), section "Pick the
agent by the work". The model choices of the automated plot pipeline are
documented in [`project-guide.md`](project-guide.md) and are separate from
this document.

## The principle

Pick the agent by the work, and spend Claude tokens last: work that another
lane can do well goes there first.

## Claude sessions and subagents

- The main session runs on Opus; the owner starts a planning session on Fable
  when the plan matters.
- A subagent runs on Opus (`model: opus`) when it changes state outside its own
  worktree (gcloud, `gh` writes, `git push`, labels, prod) or makes judgment
  calls; on Sonnet for bounded work inside its own worktree that a command
  verifies; on Haiku only to read or poll (CI, deploys, `gh`/`gcloud` state) and
  to create Todoist tasks (pipeline model choices are separate).
- Escalate to Fable for high-risk reviews (security, prod data, sandbox,
  privacy) and genuinely hard reasoning.

How to brief a delegate (the decide-and-document split, Edit/Write only, `git`
only in its own worktree) stays in `CLAUDE.md`, because every delegation needs
it.

## The Gemini lane

- Larger steps, and the week's driving once Claude tokens run low, go to Gemini
  as brief files in `~/projects/anyplot-briefs/` (a `gemini`-labelled issue
  only when the owner asks for one) that the owner works in his interactive agy
  session, one package of at most 20 to 25 files per fresh agy subagent,
  independent packages in parallel (`/gemini-task`).
- Gemini pushes only its `gemini/*` branch and opens only draft PRs, which
  Claude reviews before marking them ready.
- Claude never runs `agy` itself, not even read-only: Google's Antigravity FAQ
  forbids running it from third-party coding agents under a consumer login.
- Never extract, copy, or proxy the agy login (Antigravity terms §6).

## Gemini reviews

- Gemini through Vertex AI in project `anyplot`, with read-only tools
  (`/zweitmeinung`), checks every code PR Claude opens before it opens (Gemini
  3.8 Flash; diffs only of docs, instruction files, changelog fragments, or
  `plots/`, diffs under about 20 lines, and Dependabot bumps excepted), so
  Copilot's one round ideally finds nothing. The `/open-pr` skill runs this
  check.
- A second opinion, Fable and Gemini 4 Argon side by side, runs only when the
  owner asks for one.
