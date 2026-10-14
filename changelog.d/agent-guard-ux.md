### Added

- **A request for the plot in another library gets a pointer, not a strike
  toward closing.** The scope judge has a new verdict, `other_library` ("this
  plot in Chart.js, give me the code"): a fixed answer in 11 languages says the
  chat adapts matplotlib and seaborn and points to the plot's catalogue page,
  which has it in up to 15 libraries. By default it never counts toward
  closing the session (`AGENT_OTHER_LIBRARY_COUNTS`); a live test had refused
  it as the third out-of-scope request and closed the session unwarned
  (#12180).
- **A warning before a chat closes.** The counted refusal one before the
  closing one ends with a fixed sentence in the message's language ("One more
  request outside this scope will close this chat.",
  `AGENT_SESSION_CLOSE_WARNING`) (#12180).
- **Paste limits.** The data panel's paste route now has its own per-user
  limits (`AGENT_USER_PASTES_PER_MINUTE` 10, `AGENT_USER_PASTES_PER_DAY` 100;
  only a paste that reaches the checks counts), one paste per user at a time,
  none while the user's turn runs in any session, and none in a closed session
  (`403 session_closed`). Each paste spends dataset-judge, notes-judge and
  maybe transcriber calls, and was bounded only by the daily token budget
  (#12180).

### Fixed

- **Data code that reads a URL is a data request, not an attack.** The scope
  judge classed `pd.read_csv(urlopen("https://…"))` as `attack`, a strike
  toward the day's lockout; it is now `needs_data` with the hint to paste the
  table, and `attack` is kept for code that reaches the system, its
  environment or secrets, or sends data out (#12180).
- **A question about the table's own figures is no data request.** The judge
  never sees the pasted table, so "Welches Jahr hat den grössten
  Ausländeranteil?" read as a statistics lookup and was refused `needs_data`;
  a question that picks, ranks, compares or summarises entries now counts as
  being about the table, in any language and without "my data" (#12180).
- **The strike lockout says what it is.** Three `attack` verdicts in a day now
  answer with their own `locked_out` refusal ("paused until tomorrow after
  several refused requests") instead of the `budget` text "usage limit
  reached", and the paste route answers `429 locked_out` or `429 daily_limit`
  instead of a `rate_limited` whose text read "daily limit reached" (#12180).
