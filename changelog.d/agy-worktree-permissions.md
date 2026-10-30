### Fixed

- **Gemini's parallel package agents can write in their worktrees.** agy
  creates each subagent's Git worktree under
  `~/.gemini/antigravity-cli/worktrees/`, and the agy permission rules denied
  Gemini's file tools the whole `~/.gemini` folder, so the first parallel run
  fell back to one package after another. `agy-permissions.json` now denies
  each entry of `~/.gemini` and `~/.gemini/antigravity-cli` by name, keeps the
  agy login and settings closed, and leaves only `worktrees/` open, with
  `regex:` rules for `cd` and `git -C` into it that refuse `..`. The three
  push deny rules also match when agy compares a whole command against them.
  (#12467)
