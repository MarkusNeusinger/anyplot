### Added

- **Phase-2 plan for "Use with my data" in all 15 libraries.**
  `agentic/specs/261024-agent-all-libraries.md` takes the agent network from
  matplotlib and seaborn to the other 13 catalogue libraries: a runtime registry
  in place of the hard-wired Python runtime, one fixed render command per language
  in the renderer, a harness exec mode for Node, Rscript and julia, the toolchains
  in the renderer image, a deterministic code profile per language, and five PRs in
  order (foundation plus the four no-browser Python libraries, JavaScript, plotly
  and bokeh, R, Julia). It records the first spike measurements (the JS harness and
  the Python extras under the probe harness) and the owner questions with their
  defaults.
