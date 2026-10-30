import { describe, expect, it } from 'vitest';

import { DeltaESection } from 'src/sections/palette/DeltaESection';
import { render, screen, within } from 'src/test-utils';

describe('DeltaESection', () => {
  it('renders both normal-vision and worst-CVD ΔE matrices alongside the Petroff 2021 legend', () => {
    render(<DeltaESection />);

    expect(screen.getByRole('heading', { name: /ΔE colour distance/i })).toBeInTheDocument();
    expect(screen.getByText('normal vision')).toBeInTheDocument();
    expect(screen.getByText('worst of deuter / protan / tritan')).toBeInTheDocument();

    const tables = screen.getAllByRole('table');
    expect(tables).toHaveLength(2);

    // Normal matrix has standard ΔE tooltips; worst-CVD matrix has deut/prot/trit breakdown tooltips
    expect(within(tables[0]).getByTitle('green ↔ lavender — ΔE 54.1')).toBeInTheDocument();
    expect(
      within(tables[1]).getByTitle('green ↔ lavender — deut 36.2 · prot 42.4 · trit 38.6')
    ).toBeInTheDocument();

    expect(screen.getByText('<5 indistinct')).toBeInTheDocument();
    expect(screen.getByText('<10 weak')).toBeInTheDocument();
    expect(screen.getByText('<15 acceptable')).toBeInTheDocument();
    expect(screen.getByText('≥15 comfortable')).toBeInTheDocument();
    expect(screen.getByText(/thresholds: Petroff 2021/i)).toBeInTheDocument();
  });
});
