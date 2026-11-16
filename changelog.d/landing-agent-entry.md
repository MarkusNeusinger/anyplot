### Changed

- **The landing page names "Use with my data" in plain words, and `/agent`
  without a plot explains it.** While the chat's public lane is open, the
  hero's entry below `plots.browse()` reads `.use_my_data() →` over "an ai
  agent adapts a catalogue plot to your data" and leads to `/agent`, in place of the
  muted `# new: pick any plot, then .use_my_data()` line that led to `/plots`.
  `/agent` without a catalogue pair is now an explainer with a title of its
  own: the about page's description of the chat, three example pairs in
  Python, R, and JavaScript that open the chat, and the way on to the
  catalogue. It opens no session: a visitor's browser asks only the lane's
  door, which the API answers without the agents service. The hero's
  `mcp.connect()` link is gone, since the nav's `mcp` entry right above it
  leads to the same page. In Plausible, `nav_click{source: hero_use_my_data}`
  now targets `/agent`, the source `hero_mcp` ends, and `agent_open` gains
  the source `agent_intro` for the explainer's examples. Each chat opened
  there counts as one open, also after the visitor goes back to the
  explainer and picks another example.
