### Changed

- **Gemini tasks as brief files instead of issues.** Claude now hands work to
  Gemini in the owner's agy session as a read-only brief in
  `~/projects/anyplot-briefs/`, outside both checkouts; a `gemini`-labelled
  issue is written only when the owner asks for one. The owner starts a task
  with `agy-work` (a shell function the `gemini-task` skill documents) and
  `/gemini-task <slug>`. Large work is cut into packages of at most 20 to 25
  files, each in a fresh session with mechanical convention checks in its
  Acceptance. Claude reviews against the brief, never against Gemini's PR
  text.

### Security

- **Gemini reads only the owner's issue comments.** The `gemini-task` skill
  fed every comment on a `gemini` issue to Gemini, while it already filtered
  PR comments to the owner's; on a public repository anyone can comment, so
  issue comments are now filtered the same way.
