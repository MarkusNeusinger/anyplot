import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PlotVersion } from 'src/hooks/useAgentSession';
import { RELAY_READY_TIMEOUT_MS } from 'src/sections/agent-chat/InteractivePreview';
import { ResultCard, type ResultCardProps } from 'src/sections/agent-chat/ResultCard';
import { act, fireEvent, render, screen, userEvent, waitFor } from 'src/test-utils';

// The lazy-loaded highlighter, reduced to the code and the grammar it was asked for.
vi.mock('src/components/CodeHighlighter', () => ({
  default: ({ code, language }: { code: string; language?: string }) => (
    <pre data-testid="code-highlighter" data-language={language}>
      {code}
    </pre>
  ),
}));

const pngBlob = new Blob(['png'], { type: 'image/png' });

const makeVersion = (overrides: Partial<PlotVersion> = {}): PlotVersion => ({
  number: 2,
  library: 'matplotlib',
  theme: 'light',
  result: {
    status: 'needs_attention',
    reason: null,
    attempts: 2,
    artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
    changes: ['Marker size raised'],
    residual_defects: ['VQ-03 light: markers overlap the label'],
    version: 2,
  },
  images: { light: { state: 'ready', url: 'blob:light', blob: pngBlob, status: 'ok' } },
  code: { state: 'ready', text: 'import pandas as pd\ndf = pd.read_csv("data.csv")\n' },
  ...overrides,
});

function renderCard(props: Partial<ResultCardProps> = {}) {
  const handlers = {
    onRequestTheme: vi.fn(),
    onFetchArtifact: vi.fn(async () => new Blob(['a,b\n1,2\n'], { type: 'text/csv' })),
    onTrack: vi.fn(),
    onOutcome: vi.fn(),
  };
  render(
    <ResultCard
      version={makeVersion()}
      specId="scatter-basic"
      language="python"
      latest
      busy={false}
      {...handlers}
      {...props}
    />
  );
  return handlers;
}

let clicked: { href: string; download: string }[];

