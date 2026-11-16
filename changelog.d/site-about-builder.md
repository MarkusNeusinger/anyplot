### Added

- **The about page says who built the site and how.** Under its lede, "who
  built it" names Markus Neusinger with his photo, links to LinkedIn, GitHub
  and his own site neusinger.com, and his other projects, and introduces him
  in his own words: a chart nerd, physicist by training and data analyst by
  trade, who has built anyplot alone in Visp since November 2025, with AI
  agents writing the code while he decides, tests and sends back. "how it is
  built" says that AI models write the code of the site, the API, and the
  agents, that he decides what gets built, cuts the work into tasks and tests
  what comes back, that a new spec needs his approval and that outside the
  plot pipeline the agents merge nothing without his OK; it links the
  README's "How I build anyplot" and "Engineering highlights" and the AI
  workflow page. `test_readme_claims.py` checks that those files and headings
  exist, so a renamed heading fails a test instead of a link on the site, and
  holds both "since November 2025" to the README. One person builds the site,
  so the whole page and its crawler copy speak in the first person singular,
  "I" and never "we" or "humans". The author in the structured data names
  neusinger.com too.
- **The landing hero names its builder.** The eyebrow above the headline
  reads "the open plot catalogue · by Markus Neusinger", the name a link to
  the about page and the hero's first link for the keyboard, and the intro
  adds "I approve new specs and set the rules." The masthead, the OG image
  and the crawler copy keep "the open plot catalogue" alone.
- **The about page's stack table lists the checks.** A "checks" row names
  tests and lint on every code pull request, the 80 % patch-coverage target
  of `codecov.yml`, CodeQL, every migration run on a throwaway PostgreSQL,
  and the check of the live site after a merge, which the merging agent runs
  by rule. `test_readme_claims.py` holds the target to `codecov.yml`.

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
  size up to 24 px every line keeps at least 8 px from the feedback and
  scroll-to-top buttons.
- **The stack and the running costs moved from the legal page to the about
  page.** The legal page keeps the legal notice and the privacy policy; a link
  to `/legal#transparency` leads to `/about#transparency`, which a fresh load
  now scrolls to. The crawler bodies of both pages and `llms.txt` follow.
- **The about page's description names its builder and what the page
  covers.** Search results and link previews read "About anyplot.ai: built by
  Markus Neusinger with AI agents he directs. How the catalogue is written
  and reviewed, the stack, and what it costs to run." on the page, in its
  link preview and in its crawler copy, in place of three different
  descriptions, one of them an "AI-powered" slogan the style guide rules out.
  The crawler copy now lists the stack too, one sentence per row of the
  page's table, so each part of the description has its section there.
- **The about page tells the pipeline in the first person.** The lede says
  that plot ideas come in as GitHub issues and that the builder approves new
  specs. The pipeline paragraph opens with "the pipeline runs on its own
  schedule, by rules I set" in place of "humans curate; ai executes" and "the
  catalogue maintains itself", and the diagram names what AI does (drafts,
  writes, scores against the 24 criteria, repairs up to four times) and what
  the builder does (approves the specs, sets the rules); a test compares the
  diagram character for character, and `test_readme_claims.py` holds its two
  numbers to their sources. The origin adds where pyplots.ai came from,
  everyday work, and what it covers today, fifteen libraries in four
  languages, counted from the library registry. The "use with my data"
  section says, as the chat's explainer does, that `.use_my_data()` sits on a
  plot's page. The crawler copy follows each change.
- **The landing page's description drops "human ideas, ai builds the
  rest."** and keeps the hero block, the library count, colorblind-safe and
  open source; a test now pins it.
- **The style guide follows the about page.** It drops the slogans the page
  no longer carries ("human ideas. ai builds the rest.", "AI-built,
  human-shaped", "Humans curate; AI executes", "a catalogue that maintains
  itself") and the old diagram for the page's own sentences, and its voice
  section says that the site speaks as its single builder, in the first
  person singular.
- **The README counts the releases and names the approvals.** "How I build
  anyplot" introduces a physicist and data analyst and adds that 16 releases
  have shipped, a count `test_readme_claims.py` holds to the version
  headings of `CHANGELOG.md`, so every release raises it (release procedure,
  step 4); it adds that a new spec needs the owner's approval and that
  outside the plot pipeline the agents merge nothing without his OK. The
  pipeline's step 2 says that since September 2026 the merge job ignores an
  `approved` label from any other account, and `test_readme_claims.py` holds
  that to the merge job's condition in `spec-create.yml`.

### Fixed

- **The origin gives its dates, not a weekend.** The about page and the
  style guide's origin story said pyplots.ai was built in a weekend. It
  started in November 2025, and after a few months it became anyplot.ai in
  April 2026, as the repository's first commit and the 2.0.0 relaunch in
  `CHANGELOG.md` show. The crawler copy now tells the origin too, after
  transparency, as on the page. On the page and in its crawler copy,
  `test_readme_claims.py` holds the month of the rename to that release and
  the start month to the README's "Since November 2025".
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
  the checks, and keeps the blank-image check out of the README's step.
- **Three sentences no longer say more than holds.** The about page and the
  README said that no generated plot is ever patched by hand, though the
  palette swap of May 2026 edited the plots' code catalogue-wide; they now
  state the rule: a wrong plot is fixed in its spec or a rule and
  regenerated. The README's highlight said the session id never appears in a
  URL; that holds for the public chat, whose id travels in a header, while
  the admin chat's routes carry it in the path. The AI workflow page says the
  blank site of 2026-10-22 lasted about 45 minutes, as `CLAUDE.md` and the
  README do. `test_readme_claims.py` holds the header to the public chat's
  routes and the minutes to the README's, and fails if one of the old
  sentences returns to the README or the workflow page.
- **Back leaves a redirected address in one step.** A fresh load of the old
  chat address `/debug/agent` or of a language address `/{spec}/{language}`
  left the old address one step back in the history, so Back landed on it and
  was sent forward again; the destination now takes over the old address's
  history entry, as the about page does for `/legal#transparency`.
