# A pipeline in GitHub Actions writes every plot

- Date: 2025-11-24
- Proposed: plot requests arrive as GitHub issues.
- Decided: the pipeline runs in GitHub Actions with Claude: a spec is written from the issue, and each
  library's implementation is generated, reviewed by AI and merged. A new plot goes in only through
  the pipeline, as written into `CLAUDE.md` on 2025-12-30. At the 1.0.0 launch 13 workflows carried
  it. Today's README tells contributors: "You contribute ideas, not code: the pipeline writes every
  implementation." He confirmed it as his decision on 2026-11-19.
- Where: `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `.github/workflows/spec-create.yml`
