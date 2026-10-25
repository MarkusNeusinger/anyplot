### Added

- **The agent network's runtime seam for every catalogue language.** The renderer
  holds one fixed render command per language in `agents/renderer/commands.py`,
  keyed by the job's `(language, library)` and never taken from the request; the
  probe harness gains an exec mode (`harness.py --exec -- <command>`) that runs a
  non-Python command under the same limits, start and end lines, launcher retry and
  kill path; `GET /status` reports the toolchains the image carries and a job in a
  language without one answers `503 runtime_unavailable`. On the agents side a
  registry (`agents/anyplot/render/runtimes/runtime_for`) hands the pipeline, the
  theme toggle, the local backend and the eval harness one `RuntimeAdapter` per
  library, which now also carries the language's code conventions, error grammar,
  export and the render time a repair reserves; the exported code's artifact name
  follows the language (`plot.py`, `plot.R`, `plot.jl`, `plot.js`, `plot.tsx`)
  through the wire, the BFF, the feedback case and the result card. matplotlib and
  seaborn behave as before; the table's other rows wait for their toolchains.
- **Phase-2 plan for "Use with my data" in all 15 libraries.**
  `agentic/specs/261024-agent-all-libraries.md` takes the agent network from
  matplotlib and seaborn to the other 13 catalogue libraries: a runtime registry
  in place of the hard-wired Python runtime, one fixed render command per language
  in the renderer, a harness exec mode for Node, Rscript and julia, the toolchains
  in the renderer image, a deterministic code profile per language, and seven PRs in
  order (the seam, plotnine and altair, pygal and lets-plot, R, JavaScript, plotly
  and bokeh, Julia). It records the spike measurements (the JS harness, the Python
  extras under the probe harness, plotly and bokeh, R and Julia in local Docker), the
  Fable second opinion and the owner questions with their defaults. (#12404)
