### Added

- **The about page says who built the site and how.** Under its lede, "who
  built it" names Markus Neusinger with his photo, links to LinkedIn, GitHub
  and his own site neusinger.com, and his other projects, and introduces him
  in his own words: a chart nerd, physicist by training and data analyst by
  trade, who built anyplot alone in Visp with AI agents doing the legwork.
  "how it is built" says that models write the code of the site, the API, and
  the agents, and how he leads them, and links the README's "How I build
  anyplot" and "Engineering highlights" and the AI workflow page.
  `test_readme_claims.py` checks that those files and headings exist, so a
  renamed heading fails a test instead of a link on the site. One person
  builds the site, so the whole page speaks in the first person singular,
  "I" and never "we". The author in the structured data names neusinger.com
  too.

### Changed

- **About takes the place of mcp in the main navigation, and mcp the place of
  report in the footer.** The bar keeps seven entries. The MCP page stays one
  click away from the footer, the about page and the landing page. The footer
  reads github, mcp, the builder's name, about, legal: issues are filed on
  GitHub or from a spec page's "report issue" link, and the name stays in the
  middle of the row and now shows on phones and tablets too. From 720 px, or
  wider with a larger browser font size, the footer is one row; below that
  the four links share a centred line and the name takes the line below it.
  With a larger browser font size on a narrow phone the links break as github
  and mcp over about and legal, so no line ends on a separator. Keyboard and
  screen readers follow the order each layout shows, and with a browser font
  size up to 24 px every line keeps at least 9 px from the feedback and
  scroll-to-top buttons.
- **The stack and the running costs moved from the legal page to the about
  page.** The legal page keeps the legal notice and the privacy policy; a link
  to `/legal#transparency` leads to `/about#transparency`, which a fresh load
  now scrolls to. The crawler bodies of both pages and `llms.txt` follow.
- **The about page's description names what the page covers.** Search
  results and link previews read "About anyplot.ai: who built it, how AI
  agents write and review the catalogue, the stack, and what it costs to run."
  on the page, in its link preview and in its crawler copy, in place of three
  different descriptions, one of them an "AI-powered" slogan the style guide
  rules out.

### Fixed

- **The origin gives its dates, not a weekend.** The about page and the
  style guide's origin story said pyplots.ai was built in a weekend. It
  started in November 2025, and after a few months it became anyplot.ai in
  April 2026, as the repository's first commit and the 2.0.0 relaunch in
  `CHANGELOG.md` show; `test_readme_claims.py` pins the month of the rename
  to that release.

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
  the ones a workflow runs, so the blank-image check is gone, from the
  README's pipeline step too. The crawler body says the same, and
  `test_readme_claims.py` pins the floor, the step, the nightly schedule and
  the checks, the README's included.
- **Back leaves a redirected address in one step.** A fresh load of the old
  chat address `/debug/agent` or of a language address `/{spec}/{language}`
  left the old address one step back in the history, so Back landed on it and
  was sent forward again; the destination now takes over the old address's
  history entry, as the about page does for `/legal#transparency`.
