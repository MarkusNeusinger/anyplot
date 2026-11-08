### Changed

- **The agent chat stays English until you pick another language.** A message
  or a paste in another language no longer switches the replies and the plot:
  the chat offers that language once, in one line,
  `# German detected in your message · .switch()` (or `in your data`), and
  ignoring the line keeps everything English. `.switch()` sets the replies and
  the plot labels (`PUT /language` with `via: offer`); with a plot on screen
  the next version comes in the new language, and after the switch the chat may
  offer English back once. A pick in the header's language menu, or a request
  in the chat such as "auf Deutsch bitte", ends the offers. The fixed refusals
  use the session language now, never the message's, and the reply-language
  check asks again when the assistant answers an English session in the
  language it offered. The page is English, so a visitor who never asked for
  German should not get German replies; the offer replaces the
  `# reply language: de` notice, which repeated for every paste and first
  message. Plausible counts the offers and the picks as
  `agent_language{via: shown|offer|header}`. (#12865)
