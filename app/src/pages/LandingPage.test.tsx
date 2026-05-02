import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();
const trackPageview = vi.fn();
const navigate = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview }),
    useAppData: () => ({
      specsData: [],
      librariesData: [{ id: 'matplotlib', name: 'matplotlib' }],
      stats: { specs: 100, plots: 900, libraries: 9, lines_of_code: 50000 },
    }),
  };
});

vi.mock('../hooks/useFeaturedSpecs', () => ({
  useFeaturedSpecs: () => [
    {
      spec_id: 'scatter-basic',
      spec_title: 'Basic Scatter',
      spec_description: 'A scatter plot',
      library_id: 'matplotlib',
      preview_url: 'https://cdn.example.com/scatter.png',
      preview_url_light: null,
      preview_url_dark: null,
    },
  ],
}));

vi.mock('../hooks/usePlotOfTheDay', () => ({
  usePlotOfTheDay: () => null,
}));

vi.mock('../hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useLayoutContext')>('../hooks/useLayoutContext');
  return { ...actual, useTheme: () => ({ isDark: false, toggle: vi.fn() }) };
});

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

vi.mock('../components/HeroSection', () => ({
  HeroSection: () => <div data-testid="hero" />,
}));

vi.mock('../components/NumbersStrip', () => ({
  NumbersStrip: () => <div data-testid="numbers" />,
}));

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <div data-testid="helmet">{children}</div>,
}));

import { LandingPage } from './LandingPage';

describe('LandingPage', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    trackPageview.mockClear();
    navigate.mockClear();
  });

  it('fires a pageview for / on mount', () => {
    render(<LandingPage />);
    expect(trackPageview).toHaveBeenCalledWith('/');
  });

  it('tracks library card clicks and navigates', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByText('matplotlib'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'library_card',
      target: '/plots',
      value: 'matplotlib',
    });
    expect(navigate).toHaveBeenCalledWith('/plots?lib=matplotlib');
  });

  it('tracks featured thumb clicks', async () => {
    const user = userEvent.setup();
    const { container } = render(<LandingPage />);

    const thumb = container.querySelector('a[href="/scatter-basic"]');
    expect(thumb).toBeTruthy();
    await user.click(thumb!);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'featured_thumb', target: 'spec_hub', spec: 'scatter-basic' }));
  });

  it('tracks the "more in catalogue" link', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    const more = screen.getByText(/more in the catalogue/);
    await user.click(more);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'specs_more_link', target: '/specs' });
  });

  it('tracks the suggest_spec link and the okabe-ito reference', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByText(/suggest/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'suggest_spec_link' }));

    await user.click(screen.getByText(/Okabe/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'palette_okabe_ito' }));
  });

  it('tracks the map teaser visual and the map.open() text link', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByLabelText(/Open the interactive specifications map/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'map_teaser_preview', target: '/map' });

    const mapOpenLink = screen.getByText((_, el) => el?.tagName === 'A' && el.textContent === 'map.open()');
    await user.click(mapOpenLink);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'map_teaser_link' }));
  });
});
