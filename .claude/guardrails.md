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

Owner directive, 2026-08-11, refined 2026-08-16, 2026-10-21, 2026-10-28, and
2026-10-29.

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
| Larger steps and long refactors, and the main driver once Claude tokens run low late in the week | Gemini, in the owner's interactive agy session, through a brief file in `~/projects/anyplot-briefs/`, one package of at most 20 to 25 files per fresh agy subagent, independent packages in parallel (`/gemini-task`) | The owner decides what runs without asking; Gemini pushes a `gemini/*` branch and opens a draft PR; Claude reviews it, marks it ready, and follows it through |
| Check of every code PR Claude opens, before it opens; not for diffs only of docs, instruction files, changelog fragments, or `plots/`, under about 20 lines, or Dependabot (owner, 2026-10-29) | Gemini 3.8 Flash through Vertex AI in project `anyplot`, location `global`, on Flex PayGo (`/zweitmeinung`) | Copilot gets one round per PR, so its findings should already be fixed; half price on Flex, median $0.27 per review ($0.07–1.14 over 40 runs to 2026-10-31) |
| Second opinion, only when the owner asks for one | Fable and Gemini 4 Argon side by side, Argon on the same Vertex route with thinking high | Stronger across files; median $1.21 per Argon run ($0.35–1.64 over 16 runs to 2026-10-31). Both Gemini lanes are paid per token and covered by the $100 monthly Google Cloud credit that comes with Google AI Ultra; Gemini reads tracked repository files, prefetched data, and the public API through read-only tools, with no shell and no credentials |

The pipeline's model choices are separate. Sonnet's lane is narrow on purpose:
it never runs `gh` writes, `git push`, or `gcloud`, and a task whose result no
command can check goes to Opus.

