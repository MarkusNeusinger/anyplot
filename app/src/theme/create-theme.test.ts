import { describe, expect, it } from 'vitest';

import { theme } from 'src/theme';
import { colors, typography } from 'src/theme/tokens';

describe('theme', () => {
  it('uses the MonoLisa font stack', () => {
    expect(theme.typography.fontFamily).toBe(typography.fontFamily);
  });

  it('uses the brand color as primary', () => {
    expect(theme.palette.primary.main).toBe(colors.primary);
  });

  it('keeps the editorial light palette values', () => {
    expect(theme.palette.mode).toBe('light');
    expect(theme.palette.background.default).toBe(colors.background);
    expect(theme.palette.text.primary).toBe(colors.gray[800]);
    expect(theme.palette.text.secondary).toBe(colors.gray[600]);
  });

  it('registers the CssBaseline and Tooltip overrides', () => {
    expect(theme.components?.MuiCssBaseline).toBeDefined();
    expect(theme.components?.MuiTooltip?.defaultProps?.placement).toBe('top');
    expect(theme.components?.MuiTooltip?.defaultProps?.enterDelay).toBe(200);
  });

  it('uses the 12px editorial corner radius', () => {
    expect(theme.shape.borderRadius).toBe(12);
  });
});
