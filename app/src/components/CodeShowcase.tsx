import Box from '@mui/material/Box';
import { SectionHeader } from './SectionHeader';
import { typography } from '../theme';

export function CodeShowcase() {
  return (
    <Box sx={{ maxWidth: 'var(--max)', mx: 'auto', py: { xs: 2, md: 3 } }}>
      <SectionHeader
        prompt="❯"
        title={<>One <em>import</em>.</>}
      />

      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '1fr 1.1fr' },
        gap: 6,
        alignItems: 'center',
      }}>
        {/* Left: description */}
        <Box>
          <Box component="h3" sx={{
            fontFamily: typography.serif,
            fontSize: { xs: '1.5rem', md: 'clamp(2rem, 4vw, 3rem)' },
            fontWeight: 400,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            mb: 3,
            m: 0,
            color: 'var(--ink)',
            '& em': { fontStyle: 'italic', color: 'var(--ok-green)' },
          }}>
            Same palette,<br /><em>every library</em>.
          </Box>
          <Box sx={{
            fontFamily: typography.serif,
            fontWeight: 300,
            fontSize: '1.125rem',
            lineHeight: 1.5,
            color: 'var(--ink-soft)',
            mb: 2.5,
          }}>
            every example in the catalogue uses the same Okabe-Ito palette. switch libraries
            without losing your color grammar — a <em style={{ fontStyle: 'italic' }}>gentoo penguin</em> is always blue,
            whether you draw it in matplotlib or plotly.
          </Box>
          <Box sx={{
            fontFamily: typography.mono,
            fontSize: '13px',
            color: 'var(--ink-muted)',
          }}>
            validated against deuteranopia, protanopia and tritanopia using the Machado et al. (2009) simulation model.
          </Box>
        </Box>

        {/* Right: code block — terminal showcase, intentionally dark in both themes
            so the macOS-style window dots and drop shadow stay coherent. */}
        <Box sx={{
          background: '#1A1A17',
          color: '#E8E8E0',
          p: { xs: 2.5, md: '28px 32px' },
          borderRadius: '12px',
          fontFamily: typography.mono,
          fontSize: '14px',
          lineHeight: 1.7,
          overflowX: 'auto',
          position: 'relative',
          boxShadow: '0 24px 48px -16px rgba(0,0,0,0.2)',
          '&::before': {
            content: '"● ● ●"',
            position: 'absolute',
            top: 12,
            left: 16,
            color: '#2A2A27',
            fontSize: '10px',
            letterSpacing: '4px',
          },
        }}>
          <Box component="pre" sx={{ mt: 3, m: 0, whiteSpace: 'pre' }}>
            <Box component="span" sx={{ color: '#666', fontStyle: 'italic' }}>
              {'# pick any library. the palette travels with you.\n'}
            </Box>
            <Box component="span" sx={{ color: '#56B4E9' }}>import</Box>{' anyplot '}
            <Box component="span" sx={{ color: '#56B4E9' }}>as</Box>{' ap\n\n'}
            {'data = ap.'}
            <Box component="span" sx={{ color: '#E69F00' }}>load</Box>
            {'('}
            <Box component="span" sx={{ color: '#009E73' }}>"penguins"</Box>
            {')\n\n'}
            <Box component="span" sx={{ color: '#666', fontStyle: 'italic' }}>
              {'# matplotlib\n'}
            </Box>
            {'ap.'}
            <Box component="span" sx={{ color: '#E69F00' }}>mpl</Box>
            {'.'}
            <Box component="span" sx={{ color: '#E69F00' }}>scatter</Box>
            {'(data, x='}
            <Box component="span" sx={{ color: '#009E73' }}>"bill"</Box>
            {', y='}
            <Box component="span" sx={{ color: '#009E73' }}>"flipper"</Box>
            {',\n               hue='}
            <Box component="span" sx={{ color: '#009E73' }}>"species"</Box>
            {')\n\n'}
            <Box component="span" sx={{ color: '#666', fontStyle: 'italic' }}>
              {'# plotly — same colors, interactive\n'}
            </Box>
            {'ap.'}
            <Box component="span" sx={{ color: '#E69F00' }}>plotly</Box>
            {'.'}
            <Box component="span" sx={{ color: '#E69F00' }}>scatter</Box>
            {'(data, x='}
            <Box component="span" sx={{ color: '#009E73' }}>"bill"</Box>
            {', y='}
            <Box component="span" sx={{ color: '#009E73' }}>"flipper"</Box>
            {',\n                  hue='}
            <Box component="span" sx={{ color: '#009E73' }}>"species"</Box>
            {')'}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
