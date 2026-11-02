import { useState } from 'react';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PALETTE } from 'src/pages/PalettePage.helpers';
import { HeroSection } from 'src/sections/palette/HeroSection';
import { COMPARISONS } from 'src/sections/palette/paletteHelpers';
import type { WheelDot } from 'src/sections/palette/types';
import { fireEvent, render, screen } from 'src/test-utils';

const IMPRINT_DOTS: WheelDot[] = PALETTE.map(s => ({
  hex: s.hex,
  L: s.L,
  C: s.C,
  H: s.H,
  name: s.name,
}));

function StatefulHero() {
  const [wheelOpen, setWheelOpen] = useState(false);
  const [compareId, setCompareId] = useState<string | null>(null);
  const overlayDots = COMPARISONS.find(c => c.id === compareId)?.hexes;

  return (
    <HeroSection
      wheelOpen={wheelOpen}
      setWheelOpen={setWheelOpen}
      imprintDots={IMPRINT_DOTS}
      overlayDots={overlayDots}
      compareId={compareId}
      setCompareId={setCompareId}
    />
  );
}

describe('HeroSection', () => {
  beforeEach(() => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('expands and collapses the hue–chroma wheel and updates aria-expanded', () => {
    render(<StatefulHero />);

    expect(screen.getByRole('heading', { name: /anyplot's imprint palette/i })).toBeInTheDocument();
    expect(screen.getByText('compare ▸')).toBeInTheDocument();

    const expandButton = screen.getByRole('button', {
      name: 'Expand the hue–chroma wheel to compare palettes',
    });
    expect(expandButton).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(expandButton);

    const collapseButton = screen.getByRole('button', {
      name: 'Collapse the hue–chroma wheel',
    });
    expect(collapseButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('click to close')).toBeInTheDocument();

    fireEvent.click(collapseButton);
    expect(
      screen.getByRole('button', {
        name: 'Expand the hue–chroma wheel to compare palettes',
      })
    ).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('compare ▸')).toBeInTheDocument();
  });

  it('picks and unpicks a comparison palette and updates aria-pressed and overlay rings', () => {
    render(<StatefulHero />);

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Expand the hue–chroma wheel to compare palettes',
      })
    );

    const okabeButton = screen.getByRole('button', { name: 'Okabe-Ito' });
    const tolButton = screen.getByRole('button', { name: 'Tol muted' });
    expect(okabeButton).toHaveAttribute('aria-pressed', 'false');
    expect(tolButton).toHaveAttribute('aria-pressed', 'false');
    expect(screen.queryByText(/rings =/i)).not.toBeInTheDocument();

    // Pick Okabe-Ito
    fireEvent.click(okabeButton);
    expect(okabeButton).toHaveAttribute('aria-pressed', 'true');
    expect(tolButton).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText(/· rings = Okabe-Ito/)).toBeInTheDocument();
    expect(screen.getByText('#D55E00')).toBeInTheDocument();

    // Switch directly to Tol muted
    fireEvent.click(tolButton);
    expect(tolButton).toHaveAttribute('aria-pressed', 'true');
    expect(okabeButton).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText(/· rings = Tol muted/)).toBeInTheDocument();

    // Unpick Tol muted
    fireEvent.click(tolButton);
    expect(tolButton).toHaveAttribute('aria-pressed', 'false');
    expect(screen.queryByText(/rings =/i)).not.toBeInTheDocument();
  });
});
