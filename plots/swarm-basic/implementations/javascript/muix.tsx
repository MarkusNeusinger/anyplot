// anyplot.ai
// swarm-basic: Basic Swarm Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MARGIN = { left: 110, right: 60, top: 80, bottom: 100 };
const SCORE_MIN = 40;
const SCORE_MAX = 100;
const MARKER_SIZE = 7;
const MARKER_DIAMETER_PX = MARKER_SIZE * 2 + 1;

// Columns: set these to your data's column names
const CATEGORY = "Department"; // role: category
const VALUE = "Performance Score"; // role: value

// Data: replace this block with your own records
const deptSpecs = [
  { name: "Engineering", mean: 78, std: 8, n: 40 },
  { name: "Sales", mean: 70, std: 12, n: 40 },
  { name: "Marketing", mean: 74, std: 9, n: 40 },
  { name: "Support", mean: 83, std: 6, n: 40 },
];

let lcgSeed = 42;
const data: Array<Record<string, string | number>> = [];
for (const d of deptSpecs) {
  for (let i = 0; i < d.n; i++) {
    lcgSeed = (lcgSeed * 1664525 + 1013904223) % 4294967296;
    const u1 = Math.max(lcgSeed / 4294967296, 1e-9);
    lcgSeed = (lcgSeed * 1664525 + 1013904223) % 4294967296;
    const u2 = lcgSeed / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const score = Math.min(99, Math.max(45, d.mean + z * d.std));
    data.push({
      [CATEGORY]: d.name,
      [VALUE]: Number(score.toFixed(2)),
    });
  }
}

// Plot: reads only data and the constants above
const departments: string[] = [];
for (const row of data) {
  const dept = String(row[CATEGORY]);
  if (!departments.includes(dept)) departments.push(dept);
}

const xMin = -0.6;
const xMax = departments.length - 1 + 0.6;
const plotWidthPx = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right;
const plotHeightPx = window.ANYPLOT_SIZE.height - MARGIN.top - MARGIN.bottom;
const pxPerScore = plotHeightPx / (SCORE_MAX - SCORE_MIN);
const pxPerX = plotWidthPx / (xMax - xMin);

const medianByDept: number[] = [];
const series = departments.map((department, categoryIndex) => {
  const scores = data
    .filter((r) => String(r[CATEGORY]) === department)
    .map((r) => Number(r[VALUE]))
    .sort((a, b) => a - b);

  const mid = Math.floor(scores.length / 2);
  const med =
    scores.length % 2 === 0
      ? (scores[mid - 1] + scores[mid]) / 2
      : scores[mid];
  medianByDept.push(med);

  const placed: Array<{ score: number; offsetPx: number }> = [];
  for (const score of scores) {
    const nearby = placed.filter(
      (p) => Math.abs((score - p.score) * pxPerScore) < MARKER_DIAMETER_PX,
    );
    let offsetPx = 0;
    if (nearby.length > 0) {
      const step = MARKER_DIAMETER_PX * 0.92;
      let k = 0;
      let resolved = false;
      while (!resolved && k < 200) {
        const candidate =
          k === 0
            ? 0
            : (k % 2 === 1 ? Math.ceil(k / 2) : -Math.ceil(k / 2)) * step;
        if (
          nearby.every(
            (p) =>
              Math.hypot(
                candidate - p.offsetPx,
                (score - p.score) * pxPerScore,
              ) >=
              MARKER_DIAMETER_PX * 0.95,
          )
        ) {
          offsetPx = candidate;
          resolved = true;
        }
        k += 1;
      }
    }
    placed.push({ score, offsetPx });
  }

  return {
    type: "scatter" as const,
    id: department,
    label: department,
    color: t.palette[categoryIndex % t.palette.length],
    markerSize: MARKER_SIZE,
    data: placed.map((p, idx) => ({
      id: `${department}-${idx}`,
      x: categoryIndex + p.offsetPx / pxPerX,
      y: p.score,
    })),
  };
});

function MedianTicks() {
  const xScale = useXScale("xAxis") as (v: number) => number;
  const yScale = useYScale("yAxis") as (v: number) => number;
  const halfWidth = 0.34;

  return (
    <g>
      {departments.map((department, i) => {
        const x1 = xScale(i - halfWidth);
        const x2 = xScale(i + halfWidth);
        const y = yScale(medianByDept[i]);
        return (
          <line
            key={department}
            x1={x1}
            y1={y}
            x2={x2}
            y2={y}
            stroke={t.ink}
            strokeWidth={2.5}
            strokeOpacity={0.8}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        series={series}
        xAxis={[
          {
            id: "xAxis",
            min: xMin,
            max: xMax,
            height: 60,
            tickInterval: departments.map((_, i) => i),
            valueFormatter: (v: number) => departments[Math.round(v)] ?? "",
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "yAxis",
            min: SCORE_MIN,
            max: SCORE_MAX,
            width: 84,
            label: VALUE,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={MARGIN}
      >
        <ChartsGrid horizontal />
        <ScatterPlot skipAnimation />
        <MedianTicks />
        <ChartsXAxis axisId="xAxis" />
        <ChartsYAxis axisId="yAxis" />
        <text
          x={width / 2}
          y={42}
          textAnchor="middle"
          fontSize={22}
          fontWeight={600}
          fill={t.ink}
        >
          Department Quarterly Performance Scores · swarm-basic · javascript · muix · anyplot.ai
        </text>
      </ChartsContainer>
    </div>
  );
}
