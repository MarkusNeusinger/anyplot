import { useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { GITHUB_URL } from '../constants';
import { colors, typography, textStyle, codeBlockStyle, proseLinkStyle } from '../theme';

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

export function AboutPage() {
  const { trackPageview, trackEvent } = useAnalytics();

  useEffect(() => {
    trackPageview('/about');
  }, [trackPageview]);

  return (
    <>
      <Helmet>
        <title>about | anyplot.ai</title>
        <meta
          name="description"
          content="a catalogue of plotting examples across eleven libraries in python, r, and julia. plot ideas come from humans; ai drafts the spec, generates code for every library, and reviews each implementation."
        />
        <meta property="og:title" content="about | anyplot.ai" />
        <meta
          property="og:description"
          content="humans submit ideas. ai drafts specs, generates code, reviews. humans approve."
        />
        <link rel="canonical" href="https://anyplot.ai/about" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* About (lede) */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>about</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ ...textStyle, fontSize: '18px', color: 'var(--ink)', fontWeight: 300 }}>
              a catalogue of plotting examples across nine python libraries. plot ideas come from humans;
              ai drafts the spec, generates code for every library, and reviews each implementation.
              humans approve specs and tune the rules when something repeatedly fails. every example uses
              the same colorblind-safe palette, so switching libraries never breaks your color grammar.
            </Box>
          </Box>
        </Box>

        {/* Pipeline */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>pipeline</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              humans curate; ai executes. the catalogue maintains itself: when matplotlib ships a new release,
              we re-run the pipeline; when a better example pattern emerges, we update the spec and every
              library regenerates. we never patch generated code by hand.
            </Box>
            <Box sx={{ ...codeBlockStyle, whiteSpace: 'pre', fontSize: '13px', mt: 3 }}>
              {PIPELINE_BLOCK}
            </Box>
          </Box>
        </Box>

        {/* Palette */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>palette</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              every plot uses <strong>imprint</strong>, our own colourblind-safe categorical palette —
              8 hues plus 3 semantic anchors, tuned for warm-paper rendering and validated against the
              three main forms of colour vision deficiency. it sits in the same neighbourhood as
              Okabe-Ito, Paul Tol&apos;s &ldquo;muted&rdquo;, and ColorBrewer Set2 — about 8% of men
              have some form of CVD, and most plotting libraries ignore this entirely. we make it
              the default.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              see the{' '}
              <Link
                href="/palette"
                onClick={() => trackEvent('internal_link', { destination: 'palette', source: 'about' })}
                sx={proseLinkStyle}
              >
                palette page
              </Link>{' '}
              for the full reference and usage rules.
            </Box>
          </Box>
        </Box>

        {/* Library agnostic */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>library-agnostic</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              a "gentoo penguin" is always blue, whether you draw it in matplotlib, plotly, or bokeh.
              the palette travels with you across libraries. switching tools doesn't mean re-learning
              your color grammar.
            </Box>
          </Box>
        </Box>

        {/* Origin */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>origin</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              it started as pyplots.ai, a small catalogue of python plotting examples built in a
              weekend. it grew when it became clear people wanted two things from a catalogue like
              this: inspiration for which plot fits their data, and a way to get to know libraries
              they hadn't used before — each has its own specialties. anyplot is the grown-up version,
              anchored in a colorblind-safe palette that travels across every library.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              built in Visp, a small town in the Swiss Alps, by a data scientist looking for one
              place to find the right plot for the data in front of him — and a way to explore
              what each library does best.
            </Box>
            <Box sx={{ ...textStyle, mt: 1 }}>
              curious about the stack, costs, or analytics? see{' '}
              <Link
                component={RouterLink}
                to="/legal#transparency"
                onClick={() => trackEvent('internal_link', { destination: 'legal_transparency', source: 'about' })}
                sx={proseLinkStyle}
              >
                transparency
              </Link>{' '}
              on the legal page.
            </Box>
          </Box>
        </Box>

        {/* Contribute */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>contribute</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              everything happens on GitHub — issues, releases, discussions. there's no separate forum,
              no signup, no account.
            </Box>
            <Box sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1.5,
              mt: 2,
              fontFamily: typography.mono,
            }}>
              <Link
                href={`${GITHUB_URL}/issues/new?labels=spec-request&title=%5Bplot+request%5D+`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent('external_link', { destination: 'github_plot_request', source: 'about' })}
                sx={ctaSx}
              >
                request_plot()
              </Link>
              <Link
                href={`${GITHUB_URL}/issues/new?labels=bug`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent('external_link', { destination: 'github_bug', source: 'about' })}
                sx={ctaSx}
              >
                report_bug()
              </Link>
              <Link
                href={`${GITHUB_URL}/discussions`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent('external_link', { destination: 'github_discussions', source: 'about' })}
                sx={ctaSx}
              >
                discuss()
              </Link>
              <Link
                href={`${GITHUB_URL}/releases`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent('external_link', { destination: 'github_releases', source: 'about' })}
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
