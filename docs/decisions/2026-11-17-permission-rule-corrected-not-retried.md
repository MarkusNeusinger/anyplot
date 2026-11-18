# A lost review is fixed at its cause, the permission rule, not by a retry

- Date: 2026-11-17
- Proposed: a permission rule meant to let a regeneration's review read its predecessor's files
  never matched them, so in 4 of 58 regenerations the review wrote no comparison and the gate kept
  the live version. The options: correct the rule, move the files into the checkout, or retry when
  the comparison file is missing.
- Decided: correct the rule. The first review after the merge met no refused call.
- Where: #13160
