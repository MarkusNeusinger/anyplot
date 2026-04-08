/**
 * Shared Breadcrumb component for consistent navigation across pages.
 */

import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import type { SxProps, Theme } from '@mui/material/styles';
import { fontSize, semanticColors } from '../theme';

export interface BreadcrumbItem {
  label: string;
  to?: string; // If undefined, this is the current page (not linked)
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  rightAction?: React.ReactNode;
  /** Additional sx props for the container */
  sx?: SxProps<Theme>;
}

/**
 * Breadcrumb navigation component.
 *
 * @example
 * // Simple: pyplots.ai > catalog
 * <Breadcrumb items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]} />
 *
 * @example
 * // With right action
 * <Breadcrumb
 *   items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]}
 *   rightAction={<Link to="/suggest">suggest spec</Link>}
 * />
 */
export function Breadcrumb({ items, rightAction, sx }: BreadcrumbProps) {
  return (
    <Box
      component="nav"
      aria-label="breadcrumb"
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        mx: { xs: -2, sm: -4, md: -8, lg: -12 },
        mt: -5,
        px: 2,
        py: 1,
        mb: 2,
        bgcolor: '#f3f4f6',
        borderBottom: '1px solid #e5e7eb',
        fontFamily: '"MonoLisa", monospace',
        fontSize: fontSize.base,
        ...sx,
      }}
    >
      {/* Breadcrumb links */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {items.map((item, index) => (
          <Box key={index} sx={{ display: 'flex', alignItems: 'center' }}>
            {index > 0 && (
              <Box component="span" sx={{ mx: 1, color: semanticColors.mutedText }}>
                ›
              </Box>
            )}
            {item.to ? (
              <Box
                component={Link}
                to={item.to}
                sx={{
                  color: '#3776AB',
                  textDecoration: 'none',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {item.label}
              </Box>
            ) : (
              <Box component="span" sx={{ color: '#374151' }}>
                {item.label}
              </Box>
            )}
          </Box>
        ))}
      </Box>

      {/* Right action slot */}
      {rightAction}
    </Box>
  );
}
