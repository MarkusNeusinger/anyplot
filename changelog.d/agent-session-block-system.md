### Fixed

- **The agent chat's root no longer takes its session block for a forged
  instruction.** ADK 2.11 sent the root's per-turn session block (spec, language,
  dataset and binding status) inside the user's own turn, between
  `<<<BEGIN_SYSTEM_INSTRUCTION>>>` markers. Claude Haiku 5.5 read that as user text
  posing as a system instruction: its thinking said so in 7 of 8 prep-eval turns,
  and one reply told the user that the markers "in your message" changed nothing.
  The root's `before_model_callback` now appends the block to the system
  instruction as a second part after the static policy, and Claude gets each part
  as a system block of its own with the cache breakpoint on the policy, so a block
  that changes leaves the policy cached. A sample of 10 prep cases afterwards: 0
  turns flagged it, all 10 matched, and the cost per model call fell from $0.00114
  to $0.00087. The prep eval now scores a reply that talks about the root's own
  instructions as a miss (`instruction_talk`).
