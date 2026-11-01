### Fixed

- **A follow-up message no longer changes the plot's language.** In the live
  test of 2026-11-01 a German paste gave a German plot, and the English
  follow-up "Use a log scale on y" translated its title and number format while
  the axes and months from the data stayed German; "Make the title German"
  turned the assistant's replies German too. The plot's text now has its own
  language (`session_state.plot_language`): the language the user asked for the
  plot, else the language of the session's latest plot, else the session
  language. So the first plot follows the paste, the first typed message or the
  chip as before, and later versions keep it. The root's `set_language` takes
  `applies_to` (`plot`, `replies` or `both`, the default for a request that
  names no target), the chip sets both and now says it names the replies'
  language, and the admin fan-out copies the page's plot language. (#12504)
