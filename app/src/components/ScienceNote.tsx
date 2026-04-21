import Box from '@mui/material/Box';
import { Link as RouterLink } from 'react-router-dom';
import { colors, typography } from '../theme';
import { PaletteStrip } from './PaletteStrip';

export function ScienceNote() {
  return (
    <Box sx={{
      bgcolor: 'var(--bg-surface)',
      borderTop: '1px solid var(--rule)',
      borderBottom: '1px solid var(--rule)',
      py: { xs: 4, md: 7 },
      px: 3,
    }}>
      <Box sx={{ maxWidth: 760, mx: 'auto', textAlign: 'center' }}>
        <Box sx={{
          fontFamily: typography.mono,
          fontSize: '11px',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          color: colors.primary,
          mb: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1.25,
          '&::before': {
            content: '""',
            display: 'inline-block',
            width: 18,
            height: '1px',
            background: colors.primary,
          },
        }}>
          § 03 · On the palette
        </Box>

        <Box component="h3" sx={{
          fontFamily: typography.serif,
          fontSize: { xs: '1.5rem', md: 'clamp(1.75rem, 3.5vw, 2.625rem)' },
          fontWeight: 400,
          lineHeight: 1.2,
          letterSpacing: '-0.02em',
          mb: 3,
          color: 'var(--ink)',
          '& em': { fontStyle: 'italic', color: colors.primary },
        }}>
          Colors that <em>everyone</em> can see.
        </Box>

        <Box component="blockquote" sx={{
          fontFamily: typography.serif,
          fontSize: { xs: '0.9375rem', md: '1.0625rem' },
          lineHeight: 1.6,
          color: 'var(--ink-soft)',
          fontWeight: 300,
          px: 2.5,
          m: 0,
        }}>
          "We proposed a set of colors optimized for colorblind and colorweak individuals,
          with the expectation that their use will broaden the accessibility
          of figures in scientific papers."
        </Box>

        <Box component="cite" sx={{
          display: 'block',
          fontFamily: typography.mono,
          fontSize: '11px',
          color: 'var(--ink-muted)',
          mt: 3,
          fontStyle: 'normal',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
        }}>
          — Okabe & Ito, 2008
        </Box>

        <PaletteStrip />

        <Box
          component={RouterLink}
          to="/palette"
          sx={{
            display: 'inline-block',
            mt: 3,
            fontFamily: typography.mono,
            fontSize: '12px',
            color: 'var(--ink-soft)',
            textDecoration: 'none',
            transition: 'color 0.2s',
            '&:hover': { color: colors.primary },
          }}
        >
          palette.explore()
        </Box>
      </Box>
    </Box>
  );
}
