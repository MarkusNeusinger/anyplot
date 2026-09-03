### Changed

- **The agent instructions say what the Copilot review ruleset now does: one review per PR, not
  one per push** — review-on-push was turned off in the "Automated Copilot Code Review" ruleset of
  both repositories on 2026-09-03, so the bot runs once when a PR opens or leaves draft and a push
  triggers nothing. `CLAUDE.md`'s PR follow-through and `agentic/commands/pull_request.md` now say
  so, and say not to re-request one per push: each request is a full re-read of the whole diff, and
  the bot then surfaces "previously missed" findings in files the push never touched — which draws
  another push, and another request (the sibling repo's
  [kurrentschrift#406](https://github.com/MarkusNeusinger/kurrentschrift/pull/406) collected ~15 in
  a day over a one-line docstring fix). A fresh review is requested only after a substantive
  rework, and a PR that is green with no open threads needs no further round. (#11216)
