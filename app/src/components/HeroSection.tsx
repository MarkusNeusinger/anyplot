import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import { colors, typography } from '../theme';
import { API_URL } from '../constants';
import { specPath } from '../utils/paths';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';

interface HeroSectionProps {
  stats: { specs: number; plots: number; libraries: number } | null;
}

interface PlotOfTheDayData {
  spec_id: string;
  spec_title: string;
  library_id: string;
  library_name: string;
  preview_url: string | null;
}

export function HeroSection({ stats }: HeroSectionProps) {
  const [potd, setPotd] = useState<PlotOfTheDayData | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/insights/plot-of-the-day`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setPotd)
      .catch(() => {});
  }, []);

  return (
    <Box sx={{
      maxWidth: 'var(--max)',
      mx: 'auto',
      py: { xs: 6, md: 10 },
      display: 'grid',
      gridTemplateColumns: { xs: '1fr', md: '1.1fr 1fr' },
      gap: { xs: 5, md: 9 },
      alignItems: 'center',
    }}>
      {/* Left column: text */}
      <Box>
        {/* Eyebrow */}
        <Box sx={{
          animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) backwards',
          fontFamily: typography.mono,
          fontSize: '11px',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          color: colors.primary,
          mb: 3,
          display: 'flex',
          alignItems: 'center',
          gap: 1.25,
          '&::before': {
            content: '""',
            display: 'inline-block',
            width: 18,
            height: '1px',
            background: colors.primary,
          },
        }}>
          Data Visualization Catalogue
        </Box>

        {/* Display headline */}
        <Box component="h1" sx={{
          animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.1s backwards',
          fontFamily: typography.serif,
          fontWeight: 400,
          fontSize: { xs: '2.5rem', sm: '3.5rem', md: 'clamp(3rem, 7vw, 6rem)' },
          lineHeight: 0.95,
          letterSpacing: '-0.03em',
          color: 'var(--ink)',
          m: 0,
          mb: 4,
        }}>
          <Box component="span" sx={{ fontFamily: typography.mono, fontWeight: 700, fontSize: '0.75em', letterSpacing: '-0.02em' }}>
            any<Box component="span" sx={{ color: colors.primary, display: 'inline-block', transform: 'scale(1.3)', mx: '2px' }}>.</Box>plot<Box component="span" sx={{ fontWeight: 400, opacity: 0.45 }}>()</Box>
          </Box>
          <br />
          <Box component="span" sx={{ fontFamily: typography.serif, fontWeight: 400, letterSpacing: '-0.03em' }}>
            — any library.
          </Box>
        </Box>

        {/* Lede */}
        <Box sx={{
          animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.2s backwards',
          fontFamily: typography.serif,
          fontSize: { xs: '1rem', md: '1.25rem' },
          lineHeight: 1.45,
          color: 'var(--ink-soft)',
          maxWidth: '52ch',
          mb: 5,
          fontWeight: 300,
        }}>
          A curated catalogue of visualization examples — AI-generated, open source, and built for every library you already use.
        </Box>

        {/* Tagline — prominent */}
        <Box sx={{
          animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.25s backwards',
          fontFamily: typography.serif,
          fontSize: { xs: '1.125rem', md: '1.5rem' },
          lineHeight: 1.3,
          color: 'var(--ink)',
          maxWidth: '52ch',
          mb: 5,
          fontWeight: 400,
          fontStyle: 'italic',
        }}>
          Get inspired. Grab the code. Make it yours.
        </Box>

        {/* CTAs */}
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.3s backwards' }}>
          <Box
            component={RouterLink}
            to="/plots"
            sx={{
              textDecoration: 'none',
              boxSizing: 'border-box',
              fontFamily: typography.mono,
              fontSize: '13px',
              padding: '13px 22px',
              borderRadius: '99px',
              border: '1px solid transparent',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1.25,
              bgcolor: 'var(--ink)',
              color: 'var(--bg-page)',
              transition: 'all 0.2s',
              '&:hover': {
                bgcolor: colors.primary,
                color: '#FFF',
              },
              '&:focus-visible': {
                outline: `2px solid ${colors.primary}`,
                outlineOffset: 2,
              },
            }}
          >
            Browse the catalogue <Box component="span" sx={{ transition: 'transform 0.2s' }}>→</Box>
          </Box>
          <Box
            component={RouterLink}
            to="/mcp"
            sx={{
              textDecoration: 'none',
              boxSizing: 'border-box',
              fontFamily: typography.mono,
              fontSize: '13px',
              padding: '13px 22px',
              borderRadius: '99px',
              border: '1px solid var(--rule)',
              cursor: 'pointer',
              color: 'var(--ink)',
              transition: 'all 0.2s',
              '&:hover': { borderColor: 'var(--ink)' },
            }}
          >
            use via MCP
          </Box>
        </Box>

        {/* Meta stats */}
        {stats && (
          <Box sx={{
            mt: 6,
            pt: 3,
            borderTop: '1px solid var(--rule)',
            display: 'flex',
            gap: 5,
            flexWrap: 'wrap',
            fontFamily: typography.mono,
            fontSize: '11px',
            color: 'var(--ink-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}>
            {[
              { value: String(stats.specs), label: 'specs' },
              { value: stats.plots.toLocaleString(), label: 'implementations' },
              { value: String(stats.libraries), label: 'libraries' },
            ].map((item, i) => (
              <Box key={i}>
                <Box sx={{
                  color: 'var(--ink)',
                  fontWeight: 500,
                  fontSize: { xs: '1.25rem', md: '1.75rem' },
                  letterSpacing: '-0.02em',
                  textTransform: 'none',
                  mb: 0.5,
                  fontFamily: typography.serif,
                }}>
                  {item.value}
                </Box>
                {item.label}
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* Right column: Plot of the Day */}
      {potd?.preview_url && (
        <Box sx={{
          animation: 'rise 1s cubic-bezier(0.2, 0.8, 0.2, 1) 0.3s backwards',
          bgcolor: 'var(--bg-surface)',
          border: '1px solid var(--rule)',
          borderRadius: '12px',
          p: 3.5,
          position: 'relative',
          boxShadow: '0 1px 2px rgba(0,0,0,0.02), 0 24px 48px -24px rgba(0,0,0,0.08)',
        }}>
          {/* Card header */}
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2.5,
            fontFamily: typography.mono,
            fontSize: '12px',
            color: 'var(--ink-muted)',
          }}>
            <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
              <Box sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                bgcolor: colors.primary,
                boxShadow: '0 0 0 3px rgba(0,158,115,0.15)',
              }} />
              plot of the day
            </Box>
            <Link
              component={RouterLink}
              to={specPath(potd.spec_id, potd.library_id)}
              sx={{
                fontFamily: typography.mono,
                fontSize: '12px',
                color: 'var(--ink-muted)',
                textDecoration: 'none',
                '&:hover': { color: colors.primary },
              }}
            >
              ↗ open
            </Link>
          </Box>

          {/* Image */}
          <Link
            component={RouterLink}
            to={specPath(potd.spec_id, potd.library_id)}
            sx={{ display: 'block', textDecoration: 'none' }}
          >
            <Box component="picture">
              <source type="image/webp" srcSet={buildSrcSet(potd.preview_url, 'webp')} sizes="(max-width: 899px) 80vw, 500px" />
              <source type="image/png" srcSet={buildSrcSet(potd.preview_url, 'png')} sizes="(max-width: 899px) 80vw, 500px" />
              <Box
                component="img"
                src={getFallbackSrc(potd.preview_url)}
                alt={`${potd.spec_title} — ${potd.library_name}`}
                sx={{ width: '100%', display: 'block', borderRadius: '8px' }}
              />
            </Box>
          </Link>

          {/* Card footer */}
          <Box sx={{
            mt: 2.5,
            pt: 2,
            borderTop: '1px dashed var(--rule)',
            fontFamily: typography.mono,
            fontSize: '11px',
            color: 'var(--ink-muted)',
            display: 'flex',
            justifyContent: 'space-between',
          }}>
            <span>{potd.spec_title}</span>
            <span>{potd.library_name}</span>
          </Box>
        </Box>
      )}
    </Box>
  );
}
