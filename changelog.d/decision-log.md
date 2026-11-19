### Added

- **A decision log.** `docs/decisions/` holds one small file per decision
  of the owner that someone asking how this project was shaped would look
  for. Each has the date, what was proposed, what he decided and why, and
  its source: the pull request, or the file that records it. The code here
  is written by AI agents; what he contributes is direction, standards and
  push-back, which no diff shows. A rule in `CLAUDE.md` has every agent add
  the file in the pull request that carries such a decision out and keeps
  the folder from flooding, and `tests/unit/test_decision_log.py` holds the
  form: a dated name, the four lines once and in order, and a source that
  exists. One file per decision keeps open pull requests from editing the
  same lines. It starts with 88 decisions from 2025-11-18 to 2026-11-18:
  those a public text names as his, and those he confirmed on 2026-11-19,
  each checked clause by clause against its sources by an independent
  reviewer. (#13186)

### Fixed

- **A rule credited to the owner that no source gave as his.** The AI
  workflow page's first example of his recorded decisions named a fail-closed
  rule of 2026-10-11; the design document's parenthesis behind it had moved
  when the sentence grew. Both now give the rule of that day, the data
  confirmed in a first step. (#13186)
- **The vision document's voice and the chat's inputs.** It no longer calls
  anyplot "AI-powered", which the style guide rules out, and it says that the
  chat reads dropped files as well as pasted text. (#13186)
- **A personal address in public files.** A test constant and an audit report
  held a real account address; they use a placeholder now. (#13186)
