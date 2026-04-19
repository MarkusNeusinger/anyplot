import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import { Link as RouterLink } from 'react-router-dom';

import { MastheadRule } from '../components/MastheadRule';
import { NavBar } from '../components/NavBar';
import { HeroSection } from '../components/HeroSection';
import { NumbersStrip } from '../components/NumbersStrip';
import { LibrariesSection } from '../components/LibrariesSection';
import { SectionHeader } from '../components/SectionHeader';
import { Footer } from '../components/Footer';
import { useAppData, useAnalytics } from '../hooks';
import { usePlotOfTheDay } from '../hooks/usePlotOfTheDay';
import { GITHUB_URL } from '../constants';
import { colors, typography } from '../theme';

export function LandingPage() {
  const { librariesData, stats } = useAppData();
  const { trackEvent } = useAnalytics();
  const potd = usePlotOfTheDay();

  // Every section on the landing page lives on the catalog tier so the grid
  // stays consistent from hero to footer on ultrawide displays.
  const catalogContainerSx = {
    px: { xs: 2, sm: 4, md: 8, lg: 12 },
    maxWidth: 'var(--max-catalog)',
    mx: 'auto',
  } as const;

  return (
    <>
      <Helmet>
        <title>any.plot() — any library.</title>
        <meta
          name="description"
          content="any library. get inspired. grab the code. make it yours. human ideas, ai builds the rest. 9 python plotting libraries, colorblind-safe, open source."
        />
        <link rel="canonical" href="https://anyplot.ai/" />
      </Helmet>

      <Box sx={{ minHeight: '100vh', bgcolor: 'var(--bg-page)' }}>
        <Container maxWidth={false} sx={catalogContainerSx}>
          <MastheadRule />
          <NavBar />
        </Container>

        {/* Hero — fills the viewport so the fold shows only the hero */}
        <Box
          component="section"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            minHeight: { xs: 'auto', md: 'calc(88svh - 88px)' },
          }}
        >
          <Container maxWidth={false} sx={catalogContainerSx}>
            <HeroSection potd={potd} />
            <NumbersStrip stats={stats} />
          </Container>
        </Box>

        <Container maxWidth={false} sx={catalogContainerSx}>
          <LibrariesSection
            libraries={librariesData}
            onLibraryClick={() => {}}
            widthTier="catalog"
            headerStyle="prompt"
          />
        </Container>

        <Container maxWidth={false} sx={catalogContainerSx}>
          <SpecsSection specCount={stats?.specs} />
        </Container>

        <Container maxWidth={false} sx={catalogContainerSx}>
          <Footer onTrackEvent={trackEvent} />
        </Container>
      </Box>
    </>
  );
}

/**
 * Specs section — catalog-tier layout. On narrow screens it stacks; on wide
 * screens the prompt/title sits left and the narrative + action chips sit
 * right, so the section doesn't leave a rectangle of whitespace on 2200px.
 */
function SpecsSection({ specCount }: { specCount?: number }) {
  return (
    <Box sx={{ py: { xs: 6, md: 10 } }}>
      <SectionHeader prompt="$" title={<em>specs</em>} linkText="view all" linkTo="/specs" />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(0, 1.2fr)' },
          gap: { xs: 4, md: 8, lg: 12 },
          alignItems: 'start',
        }}
      >
        <Box
          sx={{
            fontFamily: typography.serif,
            fontSize: { xs: '1rem', md: '1.25rem' },
            lineHeight: 1.55,
            color: 'var(--ink-soft)',
            fontWeight: 300,
            maxWidth: '52ch',
          }}
        >
          Every plot lives as a library-agnostic markdown spec.{' '}
          <Box component="span" sx={{ color: 'var(--ink)' }}>
            One source, nine libraries.
          </Box>{' '}
          Drafted by AI from a human idea, approved before any code is
          generated — so the intent stays with the humans.
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            fontFamily: typography.mono,
          }}
        >
          <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', mb: 1 }}>
            // spec pipeline
          </Box>
          {[
            ['idea   ', 'human-submitted'],
            ['spec   ', 'ai-drafted, human-approved'],
            ['code   ', 'ai-generated'],
            ['review ', 'ai-evaluated'],
          ].map(([k, v]) => (
            <Box
              key={k}
              sx={{
                display: 'flex',
                gap: 1.5,
                fontSize: '13px',
                lineHeight: 1.6,
              }}
            >
              <Box component="span" sx={{ color: 'var(--ink)', whiteSpace: 'pre' }}>
                {k}
              </Box>
              <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
                →
              </Box>
              <Box component="span" sx={{ color: 'var(--ink-soft)' }}>
                {v}
              </Box>
            </Box>
          ))}

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
            <ActionChip to="/specs" label={`browse ${specCount ?? ''} specs`.trim()} />
            <ActionChip href={GITHUB_URL} label="github" external />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

interface ActionChipProps {
  to?: string;
  href?: string;
  label: string;
  external?: boolean;
}

function ActionChip({ to, href, label, external }: ActionChipProps) {
  const sx = {
    fontFamily: typography.mono,
    fontSize: '13px',
    fontWeight: 500,
    color: 'var(--ink-muted)',
    bgcolor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    px: 1.25,
    py: 1,
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'baseline',
    transition: 'color 0.2s, background 0.2s',
    '&:hover': { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
    '&::before': { content: '"."', color: 'inherit' },
  } as const;

  if (href) {
    return (
      <Box
        component="a"
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
        sx={sx}
      >
        {label}()
      </Box>
    );
  }
  return (
    <Box component={RouterLink} to={to ?? '#'} sx={sx}>
      {label}()
    </Box>
  );
}
