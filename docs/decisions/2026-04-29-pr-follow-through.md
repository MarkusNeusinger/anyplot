# A pull request is followed until it is green and review-clean

- Date: 2026-04-29
- Proposed: "PR opened" counted as done, which left CI red or review feedback unaddressed.
- Decided: in release 2.2.0 the follow-through was written into `CLAUDE.md`: after opening a pull
  request, an agent stays with it until the pipeline is green and the review feedback is addressed,
  and only then calls it ready. He confirmed it as his decision on 2026-11-19.
- Where: #5553, `CLAUDE.md`, `CHANGELOG.md`
