### Changed

- **Merged branches are cleaned up locally too.** GitHub deletes a PR's
  remote branch on merge, but never the local copy, and 212 merged local
  branches had piled up by 2026-10-22. After a merge, Claude now removes the
  PR's worktree and local branch without asking (`CLAUDE.md`, the `open-pr`
  and `gemini-task` skills); unmerged branches still need the owner's OK.
