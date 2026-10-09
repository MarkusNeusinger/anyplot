### Added

- **Adaptable catalogue code design document.** `docs/concepts/adaptable-code.md`
  describes how catalogue implementations become code that people who copy it
  from the code tab, and the planned "Use with my data" agent, can point at
  other data: one `# Data` block ending in a tidy `df`, domain-named column
  constants with a role comment, a static checker plus a perturbation smoke run
  in impl-generate, the regen gate's adapt route and adapt regression, and a
  rollout through the normal daily regeneration. It records the owner's
  decisions of 2026-10-09 (score-neutral first, all 15 libraries, no targeted
  pass) so the rules PR is reviewable before anything is built. (#12108)
