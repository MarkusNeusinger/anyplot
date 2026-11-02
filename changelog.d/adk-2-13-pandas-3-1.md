### Changed

- **Google ADK 2.13 and pandas 3.1.** ADK now delivers a response schema to Claude
  as a `structured_output` tool, forced with thinking off and only offered with it
  on, which on the adapter and reviewer would sit next to the constrained
  `output_config.format`, so `VertexClaude` drops the tool and keeps the format.
  Since pandas 3.1 reads every float exactly, the loader of an exported `plot.py`
  no longer sets `float_precision`, which pandas deprecated and will remove, and
  pandas is at least 3.1.0. (#12426)

### Fixed

- **Float totals add up the cells as they are written.** A group `sum`, a group
  `mean` and a `share` now add a float column in decimals. pandas 3.1 dropped its
  compensated group sum for sorted keys, so 1,840 cells of the eval fixtures and
  test sets changed, and a monthly total of `4024.2` came back as
  `4024.2000000000003`; adding in decimals gives the sum a reader gets by hand, on
  every pandas version. (#12426)
