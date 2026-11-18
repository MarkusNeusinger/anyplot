### Added

- **The about page says who built the site and how.** Under its lede, "who
  built it" names Markus Neusinger with his photo, links to LinkedIn, GitHub
  and his own site neusinger.com, and his other projects, and introduces him
  in his own words: a chart nerd, physicist by training and senior data
  analyst by trade, who built and ran a platform for blockchain market data
  from 2022 to 2024, largely without AI, and has built anyplot alone and in
  his own time in Visp since November 2025, with AI agents writing the code
  while he decides, tests and sends back. "how it is built" says that AI
  models write the code of the site, the API, and the agents, that he decides
  what gets built, cuts the work into tasks and tests what comes back, and
  that outside the plot pipeline the agents merge nothing without his OK; it
  links the README's "How I build anyplot" and "Engineering highlights" and
  the AI workflow page. `test_readme_claims.py` checks that those files and
  headings exist, so a renamed heading fails a test instead of a link on the
  site, holds "since November 2025" to the README, and holds "senior" and the
  platform's years to the AI workflow page. One person builds the site, so
  the whole page and its crawler copy speak in the first person singular, "I"
  and never "we" or "humans". The author in the structured data names
  neusinger.com too.
- **The about page says who sets the rubric and how the chat's agents
  work.** The review section adds that what counts as a good plot is the
  builder's call, that AI helped turn it into 24 criteria and their points,
  and that the rubric has changed more than thirty times since November 2025,
  for example after a review passed a plot whose title was cut off. "use with
  my data" gets a second paragraph: one agent talks to you, an adapter writes
  the code changes and a reviewer scores the render, plain code runs the loop,
  a validator reads the code before anything runs, and a run makes one repair
  and two reviews at most; it names the builder's rules (open to everyone, no
  login, hosted in the EU, what you paste or write kept only if you send
  feedback) and links the agent design document, which records his decisions
  with their dates. The palette section says it took four rounds.
  `test_readme_claims.py` holds the 24 to the criteria registry, the repair
  and the reviews to the agents' settings, and the four rounds to
  `docs/reference/palette-variants/`. The crawler copy follows, except for
  the palette, which it has no section for.
- **The README shows three push-back cases.** Under "I know when to push
  back", nested cases tell how real weather downloads broke the import of
  pasted data, and that pasted data has had to work with notes, metadata or
  total rows around the table since then; how a review scored a parliament
  chart drawn with the real European Parliament groups 5 of 5 while three
  libraries dodged the topic, which led to invented parties and seats and a
  rubric that no longer marks a fictional chamber down; and how an audit
  found pasted values rounded or dropped without a word, which led to the
  rule that what you paste is what the data holds, or a line says what
  changed and how often. They replace the abstract sentence on security.
  `test_readme_claims.py` holds the first rule to the agents' parser.
- **The landing hero names its builder.** From 900 px the eyebrow above the
  headline reads "by Markus Neusinger", since the masthead shows "the open
  plot catalogue" at those widths; on narrower screens, where the masthead
  hides it, "the open plot catalogue" stands on a line of its own above the
  name. Only the name is a link, to the about page: it never breaks across
  lines, has no underline at rest and shows the site's green with a dotted
  underline on hover, is the hero's first link for the keyboard, has a 44 px
  touch target on phones, and counts its clicks as `nav_click` with the
  source `hero_about`. The intro adds "I approve new specs and set the
  rules." The masthead, the OG image and the crawler copy
  keep "the open plot catalogue" alone.
- **The about page's stack table lists the checks.** A "checks" row names
  tests and lint on every pull request that changes Python or frontend code
  outside the plot catalogue, the 80 % patch-coverage target of `codecov.yml`,
  CodeQL, every migration run on a throwaway PostgreSQL, and the check of the
  live site after a merge, which the merging agent runs by rule.
  `test_readme_claims.py` holds the target to `codecov.yml`.
