### Changed

- **The `verify-api` skill says how to check the deployed agent chat through the admin lane.** A scripted
  check after a deploy calls `api.anyplot.ai/debug/agent` with production's admin token and the page's client
  header, confirms the data before the first plot, and sends feedback on a plot's version. The section names
  the two refusals a first try runs into (the local token, the missing header), so the next check starts with
  neither.
