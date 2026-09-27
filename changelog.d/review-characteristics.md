### Changed

- **The AI review judges each plot against its own plot type.** Specs gain a
  closing `## What a good version looks like` section with 3-6 observable
  properties of a good render, including "expected, not a defect" items;
  spec-create writes it for new specs, spec polish never touches it, and eight
  central specs (bubble, scatter, line, bar, violin, two heatmaps, force-directed
  network) are seeded by hand. The quality criteria and the review prompt score
  against it and add three soft rules from the bubble-basic regen experiment:
  marks sit at their data values (post-hoc displacement deducts SC-03), legend
  glyphs must be visible in both themes (VQ-03), and extra encodings on a
  `-basic` spec count as the wrong variant (SC-01). Regenerations now address
  only the weaknesses that are real per that section, answer overlap with data,
  marker size or alpha instead of moving marks, and keep their data scenario.
  (#11946)
