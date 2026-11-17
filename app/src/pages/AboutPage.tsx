import { useId } from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { Ext, FactTable } from 'src/components/FactTable';
import { SectionHeader } from 'src/components/SectionHeader';
import { GITHUB_URL } from 'src/constants';
import { ANCHOR_SX, useHashScroll } from 'src/hooks/useHashScroll';
import { paths } from 'src/routes/paths';
import { OriginTimeline } from 'src/sections/about/OriginTimeline';
import { PaletteChips } from 'src/sections/about/PaletteChips';
import { PipelineFlow } from 'src/sections/about/PipelineFlow';
import { RubricBar } from 'src/sections/about/RubricBar';
import {
  colors,
  fontSize,
  proseLinkStyle,
  semanticColors,
  subheadingStyle,
  textStyle,
  typography,
} from 'src/theme';

const AVATAR_URL = 'https://storage.googleapis.com/anyplot-static/images/markusneusinger-684.webp';
const AVATAR_WIDTH = 684;
const AVATAR_HEIGHT = 1381;

// The portrait hangs in the gutter left of the 760px column where that gutter holds it with its
// 28px gap: the section 1248px wide or more, (1248 - 760) / 2 = 244 = 216 + 28. Keyed to the
// section's own width, so a scrollbar or the page's side padding can never push it past the left
// end of the section's rule.
const PORTRAIT_GUTTER_WIDTH = 216;
const PORTRAIT_GAP = 28;
const PORTRAIT_TOP = 6;
const PORTRAIT_SECTION_MIN = 760 + 2 * (PORTRAIT_GUTTER_WIDTH + PORTRAIT_GAP);
const inGutter = `@container (min-width: ${PORTRAIT_SECTION_MIN}px)` as const;

// For search results and link previews, the same as the crawler copy's (api/routers/seo.py): who
// built the site and how, then the sections that say how the catalogue is written and reviewed,
// the stack, and the running costs.
const DESCRIPTION =
  'About anyplot.ai: built by Markus Neusinger with AI agents he directs. How the catalogue is written and reviewed, the stack, and what it costs to run.';

// Files and headings on main, as GitHub renders them. Each path and heading anchor is written out
// after GITHUB_URL so tests/unit/test_readme_claims.py can find it and fail when a file moves or a
// heading is renamed.
const HOW_I_BUILD_URL = `${GITHUB_URL}/blob/main/README.md#how-i-build-anyplot`;
const HIGHLIGHTS_URL = `${GITHUB_URL}/blob/main/README.md#engineering-highlights`;
const AI_WORKFLOW_URL = `${GITHUB_URL}/blob/main/docs/concepts/ai-workflow.md`;
const AGENT_NETWORK_URL = `${GITHUB_URL}/blob/main/docs/concepts/agent-network.md`;

const ctaSx = {
  fontFamily: typography.mono,
  fontSize: '13px',
  fontWeight: 500,
  letterSpacing: '-0.01em',
  color: 'var(--ink-muted)',
  textDecoration: 'none',
  px: 1.25,
  py: 0.75,
  borderRadius: '4px',
  transition: 'color 0.2s, background 0.2s',
  '&::before': { content: '"."', color: 'var(--ink-muted)' },
  '&:hover': {
    color: colors.primary,
    background: 'var(--bg-elevated)',
    '&::before': { color: colors.primary },
  },
} as const;

const sectionSx = { py: { xs: 2, md: 3 } };
const proseColumnSx = { maxWidth: 760, mx: 'auto' };
const inlineCodeSx = {
  fontFamily: typography.mono,
  fontSize: '0.9em',
  backgroundColor: 'var(--bg-elevated)',
  padding: '2px 6px',
  borderRadius: '3px',
  color: 'var(--ink)',
} as const;

