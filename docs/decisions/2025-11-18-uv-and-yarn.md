# uv for Python and yarn for the frontend

- Date: 2025-11-18
- Proposed: pip and npm, which the rules name as the tools not to use.
- Decided: Python tooling is `uv` only, `uv sync` and `uv run`, never pip, and the frontend uses
  yarn. uv was there from the first setup on 2025-11-18, and yarn came with the frontend on
  2025-11-19; the rule "uv only, never pip" was written down on 2026-10-15, the rule for yarn on
  2026-02-09. He confirmed it as his decision on 2026-11-19.
- Where: #12188, `CLAUDE.md`, `app/package.json`
