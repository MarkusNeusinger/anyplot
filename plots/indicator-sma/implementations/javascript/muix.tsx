// anyplot.ai
// indicator-sma: Simple Moving Average (SMA) Indicator Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;
const [BRAND, SHORT_COLOR, MEDIUM_COLOR, LONG_COLOR] = t.palette;

// --- Data (in-memory, deterministic) ----------------------------------------
const SYMBOL = "AURA";
const N = 300;
const WINDOW_SHORT = 20;
const WINDOW_MEDIUM = 50;
const WINDOW_LONG = 200;
const START_PRICE = 68;

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
const cursor = new Date(2023, 5, 1);
while (dates.length < N) {
  const day = cursor.getDay();
  if (day !== 0 && day !== 6) dates.push(new Date(cursor));
  cursor.setDate(cursor.getDate() + 1);
}

// Daily close through three regimes — steady uptrend, a choppy pullback
// (death cross), then a recovery uptrend (golden cross) — so the SMA
// crossovers described in the spec's applications are visible.
const close = [START_PRICE];
for (let i = 1; i < N; i += 1) {
  const pullback = i >= 110 && i < 190;
  const driftPct = pullback ? -0.12 : 0.09;
  const dailyVolPct = pullback ? 1.3 : 0.9;
  const changePct = driftPct + dailyVolPct * gaussian();
  close.push(Math.max(10, close[i - 1] * (1 + changePct / 100)));
}

const round2 = (v) => Math.round(v * 100) / 100;

const sma = (data, window) =>
  data.map((_, i) => {
    if (i < window - 1) return null;
    const windowSlice = data.slice(i - window + 1, i + 1);
    return round2(windowSlice.reduce((sum, v) => sum + v, 0) / window);
  });

const smaShort = sma(close, WINDOW_SHORT);
const smaMedium = sma(close, WINDOW_MEDIUM);
const smaLong = sma(close, WINDOW_LONG);
const closeRounded = close.map(round2);

// Explicit y-axis bounds so the four overlapping lines use the full canvas.
const allValues = [...closeRounded, ...smaShort, ...smaMedium, ...smaLong].filter(
  (v) => v !== null,
);
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const axisPadding = (dataMax - dataMin) * 0.1;
const yMin = Math.floor((dataMin - axisPadding) / 5) * 5;
const yMax = Math.ceil((dataMax + axisPadding) / 5) * 5;

const TITLE = `${SYMBOL} · indicator-sma · javascript · muix · anyplot.ai`;

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
            tickFontSize: 40,
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (v) => `$${v.toFixed(0)}`,
            min: yMin,
            max: yMax,
          },
        ]}
        series={[
          {
            id: "smaLong",
            data: smaLong,
            color: LONG_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
            label: "SMA 200",
          },
          {
            id: "smaMedium",
            data: smaMedium,
            color: MEDIUM_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
            label: "SMA 50",
          },
          {
            id: "smaShort",
            data: smaShort,
            color: SHORT_COLOR,
            showMark: false,
            connectNulls: false,
            curve: "monotoneX",
            label: "SMA 20",
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
          "& .MuiLineElement-series-close": { strokeWidth: 3 },
          "& .MuiLineElement-series-smaShort": {
            strokeWidth: 2,
            strokeDasharray: "8 5",
          },
          "& .MuiLineElement-series-smaMedium": {
            strokeWidth: 2,
            strokeDasharray: "2 4",
          },
          "& .MuiLineElement-series-smaLong": {
            strokeWidth: 2.25,
          },
        }}
      />
    </Box>
  );
}
