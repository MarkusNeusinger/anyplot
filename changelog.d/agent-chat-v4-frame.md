### Changed

- **The agent chat is one terminal-style window.** The chat at `/agent` and
  `/debug/agent` stands in one frame with the tab label `~/anyplot.ai/agent` on
  its top border, after the hero panel's construction, with dashed rules under
  the header row and above the composer. The opening, an ineligible pair and an
  error show in the same frame, and the admin fan-out's panel stays below it.
  This is the first slice of the approved v4 design.
- **The header row speaks in plain words.** The spec's title is the link back,
  without the arrow; the library chip reads `seaborn ▾` and the language chip
  names the reply language in its own words, `Deutsch ▾`. The library's
  language and how the reply language was set stay in the accessible names.
  The how-to ⓘ moved from the `# chat` label, which is gone, into the row.
- **One status line at the frame's foot names the step.** `>>> step 1 of 2 · …`
  replaces the step header above the chat and the step lines above the message
  box, and stays the plot button's description: what the button waits for, the
  plot that runs and its `.stop()`, what to check, or the confirmed data's
  shape. After a lost confirmation it reads `back to step 1 of 2 · …`.
- **The experimental notice is one muted line above the chat.** On the public
  lane it reads `// experimental AI · answers can be wrong ⓘ`, right-aligned on
  a wide screen, without the green rule, and stays in place while the session
  opens.
