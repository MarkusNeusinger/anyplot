import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import Typography from '@mui/material/Typography';

import { parseInlineCode } from 'src/sections/spec-detail/SpecTabs/utils';
import { semanticColors, typography } from 'src/theme';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number | null;
}

export function TabPanel({ children, value, index }: TabPanelProps) {
  const isOpen = value === index;
  return (
    <Collapse in={isOpen}>
      <Box role="tabpanel" sx={{ pt: 2 }}>
        {children}
      </Box>
    </Collapse>
  );
}

// Clean heading without markdown syntax
export function MdHeading({ level, children }: { level: 1 | 2; children: React.ReactNode }) {
  return (
    <Typography
      component={level === 1 ? 'h1' : 'h2'}
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: level === 1 ? '1rem' : '0.8rem',
        fontWeight: 600,
        color: level === 1 ? 'var(--ink)' : semanticColors.mutedText,
        textTransform: level === 2 ? 'uppercase' : 'none',
        letterSpacing: level === 2 ? '0.05em' : 'normal',
        mt: level === 1 ? 0 : 2.5,
        mb: 1,
      }}
    >
      {children}
    </Typography>
  );
}

// Clean bullet list item
export function MdListItem({ children }: { children: string }) {
  return (
    <Typography
      component="li"
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: '0.85rem',
        color: semanticColors.labelText,
        lineHeight: 1.7,
        ml: 2,
        mb: 0.25,
        '&::marker': {
          color: 'var(--ink-muted)',
        },
      }}
    >
      {parseInlineCode(children)}
    </Typography>
  );
}
