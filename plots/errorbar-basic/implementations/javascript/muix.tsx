// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 88/100 | Created: 2026-06-30

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const TITLE = "errorbar-basic · javascript · muix · anyplot.ai";
const Y_PAD_SHARE = 0.14;
const CAP_BAND_SHARE = 0.22;
const MARKER_RADIUS = 10;
const SERIES_COLOR = t.palette[0];

// Columns: set these to your data's column names
const CONDITION = "Growth condition"; // role: x
const ELONGATION = "Mean stem elongation (cm / week)"; // role: y
const ERROR = "Standard deviation (cm / week)"; // role: error

// Data: replace this block with your own records
const data = [
  { [CONDITION]: "Control", [ELONGATION]: 4.2, [ERROR]: 0.5 },
  { [CONDITION]: "Low Temp", [ELONGATION]: 2.8, [ERROR]: 0.7 },
  { [CONDITION]: "High Temp", [ELONGATION]: 3.1, [ERROR]: 0.6 },
  { [CONDITION]: "Low pH", [ELONGATION]: 2.4, [ERROR]: 0.8 },
  { [CONDITION]: "High pH", [ELONGATION]: 3.6, [ERROR]: 0.5 },
  { [CONDITION]: "Drought", [ELONGATION]: 1.9, [ERROR]: 0.6 },
  { [CONDITION]: "Flood", [ELONGATION]: 2.2, [ERROR]: 0.9 },
];

// Plot: reads only data and the constants above
const categories = data.map((r) => String(r[CONDITION]));
const means = data.map((r) => Number(r[ELONGATION]));
const errors = data.map((r) => Number(r[ERROR]));

const lowerBounds = data.map((r) => Number(r[ELONGATION]) - Number(r[ERROR]));
const upperBounds = data.map((r) => Number(r[ELONGATION]) + Number(r[ERROR]));
const rawMin = Math.min(...lowerBounds);
const rawMax = Math.max(...upperBounds);
const span = rawMax - rawMin;
const yMin = rawMin - span * Y_PAD_SHARE;
const yMax = rawMax + span * Y_PAD_SHARE;
const SUBTITLE = `Error bars: ± ${ERROR} · ${categories.length} ${CONDITION}s`;

function ErrorBars() {
  const xScale = useXScale("x") as any;
  const yScale = useYScale("y") as any;

  const bw = xScale.bandwidth();
  const cap = Math.min(20, Math.round(bw * CAP_BAND_SHARE));

  return (
    <g>
      {categories.map((cond, i) => {
        const cx = xScale(cond) + bw / 2;
        const yTop = yScale(means[i] + errors[i]);
        const yBot = yScale(means[i] - errors[i]);
        const yMid = yScale(means[i]);
        return (
          <g key={cond}>
            <line
              x1={cx}
              y1={yTop}
              x2={cx}
              y2={yBot}
              stroke={SERIES_COLOR}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={cx - cap}
              y1={yTop}
              x2={cx + cap}
              y2={yTop}
              stroke={SERIES_COLOR}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={cx - cap}
              y1={yBot}
              x2={cx + cap}
              y2={yBot}
              stroke={SERIES_COLOR}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <circle
              cx={cx}
              cy={yMid}
              r={MARKER_RADIUS}
              fill={SERIES_COLOR}
              stroke={t.pageBg}
              strokeWidth={3}
            />
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
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: categories,
            height: 60,
            label: CONDITION,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 88,
            label: ELONGATION,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 20, bottom: 20, left: 24, right: 48 }}
      >
        <ChartsGrid horizontal />
        <ErrorBars />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
