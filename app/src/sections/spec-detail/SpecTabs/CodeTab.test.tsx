import { describe, expect, it, vi } from 'vitest';

import { CodeTab } from 'src/sections/spec-detail/SpecTabs/CodeTab';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

// Mock the lazy-loaded CodeHighlighter
vi.mock('src/components/CodeHighlighter', () => ({
  default: ({ code }: { code: string }) => <pre data-testid="code-highlighter">{code}</pre>,
}));

const baseProps = {
  code: 'print("hello")',
  specId: 'scatter-basic',
  libraryId: 'matplotlib',
};

describe('CodeTab', () => {
  it('renders the code through CodeHighlighter', async () => {
    render(<CodeTab {...baseProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('code-highlighter')).toBeInTheDocument();
    });
    expect(screen.getByTestId('code-highlighter')).toHaveTextContent('print("hello")');
  });

  it('renders no highlighter when code is null', () => {
    render(<CodeTab {...baseProps} code={null} />);
    expect(screen.queryByTestId('code-highlighter')).not.toBeInTheDocument();
  });

  it('copies code, fires the tracking event, and shows the copied state', async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    const onTrackEvent = vi.fn();
    render(<CodeTab {...baseProps} onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByRole('button', { name: /copy code/i }));

    expect(writeText).toHaveBeenCalledWith('print("hello")');
    expect(onTrackEvent).toHaveBeenCalledWith('copy_code', {
      spec: 'scatter-basic',
      library: 'matplotlib',
      method: 'tab',
      page: 'spec_detail',
    });
    expect(screen.getByTestId('CheckIcon')).toBeInTheDocument();
  });

  it('puts .use_my_data() beside the copy button only when the page hands its entry over', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<CodeTab {...baseProps} />);
    expect(screen.queryByRole('button', { name: 'Use with my data' })).not.toBeInTheDocument();

    const onUseWithMyData = vi.fn();
    rerender(<CodeTab {...baseProps} onUseWithMyData={onUseWithMyData} />);
    const entry = screen.getByRole('button', { name: 'Use with my data' });
    expect(entry).toHaveTextContent('.use_my_data()→');
    // Beside `.copy()`, before it in the reading order.
    expect(entry.compareDocumentPosition(screen.getByRole('button', { name: /copy code/i }))).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
    await user.click(entry);
    expect(onUseWithMyData).toHaveBeenCalledTimes(1);
  });

  it('does not copy or track when code is null', async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    const onTrackEvent = vi.fn();
    render(<CodeTab {...baseProps} code={null} onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByRole('button', { name: /copy code/i }));

    expect(writeText).not.toHaveBeenCalled();
    expect(onTrackEvent).not.toHaveBeenCalled();
  });
});
