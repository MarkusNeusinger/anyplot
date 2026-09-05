### Added

- **`.claude/guardrails.md`, the long version of the working rules.** `CLAUDE.md`
  is loaded into every session and pays its cost on every turn, so it states each
  rule as one line; the incident that produced a rule, the recipe it implies and
  the numbers that make it credible now live in a companion file that is read
  only when someone hits the situation. Three sections to start with: the two
  lines every delegate brief has to spell out, the pattern for a prod runbook the
  harness classifier refuses (one script in the scratchpad, one `! bash` line for
  the owner, rollback as its own script, a read-back from the session afterwards),
  and why a one-token substitution is not an exemption from the Edit/Write rule.
  `tests/unit/test_agent_instructions.py` pins the split: every section maps to a
  binding one-liner in `CLAUDE.md`, and the companion file has to say that
  `CLAUDE.md` outranks it.

### Changed

- **The Edit/Write rule now says what it outranks.** Auto mode hands a delegated
  agent a reminder that prescribes editing files with `sed`, heredocs and short
  scripts, and it arrives later in the context than `CLAUDE.md`, so it reads as
  the more recent instruction — three agents in the sibling repository followed
  it in one day, two of them for the single-token substitution that fills a PR
  number into a changelog fragment. `CLAUDE.md` now states the precedence
  explicitly, and the delegation rule adds the second line a brief has to carry:
  all `git` stays inside the agent's own worktree, because a `git checkout -b` in
  the shared checkout moves a ref the owner's working tree is sitting on.
- **`/open-pr` knows what "ready to merge" means since the review ruleset
  changed.** `review_on_push` is `false` in the "Automated Copilot Code Review"
  ruleset since 2026-09-03, so a fix push starts no Copilot run and the absence
  of a `copilot-*` check on the new head SHA is normal, not a reason to keep
  waiting — the skill's gotcha still claimed the opposite. The merge-on-request
  conditions are now written down: non-Copilot checks completed and green
  (deduped by name, newest wins, so a superseded run is not read as red), a
  Copilot review that actually exists on the PR — the head check run only says
  whether a round is still running, since a run reaches `completed` with
  conclusion `cancelled` and delivers nothing — and zero unresolved threads.
  `mergeable=UNKNOWN` is GitHub still computing; a conflict (`CONFLICTING`,
  `mergeStateStatus` `DIRTY`) gets no CI at all and is reported, not waited out.
  Merging stays the owner's call.
- **Commit-message and PR-body files are named after the branch.** The scratchpad
  is shared by every agent of one session, so a generic `commitmsg.txt` or
  `prbody.md` gets overwritten by a parallel agent and a later re-read commits
  someone else's text. `/open-pr` now derives the name from the branch and says
  the part that makes it safe: write and consume the file in the same step — it
  is scratch input to one command, not a record.
- **A numeric UI rule is verified against the measured result.**
  `/verify-frontend` gains § 3b: a floor, a minimum size or a cap is read off the
  element in the browser, never off the code that computed it. The case is a
  14 px x-height floor whose planner sized lines from an average advance — the
  plan met the floor and the rendered page came out at 13.9 px, because the
  frame's own padding was never in the budget.
- **Shortening a text that carries claims is now a checklist.** `/write-docs`
  gains the claim-by-claim diff duty: shortening drops qualifiers before it drops
  sentences, which is how a privacy section lost an overstated retention period,
  a condition on the right to object and part of a list of rights inside an
  otherwise good edit. The owner's own sentences stay verbatim, and a claim that
  cannot be supported is removed rather than softened.
