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

Owner directive, 2026-08-11, refined 2026-08-16 and 2026-10-21.

Pass `model: opus` when spawning subagents or workflows. Opus is the default
answer, and it is the only tier that changes state outside its own worktree.

**The lanes (2026-10-21).** The Anthropic weekly limit runs out long before
the owner's Google AI Ultra quota, so the work is split by what it needs.

| Work | Who | Why |
|---|---|---|
| Changes state: `gcloud`, `gh` writes, labels, merges, prod | Opus | Owner: he does not trust Haiku with writes |
| Reads or polls with credentials (CI, deploys, `gh`/`gcloud` state); creates Todoist tasks | Haiku | Cheap; never changes state |
| High-risk reviews (security, prod data, sandbox, privacy); genuinely hard reasoning | Fable | About 2.5 times Opus per token at API prices, so only where it pays |
| First review of a normal PR | Gemini 3.8 Flash through Vertex AI in project `anyplot`, location `global`, on Flex PayGo (`/zweitmeinung`) | Half price on Flex, $0.07–0.28 per review; on probation since 2026-10-22, measured against Copilot's findings on real PRs |
| Plans, second opinions, analysis of briefings and fetched files | Gemini 4 Argon on the same route, thinking high, next to Fable for a second opinion | Stronger across files; $0.57–1.16 per run. Both Gemini lanes are paid per token and covered by the $100 monthly Google Cloud credit that comes with Google AI Ultra; Gemini reads tracked repository files, prefetched data, and the public API through read-only tools, with no shell and no credentials |
| Credential-free implementation worth an hour or more, including long refactors | Gemini, in the owner's interactive agy session, through a `gemini`-labelled issue (`/gemini-task`) | The owner decides what runs without asking; Gemini pushes a `gemini/*` branch and opens a draft PR; Claude reviews it, marks it ready, and follows it through |

Sonnet has no lane in interactive sessions; Gemini covers that work, and the
pipeline's model choices are separate. Planning or architecture sessions may
run on Fable as the main model when the owner starts them that way; execution
then runs in an Opus session.

**Why not headless Gemini implementation.** Measured on 2026-10-21:

- **Commands would run unattended.** `agy -p` cannot ask for permission, so
  letting Gemini run commands needs `--dangerously-skip-permissions`. On this
  machine that means unattended commands with the owner's credentials.
- **A container does not fix it.** agy's login is a `cloud-platform` token of
  an account that is project owner, so copying it into a container moves owner
  rights in with it. A hostname allowlist does not confine it: Google front
  ends route by the `Host` header, so a request sent to
  `daily-cloudcode-pa.googleapis.com` with `Host: sqladmin.googleapis.com`
  reaches Cloud SQL Admin.
- **The token broker hit the terms.** A broker that kept the token outside the
  container worked technically. It breaks the Antigravity terms (section 6:
  third-party tools or proxies accessing the service), for which Google
  suspended accounts in 2026, so it was removed the same day.

So nothing extracts, copies, or proxies the agy login.

**Why Claude never runs agy (2026-10-21).** Until that day Claude ran
read-only `agy -p` for second opinions. Google's Antigravity FAQ says that
wrapping `agy` inside third-party coding agents is not supported under
consumer plans, and that using third-party tools such as Claude Code to access
Antigravity can get the account suspended. A Google staff reply on 2026-10-16
(Google AI Developers Forum, topic 189905) answered a setup like ours with "No
under consumer plans", even for the unmodified binary run as a local
subprocess without touching the token. Only the owner's own scripts and CI are
allowed. For third-party agents Google recommends calling Gemini models
through Gemini Enterprise (Google Cloud) or a Google AI Studio API key. So
second opinions call Gemini through Vertex AI, which is plain Google Cloud
usage, and only the owner starts agy, for `/gemini-task`.
The site's own agents stay on the `eu` location; second opinions use `global`,
which is 10 % cheaper and the only location with Flex PayGo.

**What the Vertex route costs (2026-10-21 and 2026-10-22).** The first Argon
review cost $1.01, and the owner's account merges about 8 PRs a day, so
routine reviews moved to Flash. Every tool turn re-sends the whole
conversation, so the cost is mostly turns:

- `--diff-base` puts the diff and the changed files into the first prompt, and
  `read_files` reads several files in one call.
- The tool configuration stays the same on every turn. A last turn without
  tools lost Vertex's implicit cache, and Flash kept calling tools anyway.
- Flex PayGo halves the price of 3.8 Flash; Argon has no Flex. A Flex request
  is tried once and waits at most 5 minutes before the run goes online: the SDK
  retries timeouts too, and one review waited over an hour that way on
  2026-10-22.
- Not worth it: explicit caching (not offered for Argon), Batch (asynchronous,
  up to 24 hours), the Interactions API (the history is still processed and
  paid), and pruning old tool output (it breaks the cached prefix).

**Long agy tasks run unattended (owner, 2026-10-22).** The owner trusts Gemini
in his own session to keep to the rules as he trusts Claude, so for a long task
he lets it run tests and builds without asking. That is his interactive use of
his own account, not automation around it. The clone holds no `.env`, and agy
starts with a minimal environment.

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
