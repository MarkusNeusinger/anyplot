import { beforeEach, describe, expect, it, vi } from 'vitest';

import { fireEvent, render, screen, styleAt, userEvent, within } from 'src/test-utils';

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

import { PlotOfTheDayTerminal, POTD_LOAD_ERROR } from 'src/sections/landing/PlotOfTheDayTerminal';

/** A quoted string with at least one character: generated content that makes a line box. */
const LINE_OF_TEXT = /^(["']).+\1$/;

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
    render(<PlotOfTheDayTerminal potd={potd} status="ready" />);

    expect(screen.queryByRole('link', { name: 'Use with my data' })).toBeNull();
    expect(agentEligibility.asked).toContainEqual(['scatter-basic', 'matplotlib']);
  });

  it('opens the public chat for its pair through the router', () => {
    agentEligibility.lane = 'public';
    render(<PlotOfTheDayTerminal potd={potd} status="ready" />);

    const link = screen.getByRole('link', { name: 'Use with my data' });
    expect(link).toHaveTextContent('.use_my_data()');
    expect(link).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=plot_of_the_day'
    );
    // Only the router cancels the click's full page load.
    expect(fireEvent.click(link)).toBe(false);
  });

  it('opens the same chat page through the router while only the admin lane answers', () => {
    // The public door is closed and the admin's eligibility answered: one chat page all the
    // same, which picks the admin lane itself (`AgentChatPage`).
    agentEligibility.lane = 'admin';
    render(<PlotOfTheDayTerminal potd={potd} status="ready" />);

    const link = screen.getByRole('link', { name: 'Use with my data' });
    expect(link).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=plot_of_the_day'
    );
    expect(fireEvent.click(link)).toBe(false);
  });

  it('reserves the empty frame without potd data: hidden, no links, no words of its own', () => {
    render(<PlotOfTheDayTerminal potd={null} status="loading" />);
    const frame = screen.getByTestId('potd-terminal-placeholder');
    expect(frame).toHaveAttribute('aria-hidden', 'true');
    expect(frame.querySelectorAll('a, button, img')).toHaveLength(0);
    expect(frame).toHaveTextContent(/^\$>>>\/\/ plot of the day$/);
  });

  it('keeps the frame after a failed request and says so, with a .retry()', async () => {
    const user = userEvent.setup();
    const retry = vi.fn();
    const { container, rerender } = render(
      <PlotOfTheDayTerminal potd={null} status="loading" onRetry={retry} />
    );
    const frame = container.firstElementChild;
    expect(frame).toHaveAttribute('aria-hidden', 'true');
    expect(screen.queryByRole('alert')).toBeNull();

    rerender(<PlotOfTheDayTerminal potd={null} status="failed" onRetry={retry} />);
    // Same element as the loading frame: the box does not move, and the entrance does not replay.
    expect(container.firstElementChild).toBe(frame);
    expect(frame).not.toHaveAttribute('aria-hidden');
    expect(screen.getByRole('alert')).toHaveTextContent(POTD_LOAD_ERROR);
    expect(POTD_LOAD_ERROR).toBe('plot of the day did not load');
    expect(frame?.querySelectorAll('a, img')).toHaveLength(0);

    await user.click(screen.getByRole('button', { name: 'Retry loading the plot of the day' }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it('gives the header the same rows in every state: the actions on a row of their own while the card is narrow', () => {
    // A phone's card, the narrow two-column card from 900 px, and a wide card.
    const narrow = 400;
    const wide = 600;
    const { rerender } = render(<PlotOfTheDayTerminal potd={null} status="loading" />);
    // The empty frame holds the actions' row with nothing in it; its pseudo-element gives it
    // the line's height without words of its own. An empty string, `none` or `normal` would
    // leave the row 0 px high, and the narrow frame would grow by a line when the plot arrives.
    const empty = screen.getByTestId('potd-terminal-actions');
    expect(empty).toBeEmptyDOMElement();
    expect(styleAt(empty, 390, narrow).flexBasis).toBe('100%');
    expect(styleAt(empty, 390, narrow, '::before').content).toMatch(LINE_OF_TEXT);
    expect(styleAt(empty, 1440, wide).flexBasis).toBe('auto');
    const rowClass = empty.className;

    rerender(<PlotOfTheDayTerminal potd={null} status="failed" onRetry={vi.fn()} />);
    const failed = screen.getByTestId('potd-terminal-actions');
    expect(failed.className).toBe(rowClass);
    expect(failed).toBeEmptyDOMElement();
    expect(styleAt(failed, 390, narrow, '::before').content).toMatch(LINE_OF_TEXT);

    // The plot without `.use_my_data()`: github.open() alone still takes the second row, and
    // its text gives the row its height, so the pseudo-element adds nothing beside it.
    rerender(<PlotOfTheDayTerminal potd={potd} status="ready" />);
    const card = screen.getByTestId('potd-terminal-actions');
    expect(card.className).toBe(rowClass);
    expect(within(card).getByLabelText('Open source on GitHub')).toBeInTheDocument();
    expect(within(card).queryByRole('link', { name: 'Use with my data' })).toBeNull();
    expect(styleAt(card, 390, narrow, '::before').content).toBe('');
    expect(styleAt(card, 390, narrow).flexBasis).toBe('100%');
    expect(styleAt(card.parentElement as Element, 390, narrow).flexWrap).toBe('wrap');
    expect(styleAt(card, 1440, wide).flexBasis).toBe('auto');
    expect(styleAt(card.parentElement as Element, 1440, wide).flexWrap).toBe('nowrap');

    // The eligibility answer adds the link into the same row, which keeps its place.
    agentEligibility.lane = 'public';
    rerender(<PlotOfTheDayTerminal potd={potd} status="ready" />);
    const withLink = screen.getByTestId('potd-terminal-actions');
    expect(withLink.className).toBe(rowClass);
    expect(within(withLink).getByRole('link', { name: 'Use with my data' })).toBeInTheDocument();
    expect(styleAt(withLink, 390, narrow).flexBasis).toBe('100%');
    expect(styleAt(withLink, 390, narrow, '::before').content).toBe('');
  });

  it('keeps `// plot of the day` in its own node when the plot arrives', () => {
    const { rerender } = render(<PlotOfTheDayTerminal potd={null} status="loading" />);
    const footer = screen.getByTestId('potd-terminal-footer');
    const tag = within(footer).getByText('// plot of the day');
    expect(footer).toHaveAttribute('aria-hidden', 'true');

    rerender(<PlotOfTheDayTerminal potd={potd} status="ready" />);
    // The same node in the same place: the library name is a node of its own, so the tag
    // does not turn into it and move.
    expect(screen.getByTestId('potd-terminal-footer')).toBe(footer);
    expect(within(footer).getByText('// plot of the day')).toBe(tag);
    expect(within(footer).getByText('Matplotlib')).not.toBe(tag);
    expect(within(footer).getByText('Basic Scatter')).toBeInTheDocument();
    expect(footer).not.toHaveAttribute('aria-hidden');
  });

  it('renders no card when the API answered without a plot of the day', () => {
    const { container } = render(<PlotOfTheDayTerminal potd={null} status="none" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders no card for a plot of the day without a preview image', () => {
    const { container } = render(
      <PlotOfTheDayTerminal potd={{ ...potd, preview_url: null }} status="ready" />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('keeps the frame element when the plot arrives, so the entrance does not replay', () => {
    const { container, rerender } = render(<PlotOfTheDayTerminal potd={null} status="loading" />);
    const frame = container.firstElementChild;
    rerender(<PlotOfTheDayTerminal potd={potd} status="ready" />);
    expect(container.firstElementChild).toBe(frame);
    expect(frame).not.toHaveAttribute('aria-hidden');
    expect(screen.queryByTestId('potd-terminal-placeholder')).toBeNull();
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('tracks nav_click on filename, github link and image', async () => {
    const user = userEvent.setup();
    render(<PlotOfTheDayTerminal potd={potd} status="ready" />);

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
