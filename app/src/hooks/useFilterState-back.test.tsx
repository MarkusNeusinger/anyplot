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

  it('removes one value, then the group with its last value, as uses of filter_remove', async () => {
    window.history.replaceState({}, '', '/plots?lib=matplotlib,seaborn&plot=bar');
    const onTrackEvent = vi.fn();
    const { Wrapper } = createLayout();
    const { result } = renderHook(
      () => useFilterState({ onTrackPageview: () => {}, onTrackEvent }),
      { wrapper: Wrapper }
    );

    act(() => result.current.handleRemoveFilter(0, 'seaborn'));
    await waitFor(() =>
      expect(result.current.activeFilters).toEqual([
        { category: 'lib', values: ['matplotlib'] },
        { category: 'plot', values: ['bar'] },
      ])
    );
    act(() => result.current.handleRemoveFilter(0, 'matplotlib'));
    await waitFor(() =>
      expect(result.current.activeFilters).toEqual([{ category: 'plot', values: ['bar'] }])
    );

    expect(onTrackEvent).toHaveBeenCalledTimes(2);
    expect(onTrackEvent).toHaveBeenLastCalledWith('ui_feature', { feature: 'filter_remove' });
    // A group that is not there is no use of anything.
    act(() => result.current.handleRemoveFilter(5, 'bar'));
    expect(onTrackEvent).toHaveBeenCalledTimes(2);
  });

  it('removes a whole group as a use of filter_remove', async () => {
    window.history.replaceState({}, '', '/plots?lib=matplotlib,seaborn&plot=bar');
    const onTrackEvent = vi.fn();
    const { Wrapper } = createLayout();
    const { result } = renderHook(
      () => useFilterState({ onTrackPageview: () => {}, onTrackEvent }),
      { wrapper: Wrapper }
    );

    act(() => result.current.handleRemoveGroup(0));
    await waitFor(() =>
      expect(result.current.activeFilters).toEqual([{ category: 'plot', values: ['bar'] }])
    );

    expect(onTrackEvent).toHaveBeenCalledTimes(1);
    expect(onTrackEvent).toHaveBeenCalledWith('ui_feature', { feature: 'filter_remove' });
  });

  it('picks a random filter from the catalogue and counts it as a use of random_filter', async () => {
    const onTrackEvent = vi.fn();
    const { Wrapper } = createLayout();
    const { result } = renderHook(
      () => useFilterState({ onTrackPageview: () => {}, onTrackEvent }),
      { wrapper: Wrapper }
    );
    // Nothing to pick from before the counts are there.
    act(() => result.current.handleRandom());
    expect(onTrackEvent).not.toHaveBeenCalled();
    await waitFor(() => expect(result.current.globalCounts).toEqual(emptyCounts));

    // The first of the categories that hold a value, and its first value.
    vi.spyOn(Math, 'random').mockReturnValue(0);
    act(() => result.current.handleRandom());

    await waitFor(() =>
      expect(result.current.activeFilters).toEqual([{ category: 'lang', values: ['python'] }])
    );
    expect(result.current.randomAnimation).toMatchObject({ index: 0, phase: 'out' });
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
    expect(onTrackEvent).toHaveBeenCalledWith('ui_feature', { feature: 'random_filter' });

    // A second roll replaces the filter it set, and is a use like the first.
    await waitFor(() => expect(result.current.filterCounts).toEqual(emptyCounts));
    vi.mocked(Math.random).mockReturnValue(0.99);
    act(() => result.current.handleRandom());
    await waitFor(() =>
      expect(result.current.activeFilters).toEqual([{ category: 'plot', values: ['bar'] }])
    );
    expect(onTrackEvent).toHaveBeenCalledTimes(2);
  });
});
