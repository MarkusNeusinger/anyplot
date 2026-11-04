### Changed

- **`CHANGELOG.md` opens with its format line, not the process.** The thirty lines on fragments,
  the release cut, the GitHub release and the exempt classes moved into `changelog.d/README.md`,
  rule for rule, under task headings; the changelog keeps the format, the versioning line and a
  link there.

### Fixed

- **The docs describe the agent chat and the catalogue as they are.** The agent network design,
  `agents/README.md`, the docs index, the app architecture and the project guide now say the chat
  is public and experimental at `/agent` since 2026-11-02 for all 15 libraries, with the admin
  tools at `/debug/agent`. The style guide names four languages, the current page color and
  border alpha with recomputed contrast ratios, the curated catalogue next to the chat, and the
  seven mobile nav items; the API and repository references show the current response and metadata
  shapes, and per-library metadata lives under `metadata/{language}/`.
- **The deploy-agents trigger filter and the Vite pin are documented as they run.** The header of
  `agents/cloudbuild.yaml` gives the trigger's ignore list that lets prompt-only changes deploy and
  the export and import route for changing it, and the Dependabot ignore for `vite` names the
  8.3.5 pin, the outage of #12225 and its fix in #12235.
