# A merged regeneration with named defects gets one repair round

- Date: 2026-11-23
- Proposed: one repair round on every defect line a merged regeneration's review still names, about
  72 % of the files replaced in batches 4 to 7, then the regen gate again; first as a second pass
  inside the same pull request, then as a follow-up regeneration after the merge.
- Decided: the follow-up. The winner merges exactly as it would have; afterwards one more
  regeneration of the pair goes after the named defects, and the same gate, with its tolerance of a
  point, judges it against the now-live winner. A follow-up is never followed up, an adapt-route
  merge gets none, and the extra rounds do not count against the nightly pair count. This amends the
  decision of 2026-09-27: every pull request still gets one review and no repair loop, and an
  implementation never gets worse, because the follow-up has to beat the winner at the same gate,
  not a lowered bar. That reason is the option's own case, which he picked.
- Where: `automation/scripts/regen_follow_up.py`
