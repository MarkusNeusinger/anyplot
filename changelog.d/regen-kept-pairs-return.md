### Fixed

- **A pair the regen gate kept on a regression comes back after the attempt
  window.** The pair-mode picker aged a kept pair from its keep, so after the
  30 days it queued behind about 4,700 pairs, years at the nightly rate. That
  parked live implementations the regeneration had clearly beaten except for one
  regression (funnel-basic/bokeh kept at 83 against 69). A `regen:kept` PR whose
  gate record has the code `regression` now holds its pair for the window and
  then lets it return at its age from before the keep, usually its metadata
  `updated`. Every other keep code still ages the pair. The picker reads the
  records from the workflow's own verdict comments in one extra listing; when
  that listing fails, every keep ages its pair as before. (#12605)
