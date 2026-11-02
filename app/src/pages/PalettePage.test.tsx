import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PalettePage } from 'src/pages/PalettePage';
import { paths } from 'src/routes/paths';
import { act, fireEvent, render, screen, within } from 'src/test-utils';

const mockTrackPageview = vi.fn();

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({
    trackPageview: mockTrackPageview,
  }),
  useTheme: () => ({
    isDark: false,
  }),
}));

const IMPRINT_LABELS = [
  'Copy #009E73 (brand green) to clipboard',
  'Copy #C475FD (lavender) to clipboard',
  'Copy #4467A3 (blue) to clipboard',
  'Copy #BD8233 (ochre) to clipboard',
  'Copy #AE3030 (matte red) to clipboard',
  'Copy #2ABCCD (cyan) to clipboard',
  'Copy #954477 (rose) to clipboard',
  'Copy #99B314 (lime) to clipboard',
];

const CVD_OPTIMAL_LABELS = [
  'Copy #009E73 (brand green) to clipboard',
  'Copy #C475FD (lavender) to clipboard',
  'Copy #99B314 (lime) to clipboard',
  'Copy #954477 (rose) to clipboard',
  'Copy #AE3030 (matte red) to clipboard',
  'Copy #2ABCCD (cyan) to clipboard',
  'Copy #4467A3 (blue) to clipboard',
  'Copy #BD8233 (ochre) to clipboard',
];

describe('PalettePage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockTrackPageview.mockReset();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('emits a pageview analytics event for paths.palette on mount', () => {
    render(<PalettePage />);

    expect(mockTrackPageview).toHaveBeenCalledTimes(1);
    expect(mockTrackPageview).toHaveBeenCalledWith(paths.palette);
  });

  it('shows copied ✓ for 1,499 ms and restores the hex at 1,500 ms for both a palette swatch and a semantic anchor', async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(<PalettePage />);

    const brandButton = screen.getByRole('button', {
      name: 'Copy #009E73 (brand green) to clipboard',
    });
    expect(within(brandButton).getByText('#009E73')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(brandButton);
    });

    expect(writeText).toHaveBeenCalledWith('#009E73');
    expect(within(brandButton).getByText('copied ✓')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1499);
    });
    expect(within(brandButton).getByText('copied ✓')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(within(brandButton).queryByText('copied ✓')).not.toBeInTheDocument();
    expect(within(brandButton).getByText('#009E73')).toBeInTheDocument();

    const amberButton = screen.getByRole('button', {
      name: 'Copy #DDCC77 (amber) to clipboard',
    });
    expect(amberButton).toHaveTextContent('#DDCC77');

    await act(async () => {
      fireEvent.click(amberButton);
    });

    expect(writeText).toHaveBeenCalledWith('#DDCC77');
    expect(amberButton).toHaveTextContent('copied ✓');

    act(() => {
      vi.advanceTimersByTime(1499);
    });
    expect(amberButton).toHaveTextContent('copied ✓');

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(amberButton).toHaveTextContent('#DDCC77');
  });

  it('reorders the palette grid to CVD-optimal order (lime third) and restores imprint default order', () => {
    render(<PalettePage />);

    const gridSection = screen
      .getByRole('heading', { name: /the 8 categorical hues/i })
      .closest('section')!;
    const getGridLabels = () =>
      within(gridSection)
        .getAllByRole('button', { name: /^Copy #[0-9A-F]{6}/ })
        .map(btn => btn.getAttribute('aria-label'));

    expect(getGridLabels()).toEqual(IMPRINT_LABELS);

    fireEvent.click(
      screen.getByRole('button', { name: 'CVD-optimal (max ΔE under colorblindness)' })
    );
    expect(getGridLabels()).toEqual(CVD_OPTIMAL_LABELS);

    fireEvent.click(screen.getByRole('button', { name: 'imprint (default)' }));
    expect(getGridLabels()).toEqual(IMPRINT_LABELS);
  });

  it('wires wheel expansion, comparison palette selection, language tabs, and the OKLCH switch through page state', () => {
    render(<PalettePage />);

    const expandWheel = screen.getByRole('button', {
      name: 'Expand the hue–chroma wheel to compare palettes',
    });
    expect(expandWheel).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(expandWheel);
    expect(screen.getByRole('button', { name: 'Collapse the hue–chroma wheel' })).toHaveAttribute(
      'aria-expanded',
      'true'
    );

    const okabeButton = screen.getByRole('button', { name: 'Okabe-Ito' });
    expect(okabeButton).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(okabeButton);
    expect(okabeButton).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('tab', { name: 'R' }));
    expect(screen.getByText(/IMPRINT <- list\(/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('switch', { name: 'OKLCH' }));
    expect(screen.getByText(/# oklch\(0\.620 0\.130 165\.5\)/)).toBeInTheDocument();
  });
});
