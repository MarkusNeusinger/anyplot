// anyplot.ai
// sequence-logo-basic: Sequence Logo for Motif Visualization
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) -----------------------------------------
// 12-bp transcription-factor binding site: a highly conserved E-box core
// (CACGTG, the canonical bHLH recognition motif) flanked by near-degenerate
// positions, letter order [A, C, G, T].
const letters = ["A", "C", "G", "T"];
const frequencyMatrix = [
  [0.28, 0.24, 0.22, 0.26],
  [0.32, 0.18, 0.22, 0.28],
  [0.25, 0.25, 0.25, 0.25],
  [0.15, 0.55, 0.1, 0.2],
  [0.05, 0.85, 0.05, 0.05],
  [0.82, 0.06, 0.06, 0.06],
  [0.05, 0.83, 0.06, 0.06],
  [0.05, 0.06, 0.84, 0.05],
  [0.05, 0.05, 0.06, 0.84],
  [0.06, 0.05, 0.83, 0.06],
  [0.22, 0.28, 0.32, 0.18],
  [0.29, 0.21, 0.24, 0.26],
];
const positions = frequencyMatrix.map((_, i) => i + 1);
const MAX_BITS = 2; // log2(4) -- max information content for a 4-letter DNA alphabet

// Standard nucleotide color convention (A=green, C=blue, G=orange/yellow,
// T=red) mapped onto the closest Imprint hues -- the Semantic Exception in
// prompts/default-style-guide.md permits this reassignment because the
// association is a widely shared domain convention, not an arbitrary choice.
const letterColor = {
  A: t.palette[0], // green
  C: t.palette[2], // blue
  G: t.palette[3], // ochre (stands in for orange/yellow)
  T: t.palette[4], // red
};

// Shannon information content per position, R(i) = max_bits - entropy(i).
const infoContent = frequencyMatrix.map((freqs) => {
  const entropy = freqs.reduce(
    (sum, p) => (p > 0 ? sum - p * Math.log2(p) : sum),
    0,
  );
  return MAX_BITS - entropy;
});

// Stack order per position, ascending by frequency, so the most frequent
// letter is drawn last (on top of the stack) -- per the spec's "most
// frequent on top" rule.
const rankedLetters = frequencyMatrix.map((freqs) =>
  letters
    .map((letter, idx) => ({ letter, freq: freqs[idx] }))
    .sort((a, b) => a.freq - b.freq),
);

// One Chart.js dataset per stack rank; each bar segment's height is that
// rank's letter frequency scaled by the position's information content.
// Segments are invisible (transparent) -- Chart.js only supplies the
// stacked layout math, the glyphs themselves are drawn by the plugin below.
const datasets = letters.map((_, rank) => ({
  data: positions.map((_, i) => rankedLetters[i][rank].freq * infoContent[i]),
  stack: "logo",
  backgroundColor: "transparent",
  borderWidth: 0,
  categoryPercentage: 1.0,
  barPercentage: 0.86,
}));

// --- Glyph-stacking plugin ---------------------------------------------------
// Draws each letter as a glyph stretched (non-uniform scale) to exactly fill
// its stack segment's rectangle, using the pixel geometry Chart.js already
// computed for the (invisible) bar segments.
const sequenceLogoGlyphs = {
  id: "sequenceLogoGlyphs",
  afterDatasetsDraw(chart) {
    const ctx = chart.ctx;
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.font = '800 100px "Arial", "Helvetica Neue", sans-serif';
    for (let rank = 0; rank < letters.length; rank++) {
      const meta = chart.getDatasetMeta(rank);
      for (let i = 0; i < positions.length; i++) {
        const value = chart.data.datasets[rank].data[i];
        if (!value) continue;
        const el = meta.data[i];
        if (!el) continue;

        const rectWidth = el.width * 0.88;
        const rectTop = el.y + 1.5;
        const rectBottom = el.base - 1.5;
        const rectHeight = rectBottom - rectTop;
        if (rectHeight <= 0) continue;

        const letter = rankedLetters[i][rank].letter;
        const metrics = ctx.measureText(letter);
        const naturalWidth = metrics.width;
        const naturalHeight = metrics.actualBoundingBoxAscent || 72;

        ctx.save();
        ctx.translate(el.x, rectBottom);
        ctx.scale(rectWidth / naturalWidth, rectHeight / naturalHeight);
        ctx.fillStyle = letterColor[letter];
        ctx.fillText(letter, 0, 0);
        ctx.restore();
      }
    }
    ctx.restore();
  },
};

// --- Mount --------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart --------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  plugins: [sequenceLogoGlyphs],
  data: {
    labels: positions.map(String),
    datasets,
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "sequence-logo-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Position", color: t.ink, font: { size: 16 } },
      },
      y: {
        stacked: true,
        min: 0,
        max: MAX_BITS,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Information content (bits)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
