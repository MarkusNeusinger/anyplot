### Added

- **Deterministic data handling for the agent network: parser, data roles,
  default bindings and the dataset store.** `agents/anyplot/data/` turns pasted
  CSV, TSV, semicolon, pipe or JSON text (at most 200 KB, 50 columns, 20,000
  rows and 200 characters per cell; control characters refused, zero-width and
  bidi characters stripped) into a canonical `data.csv` with comma delimiters,
  dot decimals, ISO dates and canonical headers, plus the `DatasetProfile`, a
  20-row preview and the dtypes the loader passes to `pd.read_csv`. Typing is
  explicit rather than left to pandas: dates are tried before numbers, so a
  `DD.MM.YYYY` column never reads as a thousands-dot number, and a decimal
  comma is accepted only when the whole column has that shape. The roles
  parser reads a spec's stored `## Data` bullets into typed roles, including
  variadic families such as `y1, y2, ...` (all 325 catalogue specs parse),
  default bindings match role kinds to column dtypes before name similarity,
  `check_bindings` validates roles, columns and dtype compatibility, and an
  in-memory, session-owned dataset store with an idle sweep and a 64 MB cap
  keeps parsed data out of ADK state. None of it imports ADK or ships in a
  service yet.
