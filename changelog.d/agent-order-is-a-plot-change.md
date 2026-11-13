### Fixed

- **"Sort biggest first" reorders the plot, not the table.** In the chat of
  "Use with my data", a wish for an order of the bars or categories was
  carried out as a sort of the user's table: a new data version, and a
  second tap on the plot button before the plot showed it. The assistant's
  rules named ordering a change of the plot in one place and `sort` a change
  of the data in another. An order is now a change of the plot, and the
  table keeps its rows as pasted; so is a figure shown with the plot, such
  as a total in the title or the sum of each category in the legend, which
  the plot code computes from the data. A sort of the table stays for a
  user who names the table or its rows, for a top N, and for the calendar
  order of months and dates. The prep eval scores where such a wish went
  (`plot_request`), with ten cases for it and two that name the table.
