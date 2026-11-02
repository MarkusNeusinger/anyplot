### Changed

- **The agent chat shows less text, with the details behind buttons.** The
  public experimental notice is one line, `# experimental AI · results can be
  wrong · stored only if you send feedback`, and its ⓘ button opens the rest
  (which AI and where, what not to paste, the daily limits, the legal page). A
  result card shows its image, toolbar and theme switch, while the rounds and
  the change list sit behind one status line and the code behind
  `.show_code()`, with `.copy()` and the downloads in view; each card keeps its
  choice for the session, and a new version starts folded. The quick feedback
  shows only the reactions until one is picked. On the admin lane `.save()`
  and its data box moved from the header row into a "⋯" menu, not into the
  feedback area, because a save downloads the session and stores nothing; the
  public lane has neither, since a visitor cannot resume a saved session and
  the feedback form covers what went wrong. The data card's
  header is `# your data ⓘ`, its how-to behind the button, and the long hint
  and the how-to paragraph under the card gave way to short placeholders.
  The chat column grows with the window up to 1360 px, so the data card,
  the plot images and the code use a wide screen, while the chat text keeps
  a readable line of about 80 characters. (#12540)
