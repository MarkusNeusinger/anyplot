import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();
const navigate = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent }),
    useAppData: () => ({
      specsData: [],
      librariesData: [{ id: 'matplotlib', name: 'matplotlib' }],
      stats: { specs: 100, plots: 900, libraries: 9, lines_of_code: 50000 },
    }),
  };
});

vi.mock('src/hooks/useFeaturedSpecs', () => ({
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

const potdHook = vi.hoisted(() => ({
  status: 'loading' as 'loading' | 'ready' | 'none' | 'failed',
  retry: (): void => {},
}));
vi.mock('src/hooks/usePlotOfTheDay', () => ({
  usePlotOfTheDay: () => ({ potd: null, status: potdHook.status, retry: potdHook.retry }),
}));

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return { ...actual, useTheme: () => ({ isDark: false, toggle: vi.fn() }) };
});

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

// Records the props the page hands the hero.
const heroProps = vi.hoisted(() => vi.fn());
vi.mock('src/sections/landing/HeroSection', () => ({
  HeroSection: (props: object) => {
    heroProps(props);
    return <div data-testid="hero" />;
  },
}));

vi.mock('src/sections/landing/NumbersStrip', () => ({
  NumbersStrip: () => <div data-testid="numbers" />,
}));

import { LandingPage } from 'src/pages/LandingPage';

describe('LandingPage', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    navigate.mockClear();
    heroProps.mockClear();
    potdHook.status = 'loading';
    potdHook.retry = () => {};
  });

  it('hands the plot-of-the-day status and its retry to the hero', () => {
    const retry = vi.fn();
    potdHook.status = 'failed';
    potdHook.retry = retry;
    render(<LandingPage />);

    expect(heroProps).toHaveBeenLastCalledWith(
      expect.objectContaining({ potd: null, potdStatus: 'failed', onRetryPotd: retry })
    );
  });

  it('keeps each palette name in its colour column, and a click copies the hex', async () => {
    const user = userEvent.setup();
    // userEvent installs its own clipboard, so the spy goes on after the setup.
    const writeText = vi.spyOn(navigator.clipboard, 'writeText');
    const { container } = render(<LandingPage />);

    // The name sits in the same flex item as its colour block, so it moves with the colour
    // when a hue expands; names in a row of their own drifted under the wrong colours.
    const hues = Array.from(container.querySelectorAll('[data-strip] > [data-hue]'));
    expect(
      hues.map(hue => [
        hue.querySelector('[data-hue-name]')?.textContent,
        hue.querySelector('[data-hue-block]')?.getAttribute('aria-label'),
      ])
    ).toEqual([
      ['brand green', 'Copy #009E73 to clipboard'],
      ['lavender', 'Copy #C475FD to clipboard'],
      ['blue', 'Copy #4467A3 to clipboard'],
      ['ochre', 'Copy #BD8233 to clipboard'],
      ['matte red', 'Copy #AE3030 to clipboard'],
      ['cyan', 'Copy #2ABCCD to clipboard'],
      ['rose', 'Copy #954477 to clipboard'],
      ['lime', 'Copy #99B314 to clipboard'],
    ]);
    expect(container.querySelectorAll('[data-hue-name]')).toHaveLength(8);

    await user.click(screen.getByRole('button', { name: 'Copy #4467A3 to clipboard' }));
    expect(writeText).toHaveBeenCalledWith('#4467A3');
    const copied = await screen.findByText('copied ✓');
    expect(copied.closest('[data-hue]')).toHaveAttribute('data-hue', 'blue');
  });

  it('describes itself by the hero block, the libraries and the palette', () => {
    render(<LandingPage />);

    expect(document.head.querySelector('meta[name="description"]')).toHaveAttribute(
      'content',
      'any library. get inspired. grab the code. make it yours. 15 plotting libraries across python, r, julia & javascript, colourblind-safe, open source.'
    );
  });

  it('tracks library card clicks and navigates', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByText('matplotlib'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'library_card',
      target: '/plots',
      library: 'matplotlib',
    });
    expect(navigate).toHaveBeenCalledWith('/plots?lib=matplotlib');
  });

  it('tracks featured thumb clicks', async () => {
    const user = userEvent.setup();
    const { container } = render(<LandingPage />);

    const thumb = container.querySelector('a[href="/scatter-basic"]');
    expect(thumb).toBeTruthy();
    await user.click(thumb!);
    expect(trackEvent).toHaveBeenCalledWith(
      'nav_click',
      expect.objectContaining({
        source: 'featured_thumb',
        target: 'spec_hub',
        spec: 'scatter-basic',
      })
    );
  });

  it('tracks the "more in catalogue" link', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    const more = screen.getByText(/more in the catalogue/);
    await user.click(more);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'specs_more_link',
      target: '/specs',
    });
  });

  it('tracks the suggest_spec link', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByText(/suggest/));
    expect(trackEvent).toHaveBeenCalledWith(
      'nav_click',
      expect.objectContaining({ source: 'suggest_spec_link' })
    );
  });

  it('tracks the map teaser visual click', async () => {
    const user = userEvent.setup();
    render(<LandingPage />);

    await user.click(screen.getByLabelText(/Open the interactive specifications map/));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'map_teaser_preview',
      target: '/map',
    });
  });
});