export function AboutPage() {
  // A fresh load of /about#transparency (and of /legal#transparency, which leads here) lands on it.
  useHashScroll();
  // The chips and the timeline are lists named by their section's heading.
  const paletteHeadingId = useId();
  const originHeadingId = useId();

  // An in-prose link to another page of the site, through the router.
  const proseLink = (to: string, label: string) => (
    <Link component={RouterLink} to={to} sx={proseLinkStyle}>
      {label}
    </Link>
  );

  return (
    <>
      <>
        <title>about | anyplot.ai</title>
        <meta name="description" content={DESCRIPTION} />
        <meta property="og:title" content="about | anyplot.ai" />
        <meta property="og:description" content={DESCRIPTION} />
        <link rel="canonical" href="https://anyplot.ai/about" />
      </>

      <Box sx={{ pb: 4 }}>
        {/* About (lede) */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>about</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ ...textStyle, fontSize: '18px', color: 'var(--ink)', fontWeight: 300 }}>
              a catalogue of plotting examples across fifteen libraries in python, r, julia, and
              javascript. plot ideas come in as GitHub issues; ai drafts the spec, generates code
              for every library, and reviews each implementation. I approve new specs and tune the
              rules when something repeatedly fails. every example uses the same colourblind-safe
              palette, so switching libraries never breaks your colour grammar.
            </Box>
          </Box>
        </Box>

        {/* Who built it */}
        <Box
          component="section"
          id="builder"
          sx={{ ...sectionSx, ...ANCHOR_SX, containerType: 'inline-size' }}
        >
          <SectionHeader prompt="❯" title={<em>who built it</em>} />
          <Box
            sx={{
              ...proseColumnSx,
              position: 'relative',
              // The portrait is out of the flow there, so the column keeps room for all of it
              // and the next section never slides under it.
              [inGutter]: {
                minHeight:
                  PORTRAIT_TOP + Math.ceil((PORTRAIT_GUTTER_WIDTH * AVATAR_HEIGHT) / AVATAR_WIDTH),
              },
            }}
          >
            <Box
              sx={{
                display: 'flex',
                gap: { xs: 3, sm: 6 },
                alignItems: 'flex-start',
                flexDirection: { xs: 'column', sm: 'row' },
              }}
            >
              {/* Decorative: the name stands beside it. Not lazy: it sits on the first screen.
                  Where the gutter holds it, it hangs there at 216px, its top at the name's line:
                  the photo gets room without taking any from the column, so name, links, bio and
                  other projects keep its full width. Narrower, it stands beside the name at
                  110px, small enough that photo, name and links end on the first screen of a
                  window 900px tall; on a phone it stands above the name at the same size. */}
              <Box
                component="img"
                src={AVATAR_URL}
                alt=""
                aria-hidden="true"
                width={AVATAR_WIDTH}
                height={AVATAR_HEIGHT}
                sx={{
                  width: 110,
                  height: 'auto',
                  flexShrink: 0,
                  display: 'block',
                  [inGutter]: {
                    position: 'absolute',
                    top: PORTRAIT_TOP,
                    right: `calc(100% + ${PORTRAIT_GAP}px)`,
                    width: PORTRAIT_GUTTER_WIDTH,
                  },
                }}
              />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  sx={{
                    fontFamily: typography.mono,
                    fontSize: fontSize.lg,
                    fontWeight: 500,
                    color: 'var(--ink)',
                    mb: 1,
                  }}
                >
                  Markus Neusinger
                </Typography>
                <Typography sx={textStyle}>
                  linkedin:{' '}
                  <Link
                    href="https://www.linkedin.com/in/markus-neusinger/"
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={proseLinkStyle}
                  >
                    markus-neusinger
                  </Link>
                  <br />
                  github:{' '}
                  <Link
                    href="https://github.com/MarkusNeusinger"
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={proseLinkStyle}
                  >
                    MarkusNeusinger
                  </Link>
                  <br />
                  {/* no noreferrer — his own site, keep the referrer for its analytics */}
                  web:{' '}
                  <Link
                    href="https://neusinger.com"
                    target="_blank"
                    rel="noopener"
                    sx={proseLinkStyle}
                  >
                    neusinger.com
                  </Link>
                </Typography>
                <Typography sx={{ ...textStyle, mb: 0 }}>
                  I&apos;m a chart nerd. physicist by training, senior data analyst by trade. since
                  2013 I have built data pipelines, models and the tools around them, lately with ai
                  agents doing the legwork. I know the stack from building it by hand: from 2022 to
                  2024 I built and ran a platform for blockchain market data, largely without ai. on
                  anyplot the agents write the code; I decide, test and send back. I have built it
                  alone and in my own time since November 2025, in Visp, a small town in the Swiss
                  Alps. I wanted one place to find the right plot for my data.
                </Typography>
              </Box>
            </Box>

            <Typography sx={subheadingStyle}>other projects</Typography>
            <Typography sx={textStyle}>
              {/* no noreferrer — own sites, keep the referrer for their analytics */}
              <Link
                href="https://kurrentschrift.ink"
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                kurrentschrift.ink
              </Link>{' '}
              — read and write old german cursive
              <br />
              <Link
                href="https://github.com/MarkusNeusinger/cite-citadel"
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                cite-citadel
              </Link>{' '}
              — llm-maintained, fully-cited personal wiki
            </Typography>
          </Box>
        </Box>

        {/* How it is built */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>how it is built</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              ai models write anyplot&apos;s code: the site, the api, and the agents behind
              &ldquo;use with my data&rdquo;. I decide what gets built, cut the work into tasks and
              give each one to Claude Code, Claude in GitHub Actions, Gemini or Copilot, depending
              on what it needs and what it costs. I test what comes back and send it back until
              it&apos;s right. outside the plot pipeline the agents merge nothing without my OK, and
              what I correct becomes a rule they follow.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              more on GitHub: <Ext href={HOW_I_BUILD_URL}>how I build anyplot</Ext> and{' '}
              <Ext href={HIGHLIGHTS_URL}>engineering highlights</Ext> in the README, and the whole
              story in <Ext href={AI_WORKFLOW_URL}>how anyplot is built with ai agents</Ext>.
            </Box>
          </Box>
        </Box>

        {/* Pipeline */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>pipeline</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the pipeline runs on its own schedule, by rules I set. every night a job regenerates
              the oldest implementations, and a new version replaces the live one only when a review
              of both finds a fixed defect and no regression; when a better example pattern emerges,
              I update the spec and regenerate its libraries. I don&apos;t fix a plot by editing its
              code: a patch fixes one plot, a fix to the spec or a rule reaches every plot it
              governs.
            </Box>
            <PipelineFlow />
          </Box>
        </Box>

        {/* Review */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>review</em>} />
          <Box sx={proseColumnSx}>
            {/* "more than thirty" is a floor on the changes to prompts/quality-criteria.md after its
                first commit (`git log -- prompts/quality-criteria.md` listed 36 commits, 35 after
                the first, when the sentence was written). CI clones the repository shallow, so no
                test can count them. */}
            <Box sx={textStyle}>
              every implementation is scored before it ships. automated checks come first: the code
              runs, the canvas has its size. then an ai reviewer scores the render on a 100-point
              rubric of 24 criteria — visual quality, design, spec compliance, data quality, code
              quality, and library mastery — with the stored score kept out of its working tree and
              its prompt. a first review needs 90; below that, ai repairs the defects the review
              named and the plot is reviewed again, up to four times, and the bar drops 10 points
              per repair, to 50 at the last review. what counts as a good plot is my call; ai helped
              turn it into 24 criteria and their points. the rubric isn&apos;t fixed: it has changed
              more than thirty times since November 2025, for example after a review passed a plot
              whose title was cut off. the {proseLink(paths.stats, 'stats page')} shows the score
              distribution per library.
            </Box>
            <RubricBar />
          </Box>
        </Box>

        {/* Use with my data */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>use with my data</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              experimental, open to everyone since november 2026.{' '}
              {proseLink(paths.plots, 'pick any plot')}, choose{' '}
              <Box component="code" sx={inlineCodeSx}>
                .use_my_data()
              </Box>{' '}
              on its page, and paste your data. an agent adapts that plot&apos;s code to your
              columns, renders it in a sandbox with no network access, reviews the render against
              the catalogue&apos;s rubric, repairs it once if needed, and hands back the image and
              the code. your chat and data live only in server memory and are deleted after an hour
              idle, unless you send feedback.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              one agent talks to you, an adapter writes the code changes, and a reviewer scores the
              render; the loop that calls them is plain code. a validator reads the code before
              anything runs, and code decides from the reviewer&apos;s points whether a repair is
              due: one repair and two reviews at most. what the review still finds comes back as
              notes with the plot. my rules: open to everyone, no login, hosted in the EU, and I
              keep what you paste or write only if you send feedback. by those rules I decided which
              model answers, where the code it writes runs, and what the usage logs may hold;{' '}
              <Ext href={AGENT_NETWORK_URL}>the design document on GitHub</Ext> records these
              decisions with their dates.
            </Box>
          </Box>
        </Box>

        {/* MCP */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>mcp</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the same catalogue, served to ai coding assistants over the model context protocol.
              six tools search specs by tag, return a spec with its implementations, and fetch one
              library&apos;s code, so your assistant starts from code that already rendered and
              passed review. setup on the {proseLink(paths.mcp, 'mcp page')}; the{' '}
              {proseLink(paths.stats, 'stats page')} shows, per day, how many assistants and
              crawlers read the catalogue and how many came on behalf of a person.
            </Box>
          </Box>
        </Box>

        {/* Palette */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader id={paletteHeadingId} prompt="❯" title={<em>palette</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              every plot uses <strong>imprint</strong>, my own colourblind-safe categorical palette
              — 8 hues plus 3 semantic anchors, tuned for warm-paper rendering and validated against
              the three main forms of colour vision deficiency. it took four rounds: the
              colour-distance numbers had to agree with what I like to look at. it sits in the same
              neighbourhood as Okabe-Ito, Paul Tol&apos;s &ldquo;muted&rdquo;, and ColorBrewer Set2
              — about 8% of men have some form of CVD, and most plotting libraries ignore this
              entirely. I make it the default.
            </Box>
            <PaletteChips labelledBy={paletteHeadingId} />
            <Box sx={{ ...textStyle, mt: 1 }}>
              the palette travels with you across libraries. switching tools doesn&apos;t mean
              re-learning your colour grammar.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              see the {proseLink(paths.palette, 'palette page')} for the full reference and usage
              rules.
            </Box>
          </Box>
        </Box>

        {/* Transparency: stack, source and running costs */}
        <Box component="section" id="transparency" sx={{ ...sectionSx, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>transparency</em>} />

          <Box sx={proseColumnSx}>
            <Typography sx={textStyle}>open source, down to what it costs to run.</Typography>

            <Typography sx={subheadingStyle}>technology stack</Typography>
            <FactTable
              rows={[
                [
                  'site',
                  <>
                    <Ext href="https://react.dev">React</Ext> 19,{' '}
                    <Ext href="https://vite.dev">Vite</Ext>, <Ext href="https://mui.com">MUI</Ext> 9
                    with <Ext href="https://mui.com/x/">MUI X</Ext>,{' '}
                    <Ext href="https://typescriptlang.org">TypeScript</Ext>
                  </>,
                ],
                [
                  'api',
                  <>
                    <Ext href="https://python.org">Python</Ext> 3.14,{' '}
                    <Ext href="https://fastapi.tiangolo.com">FastAPI</Ext>,{' '}
                    <Ext href="https://sqlalchemy.org">SQLAlchemy</Ext>,{' '}
                    <Ext href="https://postgresql.org">PostgreSQL</Ext> 18
                  </>,
                ],
                [
                  'catalogue pipeline',
                  <>
                    <Ext href="https://github.com/features/actions">GitHub Actions</Ext> with Claude
                    (<Ext href="https://www.anthropic.com/claude-code">Claude Code</Ext>); 15
                    plotting libraries in Python, R, Julia and JavaScript
                  </>,
                ],
                [
                  'data assistant',
                  <>
                    <Ext href="https://google.github.io/adk-docs/">Google ADK</Ext>,{' '}
                    <Ext href="https://www.anthropic.com/claude/haiku">Claude Haiku 5.5</Ext> via{' '}
                    <Ext href="https://cloud.google.com/vertex-ai">Vertex AI</Ext> (EU), plots
                    rendered in Cloud Run sandboxes (<Ext href="https://gvisor.dev">gVisor</Ext>)
                  </>,
                ],
                [
                  'google cloud',
                  <>
                    <Ext href="https://cloud.google.com/run">Cloud Run</Ext>, Cloud SQL, Cloud
                    Storage, Cloud Logging, BigQuery, Cloud Build and Artifact Registry in the
                    Netherlands (europe-west4), plus Secret Manager and Cloud Monitoring
                  </>,
                ],
                [
                  'edge & analytics',
                  <>
                    <Ext href="https://cloudflare.com">Cloudflare</Ext>,{' '}
                    <Ext href="https://plausible.io">Plausible</Ext> (no cookies,{' '}
                    <Ext href="https://plausible.io/anyplot.ai">public dashboard</Ext>)
                  </>,
                ],
                [
                  'reviews',
                  <>
                    <Ext href="https://deepmind.google/technologies/gemini/">Gemini</Ext> via Vertex
                    AI for second opinions,{' '}
                    <Ext href="https://github.com/features/copilot">GitHub Copilot</Ext> for pull
                    requests
                  </>,
                ],
                [
                  'checks',
                  // A no-break space keeps the percent sign with its number.
                  <>
                    tests and lint on every pull request that changes Python or frontend code
                    outside the plot catalogue, an 80&nbsp;% patch-coverage target, CodeQL, every
                    migration run on a throwaway PostgreSQL, and by rule a check of the live site
                    after a merge
                  </>,
                ],
                [
                  'editor, typography',
                  <>
                    <Ext href="https://www.jetbrains.com/pycharm/">JetBrains PyCharm</Ext>;{' '}
                    <Ext href="https://www.monolisa.dev/">MonoLisa</Ext> by Marcus Sterz;{' '}
                    <Ext href="https://github.com/JetBrains/JetBrainsMono">JetBrains Mono</Ext>{' '}
                    2.304 (<Ext href="https://openfontlicense.org">SIL Open Font License 1.1</Ext>)
                    for the attribution strip under plots created from your own data
                  </>,
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>source code</Typography>
            <Typography sx={textStyle}>
              the entire codebase is publicly available under the MIT License:
              <br />
              <Link href={GITHUB_URL} target="_blank" rel="noopener" sx={proseLinkStyle}>
                github.com/MarkusNeusinger/anyplot
              </Link>
              <br />
              bundled third-party fonts keep their own licences — JetBrains Mono is under the SIL
              Open Font License 1.1.
            </Typography>

            <Typography sx={subheadingStyle}>
              monthly running costs (as of November 2026)
            </Typography>
            <FactTable
              labelWidth="75%"
              rows={[
                ['hosting: Cloud Run (site, api, data assistant, renderer)', '~$14'],
                ['database: Cloud SQL', '~$35'],
                ['data assistant model: Claude Haiku via Vertex AI', '~$12'],
                ['storage, logs and builds', '~$6'],
                ['domain (.ai)', '~$8'],
                ['total', <strong key="total">~$75/month</strong>],
              ]}
            />
            <Typography
              sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}
            >
              at three-year commitment prices, before credits; a monthly cloud credit from a Google
              developer subscription pays most of it. infrastructure as billed for October 2026, the
              assistant&apos;s model at November&apos;s pace; it grows with use. development (test
              runs and reviews) is not included. all costs are covered privately.
            </Typography>
          </Box>
        </Box>

        {/* Origin */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader id={originHeadingId} prompt="❯" title={<em>origin</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              it started in November 2025 as pyplots.ai, a catalogue of Python plotting examples. it
              grew out of everyday work: showing colleagues a chart instead of explaining it at
              length. they, and later people who found it online, wanted two things from it: ideas
              for which plot fits their data, and to get to know libraries they hadn&apos;t used
              yet, since each has its own strengths. after a few months on pyplots.ai, I decided to
              go bigger. in April 2026 it became anyplot.ai. today it covers fifteen libraries in
              four languages, and one colourblind-safe palette travels across all of them.
            </Box>
            <OriginTimeline labelledBy={originHeadingId} />
          </Box>
        </Box>

        {/* Contribute */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>contribute</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              everything happens on GitHub — issues, releases, discussions. there's no separate
              forum, no signup, no account.
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 1.5,
                mt: 2,
                fontFamily: typography.mono,
              }}
            >
              <Link
                href={`${GITHUB_URL}/issues/new?template=request-new-plot.yml`}
                target="_blank"
                rel="noopener noreferrer"
                sx={ctaSx}
              >
                request_plot()
              </Link>
              <Link
                href={`${GITHUB_URL}/issues/new?labels=bug`}
                target="_blank"
                rel="noopener noreferrer"
                sx={ctaSx}
              >
                report_bug()
              </Link>
              <Link
                href={`${GITHUB_URL}/discussions`}
                target="_blank"
                rel="noopener noreferrer"
                sx={ctaSx}
              >
                discuss()
              </Link>
              <Link
                href={`${GITHUB_URL}/releases`}
                target="_blank"
                rel="noopener noreferrer"
                sx={ctaSx}
              >
                changelog()
              </Link>
            </Box>
          </Box>
        </Box>
      </Box>
    </>
  );
}
