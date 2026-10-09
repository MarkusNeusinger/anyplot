### Added

- **Two-profile AST validator for the plot pipeline.** `agents/anyplot/code/validate.py`
  implements the SECURITY and ADAPTATION profiles of the agent-network design
  (`docs/concepts/agent-network.md`, "Adapt and validate") with no ADK import:
  `validate_security` checks the import surface (COMMON plus the matplotlib or
  seaborn allowlist, `os` only as the THEME lookup), the banned builtins and
  attributes, every dunder in identifiers and string literals, the pandas and
  numpy I/O calls (also when reached as a string through `df.agg(...)`), classes
  and async or generator statements, URL and oversize literals and the exact
  `f"plot-{THEME}.png"` savefig target; `validate_adaptation` checks the single
  `df = load_user_data()` placeholder, bans random data generation except a seeded
  `default_rng` used for jitter and subsampling, caps numeric literal lists at 20
  values and keeps the Imprint palette prefix. Invalid code never raises: size,
  encoding and syntax problems are findings too. The tests cover every rule with a
  failing snippet and its nearest allowed sibling, every bypass the design names,
  and the whole catalogue corpus, which prints a per-rule summary under `-s`.
  (#12107)
