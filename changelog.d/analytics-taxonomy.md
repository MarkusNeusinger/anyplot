### Added

- **`ui_feature`: one event for "is this feature used at all".** Twelve single
  events (tab toggle, view mode, grid size, filter removal, random filter,
  plot rotation, library filter, theme toggle, feedback button, and three map
  interactions) are now one event with a `feature` property, sent once per
  feature and visit. A visitor who toggles a tab forty times weighs as much as
  one who did it once.
- **Every pageview names the kind of page.** The `page` property (`home`,
  `plots`, `spec_overview`, `spec_detail`, `agent_chat`, `other`) is the one
  `copy_code` and `download_image` already send, so the dashboard and its
  funnels can group pages by kind.

### Changed

- **The app sends eleven custom events, and the compiler refuses any other.**
  The set is the type `AnalyticsEvent`, and every component receives the
  sender as that type. Before, the app sent 42 event names, 23 of them without
  a goal on the public dashboard.
- **Search queries are normalised before they are sent.** `query` is the one
  property a visitor writes, and the public dashboard lists it: it is now
  lowercase, with single spaces, and cut at 40 characters.
- **`nav_click` is about the landing page only.** The menu bar, the logo, the
  breadcrumb and the gallery's compare link no longer send it: 76 % of its
  events were menu clicks, which the pageview that follows already records.
- **`open_interactive` is named `interactive_open`**, and `feedback_submitted`
  carries where it was sent from (`source`) and the plot, not the reaction or
  whether a contact was given.

### Removed

- **Ten agent chat events left the public dashboard.** Pastes, files,
  confirmations, data changes, refusals, saves, feedback and cut streams are
  lines of the server's usage telemetry; the browser repeated part of them to
  Plausible, mostly from the owner's own sessions. `agent_open` and
  `agent_plot_rendered` stay.
- **Link and click events that a pageview or the tracker script already
  records**: `external_link` (the script's `Outbound Link: Click` records the
  same click), `internal_link`, `tag_click`, `library_click`,
  `stats_top_impl_click`, `suggest_spec`, `report_issue`, and
  `page_not_found` (a missing page is a pageview under the path that was asked
  for since the pageview moved to the navigation).
