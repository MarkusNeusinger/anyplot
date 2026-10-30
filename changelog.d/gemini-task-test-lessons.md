### Changed

- **Gemini test tasks prove what their tests catch.** In the `gemini-task`
  skill, a test brief names the files where the behavior lives and carries a
  mutation table in Acceptance: one deliberate break per behavior that must
  turn a test red, and one harmless refactor that must stay green. The review
  subagent runs the table and adds breaks of its own. Larger findings go back
  as a review round, one PR comment with a section per package; Gemini works
  the independent ones in parallel on `gemini/<slug>-r<n>-<k>` branches from
  the task branch and merges them back. In the first parallel run, the section tests passed every
  gate while two of three packages tested copies of the page logic instead of
  the pages. Cleanup now asks before deleting package branches, as
  `CLAUDE.md` requires. (#12474)
