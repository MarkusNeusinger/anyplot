// anyplot.ai
// point-basic: Point Estimate Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "point-basic · javascript · muix · anyplot.ai";
const NULL_VALUE = 0;
const NULL_LABEL = "No effect";
const X_PAD_SHARE = 0.1;
const TITLE_HEIGHT = 68;
const CAP_BAND_SHARE = 0.22;
const MARKER_RADIUS = 10;

// Columns: set these to your data's column names
const SITE = "Pilot Site"; // role: category
const ESTIMATE = "Effect Size (Cohen's d)"; // role: value
const LOWER = "Lower 95% CI"; // role: low
const UPPER = "Upper 95% CI"; // role: high

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [SITE]: "Denver", [ESTIMATE]: 0.55, [LOWER]: 0.3, [UPPER]: 0.8 },
  { [SITE]: "Portland", [ESTIMATE]: 0.45, [LOWER]: 0.22, [UPPER]: 0.68 },
  { [SITE]: "Boston", [ESTIMATE]: 0.42, [LOWER]: 0.18, [UPPER]: 0.66 },
  { [SITE]: "Austin", [ESTIMATE]: 0.38, [LOWER]: 0.15, [UPPER]: 0.61 },
  { [SITE]: "Chicago", [ESTIMATE]: 0.31, [LOWER]: 0.05, [UPPER]: 0.57 },
  { [SITE]: "Seattle", [ESTIMATE]: 0.28, [LOWER]: 0.02, [UPPER]: 0.54 },
  { [SITE]: "Atlanta", [ESTIMATE]: 0.12, [LOWER]: -0.1, [UPPER]: 0.34 },
  { [SITE]: "Miami", [ESTIMATE]: -0.05, [LOWER]: -0.28, [UPPER]: 0.18 },
];

// Plot: reads only data and the constants above
const sortedSites = [...data].sort((a, b) => Number(b[ESTIMATE]) - Number(a[ESTIMATE]));
const siteNames = sortedSites.map((row) => String(row[SITE]));
const allBounds = sortedSites.flatMap((row) => [
  Number(row[LOWER]),
  Number(row[UPPER]),
  NULL_VALUE,
]);
const rawMin = Math.min(...allBounds);
const rawMax = Math.max(...allBounds);
const span = rawMax - rawMin;
const xMin = rawMin - span * X_PAD_SHARE;
const xMax = rawMax + span * X_PAD_SHARE;

function PointEstimates() {
  const xScale = useXScale("effect-size") as unknown as (v: number) => number;
  const yScale = useYScale("site") as unknown as ((s: string) => number) & {
    bandwidth: () => number;
  };
  const bandwidth = yScale.bandwidth();
  const capHalf = bandwidth * CAP_BAND_SHARE;

  return (
    <g>
      {sortedSites.map((row) => {
        const siteLabel = String(row[SITE]);
        const y = yScale(siteLabel) + bandwidth / 2;
        const xLow = xScale(Number(row[LOWER]));
        const xHigh = xScale(Number(row[UPPER]));
        const xEst = xScale(Number(row[ESTIMATE]));
        return (
          <g key={siteLabel}>
            <line
              x1={xLow}
              x2={xHigh}
              y1={y}
              y2={y}
              stroke={t.palette[0]}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={xLow}
              x2={xLow}
              y1={y - capHalf}
              y2={y + capHalf}
              stroke={t.palette[0]}
              strokeWidth={3}
            />
            <line
              x1={xHigh}
              x2={xHigh}
              y1={y - capHalf}
              y2={y + capHalf}
              stroke={t.palette[0]}
              strokeWidth={3}
            />
            <circle
              cx={xEst}
              cy={y}
              r={MARKER_RADIUS}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={2.5}
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        backgroundColor: t.pageBg,
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
          fontFamily: "inherit",
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, bottom: 16, left: 28, right: 40 }}
        xAxis={[
          {
            id: "effect-size",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 56,
            label: ESTIMATE,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "site",
            scaleType: "band",
            data: siteNames,
            width: 130,
            label: SITE,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.ink },
          },
        ]}
      >
        <ChartsGrid vertical />
        <ChartsReferenceLine
          x={NULL_VALUE}
          label={NULL_LABEL}
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
        />
        <PointEstimates />
        <ChartsXAxis axisId="effect-size" />
        <ChartsYAxis axisId="site" disableTicks />
      </ChartsContainer>
    </div>
  );
}
