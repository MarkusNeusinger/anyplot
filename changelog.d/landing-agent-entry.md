### Changed

- **The landing page names "Use with my data" in plain words, and `/agent`
  without a plot explains it.** While the chat's public lane is open, the
  hero's entry below `plots.browse()` reads `.use_my_data() →` over "an ai
  agent adapts a catalogue plot to your data" and leads to `/agent`, in place
  of the muted `# new: pick any plot, then .use_my_data()` line that led to
  `/plots`. Until the lane answers, the entry's box stands there invisible, so
  the answer moves neither the plot of the day nor anything below it; only a
  closed lane removes the box. `/agent` without a catalogue pair is now an
  explainer: the about page's description of the chat, three example pairs in
  Python, R, and JavaScript that open the chat, and the way on to the
  catalogue, under a title, a description, and a link preview (`og:title`,
  `og:description`) of its own. It opens no session: of the agent routes, a
  visitor's browser asks only the lane's door, which the API answers without
  the agents service.
  In Plausible, `nav_click{source: hero_use_my_data}` now targets `/agent`,
  and `agent_open` gains the source `agent_intro` for the explainer's
  examples. Each chat opened there counts as one open, also after the visitor
  goes back to the explainer and picks another example. A unit test checks
  that each example names an implementation under `plots/`, and CI now also
  runs the Python tests on a pull request that changes only `AgentIntro.tsx`.

### Fixed

- **The back button asks before it leaves a chat for the explainer.** The
  chat's leave warning compared only the path, so going back from a chat with
  data or a plot to `/agent` without a plot, or to another chat, ended the
  session without asking. It now asks for any move away from the chat's
  catalogue plot, as a link off the page always did; a library switch inside
  the chat still passes without a prompt.