beforeEach(() => {
  clicked = [];
  URL.createObjectURL = vi.fn(() => 'blob:download');
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement
  ) {
    clicked.push({ href: this.href, download: this.download });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('ResultCard', () => {
  it('shows the rendered image, the changes and the residual notes', () => {
    renderCard();
    expect(screen.getByAltText('Adapted plot, version 2, light theme')).toHaveAttribute(
      'src',
      'blob:light'
    );
    expect(screen.getByText('Marker size raised')).toBeInTheDocument();
    expect(screen.getByText('VQ-03 light: markers overlap the label')).toBeInTheDocument();
    expect(screen.getByTestId('result-status')).toHaveTextContent('needs attention');
    // Two attempts are the first try and one repair round, named as the progress timeline names them.
    expect(screen.getByText('second try')).toBeInTheDocument();
    expect(screen.getByTestId('result-feedback-slot')).toBeInTheDocument();
  });

  it('sizes the image box to the loaded PNG, footer strip included', () => {
    renderCard();
    const box = screen.getByTestId('result-image-box');
    expect(getComputedStyle(box).aspectRatio).toBe('3200/1864');

    const image = screen.getByAltText('Adapted plot, version 2, light theme');
    Object.defineProperty(image, 'naturalWidth', { value: 2400 });
    Object.defineProperty(image, 'naturalHeight', { value: 2448 });
    fireEvent.load(image);

    expect(getComputedStyle(box).aspectRatio).toBe('2400/2448');
  });

  it('copies the PNG with the Clipboard API', async () => {
    const write = vi.fn(async () => undefined);
    vi.stubGlobal(
      'ClipboardItem',
      class {
        constructor(readonly items: Record<string, Blob>) {}
      }
    );
    Object.defineProperty(navigator, 'clipboard', {
      value: { write, writeText: vi.fn() },
      configurable: true,
    });
    const { onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy image' }));
    expect(write).toHaveBeenCalledTimes(1);
    const [items] = write.mock.calls[0] as unknown as [{ items: Record<string, Blob> }[]];
    expect(items[0].items['image/png']).toBe(pngBlob);
    expect(await screen.findByText('>>> .copied')).toBeInTheDocument();
    expect(clicked).toEqual([]);
    expect(onOutcome.mock.calls).toEqual([['copied_image', 2]]);
  });

  it('downloads the PNG when the browser cannot copy images', async () => {
    vi.stubGlobal('ClipboardItem', undefined);
    const { onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy image' }));
    expect(clicked).toEqual([
      { href: 'blob:download', download: 'scatter-basic-matplotlib-v2-light.png' },
    ]);
    expect(await screen.findByText('>>> .downloaded')).toBeInTheDocument();
    // The user got a download, not a copy, and the beacon says so.
    expect(onOutcome.mock.calls).toEqual([['downloaded_png', 2]]);
  });

  it('downloads the PNG and opens it full size', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    const { onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Download PNG' }));
    expect(clicked.map(entry => entry.download)).toEqual(['scatter-basic-matplotlib-v2-light.png']);
    await userEvent.click(screen.getByRole('button', { name: 'Open full size' }));
    expect(open).toHaveBeenCalledWith('blob:light', '_blank', 'noopener,noreferrer');
    // Opening full size is no outcome of its own.
    expect(onOutcome.mock.calls).toEqual([['downloaded_png', 2]]);
  });

  it('copies the code and records copy_code for the agent chat', async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });
    const { onTrack, onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy code' }));
    expect(writeText).toHaveBeenCalledWith('import pandas as pd\ndf = pd.read_csv("data.csv")\n');
    expect(onTrack).toHaveBeenCalledWith('copy_code', {
      spec: 'scatter-basic',
      library: 'matplotlib',
      method: 'agent',
      page: 'agent_chat',
    });
    expect(onOutcome.mock.calls).toEqual([['copied_code', 2]]);
  });

  it('reports no copied code when the clipboard refuses it', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn(async () => Promise.reject(new Error('denied'))) },
      configurable: true,
    });
    const { onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy code' }));
    expect(onOutcome).not.toHaveBeenCalled();
  });

  it('highlights the code in its version library language, not the page language', async () => {
    const version = makeVersion({
      library: 'ggplot2',
      code: { state: 'ready', text: 'df <- readr::read_csv("data.csv")\n' },
    });
    version.result = { ...version.result, artifacts: ['plot-light.png', 'plot.R', 'data.csv'] };
    renderCard({ version, language: 'python' });
    expect(await screen.findByTestId('code-highlighter')).toHaveAttribute('data-language', 'r');
  });

  it('keeps the page language for a library the app does not know', async () => {
    renderCard({ version: makeVersion({ library: 'unknown-lib' }), language: 'python' });
    expect(await screen.findByTestId('code-highlighter')).toHaveAttribute(
      'data-language',
      'python'
    );
  });

  it('downloads the code under its language name when the version names another artifact', async () => {
    const version = makeVersion();
    version.result = { ...version.result, artifacts: ['plot-light.png', 'plot.R', 'data.csv'] };
    const { onOutcome } = renderCard({ version });
    expect(screen.getByText(".download('plot.R')")).toBeInTheDocument();
    expect(screen.getByText('# plot.R runs next to data.csv')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Download plot.R' }));
    await waitFor(() => expect(clicked.map(entry => entry.download)).toEqual(['plot.R']));
    expect(onOutcome).toHaveBeenCalledWith('downloaded_code', 2);
  });

  it('downloads plot.py and data.csv under the names the code expects', async () => {
    const { onFetchArtifact, onOutcome } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Download plot.py' }));
    await userEvent.click(screen.getByRole('button', { name: 'Download data.csv' }));
    await waitFor(() =>
      expect(clicked.map(entry => entry.download)).toEqual(['plot.py', 'data.csv'])
    );
    // plot.py comes from the code on screen; data.csv from the artifact route.
    expect(onFetchArtifact).toHaveBeenCalledTimes(1);
    expect(onFetchArtifact).toHaveBeenCalledWith(2, 'data.csv');
    expect(onOutcome.mock.calls).toEqual([
      ['downloaded_code', 2],
      ['downloaded_data', 2],
    ]);
  });

  describe("a JavaScript plot's page", () => {
    const jsVersion = (overrides: Partial<PlotVersion> = {}) => {
      const version = makeVersion({
        library: 'chartjs',
        code: { state: 'ready', text: 'const data = window.ANYPLOT_DATA;\n' },
        ...overrides,
      });
      version.result = {
        ...version.result,
        artifacts: ['plot-light.png', 'plot.js', 'plot.html', 'data.csv'],
      };
      return version;
    };
    const pageBlob = new Blob(['<!doctype html>'], { type: 'text/html' });

    it('downloads plot.html in the theme on screen and reports downloaded_page', async () => {
      const onFetchArtifact = vi.fn(async () => pageBlob);
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      expect(screen.getByText('# plot.js runs in plot.html')).toBeInTheDocument();
      await userEvent.click(
        screen.getByRole('button', { name: 'Download plot.html, light theme' })
      );
      await waitFor(() => expect(clicked.map(entry => entry.download)).toEqual(['plot.html']));
      expect(onFetchArtifact).toHaveBeenCalledWith(2, 'plot.html', 'light');
      expect(onOutcome.mock.calls).toEqual([['downloaded_page', 2]]);
    });

    it('builds the page of the other theme once the card shows it', async () => {
      const onFetchArtifact = vi.fn(async () => pageBlob);
      renderCard({
        onFetchArtifact,
        version: jsVersion({
          images: {
            light: { state: 'ready', url: 'blob:light', blob: pngBlob, status: 'ok' },
            dark: { state: 'ready', url: 'blob:dark', blob: pngBlob, status: 'ok' },
          },
        }),
      });
      await userEvent.click(screen.getByRole('button', { name: 'dark' }));
      await userEvent.click(screen.getByRole('button', { name: 'Download plot.html, dark theme' }));
      await waitFor(() => expect(onFetchArtifact).toHaveBeenCalledWith(2, 'plot.html', 'dark'));
    });

    it('waits while the session is busy, since the server builds the page', async () => {
      const onFetchArtifact = vi.fn(async () => pageBlob);
      renderCard({ version: jsVersion(), onFetchArtifact, busy: true });
      const button = screen.getByRole('button', { name: 'Download plot.html, light theme' });
      expect(button).toBeDisabled();
      await userEvent.click(button);
      expect(onFetchArtifact).not.toHaveBeenCalled();
      // The code itself stays one click away.
      expect(screen.getByRole('button', { name: 'Download plot.js' })).toBeEnabled();
    });

    it('says so when the page could not be built', async () => {
      const { onOutcome } = renderCard({
        version: jsVersion(),
        onFetchArtifact: vi.fn(async () => Promise.reject(new Error('page_unavailable'))),
      });
      await userEvent.click(
        screen.getByRole('button', { name: 'Download plot.html, light theme' })
      );
      expect(await screen.findByRole('alert')).toHaveTextContent('could not download plot.html');
      expect(onOutcome).not.toHaveBeenCalled();
    });

    it('is not offered for a plot of another language', () => {
      renderCard();
      expect(screen.queryByText(".download('plot.html')")).not.toBeInTheDocument();
      expect(screen.getByText('# plot.py runs next to data.csv')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Show interactive' })).not.toBeInTheDocument();
    });
  });

  describe("a JavaScript plot's interactive preview", () => {
    const jsVersion = (overrides: Partial<PlotVersion> = {}) => {
      const version = makeVersion({ library: 'chartjs', ...overrides });
      version.result = {
        ...version.result,
        artifacts: ['plot-light.png', 'plot.js', 'plot.html', 'data.csv'],
      };
      return version;
    };
    const page = (theme: string) => new Blob([`<p>${theme} page</p>`], { type: 'text/html' });
    const fetchPages = () =>
      vi.fn(async (_version: number, _name: string, theme?: string) => page(theme ?? 'none'));

    it('shows the page through the relay only when asked, and the image again on .preview()', async () => {
      const onFetchArtifact = fetchPages();
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      expect(onFetchArtifact).not.toHaveBeenCalled();
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();

      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));

      const frame = await screen.findByTitle('Interactive plot, version 2, light theme');
      expect(frame).toHaveAttribute('src', expect.stringMatching(/\/preview\/relay$/));
      expect(frame).toHaveAttribute('sandbox', 'allow-scripts');
      expect(onFetchArtifact).toHaveBeenCalledWith(2, 'plot.html', 'light');
      expect(onOutcome.mock.calls).toEqual([['opened_preview', 2]]);
      expect(screen.queryByRole('button', { name: 'Download PNG' })).not.toBeInTheDocument();

      await userEvent.click(screen.getByRole('button', { name: 'Show image' }));
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();
      expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
    });

    it('shows the other theme page on a theme switch and fetches each page once', async () => {
      const onFetchArtifact = fetchPages();
      const { onRequestTheme, onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');

      await userEvent.click(screen.getByRole('button', { name: 'dark' }));
      await screen.findByTitle('Interactive plot, version 2, dark theme');
      await userEvent.click(screen.getByRole('button', { name: 'light' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');

      expect(onFetchArtifact.mock.calls.map(call => call[2])).toEqual(['light', 'dark']);
      // The preview needs no PNG of the dark theme, and one opening is one beacon.
      expect(onRequestTheme).not.toHaveBeenCalled();
      expect(onOutcome.mock.calls).toEqual([['opened_preview', 2]]);
    });

    it('downloads the page the open preview shows without a second build', async () => {
      const onFetchArtifact = fetchPages();
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');

      await userEvent.click(
        screen.getByRole('button', { name: 'Download plot.html, light theme' })
      );

      await waitFor(() => expect(clicked.map(entry => entry.download)).toEqual(['plot.html']));
      expect(onFetchArtifact).toHaveBeenCalledTimes(1);
      expect(onOutcome.mock.calls).toEqual([
        ['opened_preview', 2],
        ['downloaded_page', 2],
      ]);
    });

    it('waits while the session is busy, since the server builds the page', async () => {
      const onFetchArtifact = fetchPages();
      renderCard({ version: jsVersion(), onFetchArtifact, busy: true });
      const open = screen.getByRole('button', { name: 'Show interactive' });
      expect(open).toBeDisabled();
      fireEvent.click(open);
      expect(onFetchArtifact).not.toHaveBeenCalled();
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();
    });

    it('says so when the page could not be built', async () => {
      const onFetchArtifact = vi.fn(async () =>
        Promise.reject(Object.assign(new Error('nope'), { code: 'page_unavailable' }))
      );
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      expect(await screen.findByRole('alert')).toHaveTextContent(
        'could not show the interactive plot (page_unavailable)'
      );
      expect(onOutcome).not.toHaveBeenCalled();
    });

    it('renders the PNG of a theme the preview showed once the image is back', async () => {
      const onFetchArtifact = fetchPages();
      const { onRequestTheme } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');
      await userEvent.click(screen.getByRole('button', { name: 'dark' }));
      await screen.findByTitle('Interactive plot, version 2, dark theme');

      await userEvent.click(screen.getByRole('button', { name: 'Show image' }));

      expect(onRequestTheme).toHaveBeenCalledWith(2, 'dark');
      expect(screen.getByText('rendering dark theme…')).toBeInTheDocument();
    });

    it('frames a square plot square from its page, before its PNG has loaded', async () => {
      const onFetchArtifact = vi.fn(
        async () =>
          new Blob(['<style>.frame { width: 1200px; height: 1200px; }</style>'], {
            type: 'text/html',
          })
      );
      renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));

      const frame = await screen.findByTitle('Interactive plot, version 2, light theme');
      expect(frame.style.width).toBe('1232px');
      expect(getComputedStyle(screen.getByTestId('result-image-box')).aspectRatio).toBe(
        '1232/1232'
      );
    });

    it('says so when the relay does not answer, and mounts a fresh one on a theme click', async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      try {
        renderCard({ version: jsVersion(), onFetchArtifact: fetchPages() });
        fireEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
        await screen.findByTitle('Interactive plot, version 2, light theme');

        act(() => {
          vi.advanceTimersByTime(RELAY_READY_TIMEOUT_MS);
        });

        expect(screen.getByRole('alert')).toHaveTextContent(
          'could not show the interactive plot (relay_unavailable)'
        );
        fireEvent.click(screen.getByRole('button', { name: 'light' }));
        expect(screen.getByTitle('Interactive plot, version 2, light theme')).toBeInTheDocument();
      } finally {
        vi.useRealTimers();
      }
    });

    it('drops the preview and ignores a build still under way when the card collapses', async () => {
      let finish: (blob: Blob) => void = () => undefined;
      const onFetchArtifact = fetchPages();
      onFetchArtifact.mockImplementationOnce(
        () =>
          new Promise<Blob>(resolve => {
            finish = resolve;
          })
      );
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      expect(screen.getByText('building the interactive light plot…')).toBeInTheDocument();

      await userEvent.click(screen.getByRole('button', { name: /^Version 2,/ }));
      finish(page('light'));
      await userEvent.click(screen.getByRole('button', { name: /^Version 2,/ }));
      await waitFor(() =>
        expect(screen.getByRole('button', { name: 'Show interactive' })).toBeEnabled()
      );

      // The late page went nowhere: the image is back, and no opening was reported.
      expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();
      expect(onOutcome).not.toHaveBeenCalled();

      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');
      expect(onFetchArtifact).toHaveBeenCalledTimes(2);
      expect(onOutcome.mock.calls).toEqual([['opened_preview', 2]]);
    });

    it('closes the preview when a newer version arrives', async () => {
      const onFetchArtifact = fetchPages();
      const props: ResultCardProps = {
        version: jsVersion(),
        specId: 'scatter-basic',
        language: 'javascript',
        latest: true,
        busy: false,
        onRequestTheme: vi.fn(),
        onFetchArtifact,
        onTrack: vi.fn(),
      };
      const { rerender } = render(<ResultCard {...props} />);
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');

      rerender(<ResultCard {...props} latest={false} />);
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();

      await userEvent.click(screen.getByRole('button', { name: /^Version 2,/ }));
      expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();
    });
  });

  it('reports no download when the file could not be fetched', async () => {
    const { onOutcome } = renderCard({
      onFetchArtifact: vi.fn(async () => Promise.reject(new Error('gone'))),
    });
    await userEvent.click(screen.getByRole('button', { name: 'Download data.csv' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('could not download data.csv');
    expect(onOutcome).not.toHaveBeenCalled();
  });

  it('asks for the other theme and shows that it renders', async () => {
    const { onRequestTheme } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'dark' }));
    expect(onRequestTheme).toHaveBeenCalledWith(2, 'dark');
    expect(screen.getByText('rendering dark theme…')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'dark' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows the other theme without a request once the version has it', async () => {
    const { onRequestTheme } = renderCard({
      version: makeVersion({
        images: {
          light: { state: 'ready', url: 'blob:light', blob: pngBlob, status: 'ok' },
          dark: { state: 'ready', url: 'blob:dark', blob: pngBlob, status: 'ok' },
        },
      }),
    });
    await userEvent.click(screen.getByRole('button', { name: 'dark' }));
    expect(onRequestTheme).not.toHaveBeenCalled();
    expect(screen.getByAltText('Adapted plot, version 2, dark theme')).toHaveAttribute(
      'src',
      'blob:dark'
    );
  });

  it('holds back a theme that needs a render while the session is busy', async () => {
    const { onRequestTheme } = renderCard({ busy: true });
    const dark = screen.getByRole('button', { name: 'dark' });
    expect(dark).toBeDisabled();
    await userEvent.click(dark);
    expect(onRequestTheme).not.toHaveBeenCalled();
  });

  it('switches to a theme the version already has even while busy', async () => {
    renderCard({
      busy: true,
      version: makeVersion({
        images: {
          light: { state: 'ready', url: 'blob:light', blob: pngBlob, status: 'ok' },
          dark: { state: 'ready', url: 'blob:dark', blob: pngBlob, status: 'ok' },
        },
      }),
    });
    await userEvent.click(screen.getByRole('button', { name: 'dark' }));
    expect(screen.getByAltText('Adapted plot, version 2, dark theme')).toBeInTheDocument();
  });

  it('has no composer of its own: follow-ups go through the thread', () => {
    renderCard();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('form')).not.toBeInTheDocument();
  });

  it('collapses an earlier version and opens it again on request', async () => {
    renderCard({ latest: false });
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Version 2/ }));
    expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
  });

  it('has no feedback control without onSendFeedback', () => {
    renderCard();
    expect(screen.queryByTestId('result-feedback')).not.toBeInTheDocument();
  });

  it('offers quick feedback on the version even while the session is busy', async () => {
    const onSendFeedback = vi.fn(async () => undefined);
    renderCard({ busy: true, onSendFeedback });
    expect(screen.getByRole('form', { name: 'Feedback on version 2' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Thumbs up' }));
    await userEvent.click(screen.getByRole('button', { name: 'Send feedback' }));
    expect(onSendFeedback).toHaveBeenCalledWith(2, {
      reaction: 'thumbs_up',
      message: '',
      includeData: true,
    });
  });

  it("shows the version's stored case, also on an earlier version opened again", async () => {
    renderCard({
      latest: false,
      onSendFeedback: vi.fn(async () => undefined),
      version: makeVersion({
        feedback: { reaction: 'bug', message: null, includeData: false, caseId: 'c1' },
      }),
    });
    await userEvent.click(screen.getByRole('button', { name: /Version 2/ }));
    expect(screen.getByTestId('result-feedback-sent')).toHaveTextContent('sent · v2 · bug');
  });
});
