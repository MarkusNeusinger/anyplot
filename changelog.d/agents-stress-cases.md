### Added

- **Stress cases and a model-free static stage for the agent eval harness.**
  `agents/evals/make_stress.py` writes 23 seeded cases (`stress-*`): data
  exactly at and one past the parser's caps, 100 bars and 30 pie slices,
  degenerate data, prompt injection in a header, row 4 and a long cell, and
  requests that make the code compute mass data. Each case names the bound
  that must stop it. `python -m agents.evals.matrix --cases stress --static`
  runs every step before and around the models (parse, eligibility, bindings,
  the loader, prompt sizes, where injected text lands, and renders of
  hand-written stand-ins for the adapter's answer) without spending a token,
  and exits 1 when a bound did not hold. `--cases full` leaves the stress
  cases out, so a full run and its baseline keep their 122 cases. (#12125)

### Changed

- **The agent pipeline bounds what the stress cases showed unbounded.** The
  adapter request carries the dataset profile trimmed to 16 KiB (47 text
  columns of long values made it 27,907 characters); the new advisory gate
  G9 reports plots that draw more than 200,000 points, which a
  1,000,000-step Lorenz request reached in 2.0 s of CPU at a 479 MiB peak, far
  under the sandbox limits (10,000,000 steps peak at 889 MiB, within a few
  MiB of the 1 GiB address space); the render probe measures at most 2,000
  texts and keeps the ones past a canvas edge first when it keeps only 400,
  so G3 sees a clipped label drawn late without the probe eating into the
  CPU limit; and a renderer limit that stopped a run is counted as
  `R1-<reason>`. (#12125)
