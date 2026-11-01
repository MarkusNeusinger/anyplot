### Changed

- **Pipeline-only implementation PRs start no CI runs.** The five CI workflows
  skip a PR that changes only `plots/*/implementations/**` and
  `plots/*/metadata/**`: GitHub holds the runs of a PR that the pipeline opens
  with `GITHUB_TOKEN` for an approval that never comes, and they ended as a red
  `failure` at the merge without having checked anything.
