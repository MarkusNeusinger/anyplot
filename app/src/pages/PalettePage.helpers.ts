/**
 * Helpers for the /palette page: the imprint palette data (8 categorical
 * hues with OKLCH coords + ΔE / WCAG stats) and the per-language copy-paste
 * snippet generator. Pure data + string building, extracted from
 * PalettePage.tsx so the page module only exports the component (Fast
 * Refresh) and snippet() stays unit-testable in PalettePage.snippet.test.ts.
 */

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

export function snippet(lang: Lang, oklch: boolean, sortedPalette: Swatch[]): string {
  // CSS `oklch()` literals are only consumable where the runtime parses CSS
  // colours (JS / CSS). matplotlib, ggplot2 and Makie can't read them, so those
  // snippets stay hex (runnable) and surface the OKLCH coordinate as a trailing
  // comment instead — toggling OKLCH then annotates rather than breaks the code.
  const useLiteral = oklch && lang === 'js';
  const colorVal = (s: Swatch) => (useLiteral ? s.oklch : s.hex);
  const hueComment = (s: Swatch) => (oklch && lang !== 'js' ? `  # ${s.oklch}` : '');
  const amberVal = useLiteral ? 'oklch(0.841 0.108 98.3)' : '#DDCC77';
  const seqStart = useLiteral ? 'oklch(0.620 0.130 165.5)' : '#009E73';
  const seqEnd = useLiteral ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  const divStart = useLiteral ? 'oklch(0.503 0.163 25.2)' : '#AE3030';
  const divEnd = useLiteral ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  // Theme-adaptive neutrals + diverging midpoints are kept as hex in both
  // modes — they are structural near-greys, and converting them to OKLCH adds
  // noise without helping anyone paste them.
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
    seq=["${seqStart}", "${seqEnd}"],  # sequential: green -> blue
    div=SimpleNamespace(               # diverging: red <-> midpoint <-> blue
        light=["${divStart}", "#FAF8F1", "${divEnd}"],
        dark=["${divStart}", "#1A1A17", "${divEnd}"],
    ),
)

color = IMPRINT.hues[0]  # first series is ALWAYS slot 0 (brand green)

# continuous data — build matplotlib cmaps from the stops
from matplotlib.colors import LinearSegmentedColormap
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", IMPRINT.seq)
imprint_div = LinearSegmentedColormap.from_list("imprint_div", IMPRINT.div.light)  # .dark on dark bg`;
    case 'r':
      return `# imprint — anyplot's palette (https://anyplot.ai/palette)
IMPRINT <- list(
  hues = c(
${sortedPalette.map((s, i, arr) => `    "${s.hex}"${i < arr.length - 1 ? ',' : ''}${hueComment(s)}`).join('\n')}
  ),
  amber = "${amberVal}",  # warning / caution
  neutral = list(light = "#1A1A17", dark = "#F0EFE8"),
  muted   = list(light = "#6B6A63", dark = "#A8A79F"),
  seq = c("${seqStart}", "${seqEnd}"),  # sequential: green -> blue
  div = list(                           # diverging: red <-> midpoint <-> blue
    light = c("${divStart}", "#FAF8F1", "${divEnd}"),
    dark  = c("${divStart}", "#1A1A17", "${divEnd}")
  )
)

color <- IMPRINT$hues[1]  # first series = slot 0, brand green (R is 1-based: index 1)

# continuous data — ggplot2 gradient scales
scale_color_gradientn(colours = IMPRINT$seq)        # sequential
scale_color_gradient2(low = IMPRINT$div$light[1], mid = IMPRINT$div$light[2], high = IMPRINT$div$light[3], midpoint = 0)  # diverging — 0 maps to the neutral midpoint (light theme)`;
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
    seq = [colorant"${seqStart}", colorant"${seqEnd}"],
    div = (light = [colorant"${divStart}", colorant"#FAF8F1", colorant"${divEnd}"],
           dark  = [colorant"${divStart}", colorant"#1A1A17", colorant"${divEnd}"]),
)

color = IMPRINT.hues[1]  # first series = slot 0, brand green (Julia is 1-based: index 1)

# continuous data — Makie / ColorSchemes
using ColorSchemes
imprint_seq = cgrad(IMPRINT.seq)
imprint_div = cgrad(IMPRINT.div.light)  # .dark on dark bg`;
    case 'js':
      return `// imprint — anyplot's palette (https://anyplot.ai/palette)
const IMPRINT = {
  hues: [
${sortedPalette.map(s => `    "${colorVal(s)}",`).join('\n')}
  ],
  amber: "${amberVal}", // warning / caution
  neutral: { light: "#1A1A17", dark: "#F0EFE8" },
  muted:   { light: "#6B6A63", dark: "#A8A79F" },
  seq: ["${seqStart}", "${seqEnd}"], // sequential: green -> blue
  div: {                             // diverging: red <-> midpoint <-> blue
    light: ["${divStart}", "#FAF8F1", "${divEnd}"],
    dark:  ["${divStart}", "#1A1A17", "${divEnd}"],
  },
};

const color = IMPRINT.hues[0]; // first series is ALWAYS slot 0 (brand green)

// continuous data — [stop, color] pairs for your charting lib
const imprintSeq = IMPRINT.seq.map((c, i, a) => [i / (a.length - 1), c]);
const imprintDiv = IMPRINT.div.light.map((c, i, a) => [i / (a.length - 1), c]);`;
  }
}
