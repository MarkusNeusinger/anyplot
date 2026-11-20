### Fixed

- **After a paste that replaced data, the chat answers from the new table and
  still knows what was said.** In the chat of "Use with my data", the turn that
  summarizes a second table no longer shows the assistant what it read or
  changed in the first table, nor its thinking about it. Every message of the
  visitor and every reply stays, and a fixed line marks where the new paste
  came in. Before, the note "Convert the column day to dates." sent with a
  table whose `day` held text got the answer that the column already held
  dates, taken from the first table. A visitor who adjusts the data and says
  "try again" is still understood.
