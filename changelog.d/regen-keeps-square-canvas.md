### Fixed

- **A regeneration puts an equal-aspect plot on the square canvas.** Old
  matplotlib files often drew a Venn diagram or an equal-axes plot on a
  landscape figure and let a tight crop cut the empty sides away. The
  generator drops that crop, as the library rules require, but kept the
  landscape figure, so three regenerations shrank the plot to the middle of
  the canvas with empty bands at both sides, and two of them merged as
  judged worse. The orientation now follows what the plot draws: a plot with
  a 1:1 aspect takes the square canvas, and the square list names Venn
  diagrams, circle packing, polar charts and equal-axes plots. (#13474)
