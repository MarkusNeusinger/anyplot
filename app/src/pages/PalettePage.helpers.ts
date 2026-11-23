/**
 * Helpers for the /palette page: the imprint palette data (8 categorical
 * hues with OKLCH coords + ΔE / WCAG stats) and the per-language copy-paste
 * snippet generator. Pure data + string building, extracted from
 * PalettePage.tsx so the page module only exports the component (Fast
 * Refresh) and snippet() stays unit-testable in PalettePage.snippet.test.ts.
 */

import {
  divStops,
  type RampStops,
  type RampTheme,
  type RampUse,
  SEQ_STOPS,
} from 'src/sections/palette/paletteHelpers';

export type Swatch = {
  hex: string;
  name: string;
  family: string;
  role: string;
  L: number;
  C: number;
  H: number;
  oklch: string;
  /** Per-hex min ΔE to any other imprint member under normal vision. */
  minNorm: number;
  /** Per-hex min ΔE to any other imprint member under worst CVD sim (deuter / protan / tritan). */
  minCvd: number;
  /** WCAG contrast on the cream page bg #F5F3EC (--bg-page). */
  wcagL: number;
  /** WCAG contrast on warm near-black bg #121210. */
  wcagD: number;
};

export const PALETTE: Swatch[] = [
  {
    hex: '#009E73',
    name: 'brand green',
    family: 'green',
    role: 'first series',
    L: 0.62,
    C: 0.13,
    H: 165.5,
    oklch: 'oklch(0.620 0.130 165.5)',
    minNorm: 22.51,
    minCvd: 13.7,
    wcagL: 3.08,
    wcagD: 5.48,
  },
  {
    hex: '#C475FD',
    name: 'lavender',
    family: 'purple',
    role: 'creative',
    L: 0.704,
    C: 0.202,
    H: 308.9,
    oklch: 'oklch(0.704 0.202 308.9)',
    minNorm: 30.03,
    minCvd: 13.81,
    wcagL: 2.59,
    wcagD: 6.53,
  },
  {
    hex: '#4467A3',
    name: 'blue',
    family: 'blue',
    role: 'cool / info',
    L: 0.516,
    C: 0.104,
    H: 260.6,
    oklch: 'oklch(0.516 0.104 260.6)',
    minNorm: 32.35,
    minCvd: 10.7,
    wcagL: 5.09,
    wcagD: 3.32,
  },
  {
    hex: '#BD8233',
    name: 'ochre',
    family: 'yellow',
    role: 'earth / commodity',
    L: 0.652,
    C: 0.118,
    H: 70.5,
    oklch: 'oklch(0.652 0.118 70.5)',
    minNorm: 24.0,
    minCvd: 8.81,
    wcagL: 2.95,
    wcagD: 5.72,
  },
  {
    hex: '#AE3030',
    name: 'matte red',
    family: 'red',
    role: 'bad / loss / error',
    L: 0.503,
    C: 0.163,
    H: 25.2,
    oklch: 'oklch(0.503 0.163 25.2)',
    minNorm: 20.73,
    minCvd: 15.2,
    wcagL: 5.79,
    wcagD: 2.92,
  },
  {
    hex: '#2ABCCD',
    name: 'cyan',
    family: 'cyan',
    role: 'sky / tech-cool',
    L: 0.73,
    C: 0.117,
    H: 207.1,
    oklch: 'oklch(0.730 0.117 207.1)',
    minNorm: 22.51,
    minCvd: 13.7,
    wcagL: 2.06,
    wcagD: 8.19,
  },
  {
    hex: '#954477',
    name: 'rose',
    family: 'purple',
    role: 'wellness / health',
    L: 0.508,
    C: 0.125,
    H: 343.9,
    oklch: 'oklch(0.508 0.125 343.9)',
    minNorm: 20.73,
    minCvd: 10.7,
    wcagL: 5.61,
    wcagD: 3.01,
  },
  {
    hex: '#99B314',
    name: 'lime',
    family: 'green',
    role: 'growth / nature',
    L: 0.722,
    C: 0.167,
    H: 119.8,
    oklch: 'oklch(0.722 0.167 119.8)',
    minNorm: 24.0,
    minCvd: 8.81,
    wcagL: 2.15,
    wcagD: 7.87,
  },
];

