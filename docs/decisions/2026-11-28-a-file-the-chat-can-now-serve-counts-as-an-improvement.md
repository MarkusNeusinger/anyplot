# A file the chat can now serve counts as an improvement

- Date: 2026-11-28
- Proposed: in the regeneration batch of 2026-11-27, four repair follow-ups removed a pygal
  subclass, which CQ-01 deducts and the agent chat's validator refuses, and the regen gate kept
  all four. Two of the keeps rested on a visible loss. The other two did not: on one the picture
  stayed the same, so the class removal counted as no visible improvement; on the other the
  re-score had credited the class itself as library mastery (LM-02), so removing it fell below
  the criterion floor. 21 live pygal files still define a class. Three ways were offered: fix the
  rule and then regenerate those files on purpose, regenerate them with a change request alone,
  or leave them for the second chance at the end of the catalogue pass. In the same round he kept
  the criterion floor of 2026-11-25 as it is.
- Decided: fix the rule, then regenerate the 21 files on purpose. A regeneration that the
  validator accepts where it refused the predecessor counts as an improvement even when the
  picture stays the same, and the score tolerance, the criterion floor and the regression rule
  still apply to it. A Python class earns no library-mastery credit, in the re-score of the live
  file as in the review of the new one.
- Where: #15152
