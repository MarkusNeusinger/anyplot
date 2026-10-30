import { afterEach, describe, expect, it, vi } from 'vitest';

import { CodeBlock } from 'src/sections/palette/CodeBlock';
import { act, fireEvent, render, screen } from 'src/test-utils';

describe('CodeBlock', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('renders the code text and copies it to the clipboard with a 1500 ms feedback reset', async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(<CodeBlock code="const palette = ['#009E73'];" />);

    expect(screen.getByText("const palette = ['#009E73'];")).toBeInTheDocument();
    const copyButton = screen.getByRole('button', { name: 'copy' });

    await act(async () => {
      fireEvent.click(copyButton);
    });

    expect(writeText).toHaveBeenCalledWith("const palette = ['#009E73'];");
    expect(screen.getByRole('button', { name: 'copied' })).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1499);
    });
    expect(screen.getByRole('button', { name: 'copied' })).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(screen.getByRole('button', { name: 'copy' })).toBeInTheDocument();
  });

  it('ignores clipboard write failures without flipping to copied state', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('Clipboard blocked'));
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(<CodeBlock code="print('imprint')" />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'copy' }));
    });

    expect(writeText).toHaveBeenCalledWith("print('imprint')");
    expect(screen.getByRole('button', { name: 'copy' })).toBeInTheDocument();
  });
});
