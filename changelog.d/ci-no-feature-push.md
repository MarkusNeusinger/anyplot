### Security

- **No CI on pushes to `feature/**`.** Google Jules names its own branch after
  the feature branch it starts from (`feature/<slug>-<session id>`), and a
  push run has no PR author, so the checks keyed on the PR author treated
  unread Jules code as trusted: the first such push gave `renderer-image` its
  GCP login before the run was cancelled. `ci-lint`, `ci-tests`,
  `ci-migrations`, and `ci-image` no longer run on pushes to `feature/**`;
  feature branches get CI through their pull requests. `Run E2E Tests` and
  `renderer-image` also refuse any `feature/` ref at job level, and the e2e
  job any PR into a feature branch. (#12441)
