### Added

- **The "Use with my data" chat page, for admins.** `/debug/agent?spec=&library=&language=`
  (`app/src/pages/AgentChatPage.tsx`) talks to the agent chat BFF: paste up to
  200 KB of CSV, TSV, semicolon CSV or JSON, check the 20-row preview, the
  parser's warnings and a column dropdown for every spec role (the server's
  defaults preselected, a series family such as `y1, y2, ...` one dropdown per
  member plus one for the next), then `.create_plot()` and refine in plain
  words. A progress timeline follows the stream's `status` events, a small
  counter in the chat's corner shows the place in the run queue, `.stop()`
  calls the cancel route and waits for the server to end the run, the library
  pills switch the session's library, and refusals and errors show their code
  and request id. The page starts nothing the server would refuse while a
  turn, a theme render, a parse or a binding change is in flight, deletes its
  server session on a reload or a closed tab, and reloads once when an
  expired Cloudflare Access session leaves a request without an answer. It is
  built only with `VITE_ENABLE_AGENT_CHAT=true` (off in `app/cloudbuild.yaml`,
  where the route answers the 404 page and the chunk is not in the bundle) and
  opens only for local development or an admin's browser.
- **A result card per plot version.** `app/src/sections/agent-chat/ResultCard.tsx`
  shows the rendered plot from its blob URL with the plot page's overlay
  actions (copy the PNG to the clipboard, with a download where the browser
  cannot, download it, open it full size), a light and dark switch that
  renders the other theme through the theme toggle route without a model call,
  the adapted `plot.py` with syntax highlighting and one-click copy, downloads
  of `plot.py` and `data.csv` under the names the code reads, what changed,
  the residual notes, a refine composer and a slot for the quick-feedback
  control. Earlier versions stay in the thread, collapsed.
- **A `.adapt()` button on the plot page.** The fourth overlay button of the
  implementation view opens the chat page for that spec and library with a
  full navigation, so Cloudflare Access can intercept it. It shows only when
  the build has the chat, the browser is in local development or carries the
  admin hint that the debug page now sets after a successful `/debug/status`,
  and the BFF's eligibility route accepts the pair, so a public visitor never
  sends a request to the debug API.
- **Analytics for the agent chat, with enum properties only.** The pageview
  `/debug/agent` and the events `agent_open`, `agent_data_parsed`,
  `agent_plot_rendered` and `agent_guardrail_block`, plus `copy_code` with
  `page: agent_chat`; none of them carries message text or data.
- **A local mock of the agent chat BFF.** `node app/scripts/agent-bff-mock.mjs`
  serves the documented `/debug/agent/*` routes on the loopback interface, a
  scripted `anyplot/1` stream (queue positions, the pipeline steps, a plot, a
  reply) and PNGs drawn from the pasted data, plus the catalogue routes the
  plot page needs for `scatter-basic` and `line-multi`, so the whole flow runs
  in a browser without the API, the agents service, a model or the production
  database.

### Changed

- **The `plot` event carries its version number.** The agents service stores
  an `ok` or `needs_attention` result as the session's next version and sends
  that number as `version`, which the BFF now passes on; a client addresses
  the artifact and theme toggle routes by it instead of counting plot events,
  which showed another version's files when an event got lost.
- **The dataset answer lists the spec's data roles.** `POST
  /debug/agent/sessions/{sid}/dataset` now returns `roles`, each
  `{name, kinds, required, variadic, description}`, so a client can offer a
  column choice for every role, and a refused binding set (`422 invalid`)
  keeps the binding check's lines (at most 20) instead of only the code.
