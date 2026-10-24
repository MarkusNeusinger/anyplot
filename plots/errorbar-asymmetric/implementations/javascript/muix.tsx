// anyplot.ai
// errorbar-asymmetric: Asymmetric Error Bars Plot
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";

// Constants
const X_COL = "Nitrogen Dose (kg/ha)";
const Y_COL = "Yield Increase (%)";
const ERROR_LOWER = "errorLower";
const ERROR_UPPER = "errorUpper";

const CENTRAL_LABEL = "Median yield increase";
const BOUNDS_LABEL = "10th–90th percentile range (asymmetric bounds)";
const PLATEAU_ANNOTATION = "Diminishing returns, widening spread";
const PLATEAU_SPREAD_SHARE = 0.85;
const Y_PAD_TOP_SHARE = 0.12;
const Y_PAD_BOTTOM_SHARE = 0.04;
const CAP_BAND_SHARE = 0.28;
const MARKER_RADIUS = 10;

// Data: crop yield increase (%) by nitrogen fertilizer dose (kg/ha)
const data = [
  { [X_COL]: "0", [Y_COL]: 1, [ERROR_LOWER]: 1, [ERROR_UPPER]: 2 },
  { [X_COL]: "40", [Y_COL]: 8, [ERROR_LOWER]: 3, [ERROR_UPPER]: 5 },
  { [X_COL]: "80", [Y_COL]: 19, [ERROR_LOWER]: 4, [ERROR_UPPER]: 8 },
  { [X_COL]: "120", [Y_COL]: 29, [ERROR_LOWER]: 6, [ERROR_UPPER]: 11 },
  { [X_COL]: "160", [Y_COL]: 35, [ERROR_LOWER]: 7, [ERROR_UPPER]: 13 },
  { [X_COL]: "200", [Y_COL]: 38, [ERROR_LOWER]: 8, [ERROR_UPPER]: 11 },
  { [X_COL]: "240", [Y_COL]: 36, [ERROR_LOWER]: 10, [ERROR_UPPER]: 9 },
];

// Derived series arrays and axis bounds from data extent
const categories = data.map((r) => r[X_COL]);
const centralValues = data.map((r) => r[Y_COL]);
const lowerErrors = data.map((r) => r[ERROR_LOWER]);
const upperErrors = data.map((r) => r[ERROR_UPPER]);
const totalSpreads = data.map((r) => r[ERROR_LOWER] + r[ERROR_UPPER]);

const lowerBounds = data.map((r) => r[Y_COL] - r[ERROR_LOWER]);
const upperBounds = data.map((r) => r[Y_COL] + r[ERROR_UPPER]);

const rawYMin = Math.min(...lowerBounds);
const rawYMax = Math.max(...upperBounds);
const ySpan = rawYMax - rawYMin || 1;
const yMin = Math.min(0, rawYMin - ySpan * Y_PAD_BOTTOM_SHARE);
const yMax = rawYMax + ySpan * Y_PAD_TOP_SHARE;

// Rule-based detection of the widening-spread plateau region
const maxSpread = Math.max(...totalSpreads);
const plateauStartIndex = totalSpreads.findIndex((s) => s >= maxSpread * PLATEAU_SPREAD_SHARE);

const POINT_COLOR = t.palette[0];

