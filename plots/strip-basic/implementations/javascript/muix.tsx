// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-08-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const JITTER_WIDTH = 0.27;
const POINT_ALPHA = 0.62;
const MEAN_LINE_HALF_WIDTH = 0.34;

// Columns: set these to your data's column names
const CATEGORY = "Treatment Regimen"; // role: category
const VALUE = "Time to Relief (minutes)"; // role: value

// Data: replace this block with your own records
const groupSpecs = [
  { name: "Placebo Control", mean: 46, std: 12, n: 42 },
  { name: "Ibuprofen 400 mg", mean: 30, std: 10, n: 42 },
  { name: "Naproxen 500 mg", mean: 19, std: 7, n: 42 },
  { name: "Ketorolac 10 mg", mean: 11, std: 5, n: 42 },
];

let dataSeed = 42;
const data: Array<Record<string, string | number>> = [];
for (const g of groupSpecs) {
  for (let j = 0; j < g.n; j++) {
    dataSeed = (1664525 * dataSeed + 1013904223) >>> 0;
    const u1 = Math.max(dataSeed / 4294967296, 1e-9);
    dataSeed = (1664525 * dataSeed + 1013904223) >>> 0;
    const u2 = dataSeed / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    data.push({
      [CATEGORY]: g.name,
      [VALUE]: Number(Math.max(2, g.mean + g.std * z).toFixed(2)),
    });
  }
}

// Plot: reads only data and the constants above
const categories: string[] = [];
for (const row of data) {
  const cat = String(row[CATEGORY]);
  if (!categories.includes(cat)) categories.push(cat);
}

let jitterSeed = 1337;
const groupData = categories.map((cat, catIdx) => {
  const rows = data.filter((r) => String(r[CATEGORY]) === cat);
  const points = rows.map((r, j) => {
    jitterSeed = (1664525 * jitterSeed + 1013904223) >>> 0;
    const u = jitterSeed / 4294967296;
    return {
      x: catIdx + (u * 2 - 1) * JITTER_WIDTH,
      y: Number(r[VALUE]),
      id: `${cat}-${j}`,
    };
  });
  const observedMean =
    points.reduce((sum, p) => sum + p.y, 0) / points.length;
  return { name: cat, points, observedMean };
});

const series = groupData.map((group, i) => {
  const hex = t.palette[i % t.palette.length];
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return {
    type: "scatter" as const,
    id: group.name,
    label: group.name,
    color: `rgba(${r}, ${g}, ${b}, ${POINT_ALPHA})`,
    markerSize: 9,
    data: group.points,
  };
});

function MeanLines() {
  const xScale = useXScale("group") as (v: number) => number;
  const yScale = useYScale("time") as (v: number) => number;
  return (
    <g>
      {groupData.map((group, i) => {
        const y = yScale(group.observedMean);
        return (
          <line
            key={group.name}
            x1={xScale(i - MEAN_LINE_HALF_WIDTH)}
            x2={xScale(i + MEAN_LINE_HALF_WIDTH)}
            y1={y}
            y2={y}
            stroke={t.palette[i % t.palette.length]}
            strokeWidth={3}
            strokeLinecap="round"
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
        margin={{ top: 68, right: 56, bottom: 88, left: 100 }}
        series={series}
        xAxis={[
          {
            id: "group",
            min: -0.6,
            max: categories.length - 1 + 0.6,
            height: 60,
            tickInterval: categories.map((_, i) => i),
            valueFormatter: (v: number) => categories[Math.round(v)] ?? "",
            label: CATEGORY,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "time",
            min: 0,
            width: 84,
            label: VALUE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <ScatterPlot skipAnimation />
        <MeanLines />
        <ChartsXAxis axisId="group" />
        <ChartsYAxis axisId="time" />
        <text
          x={width / 2}
          y={34}
          textAnchor="middle"
          fontSize={22}
          fontWeight={600}
          fill={t.ink}
        >
          Analgesic Time to Symptom Relief · strip-basic · javascript · muix · anyplot.ai
        </text>
      </ChartsContainer>
    </div>
  );
}
