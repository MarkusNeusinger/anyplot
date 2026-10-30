### Changed

- **Gemini reviews its own finished work before it hands over.** In the
  `gemini-task` skill, Gemini starts one fresh subagent as a reviewer once a
  task or a review round is done. The reviewer sees only Acceptance and the
  diff, reads the whole diff for defects, and runs the mutation table plus
  breaks of its own. Gemini fixes the findings that hold up and lists every
  finding in a new `## Self-review` section of the PR body, as fixed or
  declined. Claude's independent Opus review stays, because a reviewer of
  the same model shares the author's blind spots. The owner's reason: code
  quality comes before saving tokens. (#12476)
