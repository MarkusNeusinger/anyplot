### Added

- **The about page says who built the site and how.** Under its lede, "who
  built it" names Markus Neusinger with his photo, links to LinkedIn, GitHub
  and his own site neusinger.com, and his other projects; "how it is built"
  says that models write the code of the site, the API, and the agents, and how
  he leads them, in the first person as the README does, and links the README's
  "How I build anyplot" and "Engineering
  highlights" and the AI workflow page. `test_readme_claims.py` checks that
  those files and headings exist, so a renamed heading fails a test instead of
  a link on the site. The author in the structured data names neusinger.com
  too.

### Changed

- **About takes the place of mcp in the main navigation, and the footer links
  mcp.** The bar keeps seven entries. The MCP page stays one click away from
  the footer, the about page and the landing page. The footer reads github,
  report, mcp, about, legal, then the builder's name, which phones and tablets
  now show too, on a line of its own below 900 px. Below 400 px the site's own
  pages take a row of their own, so no row ends on a separator.
- **The stack and the running costs moved from the legal page to the about
  page.** The legal page keeps the legal notice and the privacy policy; a link
  to `/legal#transparency` leads to `/about#transparency`, which a fresh load
  now scrolls to. The crawler bodies of both pages and `llms.txt` follow.

### Fixed

- **The masthead fits at every width.** With MonoLisa the last menu entry ran
  into the right margin on phones narrower than about 344 px, and the screen
  cut it off below about 327 px. From 600 to about 700 px and from 900 to
  about 925 px the logo broke onto two lines; from 600 to about 640 px the
  search also ran into the right margin, and below about 609 px past the
  screen's edge. The single row now starts at 720 px, the labels on a phone
  keep at least 8 px apart, phones narrower than 360 px mark the active page
  with a small dot that stays clear of the label before it, and from 900 to
  1199 px the labels keep 20 px apart.
- **The about page no longer overstates the review and the upkeep of the
  catalogue.** It says that the bar drops 10 points per repair, to 50 at the
  last review, and that a nightly job regenerates the oldest implementations,
  instead of promising a re-run whenever a library ships a release, which no
  workflow does. Among the automated checks before the review it names only
  the ones a workflow runs, so the blank-image check is gone. The crawler body
  says the same, and `test_readme_claims.py` pins the floor, the step, the
  nightly schedule and the checks.
- **Back leaves a redirected address in one step.** A fresh load of the old
  chat address `/debug/agent` or of a language address `/{spec}/{language}`
  left the old address one step back in the history, so Back landed on it and
  was sent forward again; the destination now takes over the old address's
  history entry, as the about page does for `/legal#transparency`.
