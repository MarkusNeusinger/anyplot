import { describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

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

import { HeroSection } from 'src/sections/landing/HeroSection';
import { POTD_LOAD_ERROR } from 'src/sections/landing/PlotOfTheDayTerminal';

describe('HeroSection with the plot-of-the-day terminal', () => {
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
