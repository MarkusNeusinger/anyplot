// anyplot.ai
// ohlc-bar: OHLC Bar Chart
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02

import * as React from "react";
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

const DATE_COL = "trading_session";
const OPEN_COL = "open_usd";
const HIGH_COL = "high_usd";
const LOW_COL = "low_usd";
const CLOSE_COL = "close_usd";

// Data: 45 trading sessions of daily OHLC prices (flat scalar records)
const DATA: Array<Record<string, string | number>> = [
  { trading_session: "Jan 2", open_usd: 218.26, high_usd: 221.39, low_usd: 216.69, close_usd: 219.51 },
  { trading_session: "Jan 3", open_usd: 219.59, high_usd: 221.25, low_usd: 216.2, close_usd: 218.08 },
  { trading_session: "Jan 4", open_usd: 217.56, high_usd: 222.07, low_usd: 216.12, close_usd: 220.43 },
  { trading_session: "Jan 5", open_usd: 220.99, high_usd: 222.39, low_usd: 217.99, close_usd: 219.72 },
  { trading_session: "Jan 8", open_usd: 219.35, high_usd: 223.95, low_usd: 218.3, close_usd: 222.58 },
  { trading_session: "Jan 9", open_usd: 222.25, high_usd: 225.73, low_usd: 220.51, close_usd: 224.09 },
  { trading_session: "Jan 10", open_usd: 224.51, high_usd: 226.47, low_usd: 220.69, close_usd: 222.36 },
  { trading_session: "Jan 11", open_usd: 221.96, high_usd: 225.56, low_usd: 220.76, close_usd: 224.22 },
  { trading_session: "Jan 12", open_usd: 224.58, high_usd: 226.15, low_usd: 220.89, close_usd: 222.71 },
  { trading_session: "Jan 15", open_usd: 222.42, high_usd: 227.51, low_usd: 221.11, close_usd: 225.78 },
  { trading_session: "Jan 16", open_usd: 226.14, high_usd: 229.88, low_usd: 224.36, close_usd: 228.11 },
  { trading_session: "Jan 17", open_usd: 227.79, high_usd: 229.47, low_usd: 223.82, close_usd: 225.63 },
  { trading_session: "Jan 18", open_usd: 225.95, high_usd: 229.74, low_usd: 224.14, close_usd: 227.85 },
  { trading_session: "Jan 19", open_usd: 228.19, high_usd: 232.42, low_usd: 226.78, close_usd: 230.89 },
  { trading_session: "Jan 22", open_usd: 230.52, high_usd: 232.28, low_usd: 227.05, close_usd: 228.94 },
  { trading_session: "Jan 23", open_usd: 229.28, high_usd: 233.61, low_usd: 227.91, close_usd: 231.98 },
  { trading_session: "Jan 24", open_usd: 231.69, high_usd: 234.12, low_usd: 228.44, close_usd: 230.15 },
  { trading_session: "Jan 25", open_usd: 230.49, high_usd: 235.18, low_usd: 229.12, close_usd: 233.54 },
  { trading_session: "Jan 26", open_usd: 233.86, high_usd: 236.24, low_usd: 230.65, close_usd: 232.41 },
  { trading_session: "Jan 29", open_usd: 232.11, high_usd: 236.89, low_usd: 230.94, close_usd: 235.22 },
  { trading_session: "Jan 30", open_usd: 235.58, high_usd: 237.45, low_usd: 231.38, close_usd: 233.19 },
  { trading_session: "Jan 31", open_usd: 232.88, high_usd: 236.12, low_usd: 229.76, close_usd: 231.42 },
  { trading_session: "Feb 1", open_usd: 231.76, high_usd: 236.48, low_usd: 230.52, close_usd: 234.86 },
  { trading_session: "Feb 2", open_usd: 235.21, high_usd: 239.62, low_usd: 233.84, close_usd: 237.94 },
  { trading_session: "Feb 5", open_usd: 237.62, high_usd: 239.44, low_usd: 233.91, close_usd: 235.78 },
  { trading_session: "Feb 6", open_usd: 236.12, high_usd: 240.35, low_usd: 234.68, close_usd: 238.65 },
  { trading_session: "Feb 7", open_usd: 238.98, high_usd: 242.84, low_usd: 237.21, close_usd: 241.12 },
  { trading_session: "Feb 8", open_usd: 240.79, high_usd: 242.56, low_usd: 237.14, close_usd: 239.08 },
  { trading_session: "Feb 9", open_usd: 239.42, high_usd: 243.91, low_usd: 238.05, close_usd: 242.18 },
  { trading_session: "Feb 12", open_usd: 241.86, high_usd: 244.12, low_usd: 238.22, close_usd: 240.04 },
  { trading_session: "Feb 13", open_usd: 239.71, high_usd: 242.15, low_usd: 235.88, close_usd: 237.62 },
  { trading_session: "Feb 14", open_usd: 237.98, high_usd: 242.64, low_usd: 236.54, close_usd: 240.89 },
  { trading_session: "Feb 15", open_usd: 241.24, high_usd: 245.38, low_usd: 239.72, close_usd: 243.65 },
  { trading_session: "Feb 16", open_usd: 243.31, high_usd: 245.19, low_usd: 239.84, close_usd: 241.72 },
  { trading_session: "Feb 19", open_usd: 242.08, high_usd: 246.52, low_usd: 240.68, close_usd: 244.84 },
  { trading_session: "Feb 20", open_usd: 244.51, high_usd: 246.78, low_usd: 241.12, close_usd: 242.96 },
  { trading_session: "Feb 21", open_usd: 243.29, high_usd: 247.85, low_usd: 241.94, close_usd: 246.12 },
  { trading_session: "Feb 22", open_usd: 246.48, high_usd: 250.42, low_usd: 244.86, close_usd: 248.75 },
  { trading_session: "Feb 23", open_usd: 248.41, high_usd: 250.36, low_usd: 244.92, close_usd: 246.88 },
  { trading_session: "Feb 26", open_usd: 247.22, high_usd: 251.64, low_usd: 245.78, close_usd: 249.92 },
  { trading_session: "Feb 27", open_usd: 249.58, high_usd: 251.84, low_usd: 246.15, close_usd: 248.04 },
  { trading_session: "Feb 28", open_usd: 248.39, high_usd: 252.91, low_usd: 246.98, close_usd: 251.18 },
  { trading_session: "Feb 29", open_usd: 251.54, high_usd: 255.12, low_usd: 249.62, close_usd: 253.46 },
  { trading_session: "Mar 1", open_usd: 253.12, high_usd: 255.28, low_usd: 249.74, close_usd: 251.82 },
  { trading_session: "Mar 4", open_usd: 252.18, high_usd: 256.84, low_usd: 250.88, close_usd: 255.14 },
];

const dates = DATA.map((r) => String(r[DATE_COL]));
const opens = DATA.map((r) => Number(r[OPEN_COL]));
const highs = DATA.map((r) => Number(r[HIGH_COL]));
const lows = DATA.map((r) => Number(r[LOW_COL]));
const closes = DATA.map((r) => Number(r[CLOSE_COL]));

const yMin = Math.min(...lows);
const yMax = Math.max(...highs);
const yPad = (yMax - yMin) * Y_PAD_SHARE;

const legendItems = [
  { color: t.palette[0], label: "Up (close > open)" },
  { color: t.palette[4], label: "Down (close < open)" },
];

function OhlcBars() {
  const xScale = useXScale("sessions") as unknown as ((d: string) => number) & { bandwidth: () => number };
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
            label: "Trading Session (2024)",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelInterval: (_value: unknown, index: number) => index % TICK_INTERVAL_STEP === 0,
          },
        ]}
        yAxis={[
          {
            id: "price",
            min: yMin - yPad,
            max: yMax + yPad,
            width: 88,
            label: "Share Price (USD)",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `$${v.toFixed(0)}`,
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