export type Lang = 'python' | 'r' | 'julia' | 'js';

type Ramp = (use: RampUse, theme: RampTheme) => RampStops;
const seqRamp: Ramp = (use, theme) => SEQ_STOPS[use][theme];

const pyFloat = (n: number) => (Number.isInteger(n) ? n.toFixed(1) : String(n));
const pyStops = ({ at, hex }: RampStops) =>
  `[${hex.map((h, i) => `(${pyFloat(at[i])}, "${h}")`).join(', ')}]`;
const rStops = ({ at, hex }: RampStops) =>
  `list(colours = c(${hex.map(h => `"${h}"`).join(', ')}), values = c(${at.join(', ')}))`;
const jlStops = ({ at, hex }: RampStops) =>
  `(colors = [${hex.map(h => `colorant"${h}"`).join(', ')}], values = [${at.map(pyFloat).join(', ')}])`;
const jsStops = ({ at, hex }: RampStops) =>
  `[${hex.map((h, i) => `[${at[i]}, "${h}"]`).join(', ')}]`;

const RAMPS: [string, Ramp][] = [
  ['seq', seqRamp],
  ['div', divStops],
];
const USES: RampUse[] = ['fields', 'marks'];

/** The `seq` and `div` entries of the IMPRINT object, nested by use and theme, in one language's syntax. */
function rampEntries(lang: Lang): string {
  return RAMPS.map(([name, ramp]) => {
    const per = (use: RampUse, format: (stops: RampStops) => string) => [
      format(ramp(use, 'light')),
      format(ramp(use, 'dark')),
    ];
    switch (lang) {
      case 'python':
        return [
          `    ${name}=SimpleNamespace(`,
          ...USES.map(use => {
            const [light, dark] = per(use, pyStops);
            return `        ${use}=SimpleNamespace(\n            light=${light},\n            dark=${dark},\n        ),`;
          }),
          '    ),',
        ].join('\n');
      case 'r':
        return [
          `  ${name} = list(`,
          USES.map(use => {
            const [light, dark] = per(use, rStops);
            return `    ${use} = list(\n      light = ${light},\n      dark  = ${dark}\n    )`;
          }).join(',\n'),
          '  )',
        ].join('\n');
      case 'julia':
        return [
          `    ${name} = (`,
          ...USES.map(use => {
            const [light, dark] = per(use, jlStops);
            return `        ${use} = (\n            light = ${light},\n            dark = ${dark},\n        ),`;
          }),
          '    ),',
        ].join('\n');
      case 'js':
        return [
          `  ${name}: {`,
          ...USES.map(use => {
            const [light, dark] = per(use, jsStops);
            return `    ${use}: {\n      light: ${light},\n      dark: ${dark},\n    },`;
          }),
          '  },',
        ].join('\n');
    }
  }).join(lang === 'r' ? ',\n' : '\n');
}

