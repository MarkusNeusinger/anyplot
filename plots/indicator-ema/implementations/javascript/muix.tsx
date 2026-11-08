// anyplot.ai
// indicator-ema: Exponential Moving Average (EMA) Indicator Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsAxisHighlight } from "@mui/x-charts/ChartsAxisHighlight";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.06; // share of the price range added above and below the outermost line

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const CLOSE = "Close (USD)"; // role: close
const EMA_SHORT = "12-day EMA (USD)"; // role: ema_short
const EMA_LONG = "26-day EMA (USD)"; // role: ema_long

// Data: replace this block with your own records, one object per trading day
// 120 weekdays of a stock from 2 Jan 2024: a random walk with a mild upward drift.
// Both EMAs are seeded with the first close and use the smoothing factor 2 / (period + 1).
const data = (() => {
  const periods = 120;
  let state = 42;
  const rand = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  const round2 = (v: number) => Math.round(v * 100) / 100;

  const days: string[] = [];
  const cursor = new Date(Date.UTC(2024, 0, 2));
  while (days.length < periods) {
    if (cursor.getUTCDay() % 6 !== 0) days.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  const close: number[] = [];
  let price = 148;
  for (let i = 0; i < periods; i += 1) {
    price += 0.15 + (rand() - 0.5) * 4.2;
    close.push(round2(price));
  }

  const kShort = 2 / (12 + 1);
  const kLong = 2 / (26 + 1);
  const short = [close[0]];
  const long = [close[0]];
  for (let i = 1; i < periods; i += 1) {
    short.push(close[i] * kShort + short[i - 1] * (1 - kShort));
    long.push(close[i] * kLong + long[i - 1] * (1 - kLong));
  }

  return days.map((day, i) => ({
    [DATE]: day,
    [CLOSE]: close[i],
    [EMA_SHORT]: round2(short[i]),
    [EMA_LONG]: round2(long[i]),
  }));
})();

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const n = rows.length;
const dates = rows.map((d) => new Date(`${d[DATE]}T00:00:00`));
const closes = rows.map((d) => d[CLOSE] ?? null);
const shorts = rows.map((d) => d[EMA_SHORT] ?? null);
const longs = rows.map((d) => d[EMA_LONG] ?? null);

// A crossover is a change of side against the last day on which the two EMAs differed; its
// mark sits where the two straight segments meet, or on the day they were equal
const crossovers: { time: number; value: number; bullish: boolean }[] = [];
let side = 0; // sign of the last non-zero difference short - long
for (let i = 1; i < n; i += 1) {
  const s0 = shorts[i - 1];
  const l0 = longs[i - 1];
  const s1 = shorts[i];
  const l1 = longs[i];
  if (s0 == null || l0 == null || s1 == null || l1 == null) continue;
  const before = s0 - l0;
  const after = s1 - l1;
  if (before !== 0) side = Math.sign(before);
  if (after === 0 || side === 0 || Math.sign(after) === side) continue;
  const f = before / (before - after); // 0 when the two were equal on the day before
  crossovers.push({
    time: dates[i - 1].getTime() + f * (dates[i].getTime() - dates[i - 1].getTime()),
    value: s0 + f * (s1 - s0),
    bullish: after > 0,
  });
}
const bullishCount = crossovers.filter((c) => c.bullish).length;
const bearishCount = crossovers.length - bullishCount;

const drawn = [...closes, ...shorts, ...longs].filter((v) => v != null);
const yLow = Math.min(...drawn);
const yHigh = Math.max(...drawn);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const shortName = EMA_SHORT.replace(/\s*\([^)]*\)\s*$/, "");
const longName = EMA_LONG.replace(/\s*\([^)]*\)\s*$/, "");

const TITLE = "indicator-ema · javascript · muix · anyplot.ai";
const SUBTITLE =
  `${n} periods, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])} · ` +
  `▲ ${shortName} crosses above ${longName} (${bullishCount}×) · ▼ crosses below (${bearishCount}×)`;
const HEADER_H = 84;
const LEGEND_H = 44;
const MARK_PX = 8; // half the width of a crossover triangle

function CrossoverMarks() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {crossovers.map((c) => {
        const x = xScale(new Date(c.time));
        const y = yScale(c.value);
        const tip = c.bullish ? -1.15 * MARK_PX : 1.15 * MARK_PX;
        return (
          <path
            key={c.time}
            d={`M${x},${y + tip}L${x + MARK_PX},${y - tip * 0.6}L${x - MARK_PX},${y - tip * 0.6}Z`}
            fill={t.ink}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 12, right: 40, bottom: 8, left: 20 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "close",
            data: closes,
            label: CLOSE,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            type: "line",
            id: "emaShort",
            data: shorts,
            label: EMA_SHORT,
            color: t.palette[1],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            type: "line",
            id: "emaLong",
            data: longs,
            label: EMA_LONG,
            color: t.palette[2],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
        ]}
        xAxis={[
          {
            scaleType: "time",
            data: dates,
            domainLimit: "strict",
            label: DATE,
            height: 64,
            tickNumber: 10,
            valueFormatter: (v: Date) => dayFormat.format(v),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            width: 84,
            label: CLOSE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.ink, gap: "28px" }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 2 },
              '& .MuiLineChart-line[data-series="close"]': { strokeWidth: 3.5 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <LinePlot skipAnimation />
            <CrossoverMarks />
            <ChartsAxisHighlight x="line" />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="axis" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
