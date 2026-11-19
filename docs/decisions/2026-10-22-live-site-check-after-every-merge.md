# After every merge, a browser checks that the live site renders

- Date: 2026-10-22
- Proposed: a dependency bump passed every check and its deploy, and every page of anyplot.ai
  rendered blank for about 45 minutes. Nothing in CI or in the routine after a merge ran the app's
  JavaScript.
- Decided: he asked for a rule so that a blank site never goes unnoticed again. After every merge,
  once its deploys finish, a browser check runs against production, and a failure stops further
  merges; CI runs the same check on the built app image when its inputs change.
- Where: #12236, `scripts/site-smoke.mjs`, `.claude/guardrails.md`
