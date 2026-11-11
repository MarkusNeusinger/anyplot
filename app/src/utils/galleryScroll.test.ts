import { describe, expect, it } from 'vitest';

import { galleryScrollPercent } from 'src/utils/galleryScroll';

const PAGE = { docHeight: 5000, viewportHeight: 1000 };

describe('galleryScrollPercent', () => {
  it('is the scrolled share of the scrollable height when the whole list is loaded', () => {
    const loaded = { ...PAGE, displayedCount: 40, total: 40 };
    expect(galleryScrollPercent({ ...loaded, scrollY: 0 })).toBe(0);
    expect(galleryScrollPercent({ ...loaded, scrollY: 1000 })).toBe(25);
    expect(galleryScrollPercent({ ...loaded, scrollY: 4000 })).toBe(100);
  });

  it('scales the height up by the part of the list that is not loaded yet', () => {
    // A tenth of the list is on the page: its end is a tenth of the way.
    const tenth = { ...PAGE, displayedCount: 36, total: 360 };
    expect(galleryScrollPercent({ ...tenth, scrollY: 4000 })).toBe(10);
    expect(galleryScrollPercent({ ...tenth, scrollY: 2000 })).toBe(5);
  });

  it('stays between 0 and 100', () => {
    const loaded = { ...PAGE, displayedCount: 40, total: 40 };
    // An overscroll bounce reports offsets outside the document.
    expect(galleryScrollPercent({ ...loaded, scrollY: -80 })).toBe(0);
    expect(galleryScrollPercent({ ...loaded, scrollY: 4300 })).toBe(100);
  });

  it('is 0 for a page with nothing to scroll and for an empty list', () => {
    expect(
      galleryScrollPercent({
        scrollY: 0,
        docHeight: 1000,
        viewportHeight: 1000,
        displayedCount: 4,
        total: 4,
      })
    ).toBe(0);
    expect(galleryScrollPercent({ ...PAGE, scrollY: 0, displayedCount: 0, total: 0 })).toBe(0);
  });
});
