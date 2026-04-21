import { useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { GITHUB_URL } from '../constants';
import { colors, typography, textStyle, codeBlockStyle } from '../theme';

const PIPELINE_BLOCK = `// pipeline
idea    → human-submitted        (github issue)
spec    → ai-drafted, human-approved
code    → ai-generated           (per library)
review  → ai-evaluated
fix     → ai-retries; humans tune rules`;

const subheadSx = {
  fontFamily: typography.mono,
  fontSize: '13px',
  fontWeight: 500,
  letterSpacing: '0.04em',
  color: 'var(--ink-muted)',
  textTransform: 'uppercase' as const,
  mt: 6,
  mb: 1.5,
};

const headingSx = {
  fontFamily: typography.serif,
  fontWeight: 400,
  fontSize: { xs: '1.5rem', sm: '1.75rem' },
  letterSpacing: '-0.02em',
  color: 'var(--ink)',
  m: 0,
  mb: 2,
  '& em': { color: colors.primary, fontStyle: 'italic', fontWeight: 300 },
};

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
          content="A catalogue of Python plotting examples across nine libraries. Plot ideas come from humans; AI drafts the spec, generates code for every library, and reviews each implementation."
        />
        <meta property="og:title" content="about | anyplot.ai" />
        <meta
          property="og:description"
          content="Humans submit ideas. AI drafts specs, generates code, reviews. Humans approve."
        />
        <link rel="canonical" href="https://anyplot.ai/about" />
      </Helmet>

      <Box sx={{ maxWidth: 'var(--max, 1240px)', mx: 'auto', pb: 6 }}>
        <SectionHeader prompt="§" title={<em>about</em>} />

        <Box sx={{ maxWidth: 760, mx: 'auto' }}>
          {/* Lede */}
          <Box sx={{ ...textStyle, fontSize: '18px', color: 'var(--ink)', fontWeight: 300 }}>
            A catalogue of plotting examples across nine Python libraries. Plot ideas come from humans;
            AI drafts the spec, generates code for every library, and reviews each implementation.
            Humans approve specs and tune the rules when something repeatedly fails. Every example uses
            the same colorblind-safe palette, so switching libraries never breaks your color grammar.
          </Box>

          {/* Pipeline */}
          <Box component="h2" sx={{ ...headingSx, mt: 7 }}>
            the <em>pipeline</em>
          </Box>
          <Box sx={textStyle}>
            Humans curate; AI executes. The catalogue maintains itself: when matplotlib ships a new release,
            we re-run the pipeline; when a better example pattern emerges, we update the spec and every
            library regenerates. We never patch generated code by hand.
          </Box>

          <Box sx={{ ...codeBlockStyle, whiteSpace: 'pre', fontSize: '13px', mt: 3 }}>
            {PIPELINE_BLOCK}
          </Box>

          {/* Palette */}
          <Box component="h2" sx={{ ...headingSx, mt: 7 }}>
            the <em>palette</em>
          </Box>
          <Box sx={textStyle}>
            Every plot uses the Okabe-Ito palette, peer-reviewed for colorblind safety and designed for
            scientific publications in 2008. About 8% of men have some form of color vision deficiency —
            most plotting libraries ignore this entirely. We make it the default.
          </Box>
          <Box sx={{ ...textStyle, mt: 1 }}>
            See the{' '}
            <Link
              href="/palette"
              onClick={() => trackEvent('internal_link', { destination: 'palette', source: 'about' })}
              sx={{ color: colors.primary }}
            >
              palette page
            </Link>{' '}
            for the full reference and usage rules.
          </Box>

          {/* Library agnostic */}
          <Box component="h2" sx={{ ...headingSx, mt: 7 }}>
            <em>library-agnostic</em> by design
          </Box>
          <Box sx={textStyle}>
            A "Gentoo penguin" is always blue, whether you draw it in matplotlib, plotly, or bokeh.
            The palette travels with you across libraries. Switching tools doesn't mean re-learning
            your color grammar.
          </Box>

          {/* Origin */}
          <Box component="h2" sx={{ ...headingSx, mt: 7 }}>
            <em>origin</em>
          </Box>
          <Box sx={textStyle}>
            It started as pyplots.ai, a small Python-only catalogue built in a weekend. It grew when
            it became clear people wanted the same examples across different libraries — and the same
            safe palette everywhere. anyplot is the grown-up version: broader in scope (beyond Python),
            broader in language (beyond English), and anchored in a colorblind-safe palette that travels
            across every library.
          </Box>
          <Box sx={{ ...textStyle, mt: 1 }}>
            Built in Visp, a small town in the Swiss Alps, by a data analyst who spent too many hours
            trying to figure out why the same chart looked different in seaborn than in plotly.
          </Box>

          <Box sx={{ ...textStyle, mt: 1 }}>
            Curious about the stack, costs, or analytics? See{' '}
            <Link
              component={RouterLink}
              to="/legal#transparency"
              onClick={() => trackEvent('internal_link', { destination: 'legal_transparency', source: 'about' })}
              sx={{ color: colors.primary }}
            >
              transparency
            </Link>{' '}
            on the legal page.
          </Box>

          {/* Contribute */}
          <Box sx={subheadSx}>contribute</Box>
          <Box sx={textStyle}>
            Everything happens on GitHub — issues, releases, discussions. There's no separate forum,
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
    </>
  );
}
