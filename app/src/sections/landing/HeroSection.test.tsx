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

import {
  AGENT_ENTRY_LABEL,
  AGENT_ENTRY_NAME,
  AGENT_ENTRY_TEXT,
  HeroSection,
} from 'src/sections/landing/HeroSection';

describe('HeroSection', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    lane.open = false;
  });

  it('names the agent in plain words only while the public lane is open, leading to /agent', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_ENTRY_LABEL })).not.toBeInTheDocument();
    expect(screen.queryByText(AGENT_ENTRY_TEXT)).not.toBeInTheDocument();

    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: AGENT_ENTRY_LABEL });
    // The idiom and the plain words, both inside the one link.
    expect(link).toHaveTextContent(`${AGENT_ENTRY_NAME} →`);
    expect(link).toHaveTextContent(AGENT_ENTRY_TEXT);
    // The accessible name keeps the words on screen (WCAG 2.5.3).
    expect(AGENT_ENTRY_LABEL.toLowerCase()).toContain(AGENT_ENTRY_TEXT);
    // A decision of the launch: the chat's notice says "experimental", the hero does not.
    expect(link).not.toHaveTextContent(/experimental/i);
    expect(link).toHaveAttribute('href', '/agent');

    await user.click(link);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_use_my_data',
      target: '/agent',
    });
  });

  it('keeps the entry hidden while the lane probe is pending', () => {
    lane.open = null;
    render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_ENTRY_LABEL })).not.toBeInTheDocument();
  });

  it('tracks the primary browse CTA, mcp link and github link', async () => {
    const user = userEvent.setup();
    render(<HeroSection potd={null} />);

    await user.click(screen.getByLabelText('Browse plots'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_cta_browse',
      target: '/plots',
    });

    const mcp = screen.getByRole('link', { name: 'Connect via MCP' });
    expect(mcp).toHaveAttribute('href', '/mcp');
    await user.click(mcp);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'hero_mcp', target: '/mcp' });

    await user.click(screen.getByLabelText('Clone on GitHub'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_github',
      target: 'github',
    });
  });
});
