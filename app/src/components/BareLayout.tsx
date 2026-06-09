import { Outlet } from 'react-router-dom';

import Box from '@mui/material/Box';

/**
 * Layout for routes that opt out of the global chrome — interactive plot
 * embeds, debug surfaces. Pages own their full viewport.
 */
export function BareLayout() {
  return (
    <Box sx={{ minHeight: '100svh', bgcolor: 'var(--bg-page)' }}>
      <Outlet />
    </Box>
  );
}