export function snippet(lang: Lang, oklch: boolean, sortedPalette: Swatch[]): string {
  // CSS `oklch()` literals are only consumable where the runtime parses CSS
  // colours (JS / CSS). matplotlib, ggplot2 and Makie can't read them, so those
  // snippets stay hex (runnable) and surface the OKLCH coordinate as a trailing
  // comment instead — toggling OKLCH then annotates rather than breaks the code.
  const useLiteral = oklch && lang === 'js';
  const colorVal = (s: Swatch) => (useLiteral ? s.oklch : s.hex);
  const hueComment = (s: Swatch) => (oklch && lang !== 'js' ? `  # ${s.oklch}` : '');
  const amberVal = useLiteral ? 'oklch(0.841 0.108 98.3)' : '#DDCC77';
  // Theme-adaptive neutrals and the continuous ramps are kept as hex in both
  // modes — the ramps are positioned stops, the neutrals structural near-greys,
  // and converting them to OKLCH adds noise without helping anyone paste them.
  switch (lang) {
    case 'python':
      return `from types import SimpleNamespace

# imprint — anyplot's palette (https://anyplot.ai/palette)
IMPRINT = SimpleNamespace(
    hues=[
${sortedPalette.map(s => `        "${s.hex}",${hueComment(s)}`).join('\n')}
    ],
    amber="${amberVal}",  # warning / caution
    neutral=SimpleNamespace(light="#1A1A17", dark="#F0EFE8"),
    muted=SimpleNamespace(light="#6B6A63", dark="#A8A79F"),
    # continuous ramps: (position, hex) stops, low -> high, per use and theme
${rampEntries('python')}
)

color = IMPRINT.hues[0]  # first series is ALWAYS slot 0 (brand green)

# continuous data — build matplotlib cmaps from the stops: fields for cells
# that fill the plot, marks for points / lines / bars; .dark on dark bg
from matplotlib.colors import LinearSegmentedColormap
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", IMPRINT.seq.fields.light)
imprint_div = LinearSegmentedColormap.from_list("imprint_div", IMPRINT.div.fields.light)`;
    case 'r':
      return `# imprint — anyplot's palette (https://anyplot.ai/palette)
IMPRINT <- list(
  hues = c(
${sortedPalette.map((s, i, arr) => `    "${s.hex}"${i < arr.length - 1 ? ',' : ''}${hueComment(s)}`).join('\n')}
  ),
  amber = "${amberVal}",  # warning / caution
  neutral = list(light = "#1A1A17", dark = "#F0EFE8"),
  muted   = list(light = "#6B6A63", dark = "#A8A79F"),
  # continuous ramps: stops (colours and positions), low -> high, per use and theme
${rampEntries('r')}
)

color <- IMPRINT$hues[1]  # first series = slot 0, brand green (R is 1-based: index 1)

# continuous data — ggplot2 gradient scales: fields for cells that fill the
# plot, marks for points / lines / bars; $dark on dark bg
stops <- IMPRINT$seq$fields$light
scale_fill_gradientn(colours = stops$colours, values = stops$values)  # sequential
poles <- IMPRINT$div$fields$light$colours
scale_fill_gradient2(low = poles[1], mid = poles[2], high = poles[3], midpoint = 0)  # diverging — 0 maps to the midpoint`;
    case 'julia':
      return `using Colors  # colorant"#..."

# imprint — anyplot's palette (https://anyplot.ai/palette)
const IMPRINT = (
    hues = [
${sortedPalette.map(s => `        colorant"${s.hex}",${hueComment(s)}`).join('\n')}
    ],
    amber = colorant"${amberVal}",  # warning / caution
    neutral = (light = colorant"#1A1A17", dark = colorant"#F0EFE8"),
    muted   = (light = colorant"#6B6A63", dark = colorant"#A8A79F"),
    # continuous ramps: stops (colours and positions), low -> high, per use and theme
${rampEntries('julia')}
)

color = IMPRINT.hues[1]  # first series = slot 0, brand green (Julia is 1-based: index 1)

# continuous data — Makie colormaps: fields for cells that fill the plot,
# marks for points / lines / bars; .dark on dark bg
using CairoMakie  # cgrad
imprint_seq = cgrad(IMPRINT.seq.fields.light.colors, IMPRINT.seq.fields.light.values)
imprint_div = cgrad(IMPRINT.div.fields.light.colors, IMPRINT.div.fields.light.values)`;
    case 'js':
      return `// imprint — anyplot's palette (https://anyplot.ai/palette)
const IMPRINT = {
  hues: [
${sortedPalette.map(s => `    "${colorVal(s)}",`).join('\n')}
  ],
  amber: "${amberVal}", // warning / caution
  neutral: { light: "#1A1A17", dark: "#F0EFE8" },
  muted:   { light: "#6B6A63", dark: "#A8A79F" },
  // continuous ramps: [position, hex] stops, low -> high, per use and theme
${rampEntries('js')}
};

const color = IMPRINT.hues[0]; // first series is ALWAYS slot 0 (brand green)

// continuous data — [position, color] stops for your charting lib: fields for
// cells that fill the plot, marks for points / lines / bars; .dark on dark bg
const imprintSeq = IMPRINT.seq.fields.light;
const imprintDiv = IMPRINT.div.fields.light;`;
  }
}
