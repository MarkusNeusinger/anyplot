# A plot draws every row, and a change of rows goes through the data step

- Date: 2026-11-08
- Proposed: the plot code was allowed to derive sorting, grouping, pivots and statistics itself. In
  a persona round, a line chart of 27 measurements over 9 lengths came out as 9 averaged points, and
  a weekly series lost a week, while the confirmed data held every row.
- Decided: the plot draws every row it gets, and a change of the rows goes only through the data
  step, where it is counted and can be undone. When the prompt rule alone did not stop the code from
  averaging a repeated key, he decided on 2026-11-09 that the server guards that case in code.
- Where: #12824, #12953, `docs/concepts/agent-network.md`
