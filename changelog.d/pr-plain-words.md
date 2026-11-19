### Changed

- **Every pull request opens with a short section in plain words.** The
  `/pull_request` command, its body template, Gemini's hand-over template and
  `.github/pull_request_template.md` put `## In plain words` before
  `## Summary`: at most 150 words for a reader who does not know the code, on
  what a person ran into before, what happens now and how it is solved, then a
  fixed line on who would notice what, and where. The section says what the
  merge hangs on, claims no more than the technical sections back and names no
  file or setting. The owner merges every ordinary pull request himself, and
  the technical sections stay for the reviewer. `/open-pr` checks the section,
  the title and the fragment against the final diff before a pull request is
  reported ready, and the Gemini take-over checks the section again after its
  review, since Gemini writes it before the review rounds. Catalogue-only,
  pipeline and Dependabot pull requests are exempt.
