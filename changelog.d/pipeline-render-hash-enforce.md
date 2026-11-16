### Changed

- **A review no longer scores renders that were made from other code.** When
  the staged `render.sha256` doesn't match the implementation at the PR head,
  `impl-review.yml` stops before the review: nothing is scored and no header
  is committed. A first generation, and a forced or adopted regeneration, gets
  the label `ai-render-mismatch` and stays open until the pair is generated
  again; its review run ends as failed, and the watchdog skips the PR and
  reports it. A gated regeneration is kept by the regen gate with the new code
  `render_mismatch`, a returning keep. A hash that is missing or couldn't be
  read still only warns. (#13122)
- **`render.sha256` holds a second hash, of the code without its header.** The
  review's own header commit rewrites the whole generated header, so a manual
  re-review used to read a mismatch although no line of code had changed. The
  code hash leaves out exactly the block the header writer replaces, in all
  four languages, ignores the score like the first hash does, and keeps a
  JavaScript file's `//#` directives, which the render harness reads. A file
  staged before this change has one hash only; a mismatch against it keeps
  warning. (#13122)
