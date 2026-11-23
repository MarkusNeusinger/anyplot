# A regeneration kept for a regression is retried once

- Date: 2026-11-23
- Proposed: keep the rule that a trade is a keep, and retry a kept regeneration once with the named
  regression as its change request.
- Decided: the retry, as one follow-up regeneration after the keep, judged by the same gate against
  the live version. The regression travels as a note of its own, never as a change request, so the
  gate's allowance for a change request on a `-basic` spec stays shut. Only keeps with the code
  `regression` retry; a retry is never retried, and a kept retry ages the pair like any other
  attempt. This amends the decision of 2026-09-27 the same way as the repair round: the rule stays
  strict, and the retry goes through the same gate.
- Where: `automation/scripts/regen_follow_up.py`
