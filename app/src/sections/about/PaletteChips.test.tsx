import { describe, expect, it, vi } from 'vitest';

import { PaletteChips } from 'src/sections/about/PaletteChips';
import { render, screen, styleAt, within } from 'src/test-utils';
import { colors } from 'src/theme';

const theme = vi.hoisted(() => ({ isDark: false }));
vi.mock('src/hooks', () => ({ useTheme: () => theme }));

const swatchOf = (item: HTMLElement) => item.firstElementChild as HTMLElement;

describe('PaletteChips', () => {
  // The names are the palette page's; the hex values must be the theme's palette tokens, which
  // the plots and the palette page use, in slot order.
  it('shows the eight hues in the palette order, each with its name and hex', () => {
    theme.isDark = false;
    render(<PaletteChips />);

    const items = within(screen.getByRole('list')).getAllByRole('listitem');
    expect(items.map(item => item.textContent?.replace(/\s+/g, ' ').trim())).toEqual([
      'brand green #009E73',
      'lavender #C475FD',
      'blue #4467A3',
      'ochre #BD8233',
      'matte red #AE3030',
      'cyan #2ABCCD',
      'rose #954477',
      'lime #99B314',
    ]);
    const { green, lavender, blue, ochre, red, cyan, rose, lime } = colors.imprint;
    const tokens = [green, lavender, blue, ochre, red, cyan, rose, lime];
    expect(items.map(item => styleAt(swatchOf(item)).backgroundColor.toUpperCase())).toEqual(
      tokens.map(hex => {
        const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
        return `RGB(${r}, ${g}, ${b})`;
      })
    );
  });

  // The palette page's convention (WcagContrastSection): a hue under 3:1 against the page gets a
  // 1px ink stroke, so the chip's edge stays visible.
  it.each([
    [false, ['lavender', 'ochre', 'cyan', 'lime']],
    [true, ['matte red']],
  ])('strokes the chips under 3:1 against the page (dark: %s)', (isDark, stroked) => {
    theme.isDark = isDark;
    render(<PaletteChips />);

    const items = within(screen.getByRole('list')).getAllByRole('listitem');
    const withStroke = items
      .filter(item => {
        const style = styleAt(swatchOf(item));
        return (
          style.outlineWidth === '1px' &&
          style.outlineStyle === 'solid' &&
          style.outlineColor === 'var(--ink)'
        );
      })
      .map(item => item.textContent?.replace(/\s*#\w+$/, '').trim());
    expect(withStroke).toEqual(stroked);
  });
});
