// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: muix 9.0.0 | JavaScript 22.23.0
// Quality: pending | Created: 2026-06-30

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";
const TITLE = "dumbbell-basic · javascript · muix · anyplot.ai";

// Constants
const CATEGORY = "Department";
const START_VALUE = "Before Program";
const END_VALUE = "After Program";
const X_AXIS_LABEL = "Employee Satisfaction Score (0–10 scale)";
const X_PAD_LEFT_SHARE = 0.14;
const X_PAD_RIGHT_SHARE = 0.2;
const MARKER_SIZE = 10;

// Data: employee satisfaction scores before and after a wellness program
const rawData = [
  { [CATEGORY]: "Finance", [START_VALUE]: 5.4, [END_VALUE]: 5.9 },
  { [CATEGORY]: "Legal", [START_VALUE]: 5.7, [END_VALUE]: 5.5 },
  { [CATEGORY]: "Marketing", [START_VALUE]: 6.0, [END_VALUE]: 7.6 },
  { [CATEGORY]: "Sales", [START_VALUE]: 6.2, [END_VALUE]: 6.7 },
  { [CATEGORY]: "Operations", [START_VALUE]: 6.5, [END_VALUE]: 9.0 },
  { [CATEGORY]: "Engineering", [START_VALUE]: 6.8, [END_VALUE]: 7.7 },
  { [CATEGORY]: "HR", [START_VALUE]: 7.1, [END_VALUE]: 8.4 },
  { [CATEGORY]: "Design", [START_VALUE]: 7.4, [END_VALUE]: 8.0 },
];

// Sort ascending by start value
const data = [...rawData].sort((a, b) => a[START_VALUE] - b[START_VALUE]);

const categories = data.map((d) => d[CATEGORY]);
const startValues = data.map((d) => d[START_VALUE]);
const endValues = data.map((d) => d[END_VALUE]);
const diffs = data.map((d) => +(d[END_VALUE] - d[START_VALUE]).toFixed(1));
const n = data.length;

const allValues = [...startValues, ...endValues];
const valMin = Math.min(...allValues);
const valMax = Math.max(...allValues);
const valSpan = valMax - valMin || 1;
const xMin = valMin - valSpan * X_PAD_LEFT_SHARE;
const xMax = valMax + valSpan * X_PAD_RIGHT_SHARE;

const startSeriesData = startValues.map((x, i) => ({ id: i, x, y: i }));
const endSeriesData = endValues.map((x, i) => ({ id: i + n, x, y: i }));

const START_COLOR = t.palette[0];
const END_COLOR = t.palette[1];

function DumbbellOverlay() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  return (
    <g>
      {data.map((d, i) => {
        const x1 = xScale(d[START_VALUE]) ?? 0;
        const x2 = xScale(d[END_VALUE]) ?? 0;
        const y = yScale(i) ?? 0;
        const rightX = Math.max(x1, x2);
        const diff = diffs[i];
        const diffLabel = diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1);

        return (
          <g key={d[CATEGORY]}>
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
            tickMinStep: 1,
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v: number) => categories[Math.round(v)] ?? "",
            tickLabelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        margin={{ left: 136, right: 64, top: 18, bottom: 72 }}
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
