### Changed

- **DQ-02's content policy targets real politics, not every parliament.** The
  forbidden-topic line in `prompts/quality-criteria.md`, `prompts/quality-evaluator.md`
  and the workflow reviewer now names real parties, politicians, elections, real
  legislatures and partisan messaging, and states that a clearly fictional
  parliament (invented names carrying no real-world ideology) is not political
  content: it never scores 0 or triggers the cap, invented data the spec asks
  for is not a deduction, and the fix for flat invented names is better
  invented names, never real ones. The old
  blanket "Politics (elections, parties, voting)" read as zeroing
  `parliament-basic` itself, whose spec now requires invented parties. (#12050)
