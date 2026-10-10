### Added

- **A thinking measurement for the agent root and adapter.**
  `AGENT_ROOT_THINKING_BUDGET` and `AGENT_ADAPTER_THINKING_BUDGET` (0, off, by
  default; at most 4,096), set by the eval harness with `--thinking-budget
  ROOT,ADAPTER`, turn on Claude's adaptive thinking for that agent and add the
  budget to its output cap, so the answer keeps its headroom. Claude Haiku 5.5
  takes no thinking budget of its own, so the value is room, not a limit; the
  stamp records it and the summary names the measurement. With both at 0 no
  request changes. (#12124)

### Changed

- **Claude answers every structured question under a structured-output
  format.** The adapter plan, the reviewer verdict and the judge verdict use
  `output_config.format` with the schema made strict by the SDK's
  `transform_schema`, instead of a forced tool call, so constrained decoding
  guarantees the JSON shape, the types, the enums and the required fields; the
  repairs keep mending the lengths and counts a grammar cannot enforce. Unlike
  a forced tool call, the format lets a thinking model think first. (#12124)
- **The agent validator admits pure computing modules.** By the owner's
  decision, adapted code may import `warnings`, `typing`, `calendar`,
  `decimal`, `fractions`, `zoneinfo`, `enum`, `dataclasses`, `operator`,
  `bisect`, `heapq`, `numbers`, `cmath`, `scipy.fft`, `scipy.linalg` and
  `scipy.constants`. Each was walked for names that read, write, fetch,
  evaluate or set the process locale, and those stay banned, as do `io`, `sys`,
  `pathlib`, `random`, `locale` and `string`. A banned import's repair line names the module and
  what to use instead, and the eval record counts banned imports by module. The
  log names a module only by a word of a fixed list (the standard library, the
  allowlists and a few known packages), and any other import as `?`, so no word
  the model writes as an import path reaches the log. (#12124)
- **Edits match tolerantly, never fuzzily.** After an exact match, the edit
  applier tries the same text with the blanks before line breaks ignored, then
  whole lines whose words agree once indentation and spaces outside string
  literals are ignored, with the replacement re-indented; a literal's text must
  agree exactly. The first tier with any match decides, and the
  unique-match and protected-region checks stay. A `find` that only matches the
  code before an earlier edit of the same plan gets its own repair line, and
  the eval record counts the edits each tier applied. (#12124)

### Fixed

- **Box-basic's repair no longer fails on a protected line it must change.**
  The edit applier protected every theme conditional, including box-basic
  matplotlib's data-dependent `_tight_text_color`, so 12 of the 13
  `drift:theme_token` failures in the rerun of spike X refused a correct full
  file. A theme token is now a value picked per theme from literals and
  earlier tokens only, and the drift check compares meaning, so a token
  re-stated in other quotes or spacing passes. (#12124)
- **The placeholder failure says how to add code after `df =
  load_user_data()`.** The repair line and the adapter prompt now say to keep
  the line out of `find` and `replace` and name the line below it to anchor an
  insertion on, the cause of the rerun's 5 `protected:placeholder` failures.
  (#12124)

### Security

- **The agent validator closes module re-exports and private helpers.** An
  allowed module could hand out a module the import rules keep out
  (`statistics.sys.modules`, `collections._sys`, `enum.bltns`) or a private
  helper that runs `exec` (`dataclasses._FuncBuilder`); some of these passed
  the validator before. Such names are now banned as attributes, as `from`
  imports and as components of an import path below its root, and so is any
  private name or private submodule of an imported module; no catalogue file
  changes eligibility. (#12124)
