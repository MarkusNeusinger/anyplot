# The check that found a bad merge becomes a script and a rule for every agent

- Date: 2026-11-18
- Proposed: an agent had resolved a merge conflict by taking one side's whole file, which dropped
  three passages of a doc without any check failing. It wrote a private script to audit its merges
  and a note for itself.
- Decided: the script goes into the repository with a rule in the agents' instructions, so it holds
  for every session and every model, not for the one that made the mistake.
- Where: #13176
