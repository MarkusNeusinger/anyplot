### Added

- **The agent chat has one session language, shown as a chip.** A `lang: en`
  chip in the chat header, next to the library pills, opens the ten common
  languages (en, de, fr, es, it, pt, nl, pl, zh, ja) and a field for any other
  language in Latin letters. The first in-scope typed message sets the language
  it is written in (`lang: de · detected`, with one quiet line in the thread),
  a later message never changes it, and a choice from the chip or a request
  such as "labels in English" (the root's new `set_language` tool,
  `PUT /v1/sessions/{sid}/language` and its BFF mirror) is kept for good
  (`chosen`). English stays the default, also for a German browser, so
  "sin x" gets an English plot; the browser locale is only recorded with a
  feedback case. The `done` event carries `language: {language, source}` so
  the chip follows the chat, and the feedback bundle carries the session's
  language and each version's.
- **An eval case and scope cases for the session language.** The hand-written
  case `scatter-basic-matplotlib-german-message` has German column names and a
  German follow-up with no word about the language, so its first plot is
  English and its second must carry German plot text; the full matrix now has
  123 cases. A case may name a `language`, which the harness chooses through
  the language route before the first turn, an imported feedback case carries
  its session's when that was detected or chosen, and every run records the
  last `done` event's language. Six in-scope scope-eval cases (`plot_language`,
  three English, three German) guard the rubric's new line that a request for
  the plot's own text in another language is no translation.

### Changed

- **Text in an agent plot follows the session language instead of always
  English.** The adapter writes the title, axis titles, legend entries and
  annotations in it, while column names and labels from the data keep their
  spelling; a change whose base version was written in another language
  rewrites them (`language_changed`, with the first adaptation's literal
  budget); and the reviewer judges the plot text against it under VQ-06,
  fail-open. Code, comments and the internal change notes stay English, and
  earlier versions keep their text. A chosen language is free text, so every
  prompt that carries it, the root's session block included, fences it as
  `<plot_language>`. The refusals sent before the scope judge runs follow the
  session language instead of the browser locale. Prompts changed: `root.md`,
  `adapter.md`, `reviewer.md` and `scope_judge.md`.
