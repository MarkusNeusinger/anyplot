### Added

- **The chat header shows the plot it adapts.** A thumbnail of the catalogue
  plot sits beside the spec's title on `/agent`, in the library in use and the
  site theme, and opens large in a dialog; the columns the plot expects stand
  behind an ⓘ after the title, closed by default. The visitor keeps in view
  what the data should become without leaving the chat (#12549).
- **`.use_my_data() →` on the spec hub and in the code tab.** The hub page
  `/{spec-id}`, where links from the landing page, `/specs`, `/map` and the
  README arrive, offers the chat in its header, with one eligibility request
  per view (matplotlib where it is among the cards shown, else the first of
  them), and the plot page's code tab offers it beside `.copy()`. The chat
  records these opens as `agent_open{source: spec_hub}` and `plot_page`
  (#12549).

### Changed

- **The chat's reply-language line and remembered list are one short line
  each.** `# reply language: en` and `# remembered · 2 decisions` keep only
  what they state; where the language came from, that a plot keeps its own,
  and what the remembered decisions do stand behind an ⓘ, as the experimental
  notice does it (#12549).
