// anyplot.ai
// lollipop-grouped: Grouped Lollipop Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GROUP_PAD_FRAC = 0.18;
const Y_PAD_FRAC = 0.25;

// Columns: set these to your data's column names
const CATEGORY = "Region"; // role: category
const SERIES = "Product line"; // role: series
const VALUE = "Revenue ($M)"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [CATEGORY]: "North America", [SERIES]: "Hardware", [VALUE]: 48 },
  { [CATEGORY]: "North America", [SERIES]: "Software", [VALUE]: 71 },
  { [CATEGORY]: "North America", [SERIES]: "Services", [VALUE]: 39 },
  { [CATEGORY]: "Asia-Pacific", [SERIES]: "Hardware", [VALUE]: 52 },
  { [CATEGORY]: "Asia-Pacific", [SERIES]: "Software", [VALUE]: 45 },
  { [CATEGORY]: "Asia-Pacific", [SERIES]: "Services", [VALUE]: 33 },
  { [CATEGORY]: "Europe", [SERIES]: "Hardware", [VALUE]: 33 },
  { [CATEGORY]: "Europe", [SERIES]: "Software", [VALUE]: 58 },
  { [CATEGORY]: "Europe", [SERIES]: "Services", [VALUE]: 30 },
  { [CATEGORY]: "Latin America", [SERIES]: "Hardware", [VALUE]: 21 },
  { [CATEGORY]: "Latin America", [SERIES]: "Software", [VALUE]: 24 },
  { [CATEGORY]: "Latin America", [SERIES]: "Services", [VALUE]: 17 },
];

// Plot: reads only data and the constants above
const rawRegions: string[] = [];
const productLines: string[] = [];
for (const row of data) {
  const reg = String(row[CATEGORY]);
  const prod = String(row[SERIES]);
  if (!rawRegions.includes(reg)) rawRegions.push(reg);
  if (!productLines.includes(prod)) productLines.push(prod);
}

const regionTotals: Record<string, number> = {};
for (const reg of rawRegions) {
  regionTotals[reg] = data
    .filter((r) => String(r[CATEGORY]) === reg)
    .reduce((sum, r) => sum + Number(r[VALUE]), 0);
}
const regions = [...rawRegions].sort((a, b) => regionTotals[b] - regionTotals[a]);

const seriesColors = productLines.map((_, i) => t.palette[i]);
const maxRevenue = Math.max(...data.map((r) => Number(r[VALUE])));
const yAxisMax = maxRevenue * (1 + Y_PAD_FRAC);
const unitMatch = VALUE.match(/\(([^)]+)\)/);
const VALUE_UNIT = unitMatch ? unitMatch[1] : "";
const UNIT_PREFIX = VALUE_UNIT.startsWith("$") ? "$" : "";
const UNIT_SUFFIX = VALUE_UNIT.startsWith("$")
  ? VALUE_UNIT.slice(1)
  : VALUE_UNIT;

function GroupedLollipopsLayer() {
  const xScale = useXScale("region-axis") as unknown as ((v: string) => number) & {
    bandwidth: () => number;
  };
  const yScale = useYScale("revenue-axis") as (v: number) => number;

  const bandwidth = xScale.bandwidth();
  const groupPadding = bandwidth * GROUP_PAD_FRAC;
  const slotWidth = (bandwidth - 2 * groupPadding) / productLines.length;
  const baselineY = yScale(0);

  return (
    <g>
      {regions.map((region) =>
        productLines.map((prod, si) => {
          const row = data.find(
            (r) => String(r[CATEGORY]) === region && String(r[SERIES]) === prod,
          );
          if (!row) return null;
          const value = Number(row[VALUE]);
          const cx = xScale(region) + groupPadding + slotWidth * (si + 0.5);
          const cy = yScale(value);
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
            label: VALUE,
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