- **The about page draws its pipeline, rubric, palette and origin.** The
  pipeline's ASCII list becomes a flow of its five steps with what AI does in
  each, and the builder's own steps, "I approve" and "I set and change them",
  stand in the site's green text shade, a use the style guide now lists among
  the places green may appear. Under the review text, one bar splits the
  rubric's 100 points into its six parts, from visual quality 30 to library
  mastery 10. Eight chips show the palette's hues with their names and hex
  values, and under the origin a timeline runs from pyplots.ai in November
  2025 through the first GitHub release (1.0.0), anyplot.ai (2.0.0), R
  (2.4.0), Julia and JavaScript (3.0.0) and, its last point before today, the
  4.0.0 release, whose notes open with the public "use with my data" page.
  The page gives months, not days: a timeline label reads
  "apr 2026 · 1.0.0", and the chat section has been open to everyone
  "since November 2026". Each figure is a list that a screen reader reads in
  order, the chips and the timeline named by the headings of their sections,
  and on a phone each one stacks. `test_readme_claims.py` holds the rubric's
  points to `prompts/quality-criteria.md` and each release on the timeline to
  its `CHANGELOG.md` heading by its exact date; it holds the chat section's
  month, on the page and in the crawler copy, to the opening day of the agent
  design document, and checks that the 4.0.0 release follows that day. A test
  holds the chips to the palette tokens.

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
  now scrolls to. The crawler bodies of both pages and `llms.txt` follow. The
  cost table now shows the operation at three-year commitment prices, before
  credits and without development use: about $75 a month, where it showed
  about $60 after credits.
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
  the builder does (approves the specs, sets the rules); a test reads its
  steps in order, and `test_readme_claims.py` holds its two numbers to their
  sources. The origin adds where pyplots.ai came from,
  showing colleagues a chart in everyday work, what they and later people who
  found it online wanted from it, and what it covers today, fifteen libraries
  in four languages, counted from the library registry. The "use with my data"
  section says, as the chat's explainer does, that `.use_my_data()` sits on a
  plot's page. The crawler copy follows each change.
- **The builder's photo hangs beside the about page's text on wide
  screens.** A larger photo stands 216 px wide in the margin left of the
  760 px column wherever that margin holds it with its gap, so the bio keeps
  the column's full width; narrower, it stays 110 px wide beside the name,
  above it on phones. The picture comes in two files, 360 and 684 px wide,
  and the browser takes the smaller one (41 kB against 93 kB) wherever the
  small slot or a screen of normal density is enough.
- **The about page's palette section drops the penguin example.** The two
  sentences after it, "the palette travels with you across libraries.
  switching tools doesn't mean re-learning your colour grammar.", carry the
  point alone, in the style guide's library-agnostic story too.
- **The landing page's description drops "human ideas, ai builds the
  rest."** and keeps the hero block, the library count, colorblind-safe and
  open source; a test now pins it.
