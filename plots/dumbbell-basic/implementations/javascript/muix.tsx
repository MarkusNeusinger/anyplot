// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";
const TITLE = "dumbbell-basic · javascript · muix · anyplot.ai";
const X_PAD_LEFT_SHARE = 0.14;
const X_PAD_RIGHT_SHARE = 0.2;
const MARKER_SIZE = 10;
const START_COLOR = t.palette[0];
const END_COLOR = t.palette[1];

// Columns: set these to your data's column names
const CATEGORY = "Department"; // role: category
const START_VALUE = "Before program (satisfaction score)"; // role: start_value
const END_VALUE = "After program (satisfaction score)"; // role: end_value

// Data: replace this block with your own records
const data = [
  { [CATEGORY]: "Finance", [START_VALUE]: 5.4, [END_VALUE]: 5.9 },
  { [CATEGORY]: "Legal", [START_VALUE]: 5.7, [END_VALUE]: 5.5 },
  { [CATEGORY]: "Marketing", [START_VALUE]: 6.0, [END_VALUE]: 7.6 },
  { [CATEGORY]: "Sales", [START_VALUE]: 6.2, [END_VALUE]: 6.7 },
  { [CATEGORY]: "Operations", [START_VALUE]: 6.5, [END_VALUE]: 9.0 },
  { [CATEGORY]: "Engineering", [START_VALUE]: 6.8, [END_VALUE]: 7.7 },
  { [CATEGORY]: "HR", [START_VALUE]: 7.1, [END_VALUE]: 8.4 },
  { [CATEGORY]: "Design", [START_VALUE]: 7.4, [END_VALUE]: 8.0 },
];

// Plot: reads only data and the constants above
const sortedData = [...data].sort(
  (a, b) => Number(a[START_VALUE]) - Number(b[START_VALUE]),
);

const categories = sortedData.map((d) => String(d[CATEGORY]));
const startValues = sortedData.map((d) => Number(d[START_VALUE]));
const endValues = sortedData.map((d) => Number(d[END_VALUE]));
const diffs = sortedData.map((d) => +(Number(d[END_VALUE]) - Number(d[START_VALUE])).toFixed(1));
const n = sortedData.length;

const allValues = [...startValues, ...endValues];
const valMin = Math.min(...allValues);
const valMax = Math.max(...allValues);
const valSpan = valMax - valMin;
const xMin = valMin - valSpan * X_PAD_LEFT_SHARE;
const xMax = valMax + valSpan * X_PAD_RIGHT_SHARE;

const startSeriesData = startValues.map((x, i) => ({ id: i, x, y: i }));
const endSeriesData = endValues.map((x, i) => ({ id: i + n, x, y: i }));
const X_AXIS_LABEL = `${START_VALUE} vs ${END_VALUE}`;

function DumbbellOverlay() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  return (
    <g>
      {sortedData.map((d, i) => {
        const x1 = xScale(Number(d[START_VALUE]));
        const x2 = xScale(Number(d[END_VALUE]));
        const y = yScale(i);
        const rightX = Math.max(x1, x2);
        const diff = diffs[i];
        const diffLabel = diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1);

        return (
          <g key={String(d[CATEGORY])}>
            <line
              x1={x1}
              y1={y}
              x2={x2}
              y2={y}
              stroke={t.inkSoft}
              strokeWidth={2.5}
              strokeOpacity={0.55}
            />
            <text
              x={rightX + 16}
              y={y + 5}
              fontSize={14}
              fill={t.inkSoft}
              fontFamily={FONT}
              fontWeight={500}
            >
              {diffLabel}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const headerH = 84;
  const chartH = H - headerH;

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          height: headerH,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28, fontSize: 15, color: t.ink }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 13,
                height: 13,
                borderRadius: "50%",
                backgroundColor: START_COLOR,
                display: "inline-block",
              }}
            />
            {START_VALUE}
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 13,
                height: 13,
                borderRadius: "50%",
                backgroundColor: END_COLOR,
                display: "inline-block",
              }}
            />
            {END_VALUE}
          </span>
        </div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "start",
            label: START_VALUE,
            data: startSeriesData,
            color: START_COLOR,
            markerSize: MARKER_SIZE,
          },
          {
            type: "scatter",
            id: "end",
            label: END_VALUE,
            data: endSeriesData,
            color: END_COLOR,
            markerSize: MARKER_SIZE,
          },
        ]}
        xAxis={[
          {
            id: "xAxis",
            min: xMin,
            max: xMax,
            height: 60,
            label: X_AXIS_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "yAxis",
            min: -0.5,
            max: n - 0.5,
            width: 124,
            tickInterval: categories.map((_, i) => i),
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v: number) => categories[Math.round(v)] ?? "",
            tickLabelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        margin={{ left: 24, right: 64, top: 18, bottom: 20 }}
      >
        <ChartsGrid vertical />
        <DumbbellOverlay />
        <ScatterPlot />
        <ChartsXAxis axisId="xAxis" />
        <ChartsYAxis axisId="yAxis" />
      </ChartsContainer>
    </div>
  );
}
