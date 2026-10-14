### Changed

- **Pasted data sets the chat's language.** When you paste data into "Use with
  my data" before typing anything, the session language follows the notes
  around the table, or else the column names, with the new source `pasted`
  (`lang: de · from data` in the chat header). The two judges that already
  screen a paste name the language, so no model call is added; English or
  unclear notes and headers such as `temperature_2m_max` leave the current
  language unchanged. A typed message still replaces it,
  and a paste never overrides a typed or chosen language. The dataset route
  answers the session language as `language: {language, source}`. (#12171)

### Fixed

- **No false refusal right after a refusal.** The scope judge saw the previous
  fixed refusal as the assistant's last turn, so after a German weather question
  was refused, the next message, a question about the user's own data, was
  refused as `needs_data` too. The judge now sees the last reply a model wrote,
  never a fixed refusal, and its rubric says that a question about your own
  data ("which day was the warmest?") is in scope. A withheld message's
  placeholder now names its verdict (`[message withheld by scope policy:
  needs_data]`), so "do it anyway" after a data refusal gets the data refusal
  again. Ten scope eval cases reproduce the sequences in German and English.
  (#12171)
