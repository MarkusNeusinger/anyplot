import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useMapResize } from './useMapResize';

// jsdom doesn't ship ResizeObserver; this stub records the observed element and
// lets the test fire the callback with chosen dimensions.
type ResizeCb = (entries: { contentRect: { width: number; height: number } }[]) => void;
const observers: MockResizeObserver[] = [];
class MockResizeObserver {
  cb: ResizeCb;
  observed: Element | null = null;
  disconnect = vi.fn();
  constructor(cb: ResizeCb) {
    this.cb = cb;
    observers.push(this);
  }
  observe(target: Element) {
    this.observed = target;
  }
  unobserve() {}
}

function Probe() {
  const { containerRef, size } = useMapResize();
  return <div ref={containerRef} data-testid="map-container" data-w={size.w} data-h={size.h} />;
}

function renderedSize() {
  const el = screen.getByTestId('map-container');
  return { w: Number(el.dataset.w), h: Number(el.dataset.h) };
}

describe('useMapResize', () => {
  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', MockResizeObserver);
  });

  afterEach(() => {
    observers.length = 0;
    vi.unstubAllGlobals();
  });

  it('starts at 0 by 0 and follows the observed container size', () => {
    render(<Probe />);

    expect(renderedSize()).toEqual({ w: 0, h: 0 });
    expect(observers).toHaveLength(1);
    expect(observers[0].observed).toBe(screen.getByTestId('map-container'));

    act(() => observers[0].cb([{ contentRect: { width: 800, height: 600 } }]));
    expect(renderedSize()).toEqual({ w: 800, h: 600 });
  });

  it('ignores an empty entry list', () => {
    render(<Probe />);

    act(() => observers[0].cb([]));
    expect(renderedSize()).toEqual({ w: 0, h: 0 });
  });

  it('disconnects the observer on unmount', () => {
    const { unmount } = render(<Probe />);

    unmount();
    expect(observers[0].disconnect).toHaveBeenCalledTimes(1);
  });
});
