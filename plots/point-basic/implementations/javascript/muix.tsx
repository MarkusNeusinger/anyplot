// anyplot.ai
// point-basic: Point Estimate Plot
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "point-basic · javascript · muix · anyplot.ai";

// Constants
const SITE_COL = "Pilot Site";
const ESTIMATE_COL = "Effect Size (Cohen's d)";
const LOWER_COL = "Lower 95% CI";
const UPPER_COL = "Upper 95% CI";

const NULL_VALUE = 0;
const NULL_LABEL = "No effect";
const X_PAD_SHARE = 0.1;
const TITLE_HEIGHT = 68;
const CAP_BAND_SHARE = 0.22;
const MARKER_RADIUS = 10;

// Data: effect of an after-school tutoring program on standardized test scores
const DATA = [
  { [SITE_COL]: "Denver", [ESTIMATE_COL]: 0.55, [LOWER_COL]: 0.3, [UPPER_COL]: 0.8 },
  { [SITE_COL]: "Portland", [ESTIMATE_COL]: 0.45, [LOWER_COL]: 0.22, [UPPER_COL]: 0.68 },
  { [SITE_COL]: "Boston", [ESTIMATE_COL]: 0.42, [LOWER_COL]: 0.18, [UPPER_COL]: 0.66 },
  { [SITE_COL]: "Austin", [ESTIMATE_COL]: 0.38, [LOWER_COL]: 0.15, [UPPER_COL]: 0.61 },
  { [SITE_COL]: "Chicago", [ESTIMATE_COL]: 0.31, [LOWER_COL]: 0.05, [UPPER_COL]: 0.57 },
  { [SITE_COL]: "Seattle", [ESTIMATE_COL]: 0.28, [LOWER_COL]: 0.02, [UPPER_COL]: 0.54 },
  { [SITE_COL]: "Atlanta", [ESTIMATE_COL]: 0.12, [LOWER_COL]: -0.1, [UPPER_COL]: 0.34 },
  { [SITE_COL]: "Miami", [ESTIMATE_COL]: -0.05, [LOWER_COL]: -0.28, [UPPER_COL]: 0.18 },
];

// Sort descending by point estimate so visual hierarchy reads top-to-bottom
const sortedSites = [...DATA].sort((a, b) => Number(b[ESTIMATE_COL]) - Number(a[ESTIMATE_COL]));
const siteNames = sortedSites.map((row) => String(row[SITE_COL]));
const allBounds = sortedSites.flatMap((row) => [Number(row[LOWER_COL]), Number(row[UPPER_COL]), NULL_VALUE]);
const rawMin = Math.min(...allBounds);
const rawMax = Math.max(...allBounds);
const span = rawMax - rawMin || 1;
const xMin = rawMin - span * X_PAD_SHARE;
const xMax = rawMax + span * X_PAD_SHARE;

function PointEstimates() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;
  const bandwidth = typeof yScale.bandwidth === "function" ? yScale.bandwidth() : 0;
  const capHalf = bandwidth * CAP_BAND_SHARE;

  return (
    <g>
      {sortedSites.map((row) => {
        const siteLabel = String(row[SITE_COL]);
        const y = (yScale(siteLabel) ?? 0) + bandwidth / 2;
        const xLow = xScale(Number(row[LOWER_COL]));
        const xHigh = xScale(Number(row[UPPER_COL]));
        const xEst = xScale(Number(row[ESTIMATE_COL]));
        return (
          <g key={siteLabel}>
            <line x1={xLow} x2={xHigh} y1={y} y2={y} stroke={t.palette[0]} strokeWidth={3} strokeLinecap="round" />
            <line x1={xLow} x2={xLow} y1={y - capHalf} y2={y + capHalf} stroke={t.palette[0]} strokeWidth={3} />
            <line x1={xHigh} x2={xHigh} y1={y - capHalf} y2={y + capHalf} stroke={t.palette[0]} strokeWidth={3} />
            <circle cx={xEst} cy={y} r={MARKER_RADIUS} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={2.5} />
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
            label: ESTIMATE_COL,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "site",
            scaleType: "band",
            data: siteNames,
            width: 100,
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
