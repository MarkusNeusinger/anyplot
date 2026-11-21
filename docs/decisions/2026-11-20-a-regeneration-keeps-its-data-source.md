# A regeneration loads no built-in dataset its predecessor did not load

- Date: 2026-11-20
- Proposed: The generator prompt prefers built-in datasets (`sklearn.datasets`, `sns.load_dataset`) for real patterns, while the chat's validator refuses files that load them. In the regeneration run of 2026-11-20, one session brought such a loader into a file that had none, and the gate kept the old picture although the new one scored higher. The options were this small rule now with the larger question left to the chat stream, inline example data in every file, a chat that accepts built-in datasets, or no change.
- Decided: The small rule now: a regeneration keeps the previous file's data source and introduces no built-in dataset, and a dataset the previous file already loads stays. Whether the chat should accept such files is left to the chat stream.
- Where: `prompts/workflow-prompts/impl-generate-claude.md`
