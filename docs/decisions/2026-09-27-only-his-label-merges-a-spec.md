# A new spec merges only on his approval, and only his label counts

- Date: 2026-09-27
- Proposed: an AI agent drafts a spec from an issue and opens it as a pull request, and the merge job
  ran on an `approved` label from any account.
- Decided: in his words, "I approve new specs" (about page) and "I approve it on the issue" (README).
  Since September 2026 the merge job ignores the label from any other account: it runs only when the
  repository owner adds `approved`.
- Where: #11868, `.github/workflows/spec-create.yml`, `app/src/pages/AboutPage.tsx`, `README.md`
