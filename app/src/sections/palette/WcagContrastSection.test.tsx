import { describe, expect, it } from 'vitest';

import { WcagContrastSection } from 'src/sections/palette/WcagContrastSection';
import { render, screen } from 'src/test-utils';

// jsdom drops a `border` that contains `var(...)` from the computed style, so
// read the border the swatch's own stylesheet rule declares instead.
function declaredSwatchBorder(hex: string): string | undefined {
  const swatch = screen.getByRole('cell', { name: hex }).firstElementChild;
  if (!(swatch instanceof HTMLElement)) return undefined;
  const borders = Array.from(document.styleSheets)
    .flatMap(sheet => Array.from(sheet.cssRules))
    .filter((rule): rule is CSSStyleRule => rule instanceof CSSStyleRule)
    .filter(rule => swatch.matches(rule.selectorText))
    .map(rule => rule.style.getPropertyValue('border'))
    .filter(Boolean);
  return borders[borders.length - 1];
}

describe('WcagContrastSection', () => {
  it('renders the WCAG contrast table with pass (✓) and fail (✗) ratios on cream and on dark', () => {
    render(<WcagContrastSection isDark={false} />);

    expect(screen.getByRole('heading', { name: /WCAG contrast/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'on cream' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'on dark' })).toBeInTheDocument();

    // Brand green passes both; matte red passes cream, fails dark; lavender fails cream, passes dark
    expect(screen.getByText('3.08:1 ✓')).toBeInTheDocument();
    expect(screen.getByText('5.48:1 ✓')).toBeInTheDocument();
    expect(screen.getByText('5.79:1 ✓')).toBeInTheDocument();
    expect(screen.getByText('2.92:1 ✗')).toBeInTheDocument();
    expect(screen.getByText('2.59:1 ✗')).toBeInTheDocument();
    expect(screen.getByText('6.53:1 ✓')).toBeInTheDocument();
    expect(screen.getByText('1.46:1 ✗')).toBeInTheDocument();
    expect(screen.getByText('11.59:1 ✓')).toBeInTheDocument();
  });

  it('names each row by hex and palette name', () => {
    render(<WcagContrastSection isDark={false} />);

    expect(screen.getByRole('cell', { name: '#C475FD' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'lavender' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '#AE3030' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'matte-red' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '#DDCC77' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'amber' })).toBeInTheDocument();
  });

  it('strokes the swatches that fail on the current background with --ink', () => {
    const { rerender } = render(<WcagContrastSection isDark={false} />);
    // On cream, lavender fails and matte red passes.
    expect(declaredSwatchBorder('#C475FD')).toBe('1px solid var(--ink)');
    expect(declaredSwatchBorder('#AE3030')).toBe('1px solid var(--rule)');

    rerender(<WcagContrastSection isDark />);
    // On dark, the two swap.
    expect(declaredSwatchBorder('#C475FD')).toBe('1px solid var(--rule)');
    expect(declaredSwatchBorder('#AE3030')).toBe('1px solid var(--ink)');
  });
});
