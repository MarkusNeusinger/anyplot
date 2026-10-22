### Changed

- **Adaptable-code rollout revised after a second opinion.** The design in
  `docs/concepts/adaptable-code.md` now merges a conversion on render identity
  (both sources rendered in the same runner, under 0.5 % of pixels differing
  per theme) instead of a one-point score tolerance, converts the catalogue
  through a capped targeted pass over matplotlib and seaborn instead of one
  spec a night across 15 libraries, drops the first-generation repair trigger
  that collided with the early `ai-approved` label, keeps the Opus review for
  the first 50 identical conversions, and removes the nullable-dtype
  perturbation and the `fill_value=0` pivot that invented zero bars. The
  reasons are recorded next to the owner's decisions of 2026-10-23, so the
  document stays the single source for PR 2.
