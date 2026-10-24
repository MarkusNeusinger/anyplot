// anyplot.ai
// ohlc-bar: OHLC Bar Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "ohlc-bar · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const Y_PAD_SHARE = 0.06;
const TICK_INTERVAL_STEP = 5;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Columns: set these to your data's column names
const DATE = "Trading session"; // role: date
const OPEN = "Open (USD)"; // role: open
const HIGH = "High (USD)"; // role: high
const LOW = "Low (USD)"; // role: low
const CLOSE = "Close (USD)"; // role: close

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [DATE]: "2024-01-02", [OPEN]: 218.26, [HIGH]: 221.39, [LOW]: 216.69, [CLOSE]: 219.51 },
  { [DATE]: "2024-01-03", [OPEN]: 219.59, [HIGH]: 221.25, [LOW]: 216.2, [CLOSE]: 218.08 },
  { [DATE]: "2024-01-04", [OPEN]: 217.56, [HIGH]: 222.07, [LOW]: 216.12, [CLOSE]: 220.43 },
  { [DATE]: "2024-01-05", [OPEN]: 220.99, [HIGH]: 222.39, [LOW]: 217.99, [CLOSE]: 219.72 },
  { [DATE]: "2024-01-08", [OPEN]: 219.35, [HIGH]: 223.95, [LOW]: 218.3, [CLOSE]: 222.58 },
  { [DATE]: "2024-01-09", [OPEN]: 222.25, [HIGH]: 225.73, [LOW]: 220.51, [CLOSE]: 224.09 },
  { [DATE]: "2024-01-10", [OPEN]: 224.51, [HIGH]: 226.47, [LOW]: 220.69, [CLOSE]: 222.36 },
  { [DATE]: "2024-01-11", [OPEN]: 221.96, [HIGH]: 225.56, [LOW]: 220.76, [CLOSE]: 224.22 },
  { [DATE]: "2024-01-12", [OPEN]: 224.58, [HIGH]: 226.15, [LOW]: 220.89, [CLOSE]: 222.71 },
  { [DATE]: "2024-01-15", [OPEN]: 222.42, [HIGH]: 227.51, [LOW]: 221.11, [CLOSE]: 225.78 },
  { [DATE]: "2024-01-16", [OPEN]: 226.14, [HIGH]: 229.88, [LOW]: 224.36, [CLOSE]: 228.11 },
  { [DATE]: "2024-01-17", [OPEN]: 227.79, [HIGH]: 229.47, [LOW]: 223.82, [CLOSE]: 225.63 },
  { [DATE]: "2024-01-18", [OPEN]: 225.95, [HIGH]: 229.74, [LOW]: 224.14, [CLOSE]: 227.85 },
  { [DATE]: "2024-01-19", [OPEN]: 228.19, [HIGH]: 232.42, [LOW]: 226.78, [CLOSE]: 230.89 },
  { [DATE]: "2024-01-22", [OPEN]: 230.52, [HIGH]: 232.28, [LOW]: 227.05, [CLOSE]: 228.94 },
  { [DATE]: "2024-01-23", [OPEN]: 229.28, [HIGH]: 233.61, [LOW]: 227.91, [CLOSE]: 231.98 },
  { [DATE]: "2024-01-24", [OPEN]: 231.69, [HIGH]: 234.12, [LOW]: 228.44, [CLOSE]: 230.15 },
  { [DATE]: "2024-01-25", [OPEN]: 230.49, [HIGH]: 235.18, [LOW]: 229.12, [CLOSE]: 233.54 },
  { [DATE]: "2024-01-26", [OPEN]: 233.86, [HIGH]: 236.24, [LOW]: 230.65, [CLOSE]: 232.41 },
  { [DATE]: "2024-01-29", [OPEN]: 232.11, [HIGH]: 236.89, [LOW]: 230.94, [CLOSE]: 235.22 },
  { [DATE]: "2024-01-30", [OPEN]: 235.58, [HIGH]: 237.45, [LOW]: 231.38, [CLOSE]: 233.19 },
  { [DATE]: "2024-01-31", [OPEN]: 232.88, [HIGH]: 236.12, [LOW]: 229.76, [CLOSE]: 231.42 },
  { [DATE]: "2024-02-01", [OPEN]: 231.76, [HIGH]: 236.48, [LOW]: 230.52, [CLOSE]: 234.86 },
  { [DATE]: "2024-02-02", [OPEN]: 235.21, [HIGH]: 239.62, [LOW]: 233.84, [CLOSE]: 237.94 },
  { [DATE]: "2024-02-05", [OPEN]: 237.62, [HIGH]: 239.44, [LOW]: 233.91, [CLOSE]: 235.78 },
  { [DATE]: "2024-02-06", [OPEN]: 236.12, [HIGH]: 240.35, [LOW]: 234.68, [CLOSE]: 238.65 },
  { [DATE]: "2024-02-07", [OPEN]: 238.98, [HIGH]: 242.84, [LOW]: 237.21, [CLOSE]: 241.12 },
  { [DATE]: "2024-02-08", [OPEN]: 240.79, [HIGH]: 242.56, [LOW]: 237.14, [CLOSE]: 239.08 },
  { [DATE]: "2024-02-09", [OPEN]: 239.42, [HIGH]: 243.91, [LOW]: 238.05, [CLOSE]: 242.18 },
  { [DATE]: "2024-02-12", [OPEN]: 241.86, [HIGH]: 244.12, [LOW]: 238.22, [CLOSE]: 240.04 },
  { [DATE]: "2024-02-13", [OPEN]: 239.71, [HIGH]: 242.15, [LOW]: 235.88, [CLOSE]: 237.62 },
  { [DATE]: "2024-02-14", [OPEN]: 237.98, [HIGH]: 242.64, [LOW]: 236.54, [CLOSE]: 240.89 },
  { [DATE]: "2024-02-15", [OPEN]: 241.24, [HIGH]: 245.38, [LOW]: 239.72, [CLOSE]: 243.65 },
  { [DATE]: "2024-02-16", [OPEN]: 243.31, [HIGH]: 245.19, [LOW]: 239.84, [CLOSE]: 241.72 },
  { [DATE]: "2024-02-19", [OPEN]: 242.08, [HIGH]: 246.52, [LOW]: 240.68, [CLOSE]: 244.84 },
  { [DATE]: "2024-02-20", [OPEN]: 244.51, [HIGH]: 246.78, [LOW]: 241.12, [CLOSE]: 242.96 },
  { [DATE]: "2024-02-21", [OPEN]: 243.29, [HIGH]: 247.85, [LOW]: 241.94, [CLOSE]: 246.12 },
  { [DATE]: "2024-02-22", [OPEN]: 246.48, [HIGH]: 250.42, [LOW]: 244.86, [CLOSE]: 248.75 },
  { [DATE]: "2024-02-23", [OPEN]: 248.41, [HIGH]: 250.36, [LOW]: 244.92, [CLOSE]: 246.88 },
  { [DATE]: "2024-02-26", [OPEN]: 247.22, [HIGH]: 251.64, [LOW]: 245.78, [CLOSE]: 249.92 },
  { [DATE]: "2024-02-27", [OPEN]: 249.58, [HIGH]: 251.84, [LOW]: 246.15, [CLOSE]: 248.04 },
  { [DATE]: "2024-02-28", [OPEN]: 248.39, [HIGH]: 252.91, [LOW]: 246.98, [CLOSE]: 251.18 },
  { [DATE]: "2024-02-29", [OPEN]: 251.54, [HIGH]: 255.12, [LOW]: 249.62, [CLOSE]: 253.46 },
  { [DATE]: "2024-03-01", [OPEN]: 253.12, [HIGH]: 255.28, [LOW]: 249.74, [CLOSE]: 251.82 },
  { [DATE]: "2024-03-04", [OPEN]: 252.18, [HIGH]: 256.84, [LOW]: 250.88, [CLOSE]: 255.14 },
];

