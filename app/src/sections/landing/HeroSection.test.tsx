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

import { AGENT_LANE_LABEL, AGENT_LANE_LINE, HeroSection } from 'src/sections/landing/HeroSection';

describe('HeroSection', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    lane.open = false;
  });

  it('announces .use_my_data() only while the public lane is open, leading to the catalogue', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_LANE_LABEL })).not.toBeInTheDocument();

    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: AGENT_LANE_LABEL });
    expect(link).toHaveTextContent(`# ${AGENT_LANE_LINE} →`);
    expect(link).toHaveTextContent('# new: pick any plot, then .use_my_data() →');
    expect(link).not.toHaveTextContent(/experimental/i);
    expect(link).toHaveAttribute('href', '/plots');

    await user.click(link);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_use_my_data',
      target: '/plots',
    });
  });

  it('keeps the line hidden while the lane probe is pending', () => {
    lane.open = null;
    render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_LANE_LABEL })).not.toBeInTheDocument();
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
