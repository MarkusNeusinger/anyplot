### Fixed

- **Workflow label checks cannot lose a match to SIGPIPE.** The 15 checks of the form `echo "$LABELS" | grep -q`
  in impl-review, impl-merge, sync-labels, report-validate and spec-create now hand grep the labels as a
  here-string. Bash's `echo` writes a multi-line value one line per write, so `grep -q` could match, exit and
  leave `echo` to die on a closed pipe; under `pipefail`, the shell the workflow tests use, the check then read
  as false, and the verdict step failed now and then with "neither ai-approved nor ai-rejected". Live runs use
  `bash -e` and were unaffected. A test now refuses the pattern in every workflow file.
- **The regen gate's record and summary and the verdict step's scratch files live in `$RUNNER_TEMP`.** Under
  fixed `/tmp` paths, which every workflow test on a machine shares, a gate summary left by one test was posted
  by the next; each test now gets a `$RUNNER_TEMP` of its own. Files the reviewer reads stay in `/tmp`.
