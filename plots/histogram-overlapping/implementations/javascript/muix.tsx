// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-18
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;
const TITLE = "histogram-overlapping · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic): exam scores, control vs treatment -----
// Deterministic LCG so the sampled distributions are stable across renders —
// the browser has no seeded Math.random().
function makeLcg(seed) {
  let state = seed >>> 0;
  return function next() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
function gaussianSample() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const SAMPLE_COUNT = 240;
const controlScores = Array.from({ length: SAMPLE_COUNT }, () =>
  Math.min(100, Math.max(0, 68 + 11 * gaussianSample())),
);
const treatmentScores = Array.from({ length: SAMPLE_COUNT }, () =>
  Math.min(100, Math.max(0, 76 + 9 * gaussianSample())),
);

// Shared bin edges across both groups so the comparison is apples-to-apples.
const BIN_WIDTH = 5;
const allScores = controlScores.concat(treatmentScores);
const binStart = Math.floor(Math.min(...allScores) / BIN_WIDTH) * BIN_WIDTH;
const binEnd = Math.ceil(Math.max(...allScores) / BIN_WIDTH) * BIN_WIDTH;
const binCount = (binEnd - binStart) / BIN_WIDTH;
const binLabels = Array.from(
  { length: binCount },
  (_, i) => `${binStart + i * BIN_WIDTH}–${binStart + (i + 1) * BIN_WIDTH}`,
);

function countPerBin(samples) {
  const counts = new Array(binCount).fill(0);
  samples.forEach((value) => {
    const idx = Math.min(binCount - 1, Math.floor((value - binStart) / BIN_WIDTH));
    counts[idx] += 1;
  });
  return counts;
}
const controlCounts = countPerBin(controlScores);
const treatmentCounts = countPerBin(treatmentScores);

// Bake 55% opacity into the fill so overlapping regions stay legible.
function withAlpha(hex, alpha) {
  return hex + Math.round(alpha * 255).toString(16).padStart(2, "0");
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <BarChart
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        skipAnimation
        series={[
          {
            data: controlCounts,
            label: "Control group",
            color: withAlpha(t.palette[0], 0.55),
          },
          {
            data: treatmentCounts,
            label: "Treatment group",
            color: withAlpha(t.palette[1], 0.55),
          },
        ]}
        xAxis={[
          {
            scaleType: "band",
            data: binLabels,
            label: "Exam Score",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 13 },
            categoryGapRatio: 0.05,
            // Overlap the two series' bars instead of placing them side by
            // side: barGapRatio=-1 solves barWidth=bandWidth, offset=0 for
            // every series (see getBandSize in @mui/x-charts/BarChart/BarPlot),
            // so both groups' bars share the same position and width.
            barGapRatio: -1,
          },
        ]}
        yAxis={[
          {
            label: "Count",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ left: 80, right: 24, top: 24, bottom: 70 }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "top", horizontal: "right" },
            labelStyle: { fontSize: 14 },
          },
        }}
      />
    </div>
  );
}
