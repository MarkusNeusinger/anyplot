### Changed

- **The agent chat shows a request id only where a report needs it.** An
  error line keeps its ` · ref <id>` for a fault of the server or the
  connection (a 5xx, no answer, a stream's error). A refusal (a 4xx), such
  as a binding the server refused, a paste the parser cannot read, or a
  limit, names its cause in the text and shows no id, which only puzzled
  visitors.
