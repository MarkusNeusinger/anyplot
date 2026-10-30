import { describe, expect, it } from 'vitest';

import { DeltaEMatrix } from 'src/sections/palette/DeltaEMatrix';
import { render, screen, within } from 'src/test-utils';

const MINI_MATRIX: number[][] = [
  [0, 4.2, 8.6],
  [4.2, 0, 18.4],
  [8.6, 18.4, 0],
];

describe('DeltaEMatrix', () => {
  it('renders the title, diagonal dots, rounded ΔE values, and default pairwise tooltips', () => {
    render(<DeltaEMatrix title="normal vision" matrix={MINI_MATRIX} />);

    expect(screen.getByText('normal vision')).toBeInTheDocument();
    const table = screen.getByRole('table');
    const cells = within(table).getAllByRole('cell');

    // 3x3 matrix = 9 data cells; 3 diagonal cells show '·'
    expect(cells).toHaveLength(9);
    expect(cells[0]).toHaveTextContent('·');
    expect(cells[0]).toHaveAttribute('title', 'green');

    // Off-diagonal cells show rounded ΔE and pairwise tooltip
    expect(cells[1]).toHaveTextContent('4');
    expect(cells[1]).toHaveAttribute('title', 'green ↔ lavender — ΔE 4.2');
    expect(cells[2]).toHaveTextContent('9');
    expect(cells[2]).toHaveAttribute('title', 'green ↔ blue — ΔE 8.6');
    expect(cells[5]).toHaveTextContent('18');
    expect(cells[5]).toHaveAttribute('title', 'lavender ↔ blue — ΔE 18.4');
  });

  it('formats off-diagonal cell tooltips from the per-CVD breakdown when provided', () => {
    const deut = [
      [0, 3.5],
      [3.5, 0],
    ];
    const prot = [
      [0, 6.1],
      [6.1, 0],
    ];
    render(
      <DeltaEMatrix
        title="worst CVD"
        matrix={deut}
        breakdown={[
          { label: 'deut', m: deut },
          { label: 'prot', m: prot },
        ]}
      />
    );

    const table = screen.getByRole('table');
    const cells = within(table).getAllByRole('cell');
    expect(cells[1]).toHaveAttribute('title', 'green ↔ lavender — deut 3.5 · prot 6.1');
  });
});
