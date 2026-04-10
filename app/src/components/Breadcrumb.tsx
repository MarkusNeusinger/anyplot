/**
 * Shared Breadcrumb component for consistent navigation across pages.
 */

import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import type { SxProps, Theme } from '@mui/material/styles';
import { colors, fontSize, semanticColors, typography } from '../theme';

export interface BreadcrumbItem {
  label: string;
  shortLabel?: string; // Shown on mobile (xs) if provided
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
 * // With short labels for mobile
 * <Breadcrumb items={[
 *   { label: 'pyplots.ai', to: '/' },
 *   { label: 'scatter-basic', to: '/scatter-basic' },
 *   { label: 'matplotlib', shortLabel: 'mpl' },
 * ]} />
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
        bgcolor: colors.gray[100],
        borderBottom: `1px solid ${colors.gray[200]}`,
        fontFamily: typography.fontFamily,
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
                  color: colors.primary,
                  textDecoration: 'none',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {item.shortLabel ? (
                  <>
                    <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>{item.label}</Box>
                    <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>{item.shortLabel}</Box>
                  </>
                ) : item.label}
              </Box>
            ) : (
              <Box component="span" sx={{ color: colors.gray[700] }}>
                {item.shortLabel ? (
                  <>
                    <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>{item.label}</Box>
                    <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>{item.shortLabel}</Box>
                  </>
                ) : item.label}
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
