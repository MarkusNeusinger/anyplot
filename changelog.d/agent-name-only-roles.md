### Changed

- **The adaptability checker reads the roles the plot computes.** `COMPUTED_ROLES` and `mark_computed` moved
  from the agent to `core/spec_roles.py`, and `spec_context` applies them, so the checker, its workflow mirror
  and the smoke run no longer ask for column constants of the 27 roles of 13 specs that the agent already
  treats as computed, such as the Bollinger bands and the moving averages. `CHECKER_VERSION` is 2, so a
  record says which reading produced it (#12612).
- **The EMA chart accepts both pairs its spec names.** `EMA 50` and `EMA 200`, the golden cross of the spec's
  first application, bind without a window warning beside the example's 12 and 26, and the adapter's brief
  names the window it computes an open EMA with: 26 by default, 200 beside a bound `EMA 50` (#12612).
- **A changed `specification.md` runs the unit tests.** The role audit reads every spec's Data bullets, and a
  spec PR used to skip pytest, which left a failure to the next Python PR (#12612).

### Fixed

- **Prices no longer bind as a MACD line or an RSI, and raw measurements no longer as control-chart
  summaries.** A new name-only role class binds `macd`, `rsi` and the sample means, ranges, limits and
  center line of `spc-xbar-r` only to a column whose name holds them (`MACD_12_26_9`, `RSI 14`, `X-bar`,
  `UCL`), in the default bindings, in the bindings filled after a data change and in the columns a
  conversion makes. Before, a price table drew its opening prices as the MACD line or as an RSI on a 0 to
  100 axis, and `Sample, X1, ..., X5` drew the first measurement as the sample mean and the next ones as
  the range and the limits, each with complete bindings and no warning. Now the role stays missing and the
  page asks for its column (#12612).
