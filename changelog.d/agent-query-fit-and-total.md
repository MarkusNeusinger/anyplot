### Added

- **A question gets a grand total and a straight-line fit from the server.**
  In the chat of "Use with my data", a question about the data can now total,
  average or count every row in one step, and fit a straight line to two
  number columns by least squares: the answer is one row with the slope, the
  intercept, r squared and the number of rows, at full precision, which a
  formula in the same question can use. What a figure leaves out is
  counted: for a fit, the rows that lack either value; for a total, the
  empty cells of each column. Before, a total took two steps and a fit had
  no operation at all, so the chat worked such figures out itself and
  could state them wrong. Both stay questions: a change of the data never
  totals your table without a key or fits a line to it. (#13141)
