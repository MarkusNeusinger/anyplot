import { useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { PALETTE, type Swatch } from 'src/pages/PalettePage.helpers';
import { PaletteGridSection } from 'src/sections/palette/PaletteGridSection';
import { act, fireEvent, render, screen, within } from 'src/test-utils';

const CVD_OPTIMAL_ORDER: number[] = [0, 1, 7, 6, 4, 5, 2, 3];

function StatefulPaletteGrid() {
  const [sort, setSort] = useState<'imprint' | 'cvd'>('imprint');
  const [copiedHex, setCopiedHex] = useState<string | null>(null);

  const sortedPalette: Swatch[] =
    sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i]);

  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex(c => (c === hex ? null : c)), 1500);
      })
      .catch(() => {});
  };

  return (
    <PaletteGridSection
      sort={sort}
      setSort={setSort}
      sortedPalette={sortedPalette}
      copiedHex={copiedHex}
      copyHex={copyHex}
    />
  );
}

describe('PaletteGridSection', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('switches between imprint default and CVD-optimal sort order and toggles the trade-off table', () => {
    render(<StatefulPaletteGrid />);

    expect(screen.getByRole('heading', { name: /the 8 categorical hues/i })).toBeInTheDocument();
    expect(screen.queryByText(/why use CVD-optimal sort\?/i)).not.toBeInTheDocument();

    // Default imprint order: [brand green, lavender, blue, ochre, ...]
    const defaultButtons = screen.getAllByRole('button', { name: /Copy #[0-9A-F]{6}/i });
    expect(defaultButtons).toHaveLength(8);
    expect(defaultButtons[0]).toHaveAccessibleName('Copy #009E73 (brand green) to clipboard');
    expect(defaultButtons[2]).toHaveAccessibleName('Copy #4467A3 (blue) to clipboard');
    expect(defaultButtons[3]).toHaveAccessibleName('Copy #BD8233 (ochre) to clipboard');

    // Switch to CVD-optimal order
    fireEvent.click(
      screen.getByRole('button', { name: 'CVD-optimal (max ΔE under colorblindness)' })
    );

    expect(screen.getByText(/why use CVD-optimal sort\?/i)).toBeInTheDocument();
    const table = screen.getByRole('table');
    expect(within(table).getByText('21.45 (+5.11)')).toBeInTheDocument();
    expect(within(table).getByText('36.19 (=)')).toBeInTheDocument();

    const cvdButtons = screen.getAllByRole('button', { name: /Copy #[0-9A-F]{6}/i });
    expect(cvdButtons[2]).toHaveAccessibleName('Copy #99B314 (lime) to clipboard');
    expect(cvdButtons[3]).toHaveAccessibleName('Copy #954477 (rose) to clipboard');

    // Switch back to imprint (default)
    fireEvent.click(screen.getByRole('button', { name: 'imprint (default)' }));
    expect(screen.queryByText(/why use CVD-optimal sort\?/i)).not.toBeInTheDocument();
  });

  it('copies a swatch hex to the clipboard, shows copied feedback, and resets after 1500 ms', async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(<StatefulPaletteGrid />);

    const brandButton = screen.getByRole('button', {
      name: 'Copy #009E73 (brand green) to clipboard',
    });
    expect(within(brandButton).getByText('#009E73')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(brandButton);
    });

    expect(writeText).toHaveBeenCalledWith('#009E73');
    expect(within(brandButton).getByText('copied ✓')).toBeInTheDocument();
    // Unclicked swatches keep showing their hex
    expect(screen.getByText('#C475FD')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    expect(within(brandButton).queryByText('copied ✓')).not.toBeInTheDocument();
    expect(within(brandButton).getByText('#009E73')).toBeInTheDocument();
  });
});
