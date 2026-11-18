# Every quality review runs on Opus, though it scores lower

- Date: 2026-09-28
- Proposed: the review model followed the generation routing, so a regeneration, generated on
  Sonnet, was also reviewed on Sonnet.
- Decided: every review the pipeline starts runs on Opus; generation stays as it was. The pull
  request measured what the switch costs: on 14 plots both models scored under the same rules, Opus
  averaged 77.5 and Sonnet 85.7, so a regeneration merged afterwards usually stores a lower score
  than the one it replaces.
- Where: #11968
