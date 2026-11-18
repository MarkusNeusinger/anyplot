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
  same lines. It starts with five decisions of 2026-11-17 and 2026-11-18.
  (#13186)
