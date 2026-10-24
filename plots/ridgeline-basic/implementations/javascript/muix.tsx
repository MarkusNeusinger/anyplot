// anyplot.ai
// ridgeline-basic: Basic Ridgeline Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-07-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "ridgeline-basic · javascript · muix · anyplot.ai";
const GRID_N = 160;
const ROW_GAP = 1;
const PEAK_HEIGHT = 1.6;

// Columns: set these to your data's column names
const GROUP = "Month"; // role: group
const VALUE = "Daily High Temperature (°C)"; // role: value

// Data: replace this block with your own records
const MONTH_SPECS = [
  { month: "Jan", mean: -2, std: 4.5 },
  { month: "Feb", mean: 1, std: 4.5 },
  { month: "Mar", mean: 7, std: 4.0 },
  { month: "Apr", mean: 14, std: 3.5 },
  { month: "May", mean: 20, std: 3.0 },
  { month: "Jun", mean: 26, std: 2.5 },
  { month: "Jul", mean: 29, std: 2.3 },
  { month: "Aug", mean: 28, std: 2.3 },
  { month: "Sep", mean: 23, std: 2.8 },
  { month: "Oct", mean: 15, std: 3.3 },
  { month: "Nov", mean: 7, std: 4.0 },
  { month: "Dec", mean: -1, std: 4.5 },
];
const SAMPLE_COUNT = 200;

let seed = 42;
const data = [];
for (const spec of MONTH_SPECS) {
  for (let i = 0; i < SAMPLE_COUNT; i += 1) {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    const u1 = Math.max(seed / 4294967296, 1e-9);
    seed = (seed * 1664525 + 1013904223) >>> 0;
    const u2 = seed / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    data.push({ [GROUP]: spec.month, [VALUE]: spec.mean + spec.std * z });
  }
}

// Plot: reads only data and the constants above
const groups = Array.from(new Set(data.map((row) => String(row[GROUP]))));
const samplesByGroup = groups.map((g) =>
  data.filter((row) => String(row[GROUP]) === g).map((row) => Number(row[VALUE]))
);

const allValues = samplesByGroup.flat();
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const xPad = (dataMax - dataMin) * 0.08;
const xMin = dataMin - xPad;
const xMax = dataMax + xPad;

const grid = Array.from({ length: GRID_N }, (_, k) => xMin + (k * (xMax - xMin)) / (GRID_N - 1));
const densityByGroup = samplesByGroup.map((samples) => {
  const n = samples.length;
  const m = samples.reduce((a, b) => a + b, 0) / n;
  const variance = samples.reduce((a, b) => a + (b - m) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);
  const bandwidth = 0.9 * std * Math.pow(n, -0.2);
  const raw = grid.map((gx) => samples.reduce((sum, s) => sum + Math.exp(-0.5 * ((gx - s) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  return raw.map((v) => v / peak);
});

const nGroups = groups.length;
const yMin = -0.25;
const yMax = (nGroups - 1) * ROW_GAP + PEAK_HEIGHT + 0.15;

const seqA = parseInt(t.seq[0].slice(1), 16);
const seqB = parseInt(t.seq[1].slice(1), 16);
const ar = (seqA >> 16) & 255;
const ag = (seqA >> 8) & 255;
const ab = seqA & 255;
const br = (seqB >> 16) & 255;
const bg = (seqB >> 8) & 255;
const bb = seqB & 255;

const ridgeColors = groups.map((_, i) => {
  const frac = nGroups > 1 ? i / (nGroups - 1) : 0;
  const rr = Math.round(ar + (br - ar) * frac);
  const rg = Math.round(ag + (bg - ag) * frac);
  const rb = Math.round(ab + (bb - ab) * frac);
  return `rgb(${rr}, ${rg}, ${rb})`;
});

function RidgelineLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width: drawW } = useDrawingArea();
  const titleSize = TITLE.length > 67 ? Math.round(22 * (67 / TITLE.length)) : 22;

  return (
    <g>
      <text x={left + drawW / 2} y={top - 46} textAnchor="middle" fontSize={titleSize} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>

      <g strokeLinejoin="round">
        {groups.map((name, i) => {
          const baseline = (nGroups - 1 - i) * ROW_GAP;
          const baselineY = yScale(baseline);
          const topPoints = grid.map((gx, k) => `${xScale(gx)},${yScale(baseline + densityByGroup[i][k] * PEAK_HEIGHT)}`);
          const path = `M${xScale(grid[0])},${baselineY} L${topPoints.join(" L")} L${xScale(grid[GRID_N - 1])},${baselineY} Z`;
          return <path key={name} d={path} fill={ridgeColors[i]} fillOpacity={0.92} stroke={t.pageBg} strokeWidth={2} />;
        })}
      </g>

      {groups.map((name, i) => {
        const baseline = (nGroups - 1 - i) * ROW_GAP;
        return (
          <text
            key={name}
            x={left - 14}
            y={yScale(baseline)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={15}
            fill={t.inkSoft}
          >
            {name}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <ChartsContainer
      width={width}
      height={height}
      skipAnimation
      series={[]}
      xAxis={[
        {
          scaleType: "linear",
          min: xMin,
          max: xMax,
          height: 64,
          label: VALUE,
          labelStyle: { fontSize: 16 },
          tickLabelStyle: { fontSize: 14 },
        },
      ]}
      yAxis={[{ scaleType: "linear", min: yMin, max: yMax, position: "none" }]}
      margin={{ top: 110, right: 60, bottom: 32, left: 90 }}
    >
      <RidgelineLayer />
      <ChartsXAxis position="bottom" />
    </ChartsContainer>
  );
}
