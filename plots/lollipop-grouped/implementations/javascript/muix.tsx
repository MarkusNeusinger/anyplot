// anyplot.ai
// lollipop-grouped: Grouped Lollipop Chart
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const CATEGORY_COL = "Region" as const;
const SERIES_COL = "Product Line" as const;
const VALUE_COL = "Revenue ($M)" as const;

const GROUP_PAD_FRAC = 0.18;
const Y_PAD_FRAC = 0.25;

// Data — quarterly revenue ($M) by product line across regions
const DATA: Array<Record<string, string | number>> = [
  { [CATEGORY_COL]: "North America", [SERIES_COL]: "Hardware", [VALUE_COL]: 48 },
  { [CATEGORY_COL]: "North America", [SERIES_COL]: "Software", [VALUE_COL]: 71 },
  { [CATEGORY_COL]: "North America", [SERIES_COL]: "Services", [VALUE_COL]: 39 },
  { [CATEGORY_COL]: "Asia-Pacific", [SERIES_COL]: "Hardware", [VALUE_COL]: 52 },
  { [CATEGORY_COL]: "Asia-Pacific", [SERIES_COL]: "Software", [VALUE_COL]: 45 },
  { [CATEGORY_COL]: "Asia-Pacific", [SERIES_COL]: "Services", [VALUE_COL]: 33 },
  { [CATEGORY_COL]: "Europe", [SERIES_COL]: "Hardware", [VALUE_COL]: 33 },
  { [CATEGORY_COL]: "Europe", [SERIES_COL]: "Software", [VALUE_COL]: 58 },
  { [CATEGORY_COL]: "Europe", [SERIES_COL]: "Services", [VALUE_COL]: 30 },
  { [CATEGORY_COL]: "Latin America", [SERIES_COL]: "Hardware", [VALUE_COL]: 21 },
  { [CATEGORY_COL]: "Latin America", [SERIES_COL]: "Software", [VALUE_COL]: 24 },
  { [CATEGORY_COL]: "Latin America", [SERIES_COL]: "Services", [VALUE_COL]: 17 },
];

// Discover categories and series in order of first appearance, then sort categories by total revenue descending
const rawRegions: string[] = [];
const productLines: string[] = [];
for (const row of DATA) {
  const reg = String(row[CATEGORY_COL]);
  const prod = String(row[SERIES_COL]);
  if (!rawRegions.includes(reg)) rawRegions.push(reg);
  if (!productLines.includes(prod)) productLines.push(prod);
}

const regionTotals: Record<string, number> = {};
for (const reg of rawRegions) {
  regionTotals[reg] = DATA.filter((r) => String(r[CATEGORY_COL]) === reg).reduce(
    (sum, r) => sum + Number(r[VALUE_COL]),
    0,
  );
}
const regions = [...rawRegions].sort((a, b) => regionTotals[b] - regionTotals[a]);
const focalRegion = regions[0];

const seriesColors = productLines.map((_, i) => t.palette[i]);
const maxRevenue = Math.max(...DATA.map((r) => Number(r[VALUE_COL])));
const yAxisMax = maxRevenue * (1 + Y_PAD_FRAC);
const VALUE_UNIT = VALUE_COL.match(/\(([^)]+)\)/)?.[1] ?? "$M";
const UNIT_PREFIX = VALUE_UNIT.startsWith("$") ? "$" : "";
const UNIT_SUFFIX = VALUE_UNIT.startsWith("$") ? VALUE_UNIT.slice(1) : VALUE_UNIT;

function GroupedLollipopsLayer() {
  const xScale = useXScale("region-axis") as {
    (v: string): number | undefined;
    bandwidth?: () => number;
  };
  const yScale = useYScale("revenue-axis") as (v: number) => number | undefined;
  const { top, height } = useDrawingArea();

  if (!xScale || !yScale || typeof xScale.bandwidth !== "function") return null;

  const bandwidth = xScale.bandwidth();
  const groupPadding = bandwidth * GROUP_PAD_FRAC;
  const slotWidth = (bandwidth - 2 * groupPadding) / productLines.length;
  const baselineY = Number(yScale(0) ?? top + height);
  const focalX = Number(xScale(focalRegion) ?? 0);

  return (
    <g>
      {/* Subtle non-data chrome highlight behind the top-revenue region */}
      <rect
        x={focalX}
        y={top}
        width={bandwidth}
        height={height}
        fill={t.elevatedBg}
        fillOpacity={0.55}
        stroke={t.grid}
        strokeWidth={1}
        rx={10}
      />

      {regions.map((region) =>
        productLines.map((prod, si) => {
          const row = DATA.find(
            (r) => String(r[CATEGORY_COL]) === region && String(r[SERIES_COL]) === prod,
          );
          if (!row) return null;
          const value = Number(row[VALUE_COL]);
          const cx = Number(xScale(region) ?? 0) + groupPadding + slotWidth * (si + 0.5);
          const cy = Number(yScale(value) ?? baselineY);
          return (
            <g key={`${region}-${prod}`}>
              <line
                x1={cx}
                y1={baselineY}
                x2={cx}
                y2={cy}
                stroke={seriesColors[si]}
                strokeWidth={4}
                strokeLinecap="round"
              />
              <circle
                cx={cx}
                cy={cy}
                r={12}
                fill={seriesColors[si]}
                stroke={t.pageBg}
                strokeWidth={2.5}
              />
              <text
                x={cx}
                y={cy - 19}
                textAnchor="middle"
                fontSize={14}
                fontWeight={500}
                fill={t.ink}
              >
                {`${UNIT_PREFIX}${value}${UNIT_SUFFIX}`}
              </text>
            </g>
          );
        }),
      )}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;
  const legendHeight = 36;
  const chartHeight = height - titleHeight - legendHeight;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        lollipop-grouped · javascript · muix · anyplot.ai
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 28,
          height: legendHeight,
          alignItems: "center",
        }}
      >
        {productLines.map((name, i) => (
          <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: seriesColors[i],
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 15, color: t.inkSoft }}>{name}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, bottom: 16, left: 20, right: 24 }}
        xAxis={[
          {
            id: "region-axis",
            scaleType: "band",
            data: regions,
            categoryGapRatio: 0.3,
            height: 44,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "revenue-axis",
            scaleType: "linear",
            min: 0,
            max: yAxisMax,
            width: 84,
            label: VALUE_COL,
            valueFormatter: (v: number | null) =>
              v != null ? `${UNIT_PREFIX}${v}${UNIT_SUFFIX}` : "",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <GroupedLollipopsLayer />
        <ChartsXAxis axisId="region-axis" />
        <ChartsYAxis axisId="revenue-axis" />
      </ChartsContainer>
    </div>
  );
}
