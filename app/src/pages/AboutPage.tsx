import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { Ext, FactTable } from 'src/components/FactTable';
import { SectionHeader } from 'src/components/SectionHeader';
import { GITHUB_URL } from 'src/constants';
import { ANCHOR_SX, useHashScroll } from 'src/hooks/useHashScroll';
import { paths } from 'src/routes/paths';
import {
  codeBlockStyle,
  colors,
  fontSize,
  proseLinkStyle,
  semanticColors,
  subheadingStyle,
  textStyle,
  typography,
} from 'src/theme';

const AVATAR_URL = 'https://storage.googleapis.com/anyplot-static/images/markusneusinger.webp';

// One sentence for search results and link previews, the same as the crawler copy's
// (api/routers/seo.py); each of its four parts is a section of this page.
const DESCRIPTION =
  'About anyplot.ai: who built it, how AI agents write and review the catalogue, the stack, and what it costs to run.';

// Files and headings on main, as GitHub renders them. Each path and heading anchor is written out
// after GITHUB_URL so tests/unit/test_readme_claims.py can find it and fail when a file moves or a
// heading is renamed.
const HOW_I_BUILD_URL = `${GITHUB_URL}/blob/main/README.md#how-i-build-anyplot`;
const HIGHLIGHTS_URL = `${GITHUB_URL}/blob/main/README.md#engineering-highlights`;
const AI_WORKFLOW_URL = `${GITHUB_URL}/blob/main/docs/concepts/ai-workflow.md`;

const PIPELINE_BLOCK = `// pipeline
idea    → human-submitted        (github issue)
spec    → ai-drafted, human-approved
code    → ai-generated           (per library)
review  → ai-evaluated
fix     → ai-retries; humans tune rules`;

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
              rules when something repeatedly fails. every example uses the same colorblind-safe
              palette, so switching libraries never breaks your color grammar.
            </Box>
          </Box>
        </Box>

        {/* Who built it */}
        <Box component="section" id="builder" sx={{ ...sectionSx, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>who built it</em>} />
          <Box sx={proseColumnSx}>
            <Box
              sx={{
                display: 'flex',
                gap: { xs: 3, sm: 6 },
                alignItems: 'flex-start',
                flexDirection: { xs: 'column', sm: 'row' },
              }}
            >
              {/* Decorative: the name stands beside it. Not lazy: it sits on the first screen.
                  110px wide so photo, name and links end above the fold of a 1440x900 screen. */}
              <Box
                component="img"
                src={AVATAR_URL}
                alt=""
                aria-hidden="true"
                width={240}
                height={518}
                sx={{ width: 110, height: 'auto', flexShrink: 0, display: 'block' }}
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
                  I&apos;m a chart nerd. physicist by training, data analyst by trade. since 2013 I
                  have built data pipelines, models and the tools around them, lately with ai agents
                  doing the legwork. on anyplot they write the code; I decide, test and send back. I
                  have built it alone since November 2025, in Visp, a small town in the Swiss Alps.
                  I wanted one place to find the right plot for my data.
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
              give each one to Claude Code, Claude in GitHub Actions, Gemini or Copilot, depending on
              what it needs and what it costs. I test what comes back and send it back until
              it&apos;s right. a new spec needs my approval, and outside the plot pipeline the agents
              merge nothing without my OK. what I correct becomes a rule the agents follow. I have
              built it with ai agents since November 2025.
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
              humans curate; ai executes. the catalogue maintains itself: every night a job
              regenerates the oldest implementations, and a new version replaces the live one only
              when a review of both finds a fixed defect and no regression; when a better example
              pattern emerges, I update the spec and every library regenerates. I never patch
              generated code by hand.
            </Box>
            <Box sx={{ ...codeBlockStyle, whiteSpace: 'pre', fontSize: '13px', mt: 3 }}>
              {PIPELINE_BLOCK}
            </Box>
          </Box>
        </Box>

        {/* Review */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>review</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              every implementation is scored before it ships. automated checks come first: the code
              runs, the canvas has its size. then an ai reviewer scores the render on a 100-point
              rubric of 24 criteria — visual quality, design, spec compliance, data quality, code
              quality, and library mastery — blind to any earlier score. a first review needs 90;
              below that, ai repairs the defects the review named and the plot is reviewed again, up
              to four times, and the bar drops 10 points per repair, to 50 at the last review. the{' '}
              {proseLink(paths.stats, 'stats page')} shows the score distribution per library.
            </Box>
          </Box>
        </Box>

        {/* Use with my data */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>use with my data</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              experimental, open to everyone since 2 november 2026.{' '}
              {proseLink(paths.plots, 'pick any plot')}, choose{' '}
              <Box component="code" sx={inlineCodeSx}>
                .use_my_data()
              </Box>
              , and paste your data. an agent adapts that plot&apos;s code to your columns, renders
              it in a sandbox with no network access, reviews the render against the
              catalogue&apos;s rubric, repairs it once if needed, and hands back the image and the
              code. your chat and data live only in server memory and are deleted after an hour
              idle, unless you send feedback.
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
          <SectionHeader prompt="❯" title={<em>palette</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              every plot uses <strong>imprint</strong>, my own colourblind-safe categorical palette
              — 8 hues plus 3 semantic anchors, tuned for warm-paper rendering and validated against
              the three main forms of colour vision deficiency. it sits in the same neighbourhood as
              Okabe-Ito, Paul Tol&apos;s &ldquo;muted&rdquo;, and ColorBrewer Set2 — about 8% of men
              have some form of CVD, and most plotting libraries ignore this entirely. I make it the
              default.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              a "gentoo penguin" is always blue, whether you draw it in matplotlib, plotly, or
              bokeh. the palette travels with you across libraries. switching tools doesn't mean
              re-learning your color grammar.
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

            <Typography sx={subheadingStyle}>monthly running costs (October 2026)</Typography>
            <FactTable
              labelWidth="75%"
              rows={[
                ['hosting: Cloud Run (site, api, data assistant, renderer)', '~$10'],
                ['database: Cloud SQL', '~$25'],
                ['data assistant model: Claude Haiku via Vertex AI', '~$15'],
                ['storage, logs and builds', '~$1'],
                ['domain (.ai)', '~$8'],
                ['total', <strong key="total">~$60/month</strong>],
              ]}
            />
            <Typography
              sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}
            >
              after three-year commitments and promotional credits; the assistant&apos;s model cost
              grows with use. development tools and subscriptions are not included. all costs are
              covered privately.
            </Typography>
          </Box>
        </Box>

        {/* Origin */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>origin</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              it started in November 2025 as pyplots.ai, a catalogue of Python plotting examples.
              people wanted two things from it. they wanted ideas for which plot fits their data.
              and they wanted to get to know libraries they hadn&apos;t used yet, since each has its
              own strengths. after a few months on pyplots.ai, I decided to go bigger. in April 2026
              it became anyplot.ai. one colorblind-safe palette travels across every library.
            </Box>
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
