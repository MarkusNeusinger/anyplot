import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('src/sections/landing/PlotOfTheDayTerminal', () => ({
  PlotOfTheDayTerminal: () => <div data-testid="potd-terminal" />,
}));

vi.mock('src/sections/landing/TypewriterText', () => ({
  TypewriterText: () => <div data-testid="typewriter" />,
}));

const lane = vi.hoisted(() => ({ open: false as boolean | null }));
vi.mock('src/hooks/useAgentLaneOpen', () => ({ useAgentLaneOpen: () => lane.open }));

import { AGENT_LANE_LINE, HeroSection } from 'src/sections/landing/HeroSection';

describe('HeroSection', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    lane.open = false;
  });

  it('points to the public agent chat only while its lane is open', () => {
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.queryByText(new RegExp(AGENT_LANE_LINE))).not.toBeInTheDocument();

    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: new RegExp(AGENT_LANE_LINE) });
    expect(link).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=landing'
    );
  });

  it('tracks the primary browse CTA, mcp link and github link', async () => {
    const user = userEvent.setup();
    render(<HeroSection potd={null} />);

    await user.click(screen.getByLabelText('Browse plots'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_cta_browse',
      target: '/plots',
    });

    await user.click(screen.getByLabelText('Connect via MCP'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'hero_mcp', target: '/mcp' });

    await user.click(screen.getByLabelText('Clone on GitHub'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_github',
      target: 'github',
    });
  });
});
