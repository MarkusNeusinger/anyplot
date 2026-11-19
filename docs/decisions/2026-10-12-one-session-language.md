# The chat speaks one language per session, English unless the user picks another

- Date: 2026-10-12
- Proposed: the chat reads messages and pastes in any language, and a browser may be set to another
  language than the site's.
- Decided: one session language for the replies and the first plot's texts, English by default like
  the whole site, also when the browser is set to another language. On 2026-11-01 he set that a plot
  keeps its text's language after a follow-up in another language. On 2026-11-08 he ended detection:
  the page is English, so everything stays English until the user picks another language, and a
  message or a paste in another language only makes the page offer it once, with a button.
- Where: #12145, #12504, #12865, `docs/concepts/agent-network.md`
