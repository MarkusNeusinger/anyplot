# A plot draws every row it is given, and which rows it shows is the plot's own view

- Date: 2026-11-08
- Proposed: the plot code was allowed to derive sorting, grouping, pivots and statistics itself. In
  a persona round, a line chart of 27 measurements over 9 lengths came out as 9 averaged points, and
  a weekly series lost a week, while the confirmed data held every row.
- Decided: the plot draws every row it gets, and a change of the rows goes only through the data
  step, where it is counted and can be undone. When the prompt rule alone did not stop the code from
  averaging a repeated key, he decided on 2026-11-09 that the server guards that case in code. On
  2026-11-13 he moved selections to the plot: which rows it shows, a top N included, is a view of the
  plot, adjusted like axis limits after a look at the picture, and the order of its bars, categories
  or legend entries is the plot's too. The table stays as pasted, and cleaning stays a step of the
  table. That rule is written by meaning and names no word of any language, and the eval checks it
  with French cases, a language the rules hold no example of.
- Where: #12824, #12953, #13083, #13089, `docs/concepts/agent-network.md`
