# An axis that lost its column waits for the user instead of being filled

- Date: 2026-11-18
- Proposed: after a change of the data removed the column a plot axis was bound to, the assistant
  added a column nobody had asked for (the timestamps as days since the first date, or the row
  numbers) and put it on the chart. The options were a guard in code on the result, the same guard
  with dates offered before row numbers, only giving the assistant the facts, or the server adding a
  days column itself every time.
- Decided: the guard in code. Nothing made in such a turn lands on the axis by itself: the table keeps
  what was asked for, the reply names the axis that lost its column, the plot waits, and the next
  turn lists what the server can compute. He chose the option without a note; the reason given with
  it was the agents': code decides, so it holds for every model and language, and it keeps his
  earlier rule that turning dates into numbers is an offer.
- Where: #13198, #13757 (the same guard after a date column is refused on an axis that takes numbers)
