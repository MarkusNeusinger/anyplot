// anyplot.ai
// density-basic: Basic Density Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;
const TITLE = "density-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic): marathon finish times, right-skewed ---
// Small LCG so results are reproducible without a seeded Math.random().
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

const rand = lcg(42);

function randomNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const SAMPLE_SIZE = 400;
const LOG_MEAN = Math.log(230); // median finish time ~230 minutes
const LOG_SD = 0.18; // slower-runner tail produces the right skew

const finishTimes = Array.from({ length: SAMPLE_SIZE }, () =>
  Math.exp(LOG_MEAN + LOG_SD * randomNormal()),
);

// --- Gaussian KDE (Silverman's rule of thumb for bandwidth) -----------------
function gaussianKernel(u) {
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
}

const n = finishTimes.length;
const meanTime = finishTimes.reduce((sum, v) => sum + v, 0) / n;
const variance =
  finishTimes.reduce((sum, v) => sum + (v - meanTime) ** 2, 0) / (n - 1);
const bandwidth = 1.06 * Math.sqrt(variance) * n ** (-1 / 5);

const dataMin = Math.min(...finishTimes);
const dataMax = Math.max(...finishTimes);
const GRID_POINTS = 200;
const gridStart = dataMin - 3 * bandwidth;
const gridStep = (dataMax + 3 * bandwidth - gridStart) / (GRID_POINTS - 1);

const grid = Array.from(
  { length: GRID_POINTS },
  (_, i) => gridStart + i * gridStep,
);
// Scaled ×1000 so y-axis ticks read as clean one-decimal numbers.
const density = grid.map(
  (x) =>
    (1000 *
      finishTimes.reduce(
        (sum, xi) => sum + gaussianKernel((x - xi) / bandwidth),
        0,
      )) /
    (n * bandwidth),
);

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
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        margin={{ left: 120, right: 40, top: 20, bottom: 60 }}
        skipAnimation
        series={[
          {
            data: density,
            label: "Density",
            color: t.palette[0],
            area: true,
            curve: "natural",
            showMark: false,
          },
        ]}
        xAxis={[
          {
            data: grid,
            scaleType: "linear",
            label: "Marathon Finish Time (minutes)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => v.toFixed(0),
          },
        ]}
        yAxis={[
          {
            label: "Density (×10⁻³)",
            labelStyle: { fontSize: 16 },
            // tickFontSize only drives the axis-label offset (see ChartsYAxis
            // labelRefPoint) — actual tick glyphs stay at tickLabelStyle's 14px.
            tickFontSize: 40,
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => v.toFixed(1),
          },
        ]}
        grid={{ horizontal: true }}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiAreaElement-root": { fillOpacity: 0.35 },
          "& .MuiLineElement-root": { strokeWidth: 3 },
        }}
      />
    </div>
  );
}
