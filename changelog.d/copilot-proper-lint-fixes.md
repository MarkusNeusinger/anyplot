### Changed

- **Copilot gets the "proper lint fixes only" rule.** The lint task line in
  `.github/copilot-instructions.md` now says to fix the cause and never add
  disable comments (`eslint-disable`, `noqa`, and similar) without the owner's
  explicit approval, matching `CLAUDE.md`; the instruction tests pin the rule on
  both sides.
