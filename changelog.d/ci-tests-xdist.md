### Changed

- **The backend test job runs on four workers.** "Tests / Run Tests" spent a
  median of 675 s on a PR, 94 % of it in one serial pytest process over 9,183
  tests. It now runs pytest-xdist with `-n 4 --dist worksteal`, one worker per
  CPU of the hosted runner, and coverage measures through `sys.monitoring`
  (`core = "sysmon"`) instead of the C tracer, which cost about 45 % on Python
  3.13. Pinned to four CPUs, the CI-equivalent run took 68.9 s instead of
  300.8 s, with the same 9,162 passed and 21 skipped tests and the same
  coverage total (10,723 statements, 92 %); the job should take about 165 to
  215 s. `--durations=25` lists the slowest tests, which the interleaved
  output of four workers no longer shows by timestamp, and the Cloud SQL proxy
  step polls its port every 0.2 s instead of sleeping 5 s. The turn-cap test
  of the agent stream tolerates about 0.5 s of slow start on a busy runner
  instead of 0.2 s, and the MonoLisa font download writes one `.part` file per
  process, so two workers that miss the cache at once no longer truncate each
  other's file.
