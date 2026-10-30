import { describe, expect, it } from 'vitest';

import { WcagContrastSection } from 'src/sections/palette/WcagContrastSection';
import { render, screen } from 'src/test-utils';

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
  });

  it('renders both light and dark theme variants across all nine palette and anchor rows', () => {
    const { rerender } = render(<WcagContrastSection isDark={false} />);

    expect(screen.getByRole('cell', { name: '#C475FD' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'lavender' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '#AE3030' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'matte-red' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '#DDCC77' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'amber' })).toBeInTheDocument();

    rerender(<WcagContrastSection isDark />);
    expect(screen.getByRole('cell', { name: '#C475FD' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '#AE3030' })).toBeInTheDocument();
    expect(screen.getByText('1.46:1 ✗')).toBeInTheDocument();
    expect(screen.getByText('11.59:1 ✓')).toBeInTheDocument();
  });
});
