import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';

import { specPath } from 'src/routes/paths';

const visuallyHiddenSx = {
  position: 'absolute' as const,
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap' as const,
  border: 0,
};

export function MapA11yFallback({ specs }: { specs: { id: string; title: string }[] | null }) {
  return (
    <Box component="ul" sx={visuallyHiddenSx}>
      {(specs ?? []).map(s => (
        <li key={s.id}>
          <Link to={specPath(s.id)}>{s.title}</Link>
        </li>
      ))}
    </Box>
  );
}
