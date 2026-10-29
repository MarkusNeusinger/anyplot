### Changed

- **agy works without a prompt for every command.** The `gemini-task` skill
  ships `agy-permissions.json`, the permission rules for the owner's agy
  settings, with a one-line merge for a new machine: the toolchains, file
  tools, local Git, pushes to `gemini/*` branches, GitHub reads, and Gemini's
  own draft PR run without asking; cloud CLIs, network downloads, history
  rewrites, other GitHub writes, `chmod`, and writes to the brief folder are
  denied.
