# A review stops when its render may not come from the code it scores

- Date: 2026-11-14
- Proposed: an audit of the live catalogue on 2026-11-08 traced 50 findings to renders that didn't
  come from the merged code. A hash of the rendered code was staged beside the renders and checked,
  warning only.
- Decided: a first generation whose hash doesn't match stops with a label, with no re-render mode.
  On 2026-11-16 he set the rest: no cutoff for old staging, so a missing or unreadable hash stops the
  review too; a failed hash write fails the run; a hash that can't be downloaded retries a first
  generation and keeps the live version of a regeneration.
- Where: #13034, #13122, #13129
