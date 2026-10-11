### Added

- **Quick feedback on an agent chat result stores the case for tuning.** Every
  result card has a feedback control: thumbs up, thumbs down, bug or idea (the
  site feedback's set), an optional text of at most 500 characters and
  `# include data.csv`, ticked by default for admins in phase 1. `.send()`
  never waits for a turn and never starts one; the card then shows
  `sent · v<n>`, and an edit stores a new case that replaces it. The BFF's new
  `POST /debug/agent/sessions/{sid}/feedback` fetches that version's bundle from
  the agents service, under the same admin gate, ownership and size cap as
  `.save()`, and writes it to the private bucket `AGENT_CASES_BUCKET`
  (`anyplot-agent-cases`) as `cases/<case_id>/`: the PNG of each rendered theme,
  `plot.py`, `data.csv` only with the box ticked, and `manifest.json` last. The
  manifest carries every column the planned `agent_feedback` table needs, so the
  table can be filled from the cases later. No upload replaces an object, and a
  failed upload answers `502 storage` and leaves no manifest, so a half-written
  case never counts. Analytics: `agent_result_feedback{reaction, include_data}`.
- **`agents.evals.import_case` turns a real session into an eval case.** It reads
  a bundle that `.save()` downloaded, or a stored case directory, and writes
  `case.json`, `data.csv` and, when the version came from a typed change,
  `change_request.txt` into the git-ignored `agents/evals/.cases/`, which the
  harness runs as promoted cases. It never writes into the committed fixtures,
  because a case holds a user's data.
