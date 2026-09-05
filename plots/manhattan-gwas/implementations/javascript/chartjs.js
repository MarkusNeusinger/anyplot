// anyplot.ai
// manhattan-gwas: Manhattan Plot for GWAS
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG + Box-Muller) ----------------------------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal() {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Data: simulated GWAS summary statistics --------------------------------
// Approximate human chromosome lengths (Mb), 1-22 + X. Points-per-chromosome is
// a representative subsample (not the full 100k-1M variants) so the scatter
// stays legible and renders quickly.
const CHROM_LENGTHS_MB = [
  248, 242, 198, 190, 181, 170, 159, 145, 138, 133, 135, 133, 114, 107, 101,
  90, 83, 80, 58, 64, 46, 50, 155,
];
const CHROM_LABELS = [...Array(22).keys()].map((i) => String(i + 1)).concat("X");
const POINTS_PER_CHROM = 200;
const GENOME_WIDE = -Math.log10(5e-8); // ~7.301
const SUGGESTIVE = -Math.log10(1e-5); // 5

const chromRanges = [];
const points = [];
let cumOffset = 0;
CHROM_LABELS.forEach((label, i) => {
  const lengthMb = CHROM_LENGTHS_MB[i];
  const start = cumOffset;
  for (let j = 0; j < POINTS_PER_CHROM; j++) {
    const cumPos = start + rand() * lengthMb;
    const negLog10p = -Math.log10(Math.max(rand(), 1e-12));
    points.push({ x: cumPos, y: negLog10p, chromIndex: i });
  }
  chromRanges.push({ label, start, end: start + lengthMb, mid: start + lengthMb / 2 });
  cumOffset += lengthMb;
});

// Inject a handful of significant association peaks on selected chromosomes.
const peakChromLabels = ["2", "6", "11", "17"];
peakChromLabels.forEach((label) => {
  const range = chromRanges.find((r) => r.label === label);
  const chromIndex = CHROM_LABELS.indexOf(label);
  const peakCenter = range.start + rand() * (range.end - range.start);
  for (let k = 0; k < 14; k++) {
    const cumPos = Math.min(Math.max(peakCenter + randNormal() * 1.4, range.start), range.end);
    const negLog10p = GENOME_WIDE + Math.abs(randNormal()) * 3 + (k === 0 ? 2.5 : 0);
    points.push({ x: cumPos, y: negLog10p, chromIndex });
  }
});

// Split by chromosome parity (alternating color bands) and significance.
const evenChromPoints = [];
const oddChromPoints = [];
const significantPoints = [];
points.forEach((p) => {
  if (p.y >= GENOME_WIDE) {
    significantPoints.push({ x: p.x, y: p.y });
  } else if (p.chromIndex % 2 === 0) {
    evenChromPoints.push({ x: p.x, y: p.y });
  } else {
    oddChromPoints.push({ x: p.x, y: p.y });
  }
});

const genomeLength = cumOffset;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Chr (even)",
        data: evenChromPoints,
        backgroundColor: t.palette[0],
        pointRadius: 2.5,
        pointHoverRadius: 2.5,
      },
      {
        label: "Chr (odd)",
        data: oddChromPoints,
        backgroundColor: t.palette[2],
        pointRadius: 2.5,
        pointHoverRadius: 2.5,
      },
      {
        label: "Genome-wide significant",
        data: significantPoints,
        backgroundColor: t.palette[4],
        pointRadius: 3.5,
        pointHoverRadius: 3.5,
      },
      {
        type: "line",
        label: "Genome-wide (p < 5e-8)",
        data: [
          { x: 0, y: GENOME_WIDE },
          { x: genomeLength, y: GENOME_WIDE },
        ],
        borderColor: t.palette[4],
        borderWidth: 2,
        borderDash: [8, 6],
        pointRadius: 0,
        fill: false,
      },
      {
        type: "line",
        label: "Suggestive (p < 1e-5)",
        data: [
          { x: 0, y: SUGGESTIVE },
          { x: genomeLength, y: SUGGESTIVE },
        ],
        borderColor: t.inkSoft,
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "manhattan-gwas · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: { color: t.inkSoft, font: { size: 13 }, boxWidth: 16, padding: 16 },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: genomeLength,
        afterBuildTicks: (axis) => {
          axis.ticks = chromRanges.map((r) => ({ value: r.mid }));
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          callback: (value) => {
            const range = chromRanges.find((r) => r.mid === value);
            return range ? range.label : "";
          },
        },
        grid: { display: false },
        title: { display: true, text: "Chromosome", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: 0,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "-log10(p-value)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
