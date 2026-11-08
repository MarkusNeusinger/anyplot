// anyplot.ai
// range-interval: Range Interval Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // value-axis padding beyond the lowest minimum and highest maximum, share of the span
const BAR_SHARE = 0.42; // range bar thickness as a share of its category band
const CAP_SHARE = 0.28; // endpoint marker radius as a share of the bar thickness
const TITLE_H = 48;
const SUBTITLE_H = 28;

// Columns: set these to your data's column names
const DEPARTMENT = "Department"; // role: category
const MIN_SALARY = "Minimum base salary ($k)"; // role: min_value
const MAX_SALARY = "Maximum base salary ($k)"; // role: max_value
const SALARY = "Base salary ($k)"; // value-axis title shared by both bounds

// Data: replace this block with your own records, one object per row
// Annual base-salary bands by department at a mid-size tech company
const data = [
  { [DEPARTMENT]: "Customer Support", [MIN_SALARY]: 42, [MAX_SALARY]: 58 },
  { [DEPARTMENT]: "Marketing", [MIN_SALARY]: 48, [MAX_SALARY]: 72 },
  { [DEPARTMENT]: "Sales", [MIN_SALARY]: 45, [MAX_SALARY]: 95 },
  { [DEPARTMENT]: "Data Analytics", [MIN_SALARY]: 62, [MAX_SALARY]: 98 },
  { [DEPARTMENT]: "Product Management", [MIN_SALARY]: 78, [MAX_SALARY]: 125 },
  { [DEPARTMENT]: "DevOps & Infrastructure", [MIN_SALARY]: 88, [MAX_SALARY]: 145 },
  { [DEPARTMENT]: "Software Engineering", [MIN_SALARY]: 85, [MAX_SALARY]: 165 },
  { [DEPARTMENT]: "Engineering Leadership", [MIN_SALARY]: 120, [MAX_SALARY]: 210 },
];

// Plot: reads only data and the constants above
// Ranges sorted by midpoint, lowest at the top; a row with a missing bound is left out
const ranges = data
  .filter((d) => Number.isFinite(d[MIN_SALARY]) && Number.isFinite(d[MAX_SALARY]))
  .map((d) => ({ category: d[DEPARTMENT], lo: Math.min(d[MIN_SALARY], d[MAX_SALARY]), hi: Math.max(d[MIN_SALARY], d[MAX_SALARY]) }))
  .sort((a, b) => a.lo + a.hi - (b.lo + b.hi));
const lowest = Math.min(...ranges.map((r) => r.lo));
const highest = Math.max(...ranges.map((r) => r.hi));
const pad = (highest - lowest) * PAD_SHARE;

const TITLE = "range-interval · javascript · muix · anyplot.ai";
const unit = SALARY.match(/\(([^)]+)\)/)?.[1] ?? "";
const SUBTITLE = `${ranges.length} ranges sorted by midpoint · overall span ${lowest}–${highest} ${unit}`;

function RangeBars() {
  const xScale = useXScale();
  const yScale = useYScale();
  const thickness = yScale.bandwidth() * BAR_SHARE;

  return (
    <g>
      {ranges.map((r) => {
        const x0 = xScale(r.lo);
        const x1 = xScale(r.hi);
        const yMid = yScale(r.category) + yScale.bandwidth() / 2;
        return (
          <g key={r.category}>
            <rect x={x0} y={yMid - thickness / 2} width={x1 - x0} height={thickness} rx={4} fill={t.palette[0]} fillOpacity={0.85} />
            {[x0, x1].map((x, k) => (
              <circle key={k} cx={x} cy={yMid} r={thickness * CAP_SHARE} fill={t.palette[0]} stroke={t.ink} strokeWidth={1.5} />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - SUBTITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 20, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: lowest - pad,
            max: highest + pad,
            label: SALARY,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: ranges.map((r) => r.category),
            label: DEPARTMENT,
            width: 220,
            disableTicks: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsGrid vertical />
        <RangeBars />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
