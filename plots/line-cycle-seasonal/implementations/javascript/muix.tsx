// anyplot.ai
// line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-15

import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// --- Data: monthly online retail sales ($ billion), 2014–2023 ---
// Cycle plot layout: 12 month groups, each with 10 chronological year observations.
// Two null-position gaps between groups create visual separation.

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const N_YEARS = 10;   // 2014–2023
const GAP = 2;        // null-gap bands between month groups
const GROUP_W = N_YEARS + GAP;  // 12 positions per month group

// Seasonal multipliers (low in winter, peak in holiday season)
const SEASONAL = [0.72, 0.75, 0.88, 0.85, 0.87, 0.82, 0.84, 0.87, 0.90, 0.95, 1.10, 1.45];

// Center index within each group — used for tick label positions (year 2018 = index 4)
const CENTER_IDX = 4;

// Build flat arrays: 12 months × 12 positions = 144 slots
const xCategories: string[] = [];
const tickPositions: string[] = [];  // 12 category strings that get tick labels
const salesValues: (number | null)[] = [];
const meanValues: (number | null)[] = [];

MONTHS.forEach((month, m) => {
  const yearVals: number[] = [];

  for (let yi = 0; yi < N_YEARS; yi++) {
    const trend = 3.5 * Math.pow(1.08, yi);  // ~8 % annual growth baseline
    const noise = (((m * 7 + yi * 13) % 17) - 8) * 0.04;  // deterministic ±0.32 B
    const val = trend * SEASONAL[m] + noise;
    yearVals.push(val);

    const cat = `${month}_${2014 + yi}`;
    xCategories.push(cat);
    salesValues.push(val);

    if (yi === CENTER_IDX) tickPositions.push(cat);  // e.g. "Jan_2018"
  }

  // Gap positions — null values break the line between month groups
  for (let g = 0; g < GAP; g++) {
    xCategories.push(`__gap_${m}_${g}`);
    salesValues.push(null);
  }

  // Mean series: constant value across all year positions within this group
  const mean = yearVals.reduce((s, v) => s + v, 0) / N_YEARS;
  for (let yi = 0; yi < N_YEARS; yi++) {
    meanValues.push(mean);
  }
  for (let g = 0; g < GAP; g++) {
    meanValues.push(null);
  }
});

// Chart title (53 chars — under 67 baseline, no scaling needed)
const TITLE =
  "Monthly Retail Sales · line-cycle-seasonal · javascript · muix · anyplot.ai";

// --- Chart ---
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleH = 52;  // CSS px reserved above the LineChart for the title row

  return (
    <div
      style={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Title — rendered in wrapper div since MUI X community has no built-in title */}
      <div
        style={{
          height: titleH,
          padding: "14px 60px 0",
          fontSize: 19,
          fontWeight: 600,
          color: t.ink,
          letterSpacing: "0.01em",
          flexShrink: 0,
        }}
      >
        {TITLE}
      </div>

      <LineChart
        width={width}
        height={height - titleH}
        skipAnimation
        colors={[t.palette[0], t.palette[2]]}
        xAxis={[{
          scaleType: "band",
          data: xCategories,
          // Show tick labels only at the center of each month group ("Jan_2018" etc.)
          tickInterval: tickPositions,
          // Extract the month name from "Jan_2018"; return "" for gap entries
          valueFormatter: (val: string) => val.split("_")[0],
          tickLabelStyle: { fontSize: 14 },
        }]}
        yAxis={[{
          label: "Online Retail Sales ($ billion)",
          labelStyle: { fontSize: 14 },
          tickLabelStyle: { fontSize: 13 },
        }]}
        series={[
          {
            data: salesValues,
            label: "Monthly Sales",
            showMark: false,
            connectNulls: false,
          },
          {
            data: meanValues,
            label: "Seasonal Mean",
            showMark: false,
            connectNulls: false,
          },
        ]}
        margin={{ top: 16, right: 40, bottom: 72, left: 84 }}
      />
    </div>
  );
}
