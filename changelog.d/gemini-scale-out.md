### Changed

- **Gemini works independent packages in parallel.** When a brief task has
  two or more packages marked `independent`, the `gemini-task` skill has
  Gemini in the owner's agy session start one agy subagent per package, at
  most four at a time, each in its own Git worktree on its own
  `gemini/<slug>-<k>` branch, pushing and opening its draft PR before it ends;
  coupled packages still run one after another. One start line,
  `/gemini-task <slug>`, covers every package. `/teamwork` is ruled out for
  this repository because it builds outside it, without branches or PRs. The
  agy permission rules gain the `git -C <clone>` forms, and the repository no
  longer calls a 2026-10-16 forum reply a Google staff reply.
