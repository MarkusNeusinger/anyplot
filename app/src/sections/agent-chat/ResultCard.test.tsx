import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PlotVersion } from 'src/hooks/useAgentSession';
import { ResultCard, type ResultCardProps } from 'src/sections/agent-chat/ResultCard';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

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
    onRefine: vi.fn(),
    onTrack: vi.fn(),
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
    expect(screen.getByTestId('result-feedback-slot')).toBeInTheDocument();
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
    renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy image' }));
    expect(write).toHaveBeenCalledTimes(1);
    const [items] = write.mock.calls[0] as unknown as [{ items: Record<string, Blob> }[]];
    expect(items[0].items['image/png']).toBe(pngBlob);
    expect(await screen.findByText('>>> .copied')).toBeInTheDocument();
    expect(clicked).toEqual([]);
  });

  it('downloads the PNG when the browser cannot copy images', async () => {
    vi.stubGlobal('ClipboardItem', undefined);
    renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy image' }));
    expect(clicked).toEqual([
      { href: 'blob:download', download: 'scatter-basic-matplotlib-v2-light.png' },
    ]);
    expect(await screen.findByText('>>> .downloaded')).toBeInTheDocument();
  });

  it('downloads the PNG and opens it full size', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Download PNG' }));
    expect(clicked.map(entry => entry.download)).toEqual(['scatter-basic-matplotlib-v2-light.png']);
    await userEvent.click(screen.getByRole('button', { name: 'Open full size' }));
    expect(open).toHaveBeenCalledWith('blob:light', '_blank', 'noopener,noreferrer');
  });

  it('copies the code and records copy_code for the agent chat', async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });
    const { onTrack } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Copy code' }));
    expect(writeText).toHaveBeenCalledWith('import pandas as pd\ndf = pd.read_csv("data.csv")\n');
    expect(onTrack).toHaveBeenCalledWith('copy_code', {
      spec: 'scatter-basic',
      library: 'matplotlib',
      method: 'agent',
      page: 'agent_chat',
    });
  });

  it('downloads plot.py and data.csv under the names the code expects', async () => {
    const { onFetchArtifact } = renderCard();
    await userEvent.click(screen.getByRole('button', { name: 'Download plot.py' }));
    await userEvent.click(screen.getByRole('button', { name: 'Download data.csv' }));
    await waitFor(() =>
      expect(clicked.map(entry => entry.download)).toEqual(['plot.py', 'data.csv'])
    );
    // plot.py comes from the code on screen; data.csv from the artifact route.
    expect(onFetchArtifact).toHaveBeenCalledTimes(1);
    expect(onFetchArtifact).toHaveBeenCalledWith(2, 'data.csv');
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
    const { onRequestTheme, onRefine } = renderCard({ busy: true });
    const dark = screen.getByRole('button', { name: 'dark' });
    expect(dark).toBeDisabled();
    await userEvent.click(dark);
    expect(onRequestTheme).not.toHaveBeenCalled();
    await userEvent.type(screen.getByLabelText('Refine this plot'), 'log scale on y');
    expect(screen.getByRole('button', { name: '.refine()' })).toBeDisabled();
    expect(onRefine).not.toHaveBeenCalled();
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

  it('sends a refinement from the composer', async () => {
    const { onRefine } = renderCard();
    await userEvent.type(screen.getByLabelText('Refine this plot'), 'log scale on y');
    await userEvent.click(screen.getByRole('button', { name: '.refine()' }));
    expect(onRefine).toHaveBeenCalledWith('log scale on y');
  });

  it('collapses an earlier version and has no composer there', async () => {
    renderCard({ latest: false });
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Version 2/ }));
    expect(screen.getByAltText('Adapted plot, version 2, light theme')).toBeInTheDocument();
    expect(screen.queryByLabelText('Refine this plot')).not.toBeInTheDocument();
  });
});
