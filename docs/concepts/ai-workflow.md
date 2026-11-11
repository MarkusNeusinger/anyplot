# How anyplot is built with AI agents

> **Status (2026-11-05):** the workflow as practiced on this date. The active-day count in "Where it falls
> short" was taken on 2026-11-04 from `git log`.

Models write anyplot's code; I lead them. This page describes how that works: who does what, what I bring
to it, the path a change takes to production, how a correction becomes a rule, and where the approach
falls short. The rules themselves are in [`CLAUDE.md`](../../CLAUDE.md), which model or agent takes
which work in [`agentic/docs/agent-operations.md`](../../agentic/docs/agent-operations.md), the
incidents behind them in [`.claude/guardrails.md`](../../.claude/guardrails.md), and the procedures in
[`.claude/skills/`](../../.claude/skills/). This page explains them; it doesn't repeat them.

## Who does what

| Who | Role |
|---|---|
| Me | The vision and the decisions. I cut the work into tasks and hand them out, keep the overview, test changes myself, and send work back until it's right. I approve every spec, read every user-facing text before it ships, and give every merge outside the plot pipeline its explicit OK. |
| Claude Code sessions I direct | Plan and build the site, the API, the agent service, and the pipeline itself. A main session splits the work; each task goes to its own agent, in its own git worktree. |
| Claude in GitHub Actions | The plot pipeline: it drafts a spec from an issue, writes each library's implementation, and reviews and repairs it against the rubric; the workflows merge it. See [Workflows](../workflows/overview.md). |
| Gemini | Second opinions on plans and diffs, with read-only access to the repository ([`/zweitmeinung`](../../.claude/skills/zweitmeinung/SKILL.md)); a check of every code pull request Claude opens before it opens; and larger delegated packages that I run in my own Gemini session, which come back as draft pull requests for Claude to review ([`/gemini-task`](../../.claude/skills/gemini-task/SKILL.md)). |
| GitHub Copilot | One review round per pull request. |

## What I bring

I trained as an energy electronics technician, then studied physics at Heidelberg University (Diplom,
2012), with a thesis in physics and computer science on finding stellar streams in large public astronomy
data sets with modern clustering methods. Since 2013 I've worked as a data analyst, then senior data
analyst, in steering system development: data pipelines, the central analytics database, statistics and
SPC, machine learning, and web apps with FastAPI and React, lately MCP servers and AI agents. I know that
stack from doing it myself: from 2022 to 2024 I built and ran defichain-data, a platform for blockchain
market data (Python ETL, PostgreSQL, FastAPI, React, and TradingView charts on Google Cloud), largely
without AI, until the blockchain lost its relevance.

That's what leading the models takes: knowing which question to ask, when an answer only sounds right, and
when the structure starts to turn into a mess. It shows in four ways:

