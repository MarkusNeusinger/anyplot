### Changed

- **Review weaknesses are defects or suggestions, and only a defect carries a
  regeneration.** Each weakness either names the criterion it violates, the
  render and the observed value, or starts with `Suggestion:`; both are stored,
  so the website and the next regeneration see the class. The regen gate
  replaces a live implementation only when a visible improvement fixes a
  visual, spec, data or code defect that scores higher than in the
  predecessor's re-score, or an `A good version shows:` property; design and
  library-mastery points, storytelling layers and taste changes ride along but
  never carry a merge alone. Generation and repair act on defects and decline
  suggestions. (#11967)
- **One unasked layer on a `-basic` spec is already variant creep.** The SC-01
  rule and its mirrors in the review, generation and repair prompts name
  reference lines, highlights and callouts, and one such addition is enough;
  the review no longer suggests adding one. (#11967)

### Fixed

- **Weaknesses the spec now permits no longer count as regen improvements.**
  When the review re-scores the predecessor, it marks an older weakness that an
  `Expected, not a defect:` bullet covers as obsolete, with that bullet's id;
  the gate never counts it and the generator declines it. (#11967)
- **Regenerations of 16 implementations with an older review no longer keep
  on a context error.** Their stored checklists carry scalar keys such as
  `total_score` next to the six categories, which made the previous-review
  extraction raise; it now skips them. (#11967)
