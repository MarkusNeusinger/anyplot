### Added

- **A twelfth event measures who stays ten seconds (`stayed_10s`).** Plausible
  counts a visit as bounced unless it has a second page or a custom event, so
  a reader who lands on a plot, reads for a minute, and leaves counts like a
  crawler farm's page load. Google Analytics 4 also calls a session engaged
  when it lasts longer than ten seconds, counted while the page is in focus.
  The tracker now keeps that clock: once per visit, when the site has been
  visible and in focus for ten seconds, it sends `stayed_10s` with `input`
  (`yes` or `no`: whether a pointer, a finger, or a key was used). For about
  a week the event only measures: it goes out with `interactive: false`, so
  the bounce rate and every public number stay as they are. Whether a visit
  of more than ten seconds then counts as engaged is the owner's decision
  once the share is known for the farm and for readers. (#13100)
