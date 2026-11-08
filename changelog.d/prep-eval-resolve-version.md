### Fixed

- **The prep eval runs again.** Scoring a case by the version its turn starts from had failed on every run since the server began numbering data versions; the eval now looks the version up the way the agent does. (#12823)
