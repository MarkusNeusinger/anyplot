// anyplot.ai
// indicator-ema: Exponential Moving Average (EMA) Indicator Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 49/100 | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data: 120 trading days of daily closes, deterministic LCG walk --------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const rand = lcg(42);

const NUM_DAYS = 120;
const START_DATE = new Date(2024, 0, 2);

const dates = Array.from({ length: NUM_DAYS }, (_, day) => {
  const d = new Date(START_DATE);
  d.setDate(d.getDate() + day);
  return d;
});

// Random-walk closing price with a mild upward drift plus daily noise.
const closePrices = [];
let price = 148;
for (let day = 0; day < NUM_DAYS; day += 1) {
  const drift = 0.15;
  const shock = (rand() - 0.5) * 4.2;
  price = Math.max(80, price + drift + shock);
  closePrices.push(Math.round(price * 100) / 100);
}

const ema = (values, period) => {
  const k = 2 / (period + 1);
  const out = [values[0]];
  for (let i = 1; i < values.length; i += 1) {
    out.push(values[i] * k + out[i - 1] * (1 - k));
  }
  return out;
};

const emaShort = ema(closePrices, 12);
const emaLong = ema(closePrices, 26);

// Crossover points: where the short EMA changes sign relative to the long EMA.
// Golden cross = bullish (short moves above long); death cross = bearish.
const allCrossovers = [];
for (let i = 1; i < NUM_DAYS; i += 1) {
  const prevDiff = emaShort[i - 1] - emaLong[i - 1];
  const currDiff = emaShort[i] - emaLong[i];
  if (prevDiff !== 0 && currDiff !== 0 && Math.sign(prevDiff) !== Math.sign(currDiff)) {
    allCrossovers.push({ index: i, bullish: currDiff > 0 });
  }
}
// Keep the chart legible: cap the highlighted crossovers to a handful, and
// require a minimum day-gap so neighboring labels never collide.
const MAX_CROSSOVERS = 4;
const MIN_GAP_DAYS = 15;
const crossovers = [];
for (const c of allCrossovers) {
  const last = crossovers[crossovers.length - 1];
  if (!last || c.index - last.index >= MIN_GAP_DAYS) {
    crossovers.push(c);
  }
  if (crossovers.length >= MAX_CROSSOVERS) break;
}

const TITLE = "indicator-ema · javascript · muix · anyplot.ai";
const dateFormatter = (date) => date.toLocaleDateString("en-US", { month: "short", day: "numeric" });

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 44, bottom: 24, left: 44 };
  const titleBlockHeight = 56;
  // MUI X's built-in yAxis `label` positions itself using a fixed
  // (tickFontSize + tickSize + 10) offset rather than the tick labels'
  // measured width, so a 4-char dollar-formatted tick ("$158") collides
  // with the rotated title. Render the y-axis title ourselves in a
  // dedicated column instead, and only reserve chart-internal margin for
  // the tick labels.
  const yAxisLabelColWidth = 32;
  const chartWidth = size.width - padding.left - padding.right - yAxisLabelColWidth;
  const chartHeight = size.height - padding.top - padding.bottom - titleBlockHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography sx={{ fontSize: 22, fontWeight: 600, color: "text.primary", mb: "20px", lineHeight: 1 }}>
        {TITLE}
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center" }}>
        <Box
          sx={{
            width: yAxisLabelColWidth,
            height: chartHeight,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Typography
            sx={{
              fontSize: 16,
              color: "text.secondary",
              whiteSpace: "nowrap",
              writingMode: "vertical-rl",
              transform: "rotate(180deg)",
            }}
          >
            Price (USD)
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          margin={{ top: 20, right: 30, bottom: 40, left: 64 }}
          series={[
            {
              id: "close",
              label: "Close Price",
              data: closePrices,
              color: t.palette[0],
              showMark: false,
              valueFormatter: (v) => `$${v.toFixed(2)}`,
            },
            {
              id: "ema12",
              label: "EMA (12-day)",
              data: emaShort,
              color: t.palette[1],
              showMark: false,
              valueFormatter: (v) => `$${v.toFixed(2)}`,
            },
            {
              id: "ema26",
              label: "EMA (26-day)",
              data: emaLong,
              color: t.palette[2],
              showMark: false,
              valueFormatter: (v) => `$${v.toFixed(2)}`,
            },
          ]}
          xAxis={[
            {
              data: dates,
              scaleType: "time",
              label: "Trading Date",
              valueFormatter: dateFormatter,
              tickLabelStyle: { fontSize: 14 },
              labelStyle: { fontSize: 16 },
            },
          ]}
          yAxis={[
            {
              valueFormatter: (v) => `$${v}`,
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              direction: "row",
              labelStyle: { fontSize: 14 },
              itemMarkWidth: 18,
              itemMarkHeight: 10,
              markGap: 8,
            },
          }}
          sx={{
            "& .MuiLineElement-series-close": { strokeWidth: 3.5 },
            "& .MuiLineElement-series-ema12": { strokeWidth: 2 },
            "& .MuiLineElement-series-ema26": { strokeWidth: 2 },
          }}
        >
          {crossovers.map((c) => (
            <ChartsReferenceLine
              key={c.index}
              x={dates[c.index]}
              label={c.bullish ? "Golden cross" : "Death cross"}
              labelAlign="start"
              lineStyle={{
                stroke: c.bullish ? t.palette[0] : t.palette[4],
                strokeDasharray: "6 4",
                strokeWidth: 1.5,
              }}
              labelStyle={{ fill: c.bullish ? t.palette[0] : t.palette[4], fontSize: 13 }}
            />
          ))}
        </LineChart>
      </Box>
    </Box>
  );
}
