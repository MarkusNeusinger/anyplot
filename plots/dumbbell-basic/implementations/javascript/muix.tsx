//# anyplot-orientation: landscape
// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-30

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Department satisfaction scores (0–10) before/after a wellness program.
// Sorted ascending by "before" score to reveal the baseline-vs-gain pattern.
const departments = [
  "Finance",
  "Marketing",
  "Legal",
  "Operations",
  "Engineering",
  "Sales",
  "HR",
  "Design",
];
const beforeScores = [5.5, 5.8, 6.1, 6.3, 6.7, 7.0, 7.2, 7.5];
const afterScores  = [7.0, 7.2, 7.5, 7.6, 8.0, 8.3, 8.4, 8.7];
const N = departments.length;

// Scatter data: { id, x (score), y (category index 0…N-1) }
const beforeData = beforeScores.map((x, i) => ({ id: i,       x, y: i }));
const afterData  = afterScores.map( (x, i) => ({ id: i + 100, x, y: i }));

// Dumbbell connecting lines rendered using MUI X coordinate hooks.
// Placed before <ScatterPlot /> so dots appear on top of the lines.
function DumbbellLines() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {departments.map((_, i) => {
        const x1 = xScale(beforeScores[i]) ?? 0;
        const x2 = xScale(afterScores[i]) ?? 0;
        const y  = yScale(i) ?? 0;
        return (
          <line
            key={i}
            x1={x1} y1={y}
            x2={x2} y2={y}
            stroke={t.inkSoft}
            strokeWidth={3}
            strokeOpacity={0.4}
          />
        );
      })}
    </g>
  );
}

const TITLE = "dumbbell-basic · javascript · muix · anyplot.ai";

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <ChartContainer
      width={W}
      height={H}
      skipAnimation
      series={[
        {
          type: "scatter",
          id: "before",
          label: "Before Program",
          data: beforeData,
          color: t.palette[0],
          markerSize: 10,
        },
        {
          type: "scatter",
          id: "after",
          label: "After Program",
          data: afterData,
          color: t.palette[1],
          markerSize: 10,
        },
      ]}
      xAxis={[{
        id: "xAxis",
        min: 4.5,
        max: 9.5,
        label: "Employee Satisfaction Score (0 – 10)",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        labelStyle: { fontSize: 16, fill: t.ink },
      }]}
      yAxis={[{
        id: "yAxis",
        min: -0.5,
        max: N - 0.5,
        tickMinStep: 1,
        valueFormatter: (v) => departments[Math.round(v)] ?? "",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
      }]}
      margin={{ left: 130, right: 50, top: 70, bottom: 110 }}
    >
      <ChartsGrid vertical />
      <DumbbellLines />
      <ScatterPlot />
      <ChartsXAxis axisId="xAxis" />
      <ChartsYAxis axisId="yAxis" />
      <ChartsLegend
        position={{ vertical: "bottom", horizontal: "middle" }}
        direction="row"
      />
      <text
        x={W / 2}
        y={42}
        textAnchor="middle"
        fontSize={22}
        fontFamily="sans-serif"
        fontWeight="500"
        fill={t.ink}
      >
        {TITLE}
      </text>
    </ChartContainer>
  );
}
