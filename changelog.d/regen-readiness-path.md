### Changed

- **A regeneration that the agent chat can now serve replaces the live plot.** The regen gate
  counts it as an improvement when the chat's validator refused the predecessor and accepts the
  new file, even if the picture stays the same; the score tolerance, the criterion floor and the
  regression rule still apply. The review no longer credits a Python class as library mastery,
  since the code-quality rule deducts it and the chat refuses it. In the batch of 2026-11-27 the
  gate kept two pygal files whose class removal would have made them usable in the chat.
