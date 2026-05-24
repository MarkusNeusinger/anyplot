import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { AppDataProvider } from './Layout';
import { useAppData } from '../hooks/useLayoutContext';

// Helper component that reads the context and renders the four counts
// the user-reported NumbersStrip is built from. Acts as a black-box
// observer of AppDataProvider's data-loading useEffect.
function DataPeek() {
  const { specsData, librariesData, languagesData, stats } = useAppData();
  return (
    <div>
      <div data-testid="specs-count">{specsData.length}</div>
      <div data-testid="libraries-count">{librariesData.length}</div>
      <div data-testid="languages-count">{languagesData.length}</div>
      <div data-testid="stats-libraries">{stats ? stats.libraries : 'pending'}</div>
    </div>
  );
}

function jsonResponse(body: unknown): Response {
  return { ok: true, json: () => Promise.resolve(body) } as unknown as Response;
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('AppDataProvider', () => {
  it('fetches /specs, /libraries, /languages, /stats and exposes them via useAppData', async () => {
    const specsBody = [{ id: 'bar-grouped', title: 'Grouped Bar Chart' }];
    const libsBody = { libraries: [{ id: 'matplotlib', name: 'Matplotlib', language: 'python' }] };
    const langsBody = { languages: [{ id: 'python', name: 'Python', file_extension: '.py' }] };
    const statsBody = { specs: 7, plots: 42, libraries: 11, languages: 3 };

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/specs')) return Promise.resolve(jsonResponse(specsBody));
      if (url.endsWith('/libraries')) return Promise.resolve(jsonResponse(libsBody));
      if (url.endsWith('/languages')) return Promise.resolve(jsonResponse(langsBody));
      if (url.endsWith('/stats')) return Promise.resolve(jsonResponse(statsBody));
      throw new Error(`unexpected fetch: ${url}`);
    });
    global.fetch = fetchMock;

    render(
      <AppDataProvider>
        <DataPeek />
      </AppDataProvider>,
    );

    // All four endpoints should be hit (in parallel) — this is the regression
    // guard for the requestIdleCallback fix: previously the calls fired on
    // browser idle (could be up to 2 s late on Chrome). Now they fire on
    // mount, so the test resolves without any extra time advancement.
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    const urls = fetchMock.mock.calls.map((c) => c[0] as string);
    expect(urls.some((u) => u.endsWith('/specs'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/libraries'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/languages'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/stats'))).toBe(true);

    await waitFor(() => {
      expect(screen.getByTestId('stats-libraries')).toHaveTextContent('11');
    });
    expect(screen.getByTestId('specs-count')).toHaveTextContent('1');
    expect(screen.getByTestId('libraries-count')).toHaveTextContent('1');
    expect(screen.getByTestId('languages-count')).toHaveTextContent('1');
  });

  it('handles the /specs envelope ({specs: [...]}) as well as a bare array', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/specs')) return Promise.resolve(jsonResponse({ specs: [{ id: 'a' }, { id: 'b' }] }));
      if (url.endsWith('/libraries')) return Promise.resolve(jsonResponse({ libraries: [] }));
      if (url.endsWith('/languages')) return Promise.resolve(jsonResponse({ languages: [] }));
      if (url.endsWith('/stats')) return Promise.resolve(jsonResponse({ specs: 2, plots: 0, libraries: 0 }));
      throw new Error(`unexpected fetch: ${url}`);
    });
    global.fetch = fetchMock;

    render(
      <AppDataProvider>
        <DataPeek />
      </AppDataProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('specs-count')).toHaveTextContent('2');
    });
  });

  it('swallows fetch errors without crashing — context falls back to empty defaults', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    global.fetch = vi.fn().mockRejectedValue(new Error('boom'));

    render(
      <AppDataProvider>
        <DataPeek />
      </AppDataProvider>,
    );

    await waitFor(() => {
      expect(warnSpy).toHaveBeenCalled();
    });
    expect(screen.getByTestId('specs-count')).toHaveTextContent('0');
    expect(screen.getByTestId('libraries-count')).toHaveTextContent('0');
    expect(screen.getByTestId('stats-libraries')).toHaveTextContent('pending');

    warnSpy.mockRestore();
  });

  it('aborts in-flight fetches when the provider unmounts', async () => {
    // Hold all fetches open so the abort path is exercised in the cleanup.
    const fetchMock = vi.fn().mockImplementation(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_, reject) => {
          init?.signal?.addEventListener('abort', () => {
            // Real fetch rejects with an AbortError DOMException on signal
            // abort; mimic the `name` so the catch in Layout.tsx treats it
            // the same way. Use a tagged Error to avoid ESLint's no-undef
            // for the DOMException browser global.
            const err = new Error('aborted');
            err.name = 'AbortError';
            reject(err);
          });
        }),
    );
    global.fetch = fetchMock;

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { unmount } = render(
      <AppDataProvider>
        <DataPeek />
      </AppDataProvider>,
    );

    // Pending — no data resolved yet
    expect(screen.getByTestId('stats-libraries')).toHaveTextContent('pending');

    unmount();

    // The aborted rejection must not surface as an unhandled warn — the
    // catch branch's `if (signal.aborted) return` guards it.
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(warnSpy).not.toHaveBeenCalled();

    warnSpy.mockRestore();
  });
});
