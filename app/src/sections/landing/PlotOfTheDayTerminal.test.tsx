import { beforeEach, describe, expect, it, vi } from 'vitest';

import { fireEvent, render, screen, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();

// The lane `useAgentEligibility` names for the pair; null is no entry (also while it probes).
const agentEligibility: {
  lane: 'admin' | 'public' | null;
  asked: [string | null | undefined, string | null | undefined][];
} = { lane: null, asked: [] };
vi.mock('src/hooks/useAgentEligibility', () => ({
  useAgentEligibility: (spec: string | null | undefined, library: string | null | undefined) => {
    agentEligibility.asked.push([spec, library]);
    return agentEligibility.lane;
  },
}));

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return { ...actual, useTheme: () => ({ isDark: false, toggle: vi.fn() }) };
});

import { PlotOfTheDayTerminal } from 'src/sections/landing/PlotOfTheDayTerminal';

const potd = {
  spec_id: 'scatter-basic',
  spec_title: 'Basic Scatter',
  description: null,
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  quality_score: 9,
  preview_url: 'https://cdn.example.com/plot.png',
  preview_url_light: null,
  preview_url_dark: null,
  image_description: null,
  library_version: '3.8.0',
  python_version: '3.12',
  language_version: '3.12',
  date: '2026-04-25',
};

describe('PlotOfTheDayTerminal', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    agentEligibility.lane = null;
    agentEligibility.asked = [];
  });

  it('shows no .use_my_data() while the eligibility names no lane, and asks about its pair', () => {
    render(<PlotOfTheDayTerminal potd={potd} />);

    expect(screen.queryByRole('link', { name: 'Use with my data' })).toBeNull();
    expect(agentEligibility.asked).toContainEqual(['scatter-basic', 'matplotlib']);
  });

  it('opens the public chat for its pair through the router', () => {
    agentEligibility.lane = 'public';
    render(<PlotOfTheDayTerminal potd={potd} />);

    const link = screen.getByRole('link', { name: 'Use with my data' });
    expect(link).toHaveTextContent('.use_my_data()');
    expect(link).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=plot_of_the_day'
    );
    // Only the router cancels the click's full page load.
    expect(fireEvent.click(link)).toBe(false);
  });

  it('opens the admin chat with a full page load while the public lane is closed', () => {
    agentEligibility.lane = 'admin';
    render(<PlotOfTheDayTerminal potd={potd} />);

    const link = screen.getByRole('link', { name: 'Use with my data' });
    expect(link).toHaveAttribute(
      'href',
      '/debug/agent?spec=scatter-basic&library=matplotlib&language=python&source=plot_of_the_day'
    );
    // A plain anchor: nothing before `window` cancels the click, so the browser loads the page
    // in full. The listener records that, then cancels it, because jsdom cannot navigate.
    let cancelled: boolean | null = null;
    const observe = (event: MouseEvent) => {
      cancelled = event.defaultPrevented;
      event.preventDefault();
    };
    window.addEventListener('click', observe);
    fireEvent.click(link);
    window.removeEventListener('click', observe);
    expect(cancelled).toBe(false);
  });

  it('renders nothing without potd data', () => {
    const { container } = render(<PlotOfTheDayTerminal potd={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('tracks nav_click on filename, github link and image', async () => {
    const user = userEvent.setup();
    render(<PlotOfTheDayTerminal potd={potd} />);

    await user.click(screen.getByText(/plots\/scatter-basic\/matplotlib\.py/));
    expect(trackEvent).toHaveBeenCalledWith(
      'nav_click',
      expect.objectContaining({ source: 'potd_terminal_filename' })
    );

    const githubLink = screen.getByLabelText('Open source on GitHub');
    expect(githubLink.getAttribute('href')).toMatch(
      /\/blob\/main\/plots\/scatter-basic\/implementations\/python\/matplotlib\.py$/
    );
    await user.click(githubLink);
    expect(trackEvent).toHaveBeenCalledWith(
      'nav_click',
      expect.objectContaining({ source: 'potd_terminal_github' })
    );

    await user.click(screen.getByLabelText(/Open Basic Scatter implementation/));
    expect(trackEvent).toHaveBeenCalledWith(
      'nav_click',
      expect.objectContaining({ source: 'potd_terminal_image' })
    );
  });
});
