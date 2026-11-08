// anyplot.ai
// indicator-sma: Simple Moving Average (SMA) Indicator Chart
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
const CLOSE = "AURA close (USD)"; // role: close
const SMA_SHORT = "SMA 20 (USD)"; // role: sma_short
const SMA_MEDIUM = "SMA 50 (USD)"; // role: sma_medium
const SMA_LONG = "SMA 200 (USD)"; // role: sma_long

// Data: replace this block with your own records, one object per trading day
// 300 weekdays of a stock from 1 Jun 2023: a steady uptrend, a choppy pullback (days 110-189)
// that gives back about 12 % of the price, and a recovery. Each SMA averages the last 20, 50
// or 200 closes and stays empty until its window is full.
const data = (() => {
  const periods = 300;
  let seed = 42;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const round2 = (v: number) => Math.round(v * 100) / 100;

  const days: string[] = [];
  const cursor = new Date(Date.UTC(2023, 5, 1));
  while (days.length < periods) {
    if (cursor.getUTCDay() % 6 !== 0) days.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  const close = [68];
  for (let i = 1; i < periods; i += 1) {
    const pullback = i >= 110 && i < 190;
    const changePct = (pullback ? -0.3 : 0.09) + (pullback ? 1.3 : 0.9) * gaussian();
    close.push(close[i - 1] * (1 + changePct / 100));
  }

  // Running sums over the last 20, 50 and 200 closes
  let sumShort = 0;
  let sumMedium = 0;
  let sumLong = 0;
  const rows = [];
  for (let i = 0; i < periods; i += 1) {
    sumShort += close[i] - (i >= 20 ? close[i - 20] : 0);
    sumMedium += close[i] - (i >= 50 ? close[i - 50] : 0);
    sumLong += close[i] - (i >= 200 ? close[i - 200] : 0);
    rows.push({
      [DATE]: days[i],
      [CLOSE]: round2(close[i]),
      [SMA_SHORT]: i >= 19 ? round2(sumShort / 20) : null,
      [SMA_MEDIUM]: i >= 49 ? round2(sumMedium / 50) : null,
      [SMA_LONG]: i >= 199 ? round2(sumLong / 200) : null,
    });
  }
  return rows;
})();

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const n = rows.length;
const dates = rows.map((d) => new Date(`${d[DATE]}T00:00:00`));
const closes = rows.map((d) => d[CLOSE] ?? null);
const shorts = rows.map((d) => d[SMA_SHORT] ?? null);
const mediums = rows.map((d) => d[SMA_MEDIUM] ?? null);
const longs = rows.map((d) => d[SMA_LONG] ?? null);

// A crossover of the short over the medium SMA is a change of side against the last day on
// which the two differed; its mark sits where the two straight segments meet, or on the day
// they were equal
const crossovers: { time: number; value: number; upward: boolean }[] = [];
let side = 0; // sign of the last non-zero difference short - medium
for (let i = 1; i < n; i += 1) {
  const s0 = shorts[i - 1];
  const m0 = mediums[i - 1];
  const s1 = shorts[i];
  const m1 = mediums[i];
  if (s0 == null || m0 == null || s1 == null || m1 == null) continue;
  const before = s0 - m0;
  const after = s1 - m1;
  if (before !== 0) side = Math.sign(before);
  if (after === 0 || side === 0 || Math.sign(after) === side) continue;
  const f = before / (before - after); // 0 when the two were equal on the day before
  crossovers.push({
    time: dates[i - 1].getTime() + f * (dates[i].getTime() - dates[i - 1].getTime()),
    value: s0 + f * (s1 - s0),
    upward: after > 0,
  });
}
const upwardCount = crossovers.filter((c) => c.upward).length;
const downwardCount = crossovers.length - upwardCount;

const drawn = [...closes, ...shorts, ...mediums, ...longs].filter((v) => v != null);
const yLow = Math.min(...drawn);
const yHigh = Math.max(...drawn);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const monthFormat = new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const shortName = SMA_SHORT.replace(/\s*\([^)]*\)\s*$/, "");
const mediumName = SMA_MEDIUM.replace(/\s*\([^)]*\)\s*$/, "");

const TITLE = "indicator-sma · javascript · muix · anyplot.ai";
const SUBTITLE =
  `${n} periods, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])} · ` +
  `▲ ${shortName} crosses above ${mediumName} (${upwardCount}×) · ▼ crosses below (${downwardCount}×)`;
const HEADER_H = 84;
const LEGEND_H = 44;
const MARK_PX = 8; // half the width of a crossover triangle

// One stroke style per series, shared by the plotted line and its legend sample
const STROKES = {
  close: { width: 3, dash: undefined },
  smaShort: { width: 2, dash: "8 5" },
  smaMedium: { width: 2.75, dash: "2 4" },
  smaLong: { width: 2.25, dash: undefined },
};
const SAMPLE_W = 40;
const SAMPLE_H = 10;

// The built-in "line" mark is a short solid bar; this sample carries the series' dash pattern
const lineSample = ({ width, dash }: { width: number; dash?: string }) =>
  function LineSample({ color }: { color: string }) {
    return (
      <svg viewBox={`0 0 ${SAMPLE_W} ${SAMPLE_H}`}>
        <line x1={1} y1={SAMPLE_H / 2} x2={SAMPLE_W - 1} y2={SAMPLE_H / 2} stroke={color} strokeWidth={width} strokeDasharray={dash} />
      </svg>
    );
  };
const lineStyle = (id: keyof typeof STROKES) => ({ strokeWidth: STROKES[id].width, strokeDasharray: STROKES[id].dash });

function CrossoverMarks() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {crossovers.map((c) => {
        const x = xScale(new Date(c.time));
        const y = yScale(c.value);
        const tip = c.upward ? -1.15 * MARK_PX : 1.15 * MARK_PX;
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
        // The averages come first so the close is drawn on top of them; the legend reverses
        // this order so it reads close, then the SMAs by ascending period
        series={[
          {
            type: "line",
            id: "smaLong",
            data: longs,
            label: SMA_LONG,
            color: t.palette[3],
            curve: "linear",
            showMark: false,
            labelMarkType: lineSample(STROKES.smaLong),
          },
          {
            type: "line",
            id: "smaMedium",
            data: mediums,
            label: SMA_MEDIUM,
            color: t.palette[2],
            curve: "linear",
            showMark: false,
            labelMarkType: lineSample(STROKES.smaMedium),
          },
          {
            type: "line",
            id: "smaShort",
            data: shorts,
            label: SMA_SHORT,
            color: t.palette[1],
            curve: "linear",
            showMark: false,
            labelMarkType: lineSample(STROKES.smaShort),
          },
          {
            type: "line",
            id: "close",
            data: closes,
            label: CLOSE,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            labelMarkType: lineSample(STROKES.close),
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
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? monthFormat.format(v) : fullFormat.format(v),
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
          <ChartsLegend
            sx={{
              fontSize: 15,
              color: t.ink,
              gap: "28px",
              flexDirection: "row-reverse",
              "& .MuiChartsLegend-mark": { width: SAMPLE_W, height: SAMPLE_H },
            }}
          />
          <ChartsSurface
            sx={{
              '& .MuiLineChart-line[data-series="close"]': lineStyle("close"),
              '& .MuiLineChart-line[data-series="smaShort"]': lineStyle("smaShort"),
              '& .MuiLineChart-line[data-series="smaMedium"]': lineStyle("smaMedium"),
              '& .MuiLineChart-line[data-series="smaLong"]': lineStyle("smaLong"),
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
