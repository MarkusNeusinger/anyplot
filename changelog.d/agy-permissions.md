### Changed

- **agy runs the gates without asking.** The `gemini-task` skill's one-time
  setup now lists the permission rules for the owner's agy settings: the
  gates (`yarn`, `uv run`), local Git, and GitHub reads run without a prompt,
  `git push` and opening the draft PR still ask once per hand-over, and
  `gcloud`, force pushes, pushes to `main`, and writes to the brief folder
  are denied.