- **Decisions on record.** The [agent chat's design](agent-network.md) names an owner decision, rule, or
  request more than 80 times, each with its date and reason. Three examples: a safety check that can't answer
  refuses instead of guessing (2026-10-11); data keeps the precision it came with (2026-10-15); and usage
  telemetry never holds a message, a data value, or a column name (2026-10-16).
- **Pushing back after testing.** On 2026-10-14 a live test showed plain answers, and even refusals,
  waiting about 60 seconds behind the plot queue. My note was "bei sowas muss schnell die antwort kommen"
  (with something like this, the answer has to come fast). The same day the queue shrank to the sandbox
  work alone.
- **Research before a decision.** Where a plot type has its field's conventions, I had the agents
  research them and cite their sources before writing what a good version looks like. One batch of line
  and time-series specs cites 30 sources ([#12013](https://github.com/MarkusNeusinger/anyplot/pull/12013)).
  The agent chat's design was fact-checked against the ADK source and the Vertex AI documentation, and
  measured spikes of the sandbox came before the sandbox itself.
- **Knowing what has to hold.** Security is a good example: I know what has to hold, private data and no
  way to abuse the service, and asking the right question is often enough for a model to find what still
  needs hardening. Before the chat went public, the question of what the request logs keep moved the
  session id out of every URL, because Cloud Run keeps a request's URL together with the client's address
  for 30 days ([`agent_public.py`](../../api/routers/agent_public.py)).

## The path of a change

1. **Idea and plan.** I say what I want and why. For a change that matters, a planning session writes
   the plan first.
2. **Second opinion.** A large plan goes to Fable and Gemini 4 Argon side by side. I decide what to take
   from their findings.
3. **Build.** One build agent per task works in its own worktree, never on `main`. It runs the
   verification skill for what it touches, such as a browser check at two widths in both themes for the
   frontend, or every migration against a throwaway PostgreSQL. A larger change also gets a mutation
   table: one deliberate break per behavior, and each break must turn a test red.
4. **My test.** I try the change locally and send it back until I like it.
5. **Pre-PR check.** Gemini 3.8 Flash reads the whole diff before the pull request opens, so that
   Copilot's round ideally finds nothing.
6. **Pull request.** When it changes user-facing text, its body lists each string verbatim under "Texts
   to read", and I read them. CI requires a changelog fragment.
7. **Review.** Copilot reviews once. The build agent fixes the findings that hold up and resolves the
   threads.
8. **Merge.** Only on my explicit OK.
9. **After the merge.** The agent watches the deploys, then checks that the live site renders
   ([`scripts/site-smoke.mjs`](../../scripts/site-smoke.mjs)). The whole loop from the pull request on
   is [`/open-pr`](../../.claude/skills/open-pr/SKILL.md).

## Corrections become rules

Every agent reads `CLAUDE.md` when its session starts. So when a mistake comes back, I don't explain it
again: it becomes a rule with its reason, a step in a skill, or a test, and the incident goes into
`.claude/guardrails.md` with its date. `CLAUDE.md` keeps one line per rule, because every session pays
for every line; the stories live in the guardrails file. Three examples:

- **2026-05, a deploy that shipped nothing.** The frontend fixes of
  [#6961](https://github.com/MarkusNeusinger/anyplot/pull/6961) never reached anyplot.ai. An unrelated
  TypeScript error that had been left for later broke the next production build, while every check on
  the pull request was green. Since then an agent fixes a small build or test blocker on the spot, even
  when it's outside its task.
- **2026-10-22, a blank site.** A dependency bump passed every check and deployed, and every page of
  anyplot.ai rendered blank. I noticed about 45 minutes later. Since then the agent checks the live site
  after every merge, and CI runs the same check on the built image.
- **2026-10-30, a stall nobody reported.** A build agent stopped at midday while waiting for its own
  tests. A context summary called it "still working", and in the evening I was the one who asked
  whether anything was still running. Since then, about 30 minutes without a commit or a message counts
  as a suspected stall: the main session checks the agent's real state and reports it.

## An example: one click to the plot

[#12557](https://github.com/MarkusNeusinger/anyplot/pull/12557) on 2026-11-04, times in UTC:

| Time | What happened |
|---|---|
| 17:00 to 18:16 | A build agent commits the first version: one call to action at the end of the chat's message box, and the site's loader in the chat's waiting places. |
| 17:56 | Fable and Gemini 4 Argon review the build. |
| 19:54 | I tried it locally and rejected the loader's ochre dot. The commit: "a gray resting pair and a green runner, no ochre". |
| 20:16 | Testing further, I had clicked the filled `.confirm()` button expecting a plot. Nothing started; it needed a second click, and the outlined `.send()` beside it looked blocked. A redesign goes to Fable and Gemini 4 Argon; both answer "sound with changes". |
| 20:55 | The commit that makes `.create_plot()` confirm the data and start the plot in one click. |
| 21:15 | Gemini 3.8 Flash checks the whole diff and finds two low-severity issues; both are fixed at 21:25. |
| 21:29 | The pull request opens. Its test plan has a mutation table: 10 behaviors, each broken on purpose, each turning between 1 and 11 page tests red. |
| 21:36 | Copilot's review: no open issues. |
| 21:55 | I merge it. |
| 22:00 | The app and agent service deploys finish. |
| 22:01 | The site smoke passes: the API's health check, then `/`, `/plots`, and `/scatter-basic` with the new bundle. |

## Where it falls short

- **One prompt and waiting doesn't work yet.** Since the first commit on 2025-11-18, more than 950 pull
  requests from my account have merged, and up to 2026-11-04, 208 of those 351 days had a commit under
  my name.
- **Models make confident mistakes.** A reply described an axis value the plot didn't draw, a summary
  said an agent was working hours after it had stopped, and a green deploy left the site blank. So
  nothing counts as done because a model says it is: tests, reviews by other models, and my own testing
  check every claim.
