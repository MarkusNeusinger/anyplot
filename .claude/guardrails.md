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

## Pick the agent by the work, and spend Claude tokens last

Owner directive, 2026-08-11, refined 2026-08-16, 2026-10-21, and 2026-10-28.

**The lanes (2026-10-28).** The Anthropic weekly limit runs out long before
the owner's Google AI Ultra quota, so the work is split by what it needs, and
work that Google's quota can do goes there first.

| Work | Who | Why |
|---|---|---|
| The main session | Opus; Fable when the owner starts a planning session on it | Fable plans; execution then runs in an Opus session |
| Subagent that changes state outside its worktree (`gcloud`, `gh` writes, labels, merges, prod) or makes judgment calls | Opus | Owner: he does not trust the smaller models with writes |
| Subagent with bounded work inside its own worktree, verified by a command it runs | Sonnet | Cheaper for work whose result a command checks; never writes outside its worktree |
| Reads or polls with credentials (CI, deploys, `gh`/`gcloud` state); creates Todoist tasks | Haiku | Cheap; never changes state |
| High-risk reviews (security, prod data, sandbox, privacy); genuinely hard reasoning | Fable | About 2.5 times Opus per token at API prices, so only where it pays |
| Credential-free implementation that fits a roughly 30-minute cloud run | Google Jules through its MCP server (`/jules-task`), model chosen in the Jules account (Flash since 2026-10-28) | 300 tasks a day on Ultra, each counted once whatever it consumes; Claude spends tokens only on the prompt and the review |
| Larger steps and long refactors, and the main driver once Claude tokens run low late in the week | Gemini, in the owner's interactive agy session, through a `gemini`-labelled issue (`/gemini-task`) | The owner decides what runs without asking; Gemini pushes a `gemini/*` branch and opens a draft PR; Claude reviews it, marks it ready, and follows it through |
| Check of every PR Claude opens, before it opens | Gemini 3.8 Flash through Vertex AI in project `anyplot`, location `global`, on Flex PayGo (`/zweitmeinung`) | Copilot gets one round per PR, so its findings should already be fixed; half price on Flex, $0.07–0.28 per review |
| Second opinion, only when the owner asks for one | Fable and Gemini 4 Argon side by side, Argon on the same Vertex route with thinking high | Stronger across files; $0.57–1.16 per Argon run. Both Gemini lanes are paid per token and covered by the $100 monthly Google Cloud credit that comes with Google AI Ultra; Gemini reads tracked repository files, prefetched data, and the public API through read-only tools, with no shell and no credentials |

The pipeline's model choices are separate. Sonnet's lane is narrow on purpose:
it never runs `gh` writes, `git push`, or `gcloud`, and a task whose result no
command can check goes to Opus. Sonnet and Jules both take bounded,
command-verified work. Jules wins whenever the work can start from a pushed
branch; Sonnet keeps the work that needs unpushed local state or a local
service (browser, Docker renderer, throwaway Postgres), or that takes under
about ten minutes, where a 15- to 30-minute cloud run would stall the session.

**Why Jules is allowed when agy is not (2026-10-28).** Jules has an official
REST API (`jules.googleapis.com`) authenticated by an API key from the Jules
settings page, which Google documents for embedding Jules in other tools, and
the MCP server comes from Google Labs (`@google/jules-mcp`). Nothing touches
the owner's Google login. Claude never runs the `jules` command-line tool,
which signs in with that login, for the same reason it never runs `agy`.

**Jules's merge rule (owner, 2026-10-28).** With up to 300 Jules PRs a day the
owner cannot read each one. So Claude merges the sub-PRs Jules opens into a
`feature/*` branch the session leads, after reading the diff, and the owner
reviews once, when that branch goes to `main`. CI runs on pushes to
`feature/**` but not on pull requests into it, so the merge is gated by
Jules's own verification and Claude's reading, and CI checks the result right
after. Copilot's ruleset covers only PRs into `main`, so the sub-PRs cost no
Copilot round.

**Gemini 3 Pro against Flash in Jules (2026-10-28).** The same two prompts
(#9636, a three-file dedup; #9629, a 29-file migration) ran on both. Flash
opened correct PRs in 23 and 17 minutes. Pro opened an empty commit for the
first, failed after 27 minutes on the second, and spent 74 minutes on a
follow-up in which it committed four helper scripts and rewrote a meta
description nobody had asked about. Two tasks are thin evidence, so the choice
is provisional: Flash is the account setting until a newer Pro model beats it
on the same prompts.

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
- Flex PayGo halves the price of 3.8 Flash; Argon has no Flex. Flex gets 5
  minutes per run, then the run goes online. The SDK retries timeouts too, so
  one review waited over an hour on 15-minute attempts on 2026-10-22, and
  with 5 minutes per request the next one still ran for over 25 minutes.
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

## After every merge, check that the site renders

Owner rule, 2026-10-22, after an outage nothing caught.

**What happened.** A Dependabot batch merged nine PRs in an afternoon, one
lock file at a time, each with green checks. One of them, vite 8.0.16 to
8.1.6 (#12225), deployed at 17:55 UTC. Rolldown 1.1.5 put its CJS-interop
runtime helper into the app's `theme` chunk, which imports `mui`, while
`mui` imports the helper back. The chunk cycle left the helper undefined, the
bundle threw `TypeError: t is not a function` at module load, and every page
on anyplot.ai rendered blank. Every PR check passed, including "Build app
image and smoke the origin gate", which proves nginx serves the shell but
never runs the JavaScript. The deploy was green too. The owner noticed about
45 minutes later; a cloud session found the cause and shipped vite 8.3.5
(#12235), which emits the helper as its own `rolldown-runtime` chunk.

**The check.** `scripts/site-smoke.mjs` loads `/`, `/plots` and
`/scatter-basic` in headless Chromium and fails on a status other than 200,
an uncaught page error, or a `#root` with next to no text; it also checks
`api.anyplot.ai/health`. It takes about two seconds. The recipe is in
`/open-pr` §4. Run against a build of the broken commit, it fails exactly as
the outage did; against a healthy one it passes, with the CORS error of a
foreign origin reported as a warning only.

**Two layers.** The `app-image` job of `ci-image.yml` runs the same script
against the built container before the merge, so a bump that breaks the boot
fails its PR. It runs when the container's inputs change (`package.json`,
`yarn.lock`, `vite.config.ts` and the like), not for `app/src` edits, and it
cannot see what only production has: the CDN, the origin gate armed, the real
data. The post-merge run covers those, and every merge that never builds the
container.

**Why after every merge.** A merge that touches no `app/` file can still
break the site through the API, a Cloudflare rule, or a data change, and the
run costs seconds. A `FAIL` stops further merges until the site renders,
because each extra merge widens the set of suspects and the revert.

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
