### Changed

- **Gemini test tasks prove what their tests catch.** The `gemini-task` skill
  has a brief for tests name the files where the behavior lives and carry a
  mutation table in Acceptance: one deliberate break per behavior that must
  turn a test red, and one harmless refactor that must stay green. The review
  subagent runs the table and adds breaks of its own. Larger findings go back
  as a review round, one PR comment with a section per package, which Gemini
  works in parallel on `gemini/<slug>-r<n>-<k>` branches from the task branch
  and merges back. In the first parallel run, the section tests passed every
  gate while two of three packages tested copies of the page logic instead of
  the pages. Cleanup now asks before deleting package branches, as
  `CLAUDE.md` requires.