**Briefs instead of issues for Gemini (owner, 2026-10-29).** Every Gemini task
used to need its own `gemini`-labelled issue; the owner wanted to hand over
larger packages with less ceremony. A second opinion (Fable and Gemini 4
Argon) rejected a pasted work order: it exists nowhere durable until Gemini's
first push, and Claude's review would read Acceptance from Gemini's own PR
text. So Claude writes a read-only brief file into `~/projects/anyplot-briefs/`,
outside both checkouts: Gemini cannot commit it by accident, and the Acceptance
it is judged against is not in the tree it edits. The read-only bit only stops
an accidental edit, since agy runs as the same Unix user (Copilot on #12458);
the skill's rule that Gemini never edits a brief carries the rest. The draft PR
carries a copy, and Claude deletes the file after the merge. An issue remains for a task the owner wants in the public
backlog. Both reviewers also found that the skill fed every issue comment to
Gemini, while it already filtered PR comments to the owner's; issue comments
are filtered the same way now. Packages stay at 20 to 25 files per fresh
session because of the 2026-10-24 drift (a convention dropped for 76 files
after about 22).

**Gemini scales out with agy subagents (owner, 2026-10-30).** The owner wanted
Gemini to scale when there is work for several agents. Research against the
Antigravity docs on 2026-10-30 found two mechanisms. Subagents
(`invoke_subagent`) run concurrently in the background, start without the
parent's conversation, can each get an isolated Git worktree, and report back
to the parent; agy deletes that worktree when the subagent ends. `/teamwork`
runs a fixed team of roles (coordinator, orchestrator, workers, critics,
auditors) on paid plans, but in its own folder `~/teamwork_projects/<project>`,
with no branches or PRs in its docs, so it does not fit work on this
repository. So independent packages go to one subagent each, at most eight at
a time (the docs give no concurrency limit and no quota figures; the owner
says when the quota runs short), each pushing its own `gemini/<slug>-<k>`
branch before it ends. The coordinator merges them into one branch and opens
one draft PR per task, not one per package: every PR costs a Copilot round, a
changelog fragment, CI, a merge, and a deploy (owner, 2026-10-30).
Running agents in parallel inside the owner's own agy session is a documented
product feature; what Google's FAQ forbids is a third-party agent such as
Claude Code driving agy under the consumer login.

**Google Jules, 2026-10-28 to 2026-10-29 (retired).** For two days Google
Jules took credential-free tasks of about 30 minutes through its official MCP
server: 300 tasks a day on Ultra, each counted once whatever it consumed, PRs
only into a `feature/*` branch, which Claude merged. The tasks paid off only
when a command could verify them. Claude's share was the prompt, every watch
event (each one a Claude turn), and the review, and on 2026-10-29 only three of
nine page-split variants kept their page unchanged. Flash beat Gemini 3 Pro on
the same prompts, Pro opening an empty commit and committing helper scripts.
The same day Google announced that Jules takes no new sessions after
2026-11-11 and shuts down on 2026-12-31, and the owner removed the lane. Two
things outlast it: the CI split below, and the checks that prove a refactor
left behaviour unchanged, now in `/gemini-task`.

**Jules PRs run CI without secrets or an OIDC token (2026-10-29).** The Fable second opinion
on the lane found that `ci-tests.yml` logged in to GCP, started the Cloud SQL
proxy, and put the database password into the environment for every PR author
but Dependabot. A Jules PR therefore ran its tests with production database
access the moment it opened, before Claude had read a line, and Jules reads a
public repository where an issue can carry a prompt injection.

Skipping the login steps was not enough, as Copilot's review of #12429
pointed out: a job with `id-token: write` lets any code in it mint a GitHub
OIDC token and trade it at the Workload Identity provider itself. So the fix
moves the permission, not just the steps:

- `ci-tests.yml` runs unit and integration tests in `Run Tests`, which has no
  `id-token` permission, for every author. Every GCP step (login, Cloud SQL
  proxy, database password, e2e tests) sits in a separate `Run E2E Tests` job
  that runs after it, and only when the PR author is neither Dependabot nor
  Jules. The Codecov token is withheld from both untrusted authors too.
- `ci-image.yml`'s `renderer-image`, the only other job with `id-token`, never
  runs for a Jules PR, and its Artifact Registry login skips Dependabot PRs.
- Jules opened PRs only into `feature/*`, which `ci-image.yml` does not cover.
  The renderer guard protected against one landing on `main` by mistake.

Every condition uses the PR author, not `github.actor`: on Jules branches most
runs showed the repository owner as the actor, and a re-run can change who
triggered it. A Jules change got its e2e run on the PR into `main`, after the
diff was read. The Jules conditions stay in the workflows until Jules stops
taking sessions on 2026-11-11, because closing a Jules PR wakes its session,
which can push again.

**No CI on pushes to `feature/**` (2026-10-29).** The PR-author conditions had
a gap the first feature-branch run exposed within the hour. Jules names its
own branch after the one it starts from (`feature/head-metadata-dedup-<session
id>`), and `ci-lint`, `ci-tests`, `ci-migrations`, and `ci-image` also ran on
every push to `feature/**`. A push run has no PR, so no author, and the
pusher is the repository owner, because Jules pushes with the owner's GitHub
grant. The `renderer-image` job of that push run got its GCP login before
Claude cancelled it; only code Jules had not touched ran with it. Since then
`feature/**` is gone from every push trigger, so a feature branch and Jules's
branches under it get CI only through pull requests, and `Run E2E Tests` and
`renderer-image` also refuse any ref under refs/heads/feature at job level.

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
Antigravity can get the account suspended. A forum reply on 2026-10-16 (Google
AI Developers Forum, topic 189905) answered a setup like ours with "No under
consumer plans", even for the unmodified binary run as a local subprocess
without touching the token; a check on 2026-10-30 found it is not marked as a
Google staff reply, so the FAQ is the authority. Only the owner's own scripts
and CI are allowed. For third-party agents Google recommends calling Gemini models
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

**One builder per scope, and one message per round** (2026-10-31 retro). The
review-fix rounds of a change stay with the builder that wrote it: it already
holds the context, and a fresh agent would spend its first hour rebuilding
it. New scope gets a new delegate on a fresh worktree instead of being fed to
a long-lived one instruction by instruction. In the session of 2026-10-28 to
2026-10-31, four builders that were steered that way (`ci-auth`,
`js-page-export`, `pb1-exec`, `pb2-serve`) grew to 11 to 19 MB of transcript
with two compactions each. Every message to an idle delegate also costs the
main loop a turn when the hand-back arrives: 67 messages drew 28 hand-backs
and at least 14 main-loop turns that only acknowledged an idle notice. So
collect what a delegate needs to hear, review findings and corrections
together, and send it as one message.

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

**A denial binds the whole session, delegates included** (2026-10-31). The
classifier refused a delegate's download of `actionlint`. The main loop then
asked the same delegate, in a batch of instructions, to try it through a
Docker image instead, "and if that is blocked too, say so and I run it". The
classifier refused that message itself as an auto-mode bypass, at 15:02 UTC.
The harness's own guidance speaks of denials "in your session", which reads
as if a peer were a fresh start; it is not, because the peer runs under the
same owner's permission decision. So a denial anywhere in the session is
final for every agent in it. The next step goes to the owner: the exact
command for a named yes, or a `!` line to run. Here the owner said yes and the
pinned image ran at 15:09.

**Console wizards: a private artifact the owner's own browser agent follows**
(2026-10-31). Some setups exist only as clicks in a vendor console, such as
the Claude Console workload identity federation for CI. The WSL session has
no Chrome tools, so when the owner asked it to set this up through Claude in
Chrome, it could not. What worked: write the steps as a private artifact,
each field name copied from the vendor's documentation rather than recalled,
with the values to enter and the result to paste back. The owner handed the
link to Claude in Chrome in the owner's own browser, which clicked through
the wizard, and the result came back about 10 minutes after the request (14:37 to
14:48 UTC).

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

## Long-running work reports progress proactively

**What happened (2026-10-30).** The `plot-all-pill` builder wrote "The gates
are still running (test and build); waiting for them to finish" at 12:09 UTC
and ended its turn on that line, without a commit and without a report; it
never woke again. The context compaction at 16:27 UTC summarised it as "still
working on the Flash fixes", and the main loop trusted the summary, which is
the only thing that survives a compaction. The main loop itself made no entry
between 17:48 and 19:46 UTC. At 19:46 the owner asked "läuft wirklich noch
was?" ("is anything really still running?"), and the answer at 19:50 was that
nothing had run since midday. The changes in the worktree were nearly
complete; the main loop finished them into #12478. On 2026-10-31 at 16:08 the
owner was again the first to say that work had gone idle ("es ist einiges
idle weiter").

**The check.** About 30 minutes with no new commit and no message from a
delegate is a suspected stall. So is any "still working" that a compaction
summary hands over. Before repeating one, read the delegate's real state:

```bash
# ListAgents first: is it listed, busy or idle?
git -C <worktree> log -1 --format='%ci %h %s'   # its last commit, and when
git -C <worktree> status --porcelain | head     # uncommitted work it may have left
```

Idle, with no commit since the brief and changes left in the worktree,
means stopped, whatever the summary says. Report it to the owner at once,
with that evidence, and then either send the delegate one message that
resumes it or take the work over. A delegate that ended its turn "waiting
for" its own background job is the pattern to look for: nothing guarantees
it is woken when the job finishes.

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
