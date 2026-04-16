import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import { Link } from 'react-router-dom';

import { MastheadRule } from '../components/MastheadRule';
import { NavBar } from '../components/NavBar';
import { HeroSection } from '../components/HeroSection';
import { LibrariesSection } from '../components/LibrariesSection';
import { SectionHeader } from '../components/SectionHeader';
import { Footer } from '../components/Footer';
import { useAppData } from '../hooks';
import { useAnalytics } from '../hooks';
import { GITHUB_URL } from '../constants';
import { colors } from '../theme';

export function LandingPage() {
  const { librariesData, stats } = useAppData();
  const { trackEvent } = useAnalytics();

  return (
    <>
      <Helmet>
        <title>anyplot.ai — any library. one plot.</title>
        <meta name="description" content="library-agnostic, ai-powered visualization examples. get inspired. grab the code. make it yours. 9 libraries, colorblind-safe, open source." />
        <link rel="canonical" href="https://anyplot.ai/" />
      </Helmet>

      <Box sx={{ minHeight: '100vh', bgcolor: 'var(--bg-page)' }}>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 4, md: 8, lg: 12 }, maxWidth: 1400, mx: 'auto' }}>
      <MastheadRule />
      <NavBar />

      <HeroSection stats={stats} />

      {/* § 01 Languages */}
      <Box sx={{ maxWidth: 'var(--max)', mx: 'auto', py: { xs: 6, md: 10 } }}>
        <SectionHeader number="§ 01" title={<><em>Languages</em></>} />

        <Box sx={{ display: 'flex', gap: 2.5, flexWrap: 'wrap' }}>
          <Box
            component={Link}
            to="/plots"
            sx={{
              textDecoration: 'none',
              fontFamily: 'var(--mono)', fontSize: '15px', fontWeight: 700,
              color: 'var(--ink)', bgcolor: 'var(--bg-surface)',
              border: `2px solid ${colors.primary}`,
              borderRadius: '12px', px: 3, py: 2,
              display: 'flex', alignItems: 'center', gap: 1.5,
              transition: 'all 0.2s',
              '&:hover': { bgcolor: 'var(--bg-elevated)' },
            }}
          >
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: colors.primary }} />
            Python
            <Box component="span" sx={{ fontWeight: 400, fontSize: '11px', color: 'var(--ink-muted)', ml: 1 }}>
              {stats ? `${stats.specs} specs` : ''}
            </Box>
          </Box>
          <Box sx={{
            fontFamily: 'var(--mono)', fontSize: '13px',
            color: 'var(--ink-muted)',
            border: '1px dashed var(--rule)',
            borderRadius: '12px', px: 3, py: 2,
            display: 'flex', alignItems: 'center',
            fontStyle: 'italic',
          }}>
            more languages coming
          </Box>
        </Box>
      </Box>

      {/* § 02 Libraries */}
      <LibrariesSection libraries={librariesData} onLibraryClick={() => {}} />

      {/* § 03 Specifications */}
      <Box sx={{ maxWidth: 'var(--max)', mx: 'auto', py: { xs: 6, md: 10 } }}>
        <SectionHeader
          number="§ 03"
          title={<><em>Specifications</em></>}
          linkText="view all"
          linkTo="/specs"
        />

        <Box sx={{
          fontFamily: 'var(--serif)', fontWeight: 300,
          fontSize: { xs: '0.9375rem', md: '1.0625rem' },
          color: 'var(--ink-soft)', lineHeight: 1.6, maxWidth: '65ch', mb: 4,
        }}>
          Every plot starts as a library-agnostic specification. AI generates implementations for all supported libraries, reviews quality, and maintains the code.
        </Box>

        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
          <Box
            component={Link}
            to="/specs"
            sx={{
              fontFamily: 'var(--mono)', fontSize: '13px',
              padding: '10px 18px', borderRadius: '99px',
              border: '1px solid var(--rule)', color: 'var(--ink)',
              textDecoration: 'none', transition: 'all 0.2s',
              '&:hover': { borderColor: 'var(--ink)' },
            }}
          >
            browse all {stats ? stats.specs : ''} specifications →
          </Box>
          <Box
            component="a"
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              fontFamily: 'var(--mono)', fontSize: '13px',
              padding: '10px 18px', borderRadius: '99px',
              border: '1px solid var(--rule)', color: 'var(--ink-muted)',
              textDecoration: 'none', transition: 'all 0.2s',
              '&:hover': { borderColor: 'var(--ink-soft)', color: 'var(--ink-soft)' },
            }}
          >
            open source on github ↗
          </Box>
        </Box>
      </Box>

      <Footer onTrackEvent={trackEvent} />
      </Container>
      </Box>
    </>
  );
}
