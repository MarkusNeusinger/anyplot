import { describe, expect, it } from 'vitest';

import {
  FAB_GAP,
  FAB_INSET,
  FAB_ROW_CENTER_XS,
  FAB_SIZE,
  FAB_SLOT_ABOVE,
  FAB_SLOT_LEFT,
  MINI_FAB_SIZE,
} from 'src/theme/floating-actions';

type Bp = 'xs' | 'sm';
type Rect = { left: number; top: number; right: number; bottom: number };

// A fixed-position box given by its right/bottom offsets, in viewport px.
const box = (
  vw: number,
  vh: number,
  right: number,
  bottom: number,
  w: number,
  h: number
): Rect => ({
  left: vw - right - w,
  top: vh - bottom - h,
  right: vw - right,
  bottom: vh - bottom,
});

const overlaps = (a: Rect, b: Rect) =>
  Math.min(a.right, b.right) > Math.max(a.left, b.left) &&
  Math.min(a.bottom, b.bottom) > Math.max(a.top, b.top);

describe('floating-actions geometry', () => {
  it('pins the corner slots', () => {
    expect(FAB_SLOT_ABOVE).toEqual({ right: { xs: 12, sm: 20 }, bottom: { xs: 60, sm: 72 } });
    expect(FAB_SLOT_LEFT).toEqual({ right: { xs: 60, sm: 72 }, bottom: { xs: 12, sm: 20 } });
    expect(FAB_ROW_CENTER_XS).toBe(32);
  });

  // jsdom ignores @media, so this is the only guard for the sm+ values.
  it.each<[Bp, number, number]>([
    ['xs', 390, 844],
    ['sm', 1440, 900],
  ])('keeps every floating element clear of the others at %s (%ix%i)', (bp, vw, vh) => {
    const fab = box(vw, vh, FAB_INSET[bp], FAB_INSET[bp], FAB_SIZE[bp], FAB_SIZE[bp]);
    const stack = box(
      vw,
      vh,
      FAB_SLOT_ABOVE.right[bp],
      FAB_SLOT_ABOVE.bottom[bp],
      MINI_FAB_SIZE,
      3 * MINI_FAB_SIZE + 2 * FAB_GAP
    );
    const toast = box(vw, vh, FAB_INSET[bp], FAB_SLOT_ABOVE.bottom[bp], 80, 28);
    const scrollTop = box(
      vw,
      vh,
      FAB_SLOT_LEFT.right[bp],
      FAB_SLOT_LEFT.bottom[bp],
      MINI_FAB_SIZE,
      MINI_FAB_SIZE
    );

    expect(overlaps(scrollTop, fab)).toBe(false);
    expect(overlaps(scrollTop, stack)).toBe(false);
    expect(overlaps(scrollTop, toast)).toBe(false);
    expect(overlaps(stack, fab)).toBe(false);
    expect(overlaps(toast, fab)).toBe(false);
    // One row: both buttons share the centre line the footer lift pivots on.
    expect((scrollTop.top + scrollTop.bottom) / 2).toBe((fab.top + fab.bottom) / 2);
  });
});
