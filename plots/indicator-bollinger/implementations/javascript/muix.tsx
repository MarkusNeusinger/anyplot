// anyplot.ai
// indicator-bollinger: Bollinger Bands Indicator Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;
const [BRAND, SMA_COLOR, BAND_COLOR] = t.palette;

const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const BAND_FILL = hexToRgba(BAND_COLOR, 0.16);

// --- Data (in-memory, deterministic) ----------------------------------------
const SYMBOL = "MRDN";
const N = 120;
const WINDOW = 20;
const START_PRICE = 162.5;

// Fixed-seed LCG (Numerical Recipes constants) — the browser has no seeded RNG.
let seed = 42;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};
const gaussian = () => {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

// Trading dates (weekdays only)
const dates = [];
const cursor = new Date(2024, 0, 2);
while (dates.length < N) {
  const day = cursor.getDay();
  if (day !== 0 && day !== 6) dates.push(new Date(cursor));
  cursor.setDate(cursor.getDate() + 1);
}

// Daily close, with a calm "squeeze" regime and a high-volatility breakout
// regime so the bands visibly narrow and then widen (see spec "Notes").
const close = [START_PRICE];
for (let i = 1; i < N; i += 1) {
  const squeeze = i >= 40 && i < 65;
  const breakout = i >= 90;
  const dailyVolPct = squeeze ? 0.35 : breakout ? 1.7 : 0.9;
  const driftPct = 0.05;
  const changePct = driftPct + dailyVolPct * gaussian();
  close.push(Math.max(20, close[i - 1] * (1 + changePct / 100)));
}

const round2 = (v) => Math.round(v * 100) / 100;

// Rolling 20-period SMA and population std dev -> upper/lower bands.
const sma = [];
const upperBand = [];
const lowerBand = [];
const bandWidth = [];
for (let i = 0; i < N; i += 1) {
  if (i < WINDOW - 1) {
    sma.push(null);
    upperBand.push(null);
    lowerBand.push(null);
    bandWidth.push(null);
    continue;
  }
  const windowSlice = close.slice(i - WINDOW + 1, i + 1);
  const mean = windowSlice.reduce((sum, v) => sum + v, 0) / WINDOW;
  const variance =
    windowSlice.reduce((sum, v) => sum + (v - mean) ** 2, 0) / WINDOW;
  const stdDev = Math.sqrt(variance);
  const upper = round2(mean + 2 * stdDev);
  const lower = round2(mean - 2 * stdDev);
  sma.push(round2(mean));
  upperBand.push(upper);
  lowerBand.push(lower);
  bandWidth.push(round2(upper - lower));
}
const closeRounded = close.map(round2);

// Explicit y-axis bounds: the stacked band series' domain runs from 0 (its
// hidden base) to the upper band, which would force the axis to include 0
// and waste most of the canvas on empty space above/below the real range.
const allValues = [...closeRounded, ...sma, ...upperBand, ...lowerBand].filter(
  (v) => v !== null,
);
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const axisPadding = (dataMax - dataMin) * 0.15;
const yMin = Math.floor((dataMin - axisPadding) / 5) * 5;
const yMax = Math.ceil((dataMax + axisPadding) / 5) * 5;

const TITLE = `${SYMBOL} · indicator-bollinger · javascript · muix · anyplot.ai`;

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 64;

  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Typography
        color="text.primary"
        sx={{
          height: titleHeight,
          lineHeight: `${titleHeight}px`,
          pl: 1,
          fontSize: 22,
          fontWeight: 600,
        }}
      >
        {TITLE}
      </Typography>
      <LineChart
        width={width}
        height={height - titleHeight}
        skipAnimation
        margin={{ top: 72, right: 48, bottom: 76, left: 132 }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            label: "Trading Date",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (date) =>
              date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              }),
          },
        ]}
        yAxis={[
          {
            label: "Price (USD)",
            labelStyle: { fontSize: 16 },
            // tickFontSize pushes the rotated axis title clear of the "$NNN"
            // tick labels — the actual tick text size is set via tickLabelStyle.
            tickFontSize: 40,
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => `$${v.toFixed(0)}`,
            min: yMin,
            max: yMax,
          },
        ]}
        series={[
          {
            id: "bandBase",
            data: lowerBand,
            area: true,
            stack: "band",
            color: BAND_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
          },
          {
            id: "bandWidth",
            data: bandWidth,
            area: true,
            stack: "band",
            color: BAND_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
            label: "Bollinger Band (SMA ± 2σ)",
          },
          {
            id: "sma",
            data: sma,
            color: SMA_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
            label: "20-Day SMA",
          },
          {
            id: "close",
            data: closeRounded,
            color: BRAND,
            showMark: false,
            curve: "monotoneX",
            label: `${SYMBOL} Close`,
          },
        ]}
        grid={{ horizontal: true }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "top", horizontal: "middle" },
            labelStyle: { fontSize: 14 },
          },
        }}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 2 },
          "& .MuiLineElement-series-close": { strokeWidth: 3.5 },
          "& .MuiLineElement-series-sma": {
            strokeWidth: 2.25,
            strokeDasharray: "10 6",
          },
          "& .MuiLineElement-series-bandBase": {
            strokeWidth: 1.5,
            strokeOpacity: 0.6,
          },
          "& .MuiLineElement-series-bandWidth": {
            strokeWidth: 1.5,
            strokeOpacity: 0.6,
          },
          "& .MuiAreaElement-series-bandBase": { fill: "none" },
          "& .MuiAreaElement-series-bandWidth": { fill: BAND_FILL },
        }}
      />
    </Box>
  );
}
