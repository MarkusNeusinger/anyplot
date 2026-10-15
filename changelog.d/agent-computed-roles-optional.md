### Changed

- **Computed roles take a column when the data has one.** A role the plot can
  compute, such as the rolling average of `line-timeseries-rolling`, the
  Bollinger bands of `indicator-bollinger` and the fitness, fatigue and form
  of `line-training-load-pmc`, is now optional. The default bindings bind it to
  a column whose name clearly holds it (`SMA 20`, `BBU_20_2.0`, `Fitness (CTL)`),
  never one a required role needs or whose name says it is something else
  (`Upper Shadow`, `Volume SMA`), and warn when its window differs from the
  spec's (`SMA 200`),
  you can bind any column by hand, and the data panel shows
  `— computed by the plot —` while it is open. The adapter learns per role
  whether to use the bound column or compute the value from the data. (#12195)
