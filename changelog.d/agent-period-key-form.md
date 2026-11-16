### Fixed

- **A date range on a month key no longer drops the first month.** In the
  chat of "Use with my data", a sum or mean by month, quarter or year writes
  its key as text labels such as `2024-01`, which compare as text, so a range
  from `2024-01-01` on such a key left January out without an error. A
  condition with a value of another date or period shape on such labels is
  now refused with the labels' form and an example, so the assistant can give
  the bound again in that form. A column of four-digit codes kept as text
  compares as before. (#13140)
- **The data lines name the form of a period key and the lowest and highest
  value that stayed.** The line of a sum or mean by month, quarter or year
  says that the key is now text labels and in which form
  (`month, as text labels YYYY-MM`), as the line of a week says each week is
  its Monday. The line of "keep only the rows where" names the lowest and the
  highest kept value of each tested column of dates or period labels, so a
  selection that starts a month late shows in the result. The two values say
  nothing about the values between them. (#13140)
