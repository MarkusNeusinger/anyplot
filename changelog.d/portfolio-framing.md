### Added

- **The README says who builds anyplot and how.** A "How I build anyplot" section on its first screen
  says who leads the models and how. "Engineering highlights" names seven decisions, each with its
  reason and a link to the code that carries it out. An "Architecture" section draws the services and
  the pipeline as two Mermaid diagrams. Before this, the README described the system in passive voice
  and never said what the human behind it does. (#12559)
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
