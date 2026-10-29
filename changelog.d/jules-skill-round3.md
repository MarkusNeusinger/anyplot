### Changed

- **Jules lane after three test rounds.** The `jules-task` skill now limits
  Jules to mechanically verifiable work (codemods, migrations, tests, lint
  fixes) and sends behaviour-preserving refactors to `/gemini-task`, after
  three of nine page-split variants kept their page unchanged. It cuts
  Claude's share: one low-noise watch per round (`watch-sessions.py` gains
  `--changes-only` and `--allow`, which flags scratch files outside the named
  paths), prompts that forbid asking for confirmation and string-sliced code
  edits, a budget for stuck sessions, and a REST fallback for messages. It
  records how to prove unchanged behaviour (a jsdom snapshot with the existing
  test's mocks, a browser comparison against the production API) and that a
  branch cut before a CI change keeps its old workflow triggers. (#12453)
