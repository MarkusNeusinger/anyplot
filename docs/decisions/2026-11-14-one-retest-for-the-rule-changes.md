# The review plan's rule changes get one retest together, not one each

- Date: 2026-11-14
- Proposed: each change to the review rules carries its own retest arm against a baseline before it
  merges.
- Decided: the rule changes of the review plan get one proper retest together, once all of them are
  built, with the rules of `main` at 47f06814c as the baseline.
- Where: #13102
