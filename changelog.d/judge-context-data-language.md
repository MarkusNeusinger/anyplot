### Changed

- **Pasted data sets the chat's language.** When you paste data into "Use with
  my data" before typing anything, the session language follows the notes
  around the table, or else the column names, with the new source `pasted`
  (`lang: de · from data` in the chat header). The two judges that already
  screen a paste name the language, so no model call is added; unclear headers
  such as `temperature_2m_max` keep English. A typed message still replaces it,
  and a paste never overrides a typed or chosen language. The dataset route
  answers the session language as `language: {language, source}`. (#12171)

### Fixed

- **No false refusal right after a refusal.** The scope judge saw the previous
  fixed refusal as the assistant's last turn, so after a German weather question
  was refused, the next message, a question about the user's own data, was
  refused as `needs_data` too. The judge now sees the last reply a model wrote,
  never a fixed refusal, and its rubric says that a question about your own
  data ("which day was the warmest?") is in scope. Eight scope eval cases
  reproduce the sequence in German and English. (#12171)
