import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, styleAt, userEvent, within } from 'src/test-utils';

// The hero with its real plot-of-the-day terminal (HeroSection.test.tsx stubs the terminal):
// the request's status and retry have to reach the card through the hero.

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return { ...actual, useAnalytics: () => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }) };
});

vi.mock('src/sections/landing/TypewriterText', () => ({
  TypewriterText: () => <div data-testid="typewriter" />,
}));

vi.mock('src/hooks/useAgentLaneOpen', () => ({ useAgentLaneOpen: () => false }));

// The lane the card's eligibility names for the pair; null is no `.use_my_data()`.
const eligibility: { lane: 'public' | null } = { lane: null };
vi.mock('src/hooks/useAgentEligibility', () => ({ useAgentEligibility: () => eligibility.lane }));

import { HeroSection } from 'src/sections/landing/HeroSection';
import { POTD_LOAD_ERROR } from 'src/sections/landing/PlotOfTheDayTerminal';

const potd = {
  spec_id: 'scatter-basic',
  spec_title: 'Basic Scatter',
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  preview_url: 'https://cdn.example.com/plot.png',
};

describe('HeroSection with the plot-of-the-day terminal', () => {
  beforeEach(() => {
    eligibility.lane = null;
  });

  it('keeps the card header rows from the empty frame to the plot and its .use_my_data()', () => {
    // A phone's card is about 358 px wide: the actions take the header's second row throughout.
    const phoneCard = 358;
    const { rerender } = render(
      <HeroSection potd={null} potdStatus="loading" onRetryPotd={vi.fn()} />
    );
    const frame = screen.getByTestId('potd-terminal-placeholder');
    const empty = screen.getByTestId('potd-terminal-actions');
    expect(styleAt(empty, 390, phoneCard).flexBasis).toBe('100%');
    // The empty row is a line high (its pseudo-element's no-break space), not 0 px.
    expect(styleAt(empty, 390, phoneCard, '::before').content).toMatch(/^(["']).+\1$/);

    rerender(<HeroSection potd={potd} potdStatus="ready" onRetryPotd={vi.fn()} />);
    // The hero hands the plot to the same card element, so the reserved box stays.
    expect(frame).toBeInTheDocument();
    expect(frame).not.toHaveAttribute('data-testid');
    const row = screen.getByTestId('potd-terminal-actions');
    expect(row.className).toBe(empty.className);
    expect(within(row).queryByRole('link', { name: 'Use with my data' })).toBeNull();

    eligibility.lane = 'public';
    rerender(<HeroSection potd={potd} potdStatus="ready" onRetryPotd={vi.fn()} />);
    const withLink = screen.getByTestId('potd-terminal-actions');
    expect(withLink.className).toBe(empty.className);
    expect(within(withLink).getByRole('link', { name: 'Use with my data' })).toBeInTheDocument();
    expect(styleAt(withLink, 390, phoneCard).flexBasis).toBe('100%');
  });

  it('shows the failed frame with a working .retry() when the request failed', async () => {
    const user = userEvent.setup();
    const retry = vi.fn();
    render(<HeroSection potd={null} potdStatus="failed" onRetryPotd={retry} />);

    expect(screen.getByRole('alert')).toHaveTextContent(POTD_LOAD_ERROR);
    await user.click(screen.getByRole('button', { name: 'Retry loading the plot of the day' }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it('keeps the frame empty and hidden while the request is in flight', () => {
    render(<HeroSection potd={null} potdStatus="loading" onRetryPotd={vi.fn()} />);

    expect(screen.getByTestId('potd-terminal-placeholder')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('renders no card when the API answered without a plot of the day', () => {
    render(<HeroSection potd={null} potdStatus="none" onRetryPotd={vi.fn()} />);

    expect(screen.queryByTestId('potd-terminal-placeholder')).toBeNull();
  });
});
