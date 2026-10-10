### Added

- **`AGENT_MAX_ATTEMPTS` bounds the agent pipeline's adapter attempts.** The
  plot pipeline makes 1 to 3 attempts, 2 by default, so the design's "at most
  one repair round" stays what the service runs. The eval harness takes
  `--max-attempts` and records the effective value in the report's stamp, so a
  run can measure what a second repair round buys, or what the first attempt
  achieves without one. Every attempt after the first needs the repair's 75 s
  of the soft deadline and allows a full file, and feedback goes to the next
  attempt before any review while one is left. `PlotResult.attempts` now
  accepts 3, and the report counts a pass from any repair attempt as repaired.