function ErrorBars() {
  const xScale = useXScale() as unknown as {
    (v: string): number | undefined;
    bandwidth: () => number;
    step: () => number;
  };
  const yScale = useYScale() as unknown as {
    (v: number): number | undefined;
    range: () => [number, number];
  };

  if (!xScale || !yScale || typeof xScale.bandwidth !== "function") return null;

  const capHalfWidth = Math.min(18, xScale.bandwidth() * CAP_BAND_SHARE);
  const halfGap = (xScale.step() - xScale.bandwidth()) / 2;
  const [yRange0, yRange1] = yScale.range();
  const plotTop = Math.min(yRange0, yRange1);
  const plotBottom = Math.max(yRange0, yRange1);

  const showPlateau = plateauStartIndex >= 0 && plateauStartIndex < categories.length;
  const plateauX0 = showPlateau
    ? (xScale(categories[plateauStartIndex]) ?? 0) - halfGap
    : 0;
  const plateauX1 = showPlateau
    ? (xScale(categories[categories.length - 1]) ?? 0) + xScale.bandwidth() + halfGap
    : 0;

  return (
    <g>
      {showPlateau && (
        <g>
          <rect
            x={plateauX0}
            y={plotTop}
            width={plateauX1 - plateauX0}
            height={plotBottom - plotTop}
            fill={t.elevatedBg}
            stroke={t.grid}
            strokeDasharray="4 4"
            opacity={0.75}
          />
          <text
            x={(plateauX0 + plateauX1) / 2}
            y={plotTop + 24}
            textAnchor="middle"
            fontSize={14}
            fontStyle="italic"
            fontFamily={FONT}
            fill={t.inkSoft}
          >
            {PLATEAU_ANNOTATION}
          </text>
        </g>
      )}

      {categories.map((cat, i) => {
        const cx = (xScale(cat) ?? 0) + xScale.bandwidth() / 2;
        const yTop = yScale(centralValues[i] + upperErrors[i]) ?? 0;
        const yBottom = yScale(centralValues[i] - lowerErrors[i]) ?? 0;
        const yMid = yScale(centralValues[i]) ?? 0;

        return (
          <g key={cat}>
            <line
              x1={cx}
              x2={cx}
              y1={yTop}
              y2={yBottom}
              stroke={POINT_COLOR}
              strokeWidth={3}
            />
            <line
              x1={cx - capHalfWidth}
              x2={cx + capHalfWidth}
              y1={yTop}
              y2={yTop}
              stroke={POINT_COLOR}
              strokeWidth={3}
            />
            <line
              x1={cx - capHalfWidth}
              x2={cx + capHalfWidth}
              y1={yBottom}
              y2={yBottom}
              stroke={POINT_COLOR}
              strokeWidth={3}
            />
            <circle
              cx={cx}
              cy={yMid}
              r={MARKER_RADIUS}
              fill={POINT_COLOR}
              stroke={t.pageBg}
              strokeWidth={3}
            />
          </g>
        );
      })}
    </g>
  );
}

const TITLE = "errorbar-asymmetric · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 58;
const SUBTITLE_HEIGHT = 42;
const MARGIN = { top: 20, right: 56, bottom: 72, left: 96 };

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT - SUBTITLE_HEIGHT;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: FONT,
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          pb: "4px",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, fontFamily: FONT }}>
          {TITLE}
        </Typography>
      </Box>
      <Box
        sx={{
          height: SUBTITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "28px",
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box
            sx={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              backgroundColor: POINT_COLOR,
              border: `2px solid ${t.pageBg}`,
              boxShadow: `0 0 0 1px ${POINT_COLOR}`,
            }}
          />
          <Typography sx={{ color: t.ink, fontSize: 15, fontFamily: FONT }}>
            {CENTRAL_LABEL}
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width={22} height={16} viewBox="0 0 22 16">
            <line x1={2} x2={2} y1={3} y2={13} stroke={POINT_COLOR} strokeWidth={2.5} />
            <line x1={20} x2={20} y1={3} y2={13} stroke={POINT_COLOR} strokeWidth={2.5} />
            <line x1={2} x2={20} y1={8} y2={8} stroke={POINT_COLOR} strokeWidth={2.5} />
          </svg>
          <Typography sx={{ color: t.inkSoft, fontSize: 15, fontFamily: FONT }}>
            {BOUNDS_LABEL}
          </Typography>
        </Box>
      </Box>

      <ChartsContainer
        skipAnimation
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={[]}
        xAxis={[
          {
            scaleType: "band",
            data: categories,
            height: 60,
            label: X_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            tickSize: 0,
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 84,
            label: Y_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            tickSize: 0,
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeOpacity: 0.5 },
        }}
      >
        <ChartsGrid horizontal />
        <ErrorBars />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
