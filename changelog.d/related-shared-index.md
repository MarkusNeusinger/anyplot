### Fixed

- **Related plots load in about a millisecond instead of about 750 ms.** The
  related-plots block on every spec and implementation page was cached per spec,
  library, mode and limit. Those thousands of keys evicted each other from the
  shared 1,000-entry cache, so nearly every call reloaded all specs from the
  database (p50 755 ms, p99 1.6 s in the LinkedIn traffic of 2026-10-18/19).
  `/insights/related` now caches the catalogue once as a plain-value index under
  a single key and ranks against it in memory. The results are identical: 1,266
  spec, library, mode and limit combinations on the live catalogue gave
  byte-equal responses.
