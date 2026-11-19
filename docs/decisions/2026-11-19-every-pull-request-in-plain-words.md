# Every pull request opens with a short section in plain words

- Date: 2026-11-19
- Proposed: pull request descriptions written for a reviewer only: what changed, the plan and the
  test plan, in the terms of the code.
- Decided: every pull request, whatever it changes, gets a section in plain words, only as long as
  it needs to be, written so that someone who is not deep in the technology sees quickly what the
  pull request is for: the idea, how it is solved, and an example where one fits. The technical part
  stays as it is. His reason: he merges every ordinary pull request himself, and from its description
  he could not tell what the largest open pull request actually did; if the opening does not make
  the point of a change clear, the technical part after it does not either, and it shows whether the
  whole pull request makes sense as it was meant. He asked for a second opinion on the section's
  form, which Fable and Gemini 4 Carbon gave, and for the rule to go into the instructions agents
  follow when they write a pull request.
- Where: `agentic/commands/pull_request.md`
