// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: muix 9.0.0 | JavaScript 22.23.0
// Quality: pending | Created: 2026-06-30

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const TITLE = "errorbar-basic · javascript · muix · anyplot.ai";

// Constants
const X_COL = "Growth Condition";
const Y_COL = "Mean Stem Elongation (cm / week)";
const ERROR_COL = "errorSd";

const SUBTITLE_SUFFIX = "mean ± 1 SD across growth conditions";
const Y_PAD_SHARE = 0.14;
const CAP_BAND_SHARE = 0.22;
const MARKER_RADIUS = 10;

// Data: plant stress experiment — mean stem elongation (cm/week) ± 1 SD across 7 growth conditions
const data = [
  { [X_COL]: "Control", [Y_COL]: 4.2, [ERROR_COL]: 0.5 },
  { [X_COL]: "Low Temp", [Y_COL]: 2.8, [ERROR_COL]: 0.7 },
  { [X_COL]: "High Temp", [Y_COL]: 3.1, [ERROR_COL]: 0.6 },
  { [X_COL]: "Low pH", [Y_COL]: 2.4, [ERROR_COL]: 0.8 },
  { [X_COL]: "High pH", [Y_COL]: 3.6, [ERROR_COL]: 0.5 },
  { [X_COL]: "Drought", [Y_COL]: 1.9, [ERROR_COL]: 0.6 },
  { [X_COL]: "Flood", [Y_COL]: 2.2, [ERROR_COL]: 0.9 },
];

// Derived series arrays and axis bounds from data extent
const categories = data.map((r) => r[X_COL]);
const means = data.map((r) => r[Y_COL]);
const errors = data.map((r) => r[ERROR_COL]);

const lowerBounds = data.map((r) => r[Y_COL] - r[ERROR_COL]);
const upperBounds = data.map((r) => r[Y_COL] + r[ERROR_COL]);
const rawMin = Math.min(...lowerBounds);
const rawMax = Math.max(...upperBounds);
const span = rawMax - rawMin || 1;
const yMin = rawMin - span * Y_PAD_SHARE;
const yMax = rawMax + span * Y_PAD_SHARE;

const SERIES_COLOR = t.palette[0];

function ErrorBars() {
  const xScale = useXScale("x") as unknown as {
    (v: string): number | undefined;
    bandwidth: () => number;
  };
  const yScale = useYScale("y") as unknown as (v: number) => number | undefined;
  if (!xScale || !yScale || typeof xScale.bandwidth !== "function") return null;

  const bw = xScale.bandwidth();
  const cap = Math.min(20, Math.round(bw * CAP_BAND_SHARE));

  return (
    <g>
      {categories.map((cond, i) => {
        const cx = (xScale(cond) ?? 0) + bw / 2;
        const yTop = yScale(means[i] + errors[i]) ?? 0;
        const yBot = yScale(means[i] - errors[i]) ?? 0;
        const yMid = yScale(means[i]) ?? 0;
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
        <div style={{ fontSize: 15, color: t.inkSoft }}>
          {Y_COL} · {SUBTITLE_SUFFIX} (n = {data.length})
        </div>
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
            label: X_COL,
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
            label: Y_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 20, bottom: 72, left: 100, right: 64 }}
      >
        <ChartsGrid horizontal />
        <ErrorBars />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
