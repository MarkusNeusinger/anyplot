### Fixed

- **When you say your dates are month first, the chat re-reads them.** In
  the chat of "Use with my data", a pasted date column such as `03/04/2024`
  whose every day is at most 12 reads both ways, and the paste reads it day
  first. When you then say the dates are month first, the chat now re-reads
  the column that way instead of saying that it already is. The assistant
  never saw the paste's note about that guess, only the dates as ISO dates
  (`2024-04-03`). Now the column's profile says which order its cells were
  read in, and the field changes when the column is re-read.
