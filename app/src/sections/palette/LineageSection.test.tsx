import { describe, expect, it } from 'vitest';

import { LineageSection } from 'src/sections/palette/LineageSection';
import { render, screen } from 'src/test-utils';

describe('LineageSection', () => {
  it('renders the three palette history entries and reference links', () => {
    render(<LineageSection />);

    expect(screen.getByRole('heading', { name: /lineage/i })).toBeInTheDocument();
    expect(screen.getByText('version timeline')).toBeInTheDocument();

    expect(screen.getByText('v3 — imprint (current)')).toBeInTheDocument();
    expect(screen.getByText('v1 — variant D ("balanced")')).toBeInTheDocument();
    expect(screen.getByText('v0 — Okabe-Ito')).toBeInTheDocument();

    const petroffLink = screen.getByRole('link', { name: 'Petroff 2021 (arXiv)' });
    expect(petroffLink).toHaveAttribute('href', 'https://arxiv.org/abs/2107.02270');

    const okabeLink = screen.getByRole('link', { name: 'jfly.uni-koeln.de' });
    expect(okabeLink).toHaveAttribute('href', 'https://jfly.uni-koeln.de/color/');

    const draculaLink = screen.getByRole('link', { name: 'dracula-palette' });
    expect(draculaLink).toHaveAttribute('href', 'https://anselmoo.github.io/dracula-palette/');
  });
});
