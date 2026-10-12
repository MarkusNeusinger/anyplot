### Added

- **Roles that cannot be negative never get a negative column by default.** A radius,
  a size, a count, a standard deviation, a weight, and the value of a pie, donut,
  treemap, sunburst, icicle, waffle, marimekko, sankey, rose or basic funnel need
  values of 0 or more (`agents/anyplot/data/signs.py`): the default bindings pass
  over a column with a negative value, and a binding of one by hand stays valid but
  is warned about in the session block, the `set_bindings` result, the bindings
  route's new `warnings` and under the page's dropdown. Signed plots such as
  waterfall or diverging bars keep their signed `value`. The fixtures are the owner's
  cases of 2026-10-12: a sine as a polar radius, and a signed `y` given to `std`.
