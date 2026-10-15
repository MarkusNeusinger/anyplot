### Changed

- **The plot of the day features standout plots and rotates without repeats.**
  It used to be a random pick among every implementation scored 90 or more, so
  a plain chart such as a Pygal precision-recall curve could take the front
  page. It now draws from a featured pool (score 92 or more, no `-basic` spec,
  falling back to every 90+ implementation when the pool is empty), walks the
  pool's specs in an order shuffled per cycle so no spec repeats within a
  cycle, and picks the library per day among that spec's featured
  implementations.
