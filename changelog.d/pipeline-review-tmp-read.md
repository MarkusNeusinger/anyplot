### Fixed

- **A regeneration's review can read the predecessor's files.** The review
  re-scores the live implementation from files that `impl-review.yml` puts
  under `/tmp`, and the permission rule meant to allow that read,
  `Read(/tmp/*)`, never covered them: a path with one leading slash is
  anchored at the settings source (the project, or the directory of a file
  passed with `--settings`), not at the filesystem root. The rule is now
  `Read(//tmp/*)`, in `.claude/settings.json` and in the retest's settings.
  With the old form the read was refused. Most reviews found another way to
  the files. One that treated them as missing wrote no before/after file, and
  the gate kept the live implementation with `regen_json_missing`: 4 of the
  58 gated regenerations from 2026-11-10 to 2026-11-17 (#13036 to #13159).
  Every session that loads `.claude/settings.json` gets the rule: the Claude
  steps of `impl-generate`, `impl-repair`, `spec-create`, `daily-regen`,
  `util-claude`, and `report-validate`, and local sessions, now read files
  directly under `/tmp` without asking. (#13160)
- **The files that carry the stored score stay out of `/tmp`.** With a
  working rule, three files there would have put the stored score one read
  away from a review that scores blind: the copy of main's metadata, the
  predecessor's source before its header is cleaned (left behind when the
  cleaning fails), and the PR's JSON, whose body records the previous quality.
  All three now stay under `$RUNNER_TEMP`, and the retest removes its metadata
  copy once the context is built. This isn't a boundary: the session can
  still run Bash and `gh`, and the previous review it's handed can quote a
  score in its own wording. (#13160)

### Added

- **A review's log names the tool calls it was refused.** The new step "Name
  the denied tool calls" in `impl-review.yml` prints `claude_denials … count=N`
  and one warning per refused call, with the tool and, for a file tool, its
  path. Until now the log gave the count alone. (#13160)

### Changed

- **The retest's harness version is 2.** A regen cell's session now reads the
  predecessor's files with the Read tool and no longer finds the predecessor's
  metadata beside them. A resume doesn't reuse a cell recorded on version 1,
  and a comparison with a version 1 arm is flagged "harness changed": record
  the baseline again before you compare. (#13160)
