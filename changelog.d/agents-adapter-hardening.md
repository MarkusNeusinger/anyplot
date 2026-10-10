### Added

- **A thinking measurement for the agent root and adapter.**
  `AGENT_ROOT_THINKING_BUDGET` and `AGENT_ADAPTER_THINKING_BUDGET` (0, off, by
  default; at most 4,096), set by the eval harness with `--thinking-budget
  ROOT,ADAPTER`, turn on Claude's adaptive thinking for that agent and add the
  budget to its output cap, so the answer keeps its headroom. Claude Haiku 5.5
  takes no thinking budget of its own, so the value is room, not a limit; the
  stamp records it and the summary names the measurement. With both at 0 no
  request changes.

### Changed

- **Claude answers every structured question under a structured-output
  format.** The adapter plan, the reviewer verdict and the judge verdict use
  `output_config.format` with the schema made strict by the SDK's
  `transform_schema`, instead of a forced tool call, so constrained decoding
  guarantees the JSON shape, the types, the enums and the required fields; the
  repairs keep mending the lengths and counts a grammar cannot enforce. Unlike
  a forced tool call, the format lets a thinking model think first.
- **The agent validator admits pure computing modules.** By the owner's
  decision, adapted code may import `warnings`, `typing`, `calendar`,
  `decimal`, `fractions`, `zoneinfo`, `enum`, `dataclasses`, `operator`,
  `bisect`, `heapq`, `numbers`, `cmath`, `scipy.fft`, `scipy.linalg` and
  `scipy.constants`. Each was walked for names that read, write, fetch or
  evaluate, and those stay banned, as do `io`, `sys`, `pathlib`, `random`,
  `locale` and `string`. A banned import's repair line names the module and
  what to use instead, and the eval record counts banned imports by module.
- **Edits match tolerantly, never fuzzily.** After an exact match, the edit
  applier tries the same text with the blanks before line breaks ignored, then
  whole lines whose words agree once indentation and spaces are ignored, with
  the replacement re-indented; the first tier with any match decides, and the
  unique-match and protected-region checks stay. A `find` that only matches the
  code before an earlier edit of the same plan gets its own repair line, and
  the eval record counts the edits each tier applied.

### Fixed

- **Box-basic's repair no longer fails on a protected line it must change.**
  The edit applier protected every theme conditional, including box-basic
  matplotlib's data-dependent `_tight_text_color`, so 12 of the 13
  `drift:theme_token` failures in the rerun of spike X refused a correct full
  file. A theme token is now a value picked per theme from literals and
  earlier tokens only, and the drift check compares meaning, so a token
  re-stated in other quotes or spacing passes.
- **The placeholder failure says how to add code after `df =
  load_user_data()`.** The repair line and the adapter prompt now say to keep
  the line out of `find` and `replace` and name the line below it to anchor an
  insertion on, the cause of the rerun's 5 `protected:placeholder` failures.

### Security

- **The agent validator closes module re-exports and private helpers.** An
  allowed module could hand out a module the import rules keep out
  (`statistics.sys.modules`, `collections._sys`, `enum.bltns`) or a private
  helper that runs `exec` (`dataclasses._FuncBuilder`); some of these passed
  the validator before. Such names are now banned as attributes and as `from`
  imports, and so is any private name of an imported module; no catalogue
  file changes eligibility.
