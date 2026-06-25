// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-25
//# anyplot-orientation: landscape
// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Deterministic LCG (seed 42) — no Math.random() in browser harness
let _seed = 42;
function lcg() {
  _seed = (1664525 * _seed + 1013904223) >>> 0;
  return _seed / 4294967296;
}
function randn() {
  const u = lcg(), v = lcg();
  return Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
}

// Data: Weekly creative project hours vs employee innovation score
// Scenario: 120 tech-sector employees; moderate positive correlation (r ≈ 0.72)
const N = 120;
const scatterData = Array.from({ length: N }, (_, id) => {
  const hours = 2 + lcg() * 36;                        // 2–38 h/week
  const score = 28 + (hours / 40) * 58 + randn() * 11; // linear + noise
  return {
    id,
    x: Math.round(hours * 10) / 10,
    y: Math.min(98, Math.max(12, Math.round(score * 10) / 10)),
  };
});

// Brand green at 72 % opacity — satisfies "alpha ~0.7" spec requirement
const BRAND_RGBA = "rgba(0, 158, 115, 0.72)";

const TITLE = "scatter-basic · javascript · muix · anyplot.ai";
const MARGIN = { top: 72, right: 52, bottom: 90, left: 100 };

export default function Chart() {
  return (
    <ChartContainer
      width={width}
      height={height}
      margin={MARGIN}
      series={[{
        type: "scatter",
        id: "employees",
        label: "Employee",
        color: BRAND_RGBA,
        markerSize: 7,
        data: scatterData,
        valueFormatter: (v) => v ? `${v.x} h/wk · score ${v.y}` : "",
      }]}
      xAxis={[{
        scaleType: "linear",
        min: 0,
        max: 42,
        label: "Weekly Hours on Creative Projects",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        labelStyle: { fontSize: 16, fill: t.ink },
      }]}
      yAxis={[{
        scaleType: "linear",
        min: 8,
        max: 105,
        label: "Innovation Score",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        labelStyle: { fontSize: 16, fill: t.ink },
      }]}
    >
      <ChartsGrid horizontal vertical />
      <ScatterPlot skipAnimation />
      <ChartsXAxis />
      <ChartsYAxis />

      {/* L-frame: paint over top and right axis lines to get clean L-shape */}
      <line
        x1={MARGIN.left - 1} y1={MARGIN.top}
        x2={width - MARGIN.right + 1} y2={MARGIN.top}
        stroke={t.pageBg}
        strokeWidth={3}
      />
      <line
        x1={width - MARGIN.right} y1={MARGIN.top - 1}
        x2={width - MARGIN.right} y2={height - MARGIN.bottom + 1}
        stroke={t.pageBg}
        strokeWidth={3}
      />

      {/* Title */}
      <text
        x={width / 2}
        y={38}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
    </ChartContainer>
  );
}
