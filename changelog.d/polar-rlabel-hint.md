### Added

- **A repair moves a polar plot's radial labels to a measured free direction.** The
  render probe now describes each polar axes (the radial labels' angle and a
  histogram of the plotted points by angle and radius), and when the labels sit on
  the data the next repair attempt gets the measured target, such as "at 67.5° they
  sit on 10 plotted points → ax.set_rlabel_position(270), 0 points there", instead
  of guessing an angle. The line never starts a repair on its own.
