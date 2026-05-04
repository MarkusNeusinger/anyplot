import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('../hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useLayoutContext')>('../hooks/useLayoutContext');
  return { ...actual, useTheme: () => ({ isDark: false, toggle: vi.fn() }) };
});

import { PlotOfTheDayTerminal } from './PlotOfTheDayTerminal';

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
  date: '2026-04-25',
};

describe('PlotOfTheDayTerminal', () => {
  beforeEach(() => {
    trackEvent.mockClear();
  });

  it('renders nothing without potd data', () => {
    const { container } = render(<PlotOfTheDayTerminal potd={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('tracks nav_click on filename, github link and image', async () => {
    const user = userEvent.setup();
    render(<PlotOfTheDayTerminal potd={potd} />);

    await user.click(screen.getByText(/plots\/scatter-basic\/matplotlib\.py/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'potd_terminal_filename' }));

    const githubLink = screen.getByLabelText('Open source on GitHub');
    expect(githubLink.getAttribute('href')).toMatch(
      /\/blob\/main\/plots\/scatter-basic\/implementations\/python\/matplotlib\.py$/,
    );
    await user.click(githubLink);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'potd_terminal_github' }));

    await user.click(screen.getByLabelText(/Open Basic Scatter implementation/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'potd_terminal_image' }));
  });
});
