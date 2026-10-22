### Changed

- **Gemini tasks after the first pilot.** The `gemini-task` skill now reads
  issues with `gh issue view --json` and updates PR bodies through `gh api`,
  because both bare commands fail on this repository; asks issue authors for
  cases where the existing rules must still win and for the files the gates
  couple; names the environment sync with the `agents` extra; and has Gemini
  hand over in the repository's PR format. The changelog check names a
  fragment that is on disk but not yet committed.
