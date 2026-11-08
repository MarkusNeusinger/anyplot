### Fixed

- **The prep eval reads the version a turn starts from again.** It still called `resolve_version` with the session view that the server's version numbering removed, so every prep run and 11 unit tests failed on `main`. (#12823)