// Plot: reads only data and the constants above
const sortedData = [...data].sort((a, b) => String(a[DATE]).localeCompare(String(b[DATE])));
const dates = sortedData.map((r) => String(r[DATE]));
const opens = sortedData.map((r) => Number(r[OPEN]));
const highs = sortedData.map((r) => Number(r[HIGH]));
const lows = sortedData.map((r) => Number(r[LOW]));
const closes = sortedData.map((r) => Number(r[CLOSE]));

const years = Array.from(new Set(dates.map((d) => d.slice(0, 4)).filter((y) => /^\d{4}$/.test(y))));
const yearSuffix =
  years.length === 1
    ? ` (${years[0]})`
    : years.length > 1
      ? ` (${years[0]}–${years[years.length - 1]})`
      : "";
const xAxisLabel = `${DATE}${yearSuffix}`;

const yMin = Math.min(...lows);
const yMax = Math.max(...highs);
const yPad = (yMax - yMin) * Y_PAD_SHARE;

const legendItems = [
  { color: t.palette[0], label: "Up (close > open)" },
  { color: t.palette[4], label: "Down (close < open)" },
];

function OhlcBars() {
  const xScale = useXScale("sessions") as unknown as ((d: string) => number) & {
    bandwidth: () => number;
  };
  const yScale = useYScale("price") as unknown as (v: number) => number;
  const bandwidth = xScale.bandwidth();
  const tickWidth = Math.min(bandwidth * 0.4, 11);

  return (
    <g>
      {dates.map((date, i) => {
        const center = xScale(date) + bandwidth / 2;
        const isUp = closes[i] >= opens[i];
        const color = isUp ? t.palette[0] : t.palette[4];

        return (
          <g key={date} stroke={color} strokeWidth={2.4} strokeLinecap="round">
            <line x1={center} x2={center} y1={yScale(highs[i])} y2={yScale(lows[i])} />
            <line x1={center - tickWidth} x2={center} y1={yScale(opens[i])} y2={yScale(opens[i])} />
            <line x1={center} x2={center + tickWidth} y1={yScale(closes[i])} y2={yScale(closes[i])} />
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
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingLeft: 24,
          paddingRight: 40,
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {legendItems.map((item) => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 18,
                  height: 3,
                  borderRadius: 2,
                  backgroundColor: item.color,
                }}
              />
              <span style={{ fontSize: 14, color: t.inkSoft }}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 18, right: 36, bottom: 14, left: 18 }}
        xAxis={[
          {
            id: "sessions",
            data: dates,
            scaleType: "band",
            height: 58,
            label: xAxisLabel,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelInterval: (_value: unknown, index: number) =>
              index % TICK_INTERVAL_STEP === 0,
            valueFormatter: (iso: string) => {
              const parts = String(iso).split("-");
              if (parts.length === 3) {
                const m = Number(parts[1]) - 1;
                const d = Number(parts[2]);
                return `${MONTHS[m]} ${d}`;
              }
              return String(iso);
            },
          },
        ]}
        yAxis={[
          {
            id: "price",
            min: yMin - yPad,
            max: yMax + yPad,
            width: 88,
            label: CLOSE,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => v.toFixed(0),
          },
        ]}
      >
        <ChartsGrid
          horizontal
          sx={{
            "& .MuiChartsGrid-line": {
              stroke: t.grid,
              opacity: 0.55,
              strokeDasharray: "2 5",
            },
          }}
        />
        <OhlcBars />
        <ChartsXAxis axisId="sessions" />
        <ChartsYAxis axisId="price" />
      </ChartsContainer>
    </div>
  );
}
