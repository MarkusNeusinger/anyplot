# A regeneration replaces the live version only when it wins a side-by-side review

- Date: 2026-09-27
- Proposed: a regeneration went through the ordinary review and repair loop. In a five-round
  experiment on one spec, 39 of 75 regenerations failed their first review and merged after repairs
  at the lowered bar, replacing better versions (93 → 88); the review never saw the predecessor.
- Decided: recorded on 2026-09-27: a regeneration gets one review and no repair loop, and that review
  scores the live version again beside the new one. As the README states the gate in his words today,
  the new version replaces the live one only with no regression, a score at most a point lower, and a
  fix the review can verify; his rule: "a regeneration never makes an implementation worse." On
  2026-11-14 he added a keep for a regeneration the chat's validator would newly refuse; the pull
  request that built it counted 3 of 24 regenerations with such a regression over four nights, two of
  them merged.
- Where: #11945, #11967, #13113, `README.md`
