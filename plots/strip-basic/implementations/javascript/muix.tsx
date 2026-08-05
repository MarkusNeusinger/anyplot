// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 84/100 | Created: 2026-08-05
//# anyplot-orientation: landscape
// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-05

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Reproducible LCG (seed 42) — the browser harness has no seeded Math.random()
let seed = 42;
function rng() {
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}

// Box-Muller transform for approximately-normal samples from the LCG stream
function gaussian() {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function hexToRgba(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

// Time to symptom relief (minutes) after treatment, four groups
const GROUPS = [
  { name: "Control", mean: 46, std: 12, n: 42 },
  { name: "Drug A", mean: 30, std: 10, n: 42 },
  { name: "Drug B", mean: 19, std: 7, n: 42 },
  { name: "Drug C", mean: 11, std: 5, n: 42 },
];

const JITTER_WIDTH = 0.18; // moderate horizontal spread within each category
const POINT_ALPHA = 0.62; // frequent overlap at n=42 per group

const series = GROUPS.map((group, i) => ({
  type: "scatter",
  id: group.name,
  label: group.name,
  color: hexToRgba(t.palette[i], POINT_ALPHA),
  markerSize: 11,
  data: Array.from({ length: group.n }, (_, j) => ({
    x: i + (rng() * 2 - 1) * JITTER_WIDTH,
    y: Math.max(2, group.mean + group.std * gaussian()),
    id: `${group.name}-${j}`,
  })),
}));

const TITLE = "strip-basic · javascript · muix · anyplot.ai";

export default function Chart() {
  return (
    <ChartContainer
      width={width}
      height={height}
      margin={{ top: 62, right: 56, bottom: 88, left: 100 }}
      sx={{ "& .MuiChartsAxis-top, & .MuiChartsAxis-right": { display: "none" } }}
      series={series}
      xAxis={[
        {
          id: "group",
          min: -0.6,
          max: GROUPS.length - 1 + 0.6,
          tickInterval: GROUPS.map((_, i) => i),
          valueFormatter: (v) => GROUPS[Math.round(v)]?.name ?? "",
          label: "Treatment Group",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          id: "time",
          min: 0,
          label: "Time to Relief (minutes)",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
    >
      <ChartsGrid horizontal />
      <ScatterPlot skipAnimation />
      <ChartsXAxis
        axisId="group"
        tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
        labelStyle={{ fontSize: 16, fill: t.ink }}
      />
      <ChartsYAxis
        axisId="time"
        tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
        labelStyle={{ fontSize: 16, fill: t.ink }}
      />
      <text x={width / 2} y={30} textAnchor="middle" fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
    </ChartContainer>
  );
}
