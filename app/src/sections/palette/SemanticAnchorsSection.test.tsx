import { useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { SemanticAnchorsSection } from 'src/sections/palette/SemanticAnchorsSection';
import { act, fireEvent, render, screen } from 'src/test-utils';

function StatefulAnchors() {
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex(c => (c === hex ? null : c)), 1500);
      })
      .catch(() => {});
  };

  return <SemanticAnchorsSection copiedHex={copiedHex} copyHex={copyHex} />;
}

describe('SemanticAnchorsSection', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('renders amber, adaptive neutral, and adaptive muted anchors with their swatch buttons', () => {
    render(<StatefulAnchors />);

    expect(screen.getByRole('heading', { name: /semantic anchors/i })).toBeInTheDocument();
    expect(screen.getByText('palette.amber')).toBeInTheDocument();
    expect(screen.getByText('palette.neutral — adaptive')).toBeInTheDocument();
    expect(screen.getByText('palette.muted — adaptive')).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: 'Copy #DDCC77 (amber) to clipboard' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Copy #1A1A17 (neutral) to clipboard' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Copy #F0EFE8 (neutral) to clipboard' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Copy #6B6A63 (muted) to clipboard' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Copy #A8A79F (muted) to clipboard' })
    ).toBeInTheDocument();
  });

  it('copies an anchor swatch and resets the copied feedback after 1500 ms', async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(<StatefulAnchors />);

    const amberSwatch = screen.getByRole('button', {
      name: 'Copy #DDCC77 (amber) to clipboard',
    });
    expect(amberSwatch).toHaveTextContent('#DDCC77');

    await act(async () => {
      fireEvent.click(amberSwatch);
    });

    expect(writeText).toHaveBeenCalledWith('#DDCC77');
    expect(amberSwatch).toHaveTextContent('copied ✓');

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    expect(amberSwatch).toHaveTextContent('#DDCC77');
  });
});
