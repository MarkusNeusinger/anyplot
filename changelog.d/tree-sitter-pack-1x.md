### Changed

- **The agents' tree-sitter grammars are baked into the image, and the service
  never downloads one.** tree-sitter-language-pack moves from 0.13.0 to 1.24.0,
  whose wheel ships no grammars and whose `get_language` downloads a 23 MB bundle
  on first use. `agents/Dockerfile` now fetches the bundle at build time and keeps
  the four grammars the code profiles read (6.2 MB) in a root-owned directory. The
  service loads them through the pack's `LanguageRegistry`, which never downloads,
  and stops at its start when one is missing. A checkout and CI fetch them once
  with `uv run python -m tools.tree_sitter_grammars`. (#12943)
