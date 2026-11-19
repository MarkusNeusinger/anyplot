### Changed

- **CI's test job runs the JavaScript render tests.** "Run Tests" now sets up Node, the lock's `node_modules` and Chromium with the `setup-node` action and sets `ANYPLOT_REQUIRE_JS_RUNTIME=1`, so a missing piece fails the tests instead of skipping them, as `ANYPLOT_REQUIRE_LIBRARIES` does for the plotting libraries. Before, 121 tests skipped there, so the render harness, its sandbox limits and the page a visitor downloads were tested only on a developer's machine.
