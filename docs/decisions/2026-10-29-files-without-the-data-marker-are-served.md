# The chat serves catalogue files without the data marker, in every language

- Date: 2026-10-29
- Proposed: before R, Julia and JavaScript were served, the plan had their fixture specs
  regenerated with a `# Data` block, because the readiness scan blocked a file without the marker.
- Decided: in every language a file without the marker is `coupled`, never `blocked`: the adapter
  rewrites its data creation, and no language waits for regenerations. For ggplot2 that left 15 of
  325 files blocked, for other reasons.
- Where: #12443, `agentic/specs/261024-agent-all-libraries.md`
