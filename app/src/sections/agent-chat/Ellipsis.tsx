/**
 * The `…` of a line that says the page is working (`summarizing your data …`,
 * `# parsing your data …`), with a quiet opacity pulse: a plain indicator, no
 * spinner (docs/reference/style-guide.md §10.1). Hidden from screen readers,
 * which hear the words of the line; still under `prefers-reduced-motion`.
 */

import Box from '@mui/material/Box';

export function Ellipsis() {
  return (
    <Box
      component="span"
      aria-hidden
      sx={{
        '@keyframes agentPulse': { '0%, 100%': { opacity: 0.25 }, '50%': { opacity: 1 } },
        animation: 'agentPulse 1.6s ease-in-out infinite',
        '@media (prefers-reduced-motion: reduce)': { animation: 'none', opacity: 1 },
      }}
    >
      …
    </Box>
  );
}
