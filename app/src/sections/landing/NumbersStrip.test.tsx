import { describe, expect, it, vi } from 'vitest';

import { NumbersStrip } from 'src/sections/landing/NumbersStrip';
import { render, screen, userEvent } from 'src/test-utils';

describe('NumbersStrip', () => {
  it('shows the numbers and no .retry() when the stats loaded', () => {
    render(
      <NumbersStrip
        stats={{ specs: 3, plots: 1200, libraries: 15, languages: 4 }}
        failed={false}
        onRetry={vi.fn()}
      />
    );
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading the numbers' })).toBeNull();
  });

  it('keeps the placeholders without .retry() while the load is pending', () => {
    render(<NumbersStrip stats={null} failed={false} onRetry={vi.fn()} />);
    expect(screen.getAllByText('—')).toHaveLength(5);
    expect(screen.queryByRole('button', { name: 'Retry loading the numbers' })).toBeNull();
  });

  it('offers .retry() when the load failed and calls onRetry on click', async () => {
    const onRetry = vi.fn();
    render(<NumbersStrip stats={null} failed onRetry={onRetry} />);

    const retry = screen.getByRole('button', { name: 'Retry loading the numbers' });
    expect(retry).toHaveTextContent('.retry()');
    await userEvent.click(retry);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
