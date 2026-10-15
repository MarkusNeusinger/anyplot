### Changed

- **Copilot instructions agree with CLAUDE.md.** `.github/copilot-instructions.md`
  now carries the "fix small build/test blockers directly, even when out of
  scope" rule (under ~20 lines, ask first above that) instead of telling Copilot
  to leave pre-existing failures alone, drops the `pip` fallback in favour of
  `uv` only (now stated in both guides), and lists new plot types as a
  `spec-request` issue rather than a hand-written implementation. The
  instruction tests pin both rules on both sides.
