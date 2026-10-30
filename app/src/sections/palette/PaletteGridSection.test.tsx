import { describe, expect, it, vi } from 'vitest';

import { PALETTE } from 'src/pages/PalettePage.helpers';
import { PaletteGridSection } from 'src/sections/palette/PaletteGridSection';
import { fireEvent, render, screen, within } from 'src/test-utils';

describe('PaletteGridSection', () => {
  it('calls setSort("cvd") and setSort("imprint") from the sort buttons and shows the trade-off table when sort="cvd"', () => {
    const setSort = vi.fn();
    const { rerender } = render(
      <PaletteGridSection
        sort="imprint"
        setSort={setSort}
        sortedPalette={PALETTE}
        copiedHex={null}
        copyHex={vi.fn()}
      />
    );

    expect(screen.getByRole('heading', { name: /the 8 categorical hues/i })).toBeInTheDocument();
    expect(screen.queryByText(/why use CVD-optimal sort\?/i)).not.toBeInTheDocument();

    const buttons = screen.getAllByRole('button', { name: /Copy #[0-9A-F]{6}/i });
    expect(buttons).toHaveLength(8);
    expect(buttons[0]).toHaveAccessibleName('Copy #009E73 (brand green) to clipboard');

    fireEvent.click(
      screen.getByRole('button', { name: 'CVD-optimal (max ΔE under colorblindness)' })
    );
    expect(setSort).toHaveBeenCalledWith('cvd');

    fireEvent.click(screen.getByRole('button', { name: 'imprint (default)' }));
    expect(setSort).toHaveBeenCalledWith('imprint');

    rerender(
      <PaletteGridSection
        sort="cvd"
        setSort={setSort}
        sortedPalette={PALETTE}
        copiedHex={null}
        copyHex={vi.fn()}
      />
    );

    expect(screen.getByText(/why use CVD-optimal sort\?/i)).toBeInTheDocument();
    const table = screen.getByRole('table');
    expect(within(table).getByText('21.45 (+5.11)')).toBeInTheDocument();
    expect(within(table).getByText('36.19 (=)')).toBeInTheDocument();
  });

  it('calls copyHex with the clicked swatch hex and shows copied ✓ only on copiedHex', () => {
    const copyHex = vi.fn();
    const { rerender } = render(
      <PaletteGridSection
        sort="imprint"
        setSort={vi.fn()}
        sortedPalette={PALETTE}
        copiedHex={null}
        copyHex={copyHex}
      />
    );

    const brandButton = screen.getByRole('button', {
      name: 'Copy #009E73 (brand green) to clipboard',
    });
    expect(within(brandButton).getByText('#009E73')).toBeInTheDocument();

    fireEvent.click(brandButton);
    expect(copyHex).toHaveBeenCalledWith('#009E73');

    rerender(
      <PaletteGridSection
        sort="imprint"
        setSort={vi.fn()}
        sortedPalette={PALETTE}
        copiedHex="#009E73"
        copyHex={copyHex}
      />
    );

    expect(within(brandButton).getByText('copied ✓')).toBeInTheDocument();
    expect(screen.getAllByText('copied ✓')).toHaveLength(1);
    expect(screen.getByText('#C475FD')).toBeInTheDocument();
  });
});
