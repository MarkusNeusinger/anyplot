### Changed

- **The agents think by default.** Claude's adaptive thinking is on for the
  root (`AGENT_ROOT_THINKING_BUDGET`, 1,024 tokens of extra output room) and
  the adapter (`AGENT_ADAPTER_THINKING_BUDGET`, 2,048); 0 turns it off, and
  Gemini ignores both budgets. The measurement of 2026-10-11 on the 122 cases
  through the deployed renderer decided it: with both budgets every run passed
  the gates and 51.6 % ended `ok`, with thinking off 91.0 % and 28.7 % (the
  structured answer then misses its edit anchors in a third of the runs), for a
  median of $0.0063 instead of $0.0038 per plot and a p50 of 31.5 s instead of
  13.6 s. The thinking run is the new Claude baseline
  (`agents/evals/baselines/claude-haiku-5-5.json`). A replayed root thinking block
  whose signature no longer matches the conversation is dropped by the API instead
  of failing the call. (#12129)
