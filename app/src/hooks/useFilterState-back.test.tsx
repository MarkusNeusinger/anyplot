import { useEffect, useRef, useState } from 'react';

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useFilterState } from 'src/hooks/useFilterState';
import { type HomeState, HomeStateContext, initialHomeState } from 'src/hooks/useLayoutContext';
import type { FilterCounts, PlotImage } from 'src/types';

const emptyCounts: FilterCounts = {
  lang: { python: 2 },
  lib: { matplotlib: 1, seaborn: 1 },
  spec: { 'bar-basic': 2 },
  plot: { bar: 2 },
  data: {},
  dom: {},
  feat: {},
  dep: {},
  tech: {},
  pat: {},
  prep: {},
  style: {},
};

const images: PlotImage[] = ['matplotlib', 'seaborn'].map(library => ({
  spec_id: 'bar-basic',
  library,
  language: 'python',
  url: `https://example.com/bar-basic-${library}.png`,
}));

const response = {
  total: images.length,
  images,
  counts: emptyCounts,
  globalCounts: emptyCounts,
  orCounts: [],
  specTitles: { 'bar-basic': 'Basic Bar Chart' },
};

/**
 * The layout's persistent home state, held OUTSIDE the hook's own render
 * tree, the way Layout.tsx holds it, so it survives an unmount of /plots.
 */
function createLayout() {
  const store: { ref: { current: HomeState } } = { ref: { current: initialHomeState } };

  function Wrapper({ children }: { children: React.ReactNode }) {
    const [homeState, setHomeState] = useState<HomeState>(store.ref.current);
    const homeStateRef = useRef<HomeState>(store.ref.current);
    useEffect(() => {
      homeStateRef.current = homeState;
      store.ref.current = homeState;
    }, [homeState]);
    return (
      <HomeStateContext.Provider
        value={{ homeState, homeStateRef, setHomeState, saveScrollPosition: () => {} }}
      >
        {children}
      </HomeStateContext.Provider>
    );
  }

  return { store, Wrapper };
}

describe('useFilterState after Back', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    window.history.replaceState({}, '', '/plots');
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  const options = { onTrackPageview: () => {}, onTrackEvent: () => {} };

  it('keeps the spec titles when the gallery returns without a fetch', async () => {
    const { store, Wrapper } = createLayout();

    // First visit: the fetch fills the titles, and the hook saves them
    const first = renderHook(() => useFilterState(options), { wrapper: Wrapper });
    await waitFor(() => expect(first.result.current.specTitles).toEqual(response.specTitles));
    await waitFor(() => expect(store.ref.current.specTitles).toEqual(response.specTitles));
    first.unmount();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    // Back: same filters, so the restored state is used and nothing is fetched
    const back = renderHook(() => useFilterState(options), { wrapper: Wrapper });
    expect(back.result.current.specTitles).toEqual({ 'bar-basic': 'Basic Bar Chart' });
    expect(back.result.current.allImages).toHaveLength(2);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('reports every removed group once when all filters are cleared', async () => {
    window.history.replaceState({}, '', '/plots?lib=seaborn&plot=bar,line');
    const onTrackEvent = vi.fn();
    const { Wrapper } = createLayout();

    const { result } = renderHook(
      () => useFilterState({ onTrackPageview: () => {}, onTrackEvent }),
      { wrapper: Wrapper }
    );
    expect(result.current.activeFilters).toHaveLength(2);

    act(() => result.current.handleClearFilters());

    await waitFor(() => expect(result.current.activeFilters).toEqual([]));
    // One use of the feature, however many groups it removed.
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
    expect(onTrackEvent).toHaveBeenCalledWith('ui_feature', { feature: 'filter_remove' });
  });
});
