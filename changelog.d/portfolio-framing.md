### Added

- **The README says who builds anyplot and how.** A "How I build anyplot" section on its first screen
  says who leads the models and how. "Engineering highlights" names seven decisions, each with its
  reason and a link to the code that carries it out. An "Architecture" section draws the services and
  the pipeline as two Mermaid diagrams. Before this, the README described the system in passive voice
  and never said what the human behind it does. (#12559)
- **A showcase image in the README, drawn from live data, and a test that keeps the README honest.**
  `scripts/readme_showcase.py` lays out one spec per library from the `_800` light previews. Its
  counts come from `/stats` and the library registry, and its type is MonoLisa with the script
  italic; the script stops rather than fall back to another font. It replaces the ridgeline preview
  card and links to `/plots`. `tests/unit/test_readme_claims.py` reads each value the highlights, the
  architecture and the About page state from its source and fails when the text no longer matches:
  the rubric's criteria and points, the review bar and its step, the pipeline's bounds, the session
  idle time, the default model, the library count and the MCP tools. It also checks every relative
  link and in-page anchor. The pull-request count is now a floor ("more than 850"). The release
  procedure redraws the image and raises the floor, and `/write-docs` lists the duty. (#12559)
- **A docs page on how anyplot is built with AI agents.** `docs/concepts/ai-workflow.md` covers who does
  what, the path of a change from idea to production, how a repeated mistake becomes a rule or a test,
  a worked example (#12557), and the limits of the approach. The README links it for the full story.
  (#12559)
- **The About page explains the review, the agent chat, and the MCP server.** One short section each,
  linked to `/stats`, `/plots`, and `/mcp`, mirrored in the bot HTML of `/about` so crawlers read the
  same text. (#12559)
- **`.use_my_data()` on the landing page's plot of the day.** It sits beside `github.open()` in the
  card's header and opens the chat for that plot's spec and library. It shows only when the eligibility
  check names a lane, with one request per view, and the chat records `agent_open{source:
  plot_of_the_day}`. (#12559)
