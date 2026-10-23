### Fixed

- **The stuck-launcher executor test no longer fails on a slow CI runner.** The fake
  launcher execs the harness, so the process the test keeps alive carried the job's
  one-second `RLIMIT_CPU`; when the harness start spent that second, the kernel killed
  the "stuck" launcher inside the grace window and `stuck` read 0. The test now gives
  the run the host's full CPU cap, which a real `sandbox do` outside the sandbox always
  has, and asserts that limit on the survivor, so it fails every time without the fix
  (#12260).
