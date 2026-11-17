### Fixed

- **A regeneration's review can read the predecessor's files.** The review
  re-scores the live implementation from files that `impl-review.yml` puts
  under `/tmp`, and the permission rule meant to allow that read,
  `Read(/tmp/*)`, never covered them: a path with one leading slash is
  anchored at the project. The rule is now `Read(//tmp/*)`, in
  `.claude/settings.json` and in the retest's settings. With the old form the
  read was refused. A review that found no other way wrote no before/after
  file, and the gate kept the live implementation with `regen_json_missing`:
  4 of 54 gated regenerations from 2026-11-10 to 2026-11-17. Local sessions
  read the same file, so they now read files directly under `/tmp` without
  asking.
- **The stored score stays out of the reviewer's reach.** The copy of main's
  metadata that the regen context is built from holds the stored score and sat
  beside the files the reviewer reads. It now stays under `$RUNNER_TEMP`, and
  the retest removes its copy once the context is built.

### Added

- **A review's log names the tool calls it was refused.** The new step "Name
  the denied tool calls" in `impl-review.yml` prints `claude_denials … count=N`
  and one warning per refused call, with the tool and, for a file tool, the
  path. The refused reads above were visible only as a count in the session's
  raw output.
