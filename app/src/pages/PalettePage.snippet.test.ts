import { describe, expect, it } from 'vitest';

import { type Lang, PALETTE, snippet } from 'src/pages/PalettePage.helpers';

const LANGS: Lang[] = ['python', 'r', 'julia', 'js'];

describe('PalettePage snippet()', () => {
  // Regression: the /palette page calls the palette "imprint" everywhere
  // (heading, meta, history, imprint_seq / imprint_div colormaps), so the
  // copy-paste code must use the IMPRINT object — never ANYPLOT_*.
  it.each(LANGS)('emits a unified IMPRINT object, never ANYPLOT_*, for %s (hex)', lang => {
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

  it.each(LANGS)('still uses the IMPRINT object in OKLCH mode for %s', lang => {
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

  // The ramps have their own stops per theme and per use, with positions; a
  // snippet that drops the positions or one theme hands out a different ramp.
  it.each([
    [
      'python',
      'light=[(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]',
      'dark=[(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]',
      'light=[(0.0, "#AE3030"), (0.5, "#6B6A63"), (1.0, "#4467A3")]',
    ],
    [
      'r',
      'light = list(colours = c("#66E2B2", "#009E73", "#4467A3", "#002850"), values = c(0, 0.368, 0.582, 1))',
      'dark  = list(colours = c("#007755", "#009E73", "#CDD9FF"), values = c(0, 0.32, 1))',
      'light = list(colours = c("#AE3030", "#6B6A63", "#4467A3"), values = c(0, 0.5, 1))',
    ],
    [
      'julia',
      'values = [0.0, 0.368, 0.582, 1.0]',
      'dark = (colors = [colorant"#007755", colorant"#009E73", colorant"#CDD9FF"], values = [0.0, 0.32, 1.0])',
      'dark = (colors = [colorant"#AE3030", colorant"#686762", colorant"#4467A3"], values = [0.0, 0.5, 1.0])',
    ],
    [
      'js',
      'light: [[0, "#66E2B2"], [0.368, "#009E73"], [0.582, "#4467A3"], [1, "#002850"]]',
      'dark: [[0, "#007755"], [0.32, "#009E73"], [1, "#CDD9FF"]]',
      'dark: [[0, "#AE3030"], [0.5, "#1A1A17"], [1, "#4467A3"]]',
    ],
  ] as [Lang, string, string, string][])(
    'carries the positioned ramps per theme and per use for %s',
    (lang, ...parts) => {
      const code = snippet(lang, false, PALETTE);
      for (const part of parts) expect(code).toContain(part);
      expect(code).toContain('fields');
      expect(code).toContain('marks');
    }
  );

  // Regression: CSS oklch() literals are only valid in JS/CSS. matplotlib /
  // ggplot2 / Makie can't parse them, so in OKLCH mode those snippets must keep
  // runnable hex values and surface the coordinate as a comment instead — only
  // the JS snippet may emit a bare oklch() literal as an actual colour value.
  it.each(['python', 'r', 'julia'] as Lang[])(
    'keeps runnable hex (never a bare oklch() value) in OKLCH mode for %s',
    lang => {
      const code = snippet(lang, true, PALETTE);
      expect(code).toContain('#009E73'); // brand-green hex is still the real value
      expect(code).toContain('# oklch('); // coordinate shown as a comment
      // no oklch() literal sitting as a quoted colour value
      expect(code).not.toMatch(/"oklch\(/);
    }
  );

  it('emits oklch() literals as values in the JS snippet when OKLCH is on', () => {
    const code = snippet('js', true, PALETTE);
    expect(code).toContain('"oklch(0.620 0.130 165.5)"'); // slot-0 brand as a CSS literal
  });
});
