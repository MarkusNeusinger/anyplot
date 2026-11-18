# Catalogue code is written so the chat can adapt it, in every library, without a rubric change

- Date: 2026-10-09
- Proposed: catalogue implementations typed their data by hand. The design's example repeats the
  column names as literals, selects a highlight with a fixed value and types twelve month labels.
- Decided: a convention in all 15 library prompts, with column constants named for the domain and a
  comment naming each one's spec role, and one source of rules for the generator and the chat's
  adapter. It starts score-neutral: a flag and a self-check, never a 25th criterion. On 2026-10-23,
  after a second opinion found that the plan's score tolerance could not protect a good chart, he set
  the conversion: it merges on render identity, through a capped pass over matplotlib and seaborn,
  under stop rules, and he looks at five pair artifacts a week; two vetoes in a week halt the pass.
- Where: #12108, #12261, `docs/concepts/adaptable-code.md`
