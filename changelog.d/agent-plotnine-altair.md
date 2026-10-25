### Added

- **"Use with my data" can adapt and render plotnine and altair.** The agent
  network's Python runtime now serves the catalogue's plotnine and altair files
  next to matplotlib and seaborn: a save rule per library
  (`agents/anyplot/code/regions.py`, `SAVE_RULES`) replaces the savefig rule in the
  regions, the normaliser, the readiness scan, the edits and the validator, so
  plotnine's `save` and `ggsave` and altair's `save` are the protected final save;
  the validator gains both import surfaces, parses plotnine's `aes` and facet strings
  as code, refuses `formula=` (patsy runs Python while it parses one), and admits
  altair's PIL padding block on the PNG only; the plot guard lets altair write its
  `plot-<theme>.html` inside the sandbox, where nothing collects it, and hands
  plotnine's `Environment.capture` the plot's frame. The renderer image installs both
  libraries, and the eval fixtures gain 120 cases for them. 264 of 321 plotnine and
  269 of 325 altair files are eligible; `AGENT_LIBRARIES` keeps its default
  `matplotlib,seaborn` until each library's eval matrix reaches 80 %.

### Fixed

- **The fence regex no longer backtracks quadratically on user text.** The tag
  pattern `policy.fence` neutralises fence tags with put two blank runs around an
  optional slash, one ambiguous run that backtracked quadratically on `<` followed
  by a long run of blanks (CodeQL py/polynomial-redos). The blanks after the slash
  now sit inside the slash's own group; the matches are the same.
