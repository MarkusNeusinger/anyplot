// anyplot.ai
// histogram-basic: Basic Histogram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;
const TITLE = "histogram-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic): subscriber ages for a streaming service
// Deterministic LCG so the sampled distribution is stable across renders —
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

// Log-normal draw: a young-skewed subscriber base with a long tail of older
// loyal customers, rather than a perfectly symmetric bell curve.
const SAMPLE_COUNT = 600;
const LOG_MU = Math.log(29);
const LOG_SIGMA = 0.34;
const ages = Array.from({ length: SAMPLE_COUNT }, () => {
  const raw = Math.exp(LOG_MU + LOG_SIGMA * gaussianSample());
  return Math.round(Math.min(85, Math.max(16, raw)));
});

// Bin into 5-year age brackets covering the observed range.
const BIN_WIDTH = 5;
const minAge = Math.min(...ages);
const maxAge = Math.max(...ages);
const binStart = Math.floor(minAge / BIN_WIDTH) * BIN_WIDTH;
const binEnd = Math.ceil((maxAge + 1) / BIN_WIDTH) * BIN_WIDTH;
const binCount = (binEnd - binStart) / BIN_WIDTH;
const binLabels = Array.from(
  { length: binCount },
  (_, i) => `${binStart + i * BIN_WIDTH}–${binStart + (i + 1) * BIN_WIDTH}`,
);
const counts = new Array(binCount).fill(0);
ages.forEach((age) => {
  const idx = Math.min(binCount - 1, Math.floor((age - binStart) / BIN_WIDTH));
  counts[idx] += 1;
});

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;

  return (
    <div style={{ width, height }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          textAlign: "center",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <BarChart
        width={width}
        height={chartHeight}
        skipAnimation
        series={[
          {
            data: counts,
            label: "Subscribers",
            color: t.palette[0],
            valueFormatter: (v) => `${v} subscribers`,
          },
        ]}
        xAxis={[
          {
            scaleType: "band",
            data: binLabels,
            label: "Subscriber Age (years)",
            labelStyle: { fontSize: 16, fontWeight: 500 },
            tickLabelStyle: { fontSize: 13 },
            // No gap between bins — a histogram's bars are contiguous by
            // convention; the stroke below (sx) draws the bin-edge lines.
            categoryGapRatio: 0,
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: "Number of Subscribers",
            labelStyle: { fontSize: 16, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ left: 92, right: 32, top: 24, bottom: 76 }}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiBarElement-root": { stroke: t.pageBg, strokeWidth: 1.5 },
          "& .MuiChartsAxis-tickLabel": { fontSize: "13px" },
        }}
      />
    </div>
  );
}
