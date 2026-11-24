# A regeneration kept for a regression is retried once

- Date: 2026-11-23
- Proposed: keep the rule that a trade is a keep, and retry a kept regeneration once with the named
  regression as its change request.
- Decided: the retry, as one follow-up regeneration after the keep, judged by the same gate against
  the live version; a retry is never retried, and it does not count against the nightly pair count.
  This amends the decision of 2026-09-27 the same way as the repair round: the rule stays strict,
  and the retry goes through the same gate. The details were settled in the session that built it:
  the regression travels as a note of its own, never as a change request, so the gate's allowance
  for a change request on a `-basic` spec stays shut; only keeps with the code `regression` retry;
  a kept retry stores no second re-score and ages the pair like any other attempt.
- Where: `automation/scripts/regen_follow_up.py`
