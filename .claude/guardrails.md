# Guardrails — the long version

`CLAUDE.md` states each working rule as one line: the rule and its shortest
reason. This file holds what does not fit there — the incident that produced
the rule, the recipe it implies, the numbers that make it credible.

The split exists because `CLAUDE.md` is loaded into **every** session, so its
cost is paid on every turn, while a retro narrative is needed only when
someone actually hits the situation. Nothing here is a new rule. If this file
and `CLAUDE.md` ever disagree, `CLAUDE.md` is the rule and this is the
commentary that fell behind.

Sections follow the order in which `CLAUDE.md` states the rules.

---

## Delegated agents run on Opus by default

Owner directive, 2026-08-11, refined 2026-08-16.

Pass `model: opus` when spawning subagents or workflows — the tier the
`agentic/README.md` model table already uses for large tasks. Escalate to
Fable for genuinely hard reasoning, drop to Sonnet or Haiku for mechanical
grinding, but Opus is the default answer.

Escalation is for judgment calls, not for every detail. Within its briefed
scope a delegate decides routine matters itself and documents them; otherwise
delegation gains nothing. What comes back to the main loop, which keeps the
overview, is anything that changes scope, contradicts the brief or the docs,
or would be expensive to redo. Say that split explicitly in the prompt:
decide-and-document versus return-as-finding.

**Two lines every brief carries** (2026-09-05). A delegate reads `CLAUDE.md`
like anyone else, but it also receives harness reminders that arrive LATER in
its context and therefore read as the more recent instruction. In auto mode
one of them prescribes editing files through `sed`, heredocs and short
scripts. In the sibling repository three agents in one day followed it against
the Edit/Write rule, two of them for the single-token `sed -i` that fills the
PR number into a changelog fragment — the same fragment format this repository
uses. A fourth ran `git checkout -b` in the SHARED checkout, which moves a ref
the owner's own working tree is sitting on. So spell both out in the brief, in
the brief's own words:

1. Repo files are modified ONLY with Edit/Write — `CLAUDE.md` wins over the
   auto-mode reminder.
2. All `git` happens in the agent's own worktree; the shared checkout is left
   on the branch it was found on.

Neither is new policy. Both are precedence a brief has to make explicit,
because an agent cannot infer precedence from the order messages arrived in.

## External-system writes need explicit, named authorization

The rule is the asking. This section is about what to hand over once the
answer is yes and the agent still cannot run the command itself.

Some prod runbooks are refused by the harness permission classifier rather
than by the owner — the `gcloud run services update` plus `update-traffic`
pair that arms the site's origin gate is one, observed 2026-09-04. Reaching
for a different phrasing of the same command is the wrong move: the classifier
is not an obstacle to route around. Stopping half-way is not the danger
either, when the runbook is built for it — the pair in
`infra/cloudflare/README.md` § "Arming, in full" stages the new revision and
promotes it by name, so a config that fails to render leaves the revision
never ready and traffic on the old one, which the README calls a safe failure
and the reason its step 4 is not optional. The real danger is reading the
STAGED revision as the finished one and reporting an arm that never took
traffic.

The pattern that works: write the runbook as ONE script in the scratchpad —
never into the repo — and hand the owner a single line to paste:

```
! bash /tmp/…/scratchpad/arm-origin-gate.sh
```

The script does the whole pair under `set -euo pipefail`, echoes what it is
about to change, and ends by reading the state back — for that gate, the
`x-origin-gate` response header AND `status.traffic`, because only the second
says which revision answered. Rules for it: one action per script, and no
secret values in its output.

**The reverse direction is its own script, not the same one with a flag.**
`infra/cloudflare/README.md` § "Rolling back" is explicit about why: a
rollback has to run in the worst state the service can be in, which includes
the secret having been disabled during the incident — so it never looks the
SECRET up. It still resolves the serving revision and its image, because it
has to; what it must not do is depend on anything the incident may have taken
away.

Afterwards, VERIFY from the session with a read the agent is allowed to make,
instead of trusting a "done" in chat. A runbook that shipped this way belongs
in the owning README, so the next round starts from a reviewed text rather
than a fresh improvisation.

## Modify repo files only with the Edit/Write tools

Appending with `>>` counts — appending at the end of a file is exactly the
forbidden path, however little it feels like editing.

When a Bash command legitimately mutates a tracked file (a formatter, codegen,
`git checkout`), read the file again before the next edit; stale-state errors
cascade otherwise.

The moment this rule gets broken is when an edit ANCHOR fails — "string not
found", "file modified since read". The answer is a fresh targeted read plus a
longer anchor, never a regex rewrite from a heredoc. The other moment is a
change small enough to feel exempt: a one-token substitution reads like a
`sed` job, and `sed -i` on a changelog fragment is how three delegated agents
in one day broke the rule in the sibling repository (2026-09-05). Size is not
the criterion; the tool is.

The exemptions are narrow and stated in `CLAUDE.md`: GitHub Actions workflows
and codegen scripts write files by design. An interactive session is never one
of those.
