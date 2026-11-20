### Changed

- **The generating and the repairing session check their own Python file with
  the agent chat's validator before they commit.** Until now the readiness
  scan ran only after the session, so a regeneration that added a construct
  the chat refuses was found out when the tokens were spent: the gate kept the
  live file (`readiness_regression`, 2 of about 22 Python regenerations), and
  of 5 predecessors the chat refused only 2 came out accepted. A new step,
  "Prepare the readiness self-check", copies the validator from the
  workflow's ref to `/tmp/anyplot-readiness` before the session in
  `impl-generate.yml` and `impl-repair.yml`. The session runs
  `readiness_scan.py check` on its file and gets every refusal in the
  validator's own words, with its hint and with the line of its own file.
  Inside the existing three attempts of the adaptability self-check it removes
  every refusal it can without making the plot worse, keeps the ones the spec
  needs (a WebGL trace for a 3D plot), and names the verdict in a
  `Readiness self-check:` line of the commit body. The check decides nothing:
  the record-only scan still makes its own copy after the session and never
  reads the session's, and the regen gate stays the only thing that decides.
  `line_map` moves from `core/smoke_run.py` to `core/utils.py`, so the check
  maps the validator's lines without the smoke runner.
