# The plot pipeline's pull requests merge themselves once green

- Date: 2026-05-07
- Proposed: the pipeline's polish and implementation pull requests, each waiting for a merge.
- Decided: in release 2.3.0 they began to squash-merge themselves once their checks are green, with
  auto-merge set when they open. He confirmed it as his decision on 2026-11-19.
- Where: `CHANGELOG.md`
