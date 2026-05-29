import { describe, it, expect } from 'vitest';

import { snippet, PALETTE, type Lang } from './PalettePage';

const LANGS: Lang[] = ['python', 'r', 'julia', 'js'];

describe('PalettePage snippet()', () => {
  // Regression: the /palette page calls the palette "imprint" everywhere
  // (heading, meta, history, imprint_seq / imprint_div colormaps), so the
  // copy-paste code must use IMPRINT_* identifiers — not ANYPLOT_*.
  it.each(LANGS)('uses IMPRINT_* naming, never ANYPLOT_*, for %s (hex)', (lang) => {
    const code = snippet(lang, false, PALETTE);
    expect(code).toContain('IMPRINT_PALETTE');
    expect(code).toContain('IMPRINT_AMBER');
    expect(code).not.toContain('ANYPLOT_PALETTE');
    expect(code).not.toContain('ANYPLOT_AMBER');
    expect(code).not.toContain('ANYPLOT_SEQ');
    expect(code).not.toContain('ANYPLOT_DIV');
  });

  it.each(LANGS)('uses IMPRINT_* naming for %s (oklch)', (lang) => {
    const code = snippet(lang, true, PALETTE);
    expect(code).toContain('IMPRINT_PALETTE');
    expect(code).not.toContain('ANYPLOT_');
  });

  it('emits the brand-green hex as slot 0 of the palette', () => {
    expect(snippet('python', false, PALETTE)).toContain('#009E73');
  });

  it('uses imprint-named colormaps for the continuous scales', () => {
    expect(snippet('python', false, PALETTE)).toContain('imprint_seq');
    expect(snippet('python', false, PALETTE)).toContain('imprint_div');
    expect(snippet('julia', false, PALETTE)).toContain('IMPRINT_SEQ');
    expect(snippet('js', false, PALETTE)).toContain('IMPRINT_DIV');
  });
});
