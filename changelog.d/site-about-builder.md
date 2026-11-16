### Added

- **The about page says who built the site and how.** Under its lede, "who
  built it" names Markus Neusinger with his photo, links to LinkedIn and
  GitHub, and his other projects; "how it is built" says that models write the
  code of the site, the API, and the agents, and how he leads them, and links
  the README's "How I build anyplot" and "Engineering
  highlights" and the AI workflow page. `test_readme_claims.py` checks that
  those files and headings exist, so a renamed heading fails a test instead of
  a link on the site.
- **About is the last entry of the main navigation.** Eight entries need about
  750 px beside the logo and the search, so the two-row masthead of phones now
  also serves tablets up to 899 px; on phones narrower than 364 px the labels
  shrink to keep 8 px apart, and from 900 to 1199 px the row runs at 12 px with
  18 px gaps.

### Changed

- **The stack and the running costs moved from the legal page to the about
  page.** The legal page keeps the legal notice and the privacy policy; a link
  to `/legal#transparency` leads to `/about#transparency`, which a fresh load
  now scrolls to. The crawler bodies of both pages and `llms.txt` follow.
- **The footer shows the builder's name on phones too.** Below 600 px it takes
  a line of its own under the other links, so no row ends on a separator.

### Fixed

- **The about page no longer overstates the review bar and the upkeep of the
  catalogue.** It says that the bar drops 10 points per repair, to 50 at the
  last review, and that a nightly job regenerates the oldest implementations,
  instead of promising a re-run whenever a library ships a release, which no
  workflow does. The crawler body says the same, and `test_readme_claims.py`
  pins the floor, the step, and the nightly schedule.