- **The style guide follows the about page.** It drops the slogans the page
  no longer carries ("human ideas. ai builds the rest.", "AI-built,
  human-shaped", "Humans curate; AI executes", "a catalogue that maintains
  itself") and the old diagram for the page's own sentences, and its voice
  section says that the site speaks as its single builder, in the first
  person singular, that meta descriptions describe the site in the third
  person, and that a crawler copy that mirrors a page keeps the page's voice.
  Its pipeline line, its example of a spec and its positioning no longer speak
  of "humans" or "we", and its positioning assumes you know how to run code
  in your language, not Python alone.
- **The README counts the releases and names the approvals.** "How I build
  anyplot" introduces a physicist and data analyst and adds that 16 releases
  have shipped, a count `test_readme_claims.py` holds to the version
  headings of `CHANGELOG.md`, so every release raises it (release procedure,
  step 4); it adds that a new spec needs the owner's approval and that
  outside the plot pipeline the agents merge nothing without his OK. The
  pipeline's step 2 says that since September 2026 the merge job ignores an
  `approved` label from any other account, and `test_readme_claims.py` holds
  that to the merge job's condition in `spec-create.yml`. Its contribution
  steps say "I review and approve it" in place of "The maintainer".
- **The README's engineering highlights are six decisions, each with its
  reason.** The review loop says why pipeline reviews run on Opus: on the
  same plots it scored about 8 points below Sonnet, and its before-and-after
  gaps spread far less across repeated runs. The regen gate tells the
  experiment behind it, in which 39 of 75 regenerations merged after repairs
  at the lowered bar, and the rule that a regeneration never makes an
  implementation worse. New highlights tie a score to the code that drew it
  through the render hash and say that a check counts before it blocks: the
  figure check ships counting only, and every release runs the chat's evals
  first. The privacy highlight states the telemetry rule and the feedback
  exception, and the blank site of 2026-10-22 became a browser check after
  every merge. The chat's architecture leaves the list; its sentence on one
  repair round and two reviews now opens the README's "Use with my data"
  section, and the next bullet there says that the assistant never hands
  the server data rows but picks from a closed set of typed operations.
  "How I build anyplot" opens with the decisions the builder makes and the
  records that keep them, and counts six of them below.
  `test_readme_claims.py` holds each new claim to its source: the review
  model's default and fallback in `impl-review.yml`, the gate's one-point
  tolerance and adapt route in every text that states the gate, the
  render-hash steps and keep codes, the figure check's `log` default, the
  release procedure's eval step, the data layer's union of typed operations,
  and the count of decisions to the highlights' bullets.
- **The month the chat opened keeps its capital.** `/agent`, the about page
  and the crawler copy of each say "open to everyone since November 2026",
  as a month is a name in the site's lowercase voice too; the timeline's
  labels stay lowercase. `test_readme_claims.py` holds the month with its
  case on all three, against the opening day in the agent design document.
- **The site spells the colour-blindness words in British English.** The
  pages and their descriptions, the crawler copies, `llms.txt`, and the
  keywords and structured data of the page shell say "colourblind-safe", as
  the palette sections of the about and landing pages already did, and the
  palette page's sort button reads "max ΔE under colour blindness". The
  about page says "colour grammar" in its two sentences on it. The
  style guide follows in its sample copy and its own sentences, and its voice
  section adds the rule: British English on the site, while proper names,
  citations, code and library or API names keep their own spelling.
  `test_site_spelling.py` keeps the American forms of these words out of
  those surfaces and out of the style guide's own text. Other words are not
  swept yet.

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
- **Four sentences no longer say more than holds.** The about page and the
  README said that no generated plot is ever patched by hand, though the
  palette swap of May 2026 edited the plots' code catalogue-wide; they now
  state the rule: a wrong plot is fixed in its spec or a rule and
  regenerated. The README's highlight said the session id never appears in a
  URL; that holds for the public chat, whose id travels in a header, while
  the admin chat's routes carry it in the path. The AI workflow page said the
  same of every URL and now says the public chat's session id left its URLs.
  The AI workflow page, the guardrails and the Dependabot command say the
  site was blank for about 45 minutes on 2026-10-22, as `CLAUDE.md` and the
  README do, instead of when it was noticed. `test_readme_claims.py` holds
  the header to the public chat's routes and the minutes to the README's,
  and fails if one of the old sentences returns to the README, the workflow
  page, the guardrails or the Dependabot command.
- **Back leaves a redirected address in one step.** A fresh load of the old
  chat address `/debug/agent` or of a language address `/{spec}/{language}`
  left the old address one step back in the history, so Back landed on it and
  was sent forward again; the destination now takes over the old address's
  history entry, as the about page does for `/legal#transparency`.
- **The README's pipeline puts each check where it runs.** Its review step
  listed "the code parses and runs" and "the image exists" among the
  automated checks of `impl-review.yml`, but the code runs in generation. The
  generation step now says that `impl-generate.yml` runs the implementation
  and stops without both theme renders, and the review step's checks read
  "both renders exist and the canvas has its target size".
  `test_readme_claims.py` pins both sentences and the review's step that
  checks for both renders.
- **The README and the about page no longer overstate the review and the
  gate.** They said the reviewer scores "blind to any earlier score", but
  only its working tree and its prompt are kept free of the stored score,
  while the branch history and the pull request stay reachable. The README's
  review step, the about page and its crawler copy now say "with the stored
  score kept out of its working tree and its prompt", and a test holds them
  to the step that hides the stored review before the reviewer runs. A fix
  to a prompt, a spec or a rule reaches a plot when that plot is next
  regenerated, not at once, as the README's highlight, the about page, its
  crawler copy and the style guide now say. The gate was said to replace the
  live version only on a visible fix (the README's highlight) or only when
  a review finds a fixed defect and no regression (the README's nightly
  section, the about page, its crawler copy and the style guide). All five
  now say the same: only with no regression, a score at most a point lower
  and a fix the review can verify, while a code conversion for the chat
  passes on an unchanged render instead. The nightly regeneration names
  "the oldest single implementations" in place of a count the schedule no
  longer uses.
- **The debug page ignores a status answer that comes after it is gone.**
  Its first request set the page's state whenever it settled, also after
  the admin had moved on: a request that then failed forced a reload of the
  page they were on, and in a test run the late update was an unhandled
  error that failed a run in which every test had passed. The request's
  answer is now dropped once the page is gone or a newer request replaced
  it.
