### Fixed

- **Measurement curves bind their time to x, never a per-curve value.** Three
  curves pasted as JSON records with list fields put `temperatur_c` (one value
  per curve) on x of a line chart. The profile now names, for a number column
  with one value per group of records, that group (`constant_within`), and on a
  spec with an x axis such parameters and the id that numbers the groups rank
  like weak measures; after the years, x prefers a column named like an
  independent variable (`zeit_s`, `Frequency (Hz)`). A bar chart may still show
  the per-curve value.
- **One register per language in the chat.** A German summary said "Aus Ihren
  Notizen" where every other text said "du". The root now keeps the informal
  address the fixed refusals use (du, tu, tú, je), and a unit test checks the
  fixed texts for the formal words of German, French, Spanish and Dutch.
- **The data line never nests quotes.** A converted workbook's source reads
  `Museen_2025.xlsx · sheet ‹Übersicht›`, so the data panel shows
  `from "Museen_2025.xlsx · sheet ‹Übersicht›"` instead of quotes inside quotes.
- **Month names state their whole range.** A summary called Jan to Jun "Jan bis
  Mai" because the profile lists only five top values. The profile now carries
  the months of a text column of month names (`months`), the root names the
  range from it, and `sort` orders such a column by the calendar instead of the
  alphabet.
