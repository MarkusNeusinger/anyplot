### Added

- **A feedback case shows what the chat assistant called and what its guards said, turn by turn.** The session bundle,
  and with it every stored case, carries `turns`: per turn its number, how it ended, every tool call in order (refused
  ones too) with the guard's verdict, what the call did and the code of its answer, and the verdicts of the scope
  judge, the output guard, the reply checks, the budget and the run queue. The persona round of 2026-11-06 had to
  infer several root causes because a case held none of this. Closed codes only, no argument, result, id or time; the
  record keeps the latest 50 turns per session and is never matched against log lines. (#12948)
