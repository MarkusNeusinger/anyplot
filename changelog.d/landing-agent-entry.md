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
  catalogue, under a title, a description, and an `og:title` and
  `og:description` of its own. Below the way on, the assistant's terms of use
  stand in three quiet labelled lines, `status`, `limits`, and `your code`,
  and a fourth, `privacy`, links to the legal page's section on what the
  assistant stores. The same four lines stand under the "closed right now"
  notice while the public lane is closed, so the terms stand at `/agent`
  also while the operator has paused the assistant. It opens no session:
  of the agent routes, a visitor's browser asks only the lane's door, which
  the API answers without the agents service. The site's feedback button
  stands on the explainer: the layout, which hid it on all of `/agent`, now
  hides it only where the query names a catalogue pair, by the rule the page
  uses to pick the chat, and the closed notice shows it there itself, since
  no chat is open.
  In Plausible, `nav_click{source: hero_use_my_data}` now targets `/agent`,
  and `agent_open` gains the source `agent_intro` for the explainer's
  examples. Each chat opened there counts as one open, also after the visitor
  goes back to the explainer and picks another example. A unit test checks
  that each example names an implementation under `plots/`, and CI now also
  runs the Python tests on a pull request that changes only `AgentIntro.tsx`.

### Fixed

- **A crawler or an AI assistant that follows a link to `/agent` reads the
  page, not a 404.** `llms.txt` links the address, but nginx sends a
  recognised crawler to `/seo-proxy/agent`, which had no route and fell into
  the spec route as an unknown spec. The API now serves a copy of the
  explainer there, `noindex` as the page is: the title, the description, the
  example pairs, and the terms of use word for word, which a test pins to
  `AgentIntro.tsx`. The machine-read log names the page `agent_page` instead
  of a spec hub for a spec called `agent`.
- **The back button asks before it leaves a chat for the explainer.** The
  chat's leave warning compared only the path, so going back from a chat with
  data or a plot to `/agent` without a plot, or to another chat, ended the
  session without asking. It now asks for any move away from the chat's
  catalogue plot, as a link off the page always did; a library switch inside
  the chat still passes without a prompt.
