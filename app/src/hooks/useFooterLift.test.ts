import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useFooterLift } from 'src/hooks/useFooterLift';

const originalWidth = window.innerWidth;
const originalHeight = window.innerHeight;

function setViewport(width: number, height: number) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
  Object.defineProperty(window, 'innerHeight', { value: height, configurable: true });
}

function mountFooter(top: number) {
  const footer = document.createElement('footer');
  footer.getBoundingClientRect = () => ({ top }) as DOMRect;
  document.body.appendChild(footer);
  return footer;
}

describe('useFooterLift', () => {
  beforeEach(() => {
    // requestAnimationFrame — execute immediately
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      cb(0);
      return 0;
    });
  });

  afterEach(() => {
    document.querySelectorAll('footer').forEach(f => f.remove());
    setViewport(originalWidth, originalHeight);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('lifts the row so the footer top runs through its centre on xs', () => {
    setViewport(390, 844);
    mountFooter(758); // footer overlaps 86px; row centre sits 32px up
    const { result } = renderHook(() => useFooterLift());
    expect(result.current).toBe('translateY(-54px)');
  });

  it('stays put while the footer has not reached the row centre', () => {
    setViewport(390, 844);
    mountFooter(820);
    const { result } = renderHook(() => useFooterLift());
    expect(result.current).toBe('none');
  });

  it('never lifts from the sm breakpoint up', () => {
    setViewport(1440, 900);
    mountFooter(500);
    const { result } = renderHook(() => useFooterLift());
    expect(result.current).toBe('none');
  });

  it('stays put when the page has no footer', () => {
    setViewport(390, 844);
    const { result } = renderHook(() => useFooterLift());
    expect(result.current).toBe('none');
  });

  it('follows the footer on scroll and detaches its listeners on unmount', () => {
    setViewport(390, 844);
    const footer = mountFooter(900);
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { result, unmount } = renderHook(() => useFooterLift());
    expect(result.current).toBe('none');

    footer.getBoundingClientRect = () => ({ top: 744 }) as DOMRect;
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    expect(result.current).toBe('translateY(-68px)');

    unmount();
    const removed = removeSpy.mock.calls.map(([type]) => type);
    expect(removed).toEqual(expect.arrayContaining(['scroll', 'resize']));
  });
});
