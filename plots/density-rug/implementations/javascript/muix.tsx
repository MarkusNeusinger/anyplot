// anyplot.ai
// density-rug: Density Plot with Rug Marks
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "density-rug · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic): petal lengths from two wildflower
// populations surveyed in the same meadow, merged into one sample. -----------
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

const POP_A_SIZE = 75;
const POP_A_MEAN = 4.2;
const POP_A_SD = 0.4;

const POP_B_SIZE = 65;
const POP_B_MEAN = 6.6;
const POP_B_SD = 0.5;

const petalLengths = [
  ...Array.from(
    { length: POP_A_SIZE },
    () => POP_A_MEAN + POP_A_SD * randomNormal(),
  ),
  ...Array.from(
    { length: POP_B_SIZE },
    () => POP_B_MEAN + POP_B_SD * randomNormal(),
  ),
];

// --- Gaussian KDE -------------------------------------------------------
function gaussianKernel(u) {
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
}

const n = petalLengths.length;
const sampleMean = petalLengths.reduce((sum, v) => sum + v, 0) / n;
const variance =
  petalLengths.reduce((sum, v) => sum + (v - sampleMean) ** 2, 0) / (n - 1);
// Narrower than Silverman's rule of thumb, otherwise the two source
// populations blur into a single smoothed hump instead of staying distinct —
// the rug marks below then confirm the resulting gap is real, not a KDE artifact.
const bandwidth = 0.55 * Math.sqrt(variance) * n ** (-1 / 5);

const dataMin = Math.min(...petalLengths);
const dataMax = Math.max(...petalLengths);
const GRID_POINTS = 200;
const gridStart = dataMin - 3 * bandwidth;
const gridEnd = dataMax + 3 * bandwidth;
const gridStep = (gridEnd - gridStart) / (GRID_POINTS - 1);

const grid = Array.from(
  { length: GRID_POINTS },
  (_, i) => gridStart + i * gridStep,
);
const density = grid.map(
  (x) =>
    petalLengths.reduce(
      (sum, xi) => sum + gaussianKernel((x - xi) / bandwidth),
      0,
    ) /
    (n * bandwidth),
);

// --- Rug marks: one short tick per raw observation, anchored to the plot's
// bottom edge via the chart's own x-scale and drawing-area geometry. ---------
function RugMarks({ values, color }) {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  const axisY = top + height;
  const tickLength = 18;

  return (
    <g>
      {values.map((value, i) => (
        <line
          key={i}
          x1={xScale(value)}
          x2={xScale(value)}
          y1={axisY}
          y2={axisY - tickLength}
          stroke={color}
          strokeWidth={1.5}
          strokeOpacity={0.55}
        />
      ))}
    </g>
  );
}

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
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        margin={{ left: 110, right: 40, top: 20, bottom: 60 }}
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
            label: "Petal Length (cm)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => v.toFixed(1),
          },
        ]}
        yAxis={[
          {
            label: "Density",
            labelStyle: { fontSize: 16 },
            // tickFontSize only drives the axis-label offset (see ChartsYAxis
            // labelRefPoint) — actual tick glyphs stay at tickLabelStyle's 14px.
            tickFontSize: 40,
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => v.toFixed(2),
          },
        ]}
        grid={{ horizontal: true }}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiAreaElement-root": { fillOpacity: 0.3 },
          "& .MuiLineElement-root": { strokeWidth: 3 },
        }}
      >
        <RugMarks values={petalLengths} color={t.palette[0]} />
      </LineChart>
    </div>
  );
}
