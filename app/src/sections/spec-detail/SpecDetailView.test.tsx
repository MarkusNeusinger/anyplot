import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeContext, type ThemeContextValue } from 'src/hooks/useLayoutContext';
import { SpecDetailView } from 'src/sections/spec-detail/SpecDetailView';
import { fireEvent, render, screen, userEvent, waitFor } from 'src/test-utils';
import type { Implementation } from 'src/types';

const darkThemeValue: ThemeContextValue = {
  mode: 'dark',
  effective: 'dark',
  isDark: true,
  setMode: vi.fn(),
  cycle: vi.fn(),
};

vi.mock('src/utils/responsiveImage', () => ({
  buildDetailSrcSet: (url: string, fmt: string) => `${url}-srcset-${fmt}`,
  DETAIL_SIZES: '100vw',
}));

const makeImpl = (overrides: Partial<Implementation> = {}): Implementation => ({
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  preview_url: 'https://example.com/plot.png',
  preview_html: undefined,
  quality_score: 85,
  code: 'import matplotlib\nprint("hello")',
  ...overrides,
});

const implA = makeImpl({ library_id: 'altair', library_name: 'Altair' });
const implB = makeImpl({ library_id: 'matplotlib', library_name: 'Matplotlib' });
const implC = makeImpl({
  library_id: 'plotly',
  library_name: 'Plotly',
  preview_html: '<div>interactive</div>',
});

const defaultProps = {
  specId: 'scatter-basic',
  specTitle: 'Basic Scatter Plot',
  selectedLibrary: 'matplotlib',
  currentImpl: implB,
  implementations: [implB, implA, implC],
  imageLoaded: true,
  codeCopied: null,
  downloadDone: null,
  viewMode: 'preview' as const,
  onImageLoad: vi.fn(),
  onCopyCode: vi.fn(),
  onDownload: vi.fn(),
  onViewModeChange: vi.fn(),
  onTrackEvent: vi.fn(),
};

