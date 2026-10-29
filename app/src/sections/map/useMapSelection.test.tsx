import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useMapSelection } from './useMapSelection';

describe('useMapSelection', () => {
  it('initializes state correctly', () => {
    const { result } = renderHook(() =>
      useMapSelection({
        graphData: { idf: new Map(), topTypes: [] },
        nodeById: new Map(),
        fgRef: { current: null },
      })
    );

    expect(result.current.hoverId).toBeNull();
    expect(result.current.pinnedId).toBeNull();
    expect(result.current.pinScreen).toBeNull();
    expect(result.current.hoverType).toBeNull();
    expect(result.current.panelNodeId).toBeNull();
    expect(result.current.panelData).toBeNull();
  });
});
