### Fixed

- **The renderer's replay tests wait for the join instead of guessing its time.** The page test gave the first build
  a fixed 50 ms to start and never waited for the replay to join it. A page is not kept for replays, so on a loaded
  machine a late replay built the page a second time and the test failed. Both replay tests, the page's and the
  render's, now wait until the build runs and the service logs the replay's join of the build in flight.
