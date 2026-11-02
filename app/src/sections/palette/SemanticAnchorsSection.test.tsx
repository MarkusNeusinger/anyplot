import { describe, expect, it, vi } from 'vitest';

import { SemanticAnchorsSection } from 'src/sections/palette/SemanticAnchorsSection';
import { fireEvent, render, screen } from 'src/test-utils';

describe('SemanticAnchorsSection', () => {
  it('renders amber, adaptive neutral, and adaptive muted anchors with their swatch buttons', () => {
    render(<SemanticAnchorsSection copiedHex={null} copyHex={vi.fn()} />);

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

  it('calls copyHex with the clicked anchor hex and shows copied ✓ only on the matching swatch', () => {
    const copyHex = vi.fn();
    const { rerender } = render(<SemanticAnchorsSection copiedHex={null} copyHex={copyHex} />);

    const amberSwatch = screen.getByRole('button', {
      name: 'Copy #DDCC77 (amber) to clipboard',
    });
    expect(amberSwatch).toHaveTextContent('#DDCC77');

    fireEvent.click(amberSwatch);
    expect(copyHex).toHaveBeenCalledWith('#DDCC77');

    rerender(<SemanticAnchorsSection copiedHex="#DDCC77" copyHex={copyHex} />);
    expect(amberSwatch).toHaveTextContent('copied ✓');
    expect(screen.getAllByText('copied ✓')).toHaveLength(1);
    expect(
      screen.getByRole('button', { name: 'Copy #1A1A17 (neutral) to clipboard' })
    ).toHaveTextContent('#1A1A17');
  });
});
