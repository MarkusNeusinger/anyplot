import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PlotVersion } from 'src/hooks/useAgentSession';
import { RELAY_READY_TIMEOUT_MS } from 'src/sections/agent-chat/InteractivePreview';
import { ResultCard, type ResultCardProps } from 'src/sections/agent-chat/ResultCard';
import { act, fireEvent, render, screen, userEvent, waitFor, within } from 'src/test-utils';

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
    residual_defects: [
      'VQ-03 (light): the markers are 2 px wide → 6 px or more (+4 px). Likely cause: s=2 in ax.scatter.',
    ],
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
  it("puts the image's actions over it, and on a phone by their names on the line under it", () => {
    // On a phone the image's top right corner holds the plot's title, and no hover shows a name.
    const actionsIn = () => {
      const open = screen.getByRole('button', { name: 'Open full size' });
      return {
        image: screen.getByTestId('result-image-box').contains(open),
        line: !!screen.queryByTestId('result-image-actions')?.contains(open),
      };
    };
    const { unmount } = render(
      <ResultCard
        version={makeVersion()}
        specId="scatter-basic"
        language="python"
        latest
        busy={false}
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
      />
    );
    expect(actionsIn()).toEqual({ image: true, line: false });
    unmount();

    vi.stubGlobal(
      'matchMedia',
      vi.fn((query: string) => ({
        matches: query === '(max-width: 599.95px)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        onchange: null,
        dispatchEvent: vi.fn(),
      }))
    );
    renderCard();
    expect(actionsIn()).toEqual({ image: false, line: true });
    expect(screen.getAllByRole('button', { name: 'Download PNG' })).toHaveLength(1);
    const line = screen.getByRole('group', { name: 'Image actions' });
    // The PNG's download first, right under the image, every action by its name.
    expect(
      within(line)
        .getAllByRole('button')
        .map(button => button.textContent)
    ).toEqual(['.download()', '.copy_png()', '.open()']);
    // Each name holds the words on screen, so a voice command that says them finds the button.
    for (const button of within(line).getAllByRole('button')) {
      for (const word of (button.textContent ?? '').replace(/[.()]/g, '').split('_')) {
        expect(button).toHaveAccessibleName(new RegExp(`\\b${word}\\b`, 'i'));
      }
    }
    expect(
      screen.getByTestId('result-image-box').compareDocumentPosition(line) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    // A folded card has no image, so its actions go with it.
    fireEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
    expect(screen.queryByTestId('result-image-actions')).not.toBeInTheDocument();
  });

  it('shows the rendered image, the residual notes and the run in one status line', async () => {
    renderCard();
    expect(screen.getByAltText('Adapted plot, version 2, light theme')).toHaveAttribute(
      'src',
      'blob:light'
    );
    // The notes in plain words; the review's line, with its id, pixels and code, behind the ⓘ.
    expect(screen.getByTestId('residual-notes')).toHaveTextContent(/^some marks are hard to see$/);
    expect(screen.queryByText(/VQ-03|Likely cause/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'The notes in full' }));
    expect(screen.getByTestId('residual-details')).toHaveTextContent(
      'VQ-03 (light): the markers are 2 px wide → 6 px or more (+4 px). Likely cause: s=2 in ax.scatter.'
    );
    await userEvent.keyboard('{Escape}');
    expect(screen.getByTestId('result-status')).toHaveTextContent('needs attention');
    // Two attempts are the first try and one repair round, named as the progress timeline names them.
    const summary = screen.getByRole('button', { name: 'Run details: second try · 1 change' });
    expect(summary).toHaveAttribute('aria-expanded', 'false');
    // Folded: what changed is one click away.
    expect(screen.queryByText('Marker size raised')).not.toBeInTheDocument();
    expect(screen.getByTestId('result-feedback-slot')).toBeInTheDocument();

    await userEvent.click(summary);
    expect(summary).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('# what changed')).toBeInTheDocument();
    expect(screen.getByText('Marker size raised')).toBeInTheDocument();
    await userEvent.click(summary);
    expect(screen.queryByText('Marker size raised')).not.toBeInTheDocument();
  });

  it('opens the rounds of the run from the status line', async () => {
    const version = makeVersion();
    version.result = {
      ...version.result,
      status: 'ok',
      changes: [],
      residual_defects: [],
      rounds: [
        { attempt: 1, outcome: 'review', findings: 2, shipped: false },
        { attempt: 2, outcome: 'ok', findings: 0, shipped: true },
      ],
    } as PlotVersion['result'];
    renderCard({ version });
    expect(screen.queryByRole('table', { name: 'Rounds of version 2' })).toBeNull();
    await userEvent.click(screen.getByRole('button', { name: /^Run details: second try$/ }));
    expect(screen.getByText('# rounds')).toBeInTheDocument();
    expect(screen.getByRole('table', { name: 'Rounds of version 2' })).toBeInTheDocument();
    expect(screen.queryByText('# what changed')).not.toBeInTheDocument();
  });

  it('shows a plain status line when the run has neither rounds nor changes', () => {
    const version = makeVersion();
    version.result = { ...version.result, attempts: 1, changes: [] };
    renderCard({ version });
    expect(screen.getByTestId('result-summary')).toHaveTextContent('first try');
    expect(screen.queryByRole('button', { name: /^Run details/ })).not.toBeInTheDocument();
  });

  it('says how long the plot took in its status line, and no time for one the page did not time', () => {
    renderCard({ version: makeVersion({ readyMs: 72_400 }) });
    // The working line's clock, frozen as the version shipped (the v4 mock's `ready in 1:12`).
    expect(
      screen.getByRole('button', { name: 'Run details: ready in 1:12 · second try · 1 change' })
    ).toBeInTheDocument();
    cleanup();
    const version = makeVersion({ readyMs: 4.5 * 60_000 });
    version.result = { ...version.result, attempts: 1, changes: [] };
    renderCard({ version });
    expect(screen.getByTestId('result-summary')).toHaveTextContent(/^ready in 4:30 · first try$/);
    cleanup();
    // The late read of a cut turn: no field, no time, never a wrong one.
    renderCard();
    expect(screen.getByTestId('result-summary')).not.toHaveTextContent(/ready in/);
  });

  it('folds the code behind .show_code(), with .copy() and the downloads in view', async () => {
    renderCard();
    expect(screen.queryByTestId('code-highlighter')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy code' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Download plot.py' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download data.csv' })).toBeInTheDocument();

    const show = screen.getByRole('button', { name: 'Show code' });
    expect(show).toHaveTextContent('.show_code()');
    expect(show).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(show);
    expect(await screen.findByTestId('code-highlighter')).toHaveTextContent('import pandas as pd');
    const hide = screen.getByRole('button', { name: 'Hide code' });
    expect(hide).toHaveTextContent('.hide_code()');
    expect(hide).toHaveAttribute('aria-expanded', 'true');
    await userEvent.click(hide);
    expect(screen.queryByTestId('code-highlighter')).not.toBeInTheDocument();
  });

  it('says why .copy() waits when the code could not be loaded, also while folded', () => {
    renderCard({ version: makeVersion({ code: { state: 'failed' } }) });
    expect(screen.getByRole('alert')).toHaveTextContent('could not load plot.py');
    expect(screen.getByRole('button', { name: 'Copy code' })).toBeDisabled();
  });

  it("keeps the card's own choices across a collapse of the whole card", async () => {
    renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Show code' }));
    await userEvent.click(screen.getByRole('button', { name: /^Run details/ }));

    await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
    expect(screen.queryByTestId('code-highlighter')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));

    expect(await screen.findByTestId('code-highlighter')).toBeInTheDocument();
    expect(screen.getByText('Marker size raised')).toBeInTheDocument();
  });

  it("starts a newer version's card folded, whatever the card before it showed", async () => {
    const props: ResultCardProps = {
      version: makeVersion(),
      specId: 'scatter-basic',
      language: 'python',
      latest: true,
      busy: false,
      onRequestTheme: vi.fn(),
      onFetchArtifact: vi.fn(),
      onTrack: vi.fn(),
    };
    const { rerender } = render(<ResultCard key={2} {...props} />);
    await userEvent.click(screen.getByRole('button', { name: 'Show code' }));
    expect(await screen.findByTestId('code-highlighter')).toBeInTheDocument();

    rerender(<ResultCard key={3} {...props} version={makeVersion({ number: 3 })} />);
    expect(screen.getByAltText('Adapted plot, version 3, light theme')).toBeInTheDocument();
    expect(screen.queryByTestId('code-highlighter')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Run details/ })).toHaveAttribute(
      'aria-expanded',
      'false'
    );
  });

  it('sizes the image box to the loaded PNG, footer strip included', () => {
    renderCard();
    const box = screen.getByTestId('result-image-box');
    expect(getComputedStyle(box).aspectRatio).toBe('3200 / 1864');

    const image = screen.getByAltText('Adapted plot, version 2, light theme');
    Object.defineProperty(image, 'naturalWidth', { value: 2400 });
    Object.defineProperty(image, 'naturalHeight', { value: 2448 });
    fireEvent.load(image);

    expect(getComputedStyle(box).aspectRatio).toBe('2400 / 2448');
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
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const { onOutcome } = renderCard();
      const copy = screen.getByRole('button', { name: 'Copy code' });
      await userEvent.click(copy);
      expect(onOutcome).not.toHaveBeenCalled();
      // The refusal shows on the button and to a screen reader, and the code opens to select it.
      expect(copy).toHaveTextContent('.copy() failed · select the code');
      expect(screen.getByRole('status')).toHaveTextContent('.copy() failed · select the code');
      expect(await screen.findByTestId('code-highlighter')).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(2000);
      });
      expect(copy).toHaveTextContent(/^\.copy\(\)$/);
    } finally {
      vi.useRealTimers();
    }
  });

  it('highlights the code in its version library language, not the page language', async () => {
    const version = makeVersion({
      library: 'ggplot2',
      code: { state: 'ready', text: 'df <- readr::read_csv("data.csv")\n' },
    });
    version.result = { ...version.result, artifacts: ['plot-light.png', 'plot.R', 'data.csv'] };
    renderCard({ version, language: 'python' });
    await userEvent.click(screen.getByRole('button', { name: 'Show code' }));
    expect(await screen.findByTestId('code-highlighter')).toHaveAttribute('data-language', 'r');
  });

  it('keeps the page language for a library the app does not know', async () => {
    renderCard({ version: makeVersion({ library: 'unknown-lib' }), language: 'python' });
    await userEvent.click(screen.getByRole('button', { name: 'Show code' }));
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
        '1232 / 1232'
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

      await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
      finish(page('light'));
      await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
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

      await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
      expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
      expect(screen.queryByTestId('interactive-preview')).not.toBeInTheDocument();
    });

    it("keeps a theme's page on screen when the other theme's build fails meanwhile", async () => {
      let fail: (reason: unknown) => void = () => undefined;
      const onFetchArtifact = fetchPages();
      const { onOutcome } = renderCard({ version: jsVersion(), onFetchArtifact });
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');
      onFetchArtifact.mockImplementationOnce(
        () =>
          new Promise<Blob>((_resolve, reject) => {
            fail = reject;
          })
      );

      await userEvent.click(screen.getByRole('button', { name: 'dark' }));
      expect(screen.getByText('building the interactive dark plot…')).toBeInTheDocument();
      // The light page is there already, so its theme stays clickable while the dark one builds.
      await userEvent.click(screen.getByRole('button', { name: 'light' }));
      await screen.findByTitle('Interactive plot, version 2, light theme');
      await act(async () => fail(Object.assign(new Error('nope'), { code: 'page_unavailable' })));

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByTitle('Interactive plot, version 2, light theme')).toBeInTheDocument();
      expect(onOutcome.mock.calls).toEqual([['opened_preview', 2]]);
    });

    it('reports no opening when the card unmounts while the page builds', async () => {
      let finish: (blob: Blob) => void = () => undefined;
      const onOutcome = vi.fn();
      const { unmount } = render(
        <ResultCard
          version={jsVersion()}
          specId="scatter-basic"
          language="javascript"
          latest
          busy={false}
          onRequestTheme={vi.fn()}
          onFetchArtifact={vi.fn(
            () =>
              new Promise<Blob>(resolve => {
                finish = resolve;
              })
          )}
          onTrack={vi.fn()}
          onOutcome={onOutcome}
        />
      );
      await userEvent.click(screen.getByRole('button', { name: 'Show interactive' }));

      unmount();
      await act(async () => finish(page('light')));

      expect(onOutcome).not.toHaveBeenCalled();
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

  it('folds an earlier version to its label in one line, and opens it again on request', async () => {
    renderCard({ latest: false, summary: 'title in German' });
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    // One button, the label in the thread's flow with `▸`, named with its words in their order,
    // so a voice command that says them finds it.
    const line = screen.getByRole('button', {
      name: 'Plot v2, matplotlib, title in German',
    });
    expect(line).toHaveTextContent(/^▸plot v2 · matplotlib · title in German$/);
    expect(line).toHaveAttribute('aria-expanded', 'false');
    expect(line).not.toHaveAttribute('aria-controls');

    await userEvent.click(line);
    expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
    // The same button, now the label on the open card's border: the focus stays on it.
    expect(line).toBeInTheDocument();
    expect(line).toHaveFocus();
    expect(line).toHaveTextContent(/^plot v2 · matplotlib · title in German$/);
    expect(line).toHaveAttribute('aria-expanded', 'true');
    expect(document.getElementById(line.getAttribute('aria-controls') ?? '')).toContainElement(
      screen.getByTestId('result-image-box')
    );

    await userEvent.click(line);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(line).toHaveFocus();
  });

  it('names the version, its library and no request when it answered none', () => {
    renderCard();
    expect(screen.getByTestId('result-label')).toHaveTextContent(/^plot v2 · matplotlib$/);
    expect(screen.getByRole('article', { name: 'Plot version 2' })).toBeInTheDocument();
    // The version's status stands in the theme row, beside the run's line.
    expect(screen.getByTestId('result-status')).toHaveTextContent('needs attention');
    expect(screen.queryByText(/\.expand\(\)|\.collapse\(\)/)).not.toBeInTheDocument();
    // A version whose memory the server did not name: no kept label, no kept line.
    expect(screen.queryByTestId('result-decisions')).not.toBeInTheDocument();
  });

  describe('the decisions it kept and added', () => {
    const LONG = 'horizontal reference line at y = 7, dashed, in the colour of the first series';
    const decided = (kept: (string | null)[], added: (string | null)[]) =>
      makeVersion({
        decisions: {
          kept: kept.map((text, index) => ({ id: `m${index + 1}`, text })),
          added: added.map((text, index) => ({ id: `m${index + 10}`, text })),
        },
      });
    const phone = () =>
      vi.stubGlobal(
        'matchMedia',
        vi.fn((query: string) => ({
          matches: query === '(max-width: 599.95px)',
          media: query,
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          addListener: vi.fn(),
          removeListener: vi.fn(),
          onchange: null,
          dispatchEvent: vi.fn(),
        }))
      );

    it('keeps the request in its label and names what it kept and added on its first line, each cut, in full for a screen reader', () => {
      renderCard({
        version: decided([LONG, 'x label "Monat"', 'title in German'], ['log scale on y']),
        summary: 'log scale on y please',
      });
      const label = screen.getByRole('button', {
        name: 'Plot v2, matplotlib, log scale on y please',
      });
      expect(label).toHaveTextContent(/^plot v2 · matplotlib · log scale on y please$/);
      const line = screen.getByTestId('result-decisions');
      expect(line.firstElementChild).toHaveTextContent(
        'kept: horizontal reference line at y = 7, das… · x label "Monat" · title in German · new: log scale on y'
      );
      expect(line.firstElementChild).toHaveAttribute('aria-hidden', 'true');
      expect(line).toHaveTextContent(
        `kept: ${LONG}, x label "Monat", title in German; new: log scale on y`
      );
      // The card's first line, above the image.
      expect(
        line.compareDocumentPosition(screen.getByTestId('result-image-box')) &
          Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy();
    });

    it('shows no line for two empty lists, and never kept 0', () => {
      renderCard({ version: decided([], []), summary: 'title in German' });
      expect(screen.getByTestId('result-label')).toHaveTextContent(
        /^plot v2 · matplotlib · title in German$/
      );
      expect(screen.queryByTestId('result-decisions')).not.toBeInTheDocument();
      expect(document.body).not.toHaveTextContent('kept 0');
    });

    it('counts a decision whose text no list named, and says how many more', () => {
      renderCard({ version: decided(['title in German', null], [null]) });
      expect(screen.getByTestId('result-label')).not.toHaveTextContent('kept');
      expect(screen.getByTestId('result-decisions').firstElementChild).toHaveTextContent(
        'kept: title in German · 1 more · new: 1 decision'
      );
    });

    it('shows the same line on a phone, under the image and above its action line', () => {
      phone();
      renderCard({ version: decided(['title in German'], ['log scale on y']) });
      const line = screen.getByTestId('result-decisions');
      expect(line.firstElementChild).toHaveTextContent(
        /^kept: title in German · new: log scale on y$/
      );
      const image = screen.getByTestId('result-image-box');
      const actions = screen.getByTestId('result-image-actions');
      expect(image.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(line.compareDocumentPosition(actions) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(screen.getByTestId('result-label')).not.toHaveTextContent('kept');
    });

    it('shows what a version only kept on a phone too', () => {
      phone();
      renderCard({ version: decided(['title in German'], []) });
      expect(screen.getByTestId('result-decisions').firstElementChild).toHaveTextContent(
        /^kept: title in German$/
      );
    });
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
      includeData: false,
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
    await userEvent.click(screen.getByRole('button', { name: /^Plot v2,/ }));
    expect(screen.getByTestId('result-feedback-sent')).toHaveTextContent('sent · v2 · bug');
  });
});
