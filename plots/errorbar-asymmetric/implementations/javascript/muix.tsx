// anyplot.ai
// errorbar-asymmetric: Asymmetric Error Bars Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
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

// Constants
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";
const TITLE = "errorbar-asymmetric · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 58;
const SUBTITLE_HEIGHT = 42;
const MARGIN = { top: 20, right: 48, bottom: 20, left: 24 };
const PLATEAU_SPREAD_SHARE = 0.85;
const Y_PAD_TOP_SHARE = 0.12;
const Y_PAD_BOTTOM_SHARE = 0.04;
const CAP_BAND_SHARE = 0.28;
const MARKER_RADIUS = 10;
const POINT_COLOR = t.palette[0];

// Columns: set these to your data's column names
const DOSE = "Nitrogen dose (kg/ha)"; // role: x
const YIELD_GAIN = "Median yield increase (%)"; // role: y
const LOWER_ERROR = "10th percentile gap (%)"; // role: error_lower
const UPPER_ERROR = "90th percentile gap (%)"; // role: error_upper

// Data: replace this block with your own records
const data = [
  { [DOSE]: "0", [YIELD_GAIN]: 1, [LOWER_ERROR]: 1, [UPPER_ERROR]: 2 },
  { [DOSE]: "40", [YIELD_GAIN]: 8, [LOWER_ERROR]: 3, [UPPER_ERROR]: 5 },
  { [DOSE]: "80", [YIELD_GAIN]: 19, [LOWER_ERROR]: 4, [UPPER_ERROR]: 8 },
  { [DOSE]: "120", [YIELD_GAIN]: 29, [LOWER_ERROR]: 6, [UPPER_ERROR]: 11 },
  { [DOSE]: "160", [YIELD_GAIN]: 35, [LOWER_ERROR]: 7, [UPPER_ERROR]: 13 },
  { [DOSE]: "200", [YIELD_GAIN]: 38, [LOWER_ERROR]: 8, [UPPER_ERROR]: 11 },
  { [DOSE]: "240", [YIELD_GAIN]: 36, [LOWER_ERROR]: 10, [UPPER_ERROR]: 9 },
];

// Plot: reads only data and the constants above
const categories = data.map((r) => String(r[DOSE]));
const centralValues = data.map((r) => Number(r[YIELD_GAIN]));
const lowerErrors = data.map((r) => Number(r[LOWER_ERROR]));
const upperErrors = data.map((r) => Number(r[UPPER_ERROR]));
const totalSpreads = data.map((r) => Number(r[LOWER_ERROR]) + Number(r[UPPER_ERROR]));

const lowerBounds = data.map((r) => Number(r[YIELD_GAIN]) - Number(r[LOWER_ERROR]));
const upperBounds = data.map((r) => Number(r[YIELD_GAIN]) + Number(r[UPPER_ERROR]));

const rawYMin = Math.min(...lowerBounds);
const rawYMax = Math.max(...upperBounds);
const ySpan = rawYMax - rawYMin;
const yMin = Math.min(0, rawYMin - ySpan * Y_PAD_BOTTOM_SHARE);
const yMax = rawYMax + ySpan * Y_PAD_TOP_SHARE;

const maxSpread = Math.max(...totalSpreads);
const plateauStartIndex = totalSpreads.findIndex((s) => s >= maxSpread * PLATEAU_SPREAD_SHARE);
let plateauEndIndex = plateauStartIndex;
for (let i = totalSpreads.length - 1; i >= 0; i--) {
  if (totalSpreads[i] >= maxSpread * PLATEAU_SPREAD_SHARE) {
    plateauEndIndex = i;
    break;
  }
}
const PLATEAU_ANNOTATION = `Spread ≥ ${Math.round(PLATEAU_SPREAD_SHARE * 100)}% of maximum`;
const BOUNDS_LABEL = `Asymmetric bounds (−${LOWER_ERROR}, +${UPPER_ERROR})`;

function ErrorBars() {
  const xScale = useXScale() as any;
  const yScale = useYScale() as any;

  const capHalfWidth = Math.min(18, xScale.bandwidth() * CAP_BAND_SHARE);
  const halfGap = (xScale.step() - xScale.bandwidth()) / 2;
  const [yRange0, yRange1] = yScale.range();
  const plotTop = Math.min(yRange0, yRange1);
  const plotBottom = Math.max(yRange0, yRange1);

  const showPlateau = plateauStartIndex >= 0 && plateauEndIndex >= plateauStartIndex;
  const plateauX0 = showPlateau ? xScale(categories[plateauStartIndex]) - halfGap : 0;
  const plateauX1 = showPlateau
    ? xScale(categories[plateauEndIndex]) + xScale.bandwidth() + halfGap
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
        const cx = xScale(cat) + xScale.bandwidth() / 2;
        const yTop = yScale(centralValues[i] + upperErrors[i]);
        const yBottom = yScale(centralValues[i] - lowerErrors[i]);
        const yMid = yScale(centralValues[i]);

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
            {YIELD_GAIN}
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
            label: DOSE,
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
            label: YIELD_GAIN,
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
