### Changed

- **Every pull request opens with a short section in plain words.** The
  `/pull_request` command, its body template, Gemini's hand-over template and
  `.github/pull_request_template.md` put `## In plain words` before
  `## Summary`, for every kind of change: as few sentences as the change
  allows, 150 words at most, for a reader who does not know the code, on what
  was wrong or missing and for whom, what happens now and how it is solved,
  then a fixed line on who would notice what, and where. A reader must be able
  to tell from it alone what the change is for, and an author who cannot say
  that plainly looks at the change again before writing around it. The section
  says what the merge hangs on, claims no more than the technical sections
  back and names no file or setting. The owner merges every ordinary pull request himself, and
  the technical sections stay for the reviewer. `/open-pr` checks the section,
  the title and the fragment against the final diff before a pull request is
  reported ready, and the Gemini take-over checks the section again after its
  review, since Gemini writes it before the review rounds. Catalogue-only,
  pipeline and Dependabot pull requests are exempt.
