import { describe, it, expect } from 'vitest';

import { snippet, PALETTE, type Lang } from './PalettePage';

const LANGS: Lang[] = ['python', 'r', 'julia', 'js'];

describe('PalettePage snippet()', () => {
  // Regression: the /palette page calls the palette "imprint" everywhere
  // (heading, meta, history, imprint_seq / imprint_div colormaps), so the
  // copy-paste code must use the IMPRINT object — never ANYPLOT_*.
  it.each(LANGS)('emits a unified IMPRINT object, never ANYPLOT_*, for %s (hex)', (lang) => {
    const code = snippet(lang, false, PALETTE);
    expect(code).toContain('IMPRINT');
    // single bundled object exposes hues + the semantic anchors + cmaps
    expect(code).toContain('hues');
    expect(code).toContain('amber');
    expect(code).toContain('neutral');
    expect(code).toContain('muted');
    expect(code).toContain('seq');
    expect(code).toContain('div');
    expect(code).not.toContain('ANYPLOT');
  });

  it.each(LANGS)('still uses the IMPRINT object in OKLCH mode for %s', (lang) => {
    const code = snippet(lang, true, PALETTE);
    expect(code).toContain('IMPRINT');
    expect(code).toContain('hues');
    expect(code).not.toContain('ANYPLOT');
  });

  it('emits the brand-green hex as the first hue (slot 0)', () => {
    const code = snippet('python', false, PALETTE);
    expect(code).toContain('#009E73');
    // first series reached via the object: IMPRINT.hues[0]
    expect(code).toContain('IMPRINT.hues[0]');
  });

  it('builds imprint-named colormaps from the bundled stops', () => {
    expect(snippet('python', false, PALETTE)).toContain('imprint_seq');
    expect(snippet('python', false, PALETTE)).toContain('imprint_div');
    expect(snippet('julia', false, PALETTE)).toContain('imprint_seq');
    expect(snippet('js', false, PALETTE)).toContain('IMPRINT.div');
  });
});