const okResponse = () =>
  new Response(JSON.stringify({ status: 'ok' }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

describe('SpecDetailView', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders image with correct alt text', () => {
    render(<SpecDetailView {...defaultProps} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('alt', 'Basic Scatter Plot - matplotlib');
  });

  it('shows skeleton when image is not loaded', () => {
    const { container } = render(<SpecDetailView {...defaultProps} imageLoaded={false} />);
    // MUI Skeleton renders a span with class containing MuiSkeleton
    const skeleton = container.querySelector('.MuiSkeleton-root');
    expect(skeleton).toBeInTheDocument();
  });

  it('does not show skeleton when image is loaded', () => {
    const { container } = render(<SpecDetailView {...defaultProps} imageLoaded={true} />);
    const skeleton = container.querySelector('.MuiSkeleton-root');
    expect(skeleton).not.toBeInTheDocument();
  });

  it('renders Copy Code button that calls onCopyCode', async () => {
    const onCopyCode = vi.fn();
    const user = userEvent.setup();

    render(<SpecDetailView {...defaultProps} onCopyCode={onCopyCode} />);

    const btn = screen.getByRole('button', { name: /copy code/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onCopyCode).toHaveBeenCalledWith(implB);
  });

  it('renders Download PNG button that calls onDownload', async () => {
    const onDownload = vi.fn();
    const user = userEvent.setup();

    render(<SpecDetailView {...defaultProps} onDownload={onDownload} />);

    const btn = screen.getByRole('button', { name: /download png/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onDownload).toHaveBeenCalledWith(implB);
  });

  it('shows Show Interactive button only when preview_html exists', () => {
    // No preview_html on current impl
    const { rerender } = render(<SpecDetailView {...defaultProps} />);
    expect(screen.queryByRole('button', { name: /show interactive/i })).not.toBeInTheDocument();

    // With preview_html — renders an in-page toggle button (no longer a link)
    rerender(<SpecDetailView {...defaultProps} currentImpl={implC} selectedLibrary="plotly" />);
    expect(screen.getByRole('button', { name: /show interactive/i })).toBeInTheDocument();
  });

  it('switches between the preview and the interactive view, each a use of view_mode_change', async () => {
    const user = userEvent.setup();
    const onViewModeChange = vi.fn();
    const onTrackEvent = vi.fn();
    const props = {
      ...defaultProps,
      currentImpl: implC,
      selectedLibrary: 'plotly',
      onViewModeChange,
      onTrackEvent,
    };
    const { rerender } = render(<SpecDetailView {...props} />);

    await user.click(screen.getByRole('button', { name: /show interactive/i }));
    expect(onViewModeChange).toHaveBeenLastCalledWith('interactive');
    expect(onTrackEvent).toHaveBeenLastCalledWith('ui_feature', { feature: 'view_mode_change' });

    rerender(<SpecDetailView {...props} viewMode="interactive" />);
    await user.click(screen.getByRole('button', { name: /show static preview/i }));
    expect(onViewModeChange).toHaveBeenLastCalledWith('preview');
    expect(onTrackEvent).toHaveBeenCalledTimes(2);
    expect(onTrackEvent).toHaveBeenLastCalledWith('ui_feature', { feature: 'view_mode_change' });
  });

  it('keeps the "use with my data" entry off the image (it sits beside the carousel)', () => {
    render(<SpecDetailView {...defaultProps} />);
    expect(screen.queryByRole('button', { name: /use with my data/i })).not.toBeInTheDocument();
  });

  it('shows implementation counter with current/total', () => {
    render(<SpecDetailView {...defaultProps} />);
    // Sorted alphabetically: altair(1), matplotlib(2), plotly(3) -> matplotlib = 2/3
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('does not show implementation counter when only one implementation', () => {
    render(<SpecDetailView {...defaultProps} implementations={[implB]} />);
    expect(screen.queryByText('1/1')).not.toBeInTheDocument();
  });

  it('shows ">>> .copied" overlay when codeCopied matches current library', () => {
    render(<SpecDetailView {...defaultProps} codeCopied="matplotlib" />);
    expect(screen.getByText('>>> .copied')).toBeInTheDocument();
  });

  it('shows ">>> .downloaded" overlay when downloadDone matches current library', () => {
    render(<SpecDetailView {...defaultProps} downloadDone="matplotlib" />);
    expect(screen.getByText('>>> .downloaded')).toBeInTheDocument();
  });

  it('does not show overlay when codeCopied does not match current library', () => {
    render(<SpecDetailView {...defaultProps} codeCopied="plotly" />);
    expect(screen.queryByText('>>> .copied')).not.toBeInTheDocument();
    expect(screen.queryByText('>>> .downloaded')).not.toBeInTheDocument();
  });

  it('toggles zoom on click via aria-label change', async () => {
    const user = userEvent.setup();
    render(<SpecDetailView {...defaultProps} />);

    const zoomContainer = screen.getByRole('button', { name: 'Zoom in' });
    expect(zoomContainer).toBeInTheDocument();

    await user.click(zoomContainer);
    expect(screen.getByRole('button', { name: 'Zoom out' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Zoom out' }));
    expect(screen.getByRole('button', { name: 'Zoom in' })).toBeInTheDocument();
  });

  it('counts zooming in as a use of the plot, and zooming out as nothing more', async () => {
    // The zoom opens no page: without the event, a visitor who lands here, looks closer and
    // leaves would be one who did nothing.
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();
    render(<SpecDetailView {...defaultProps} onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByRole('button', { name: 'Zoom in' }));
    expect(onTrackEvent).toHaveBeenCalledExactlyOnceWith('ui_feature', { feature: 'plot_zoom' });

    await user.click(screen.getByRole('button', { name: 'Zoom out' }));
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
  });

  it('adapts overlay action buttons to a dark surface in dark mode', () => {
    // Light mode (default context): bright surface so buttons read on a light preview.
    const { unmount } = render(<SpecDetailView {...defaultProps} />);
    const lightBtn = screen.getByRole('button', { name: /download png/i });
    expect(lightBtn).toHaveStyle({ backgroundColor: 'rgba(255,255,255,0.9)' });
    unmount();

    // Dark mode: dark surface so the button no longer clashes with the dark preview.
    render(
      <ThemeContext.Provider value={darkThemeValue}>
        <SpecDetailView {...defaultProps} />
      </ThemeContext.Provider>
    );
    const darkBtn = screen.getByRole('button', { name: /download png/i });
    expect(darkBtn).toHaveStyle({ backgroundColor: 'rgba(36,36,32,0.9)' });
  });

  it('renders nothing special when currentImpl is null', () => {
    render(<SpecDetailView {...defaultProps} currentImpl={null} />);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /copy code/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /thumbs up/i })).not.toBeInTheDocument();
  });

  describe('plot vote', () => {
    it('renders 👍 and 👎 over the plot and no report action', () => {
      render(<SpecDetailView {...defaultProps} />);
      expect(screen.getByRole('button', { name: /thumbs up/i })).toHaveAttribute(
        'aria-pressed',
        'false'
      );
      expect(screen.getByRole('button', { name: /thumbs down/i })).toHaveAttribute(
        'aria-pressed',
        'false'
      );
      expect(screen.queryByRole('link', { name: /report issue/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /report issue/i })).not.toBeInTheDocument();
    });

    it('renders both thumbs on the interactive surface too', () => {
      render(
        <SpecDetailView
          {...defaultProps}
          currentImpl={implC}
          selectedLibrary="plotly"
          viewMode="interactive"
        />
      );
      expect(screen.getByRole('button', { name: /thumbs up/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /thumbs down/i })).toBeInTheDocument();
    });

    it('submits a thumbs_up for the current implementation and inks the button', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(okResponse());
      const user = userEvent.setup();
      render(<SpecDetailView {...defaultProps} />);

      const up = screen.getByRole('button', { name: /thumbs up/i });
      await user.click(up);

      // Optimistic highlight + toast are applied immediately.
      expect(up).toHaveAttribute('aria-pressed', 'true');
      expect(screen.getByText('>>> .liked')).toBeInTheDocument();

      await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
      expect(String(fetchSpy.mock.calls[0][0])).toMatch(/\/feedback$/);
      const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
      expect(body).toMatchObject({
        message: null,
        reaction: 'thumbs_up',
        spec_id: 'scatter-basic',
        library_id: 'matplotlib',
        language: 'python',
      });
      expect(typeof body.session_id).toBe('string');
    });

    it('locks the vote: neither thumb posts again once one is chosen', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(okResponse());
      const user = userEvent.setup();
      render(<SpecDetailView {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /thumbs up/i }));
      await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));

      const down = screen.getByRole('button', { name: /thumbs down/i });
      expect(down).toBeDisabled();
      await user.click(screen.getByRole('button', { name: /thumbs up/i }));
      // The disabled thumb rejects pointer events; a synthetic click stands in
      // for a user who works around the UI (e.g. via devtools).
      fireEvent.click(down);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      expect(screen.getByRole('button', { name: /thumbs up/i })).toHaveAttribute(
        'aria-pressed',
        'true'
      );
      expect(down).toHaveAttribute('aria-pressed', 'false');
    });

    it('rolls the highlight back when the submit fails', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 500 }));
      const user = userEvent.setup();
      render(<SpecDetailView {...defaultProps} />);

      const down = screen.getByRole('button', { name: /thumbs down/i });
      await user.click(down);
      await waitFor(() => expect(down).toHaveAttribute('aria-pressed', 'false'));
      expect(screen.queryByText('>>> .disliked')).not.toBeInTheDocument();
    });

    it('remembers the vote per implementation across remounts and library switches', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(okResponse());
      const user = userEvent.setup();
      const { rerender, unmount } = render(<SpecDetailView {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /thumbs up/i }));
      await waitFor(() =>
        expect(screen.getByRole('button', { name: /thumbs up/i })).toHaveAttribute(
          'aria-pressed',
          'true'
        )
      );

      // Another library of the same spec starts unrated.
      rerender(<SpecDetailView {...defaultProps} currentImpl={implA} selectedLibrary="altair" />);
      expect(screen.getByRole('button', { name: /thumbs up/i })).toHaveAttribute(
        'aria-pressed',
        'false'
      );

      // Coming back — even after a full remount — shows the earlier vote.
      unmount();
      render(<SpecDetailView {...defaultProps} />);
      expect(screen.getByRole('button', { name: /thumbs up/i })).toHaveAttribute(
        'aria-pressed',
        'true'
      );
    });

    describe('per version', () => {
      const v1 = makeImpl({ updated: '2026-11-01T03:00:00' });
      const v2 = makeImpl({ updated: '2026-11-08T04:54:13' });

      it('stores the vote under the version the visitor saw', async () => {
        vi.spyOn(globalThis, 'fetch').mockResolvedValue(okResponse());
        const user = userEvent.setup();
        render(<SpecDetailView {...defaultProps} currentImpl={v1} />);

        await user.click(screen.getByRole('button', { name: /thumbs up/i }));
        await waitFor(() =>
          expect(JSON.parse(localStorage.getItem('anyplot_plot_votes') ?? '{}')).toEqual({
            'scatter-basic/python/matplotlib@2026-11-01T03:00:00': 'thumbs_up',
          })
        );
      });

      it('leaves a regenerated plot unrated, so the visitor can rate the new image once', async () => {
        // A fresh Response per call: a body can be read only once.
        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => okResponse());
        const user = userEvent.setup();
        const { rerender, unmount } = render(<SpecDetailView {...defaultProps} currentImpl={v1} />);

        await user.click(screen.getByRole('button', { name: /thumbs up/i }));
        await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
        expect(screen.getByRole('button', { name: /thumbs down/i })).toBeDisabled();

        // The page now serves the regenerated implementation: a new `updated`.
        rerender(<SpecDetailView {...defaultProps} currentImpl={v2} />);
        const up = screen.getByRole('button', { name: /thumbs up/i });
        const down = screen.getByRole('button', { name: /thumbs down/i });
        expect(up).toHaveAttribute('aria-pressed', 'false');
        expect(down).toHaveAttribute('aria-pressed', 'false');
        expect(down).toBeEnabled();

        await user.click(down);
        await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
        expect(down).toHaveAttribute('aria-pressed', 'true');
        expect(up).toBeDisabled();

        // Each version keeps its own vote, also after a full remount.
        unmount();
        render(<SpecDetailView {...defaultProps} currentImpl={v2} />);
        expect(screen.getByRole('button', { name: /thumbs down/i })).toHaveAttribute(
          'aria-pressed',
          'true'
        );
        expect(JSON.parse(localStorage.getItem('anyplot_plot_votes') ?? '{}')).toEqual({
          'scatter-basic/python/matplotlib@2026-11-01T03:00:00': 'thumbs_up',
          'scatter-basic/python/matplotlib@2026-11-08T04:54:13': 'thumbs_down',
        });
      });

      it('neither inks nor blocks a thumb for a vote stored before versions were kept', async () => {
        localStorage.setItem(
          'anyplot_plot_votes',
          JSON.stringify({ 'scatter-basic/python/matplotlib': 'thumbs_down' })
        );
        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(okResponse());
        const user = userEvent.setup();
        render(<SpecDetailView {...defaultProps} currentImpl={v2} />);

        const up = screen.getByRole('button', { name: /thumbs up/i });
        const down = screen.getByRole('button', { name: /thumbs down/i });
        expect(up).toHaveAttribute('aria-pressed', 'false');
        expect(down).toHaveAttribute('aria-pressed', 'false');
        expect(up).toBeEnabled();
        expect(down).toBeEnabled();

        await user.click(up);
        await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
        expect(up).toHaveAttribute('aria-pressed', 'true');
      });
    });
  });
});
