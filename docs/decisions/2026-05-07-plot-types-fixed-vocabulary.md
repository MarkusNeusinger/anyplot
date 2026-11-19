# Plot types are a fixed vocabulary, and the other tags are advisory

- Date: 2026-05-07
- Proposed: the spec polish could strip valid niche tags.
- Decided: in release 2.3.0 the tag policy became asymmetric: `plot_type` is canonical, and a new type
  comes by pull request; `data_type`, `domain` and `features` are advisory, and the polish only moves
  misclassified tags or merges synonyms. He confirmed it as his decision on 2026-11-19.
- Where: `CHANGELOG.md`
