import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import { GITHUB_URL } from '../constants';

interface FooterProps {
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
  selectedSpec?: string;
  selectedLibrary?: string;
}

export function Footer({ onTrackEvent, selectedSpec, selectedLibrary }: FooterProps) {
  return (
    <Box component="footer" sx={{ textAlign: 'center', mt: 4, pt: 4, borderTop: '1px solid #f3f4f6' }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 1,
          fontSize: '0.8rem',
          fontFamily: '"MonoLisa", "MonoLisa Fallback", monospace',
          color: '#9ca3af',
        }}
      >
        <Link
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => onTrackEvent?.('external_link', { destination: 'github', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: '#9ca3af',
            textDecoration: 'none',
            '&:hover': { color: '#6b7280' },
          }}
        >
          github
        </Link>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/stats"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'stats', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: '#9ca3af',
            textDecoration: 'none',
            '&:hover': { color: '#6b7280' },
          }}
        >
          stats
        </Link>
        <Box component="span" sx={{ display: { xs: 'none', md: 'contents' } }}>
          <span>·</span>
          <Link
            href="https://www.linkedin.com/in/markus-neusinger/"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => onTrackEvent?.('external_link', { destination: 'linkedin', spec: selectedSpec, library: selectedLibrary })}
            sx={{
              color: '#9ca3af',
              textDecoration: 'none',
              '&:hover': { color: '#6b7280' },
            }}
          >
            markus neusinger
          </Link>
        </Box>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/mcp"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'mcp', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: '#9ca3af',
            textDecoration: 'none',
            '&:hover': { color: '#6b7280' },
          }}
        >
          mcp
        </Link>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/legal"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'legal', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: '#9ca3af',
            textDecoration: 'none',
            '&:hover': { color: '#6b7280' },
          }}
        >
          legal
        </Link>
      </Box>
    </Box>
  );
}
