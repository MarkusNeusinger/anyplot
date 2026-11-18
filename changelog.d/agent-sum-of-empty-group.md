### Fixed

- **A total of a group with no values is empty, not 0.** In the agent chat,
  a sum per group returned 0 for a group whose cells were all empty, as if
  its values had added up to nothing. That 0 stood in the answer to a
  question, in the stored data of a data step and in a chart that sums
  repeated keys, beside the zeros a table really held. A group with no
  value now has no total, as it already had no mean, minimum or first
  value, for whole numbers and decimals alike; a count of it stays 0, and a
  total over rows that all lack the value is empty too. The step's line now
  says what it left out for a grouped figure as well, per value column: the
  rows without a value and the groups left empty, for example `summed units
  by shop: 3 rows, 1 group without a value in units left empty, 3 rows
  without a value in units left out`. Until now only a figure over all rows
  counted the rows it skipped. Data versions already stored keep their 0.
  (#13180)
