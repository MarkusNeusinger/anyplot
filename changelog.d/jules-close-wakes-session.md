### Changed

- **Stop a Jules session before closing its PR.** The `jules-task` skill now
  tells the session to stop before Claude closes a losing or duplicate PR:
  closing a PR wakes its session, and on 2026-10-29 one pushed a new commit
  and recreated its deleted branch. (#12438)
