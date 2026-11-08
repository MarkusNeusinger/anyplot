// anyplot.ai
// indicator-bollinger: Bollinger Bands Indicator Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
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
const BAND_FILL_OPACITY = 0.16;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const CLOSE = "MRDN close (USD)"; // role: close
const SMA = "20-day SMA (USD)"; // role: sma
const UPPER_BAND = "Upper band, SMA + 2σ (USD)"; // role: upper_band
const LOWER_BAND = "Lower band, SMA − 2σ (USD)"; // role: lower_band

// Data: replace this block with your own records, one object per trading day
// 120 weekdays of a mid-cap stock from 2 Jan 2024: a calm stretch (days 40-64) squeezes
// the bands and a volatile run from day 90 widens them. The bands use a 20-day window and
// the population standard deviation, so the first 19 days carry no band values.
const data = (() => {
  const periods = 120;
  const lookback = 20;
  const sigmas = 2;
  let seed = 42;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const round2 = (v: number) => Math.round(v * 100) / 100;

  const days: string[] = [];
  const cursor = new Date(Date.UTC(2024, 0, 2));
  while (days.length < periods) {
    if (cursor.getUTCDay() % 6 !== 0) days.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  const close = [162.5];
  for (let i = 1; i < periods; i += 1) {
    const volPct = i >= 40 && i < 65 ? 0.35 : i >= 90 ? 1.7 : 0.9;
    close.push(close[i - 1] * (1 + (0.05 + volPct * gaussian()) / 100));
  }

  return days.map((day, i) => {
    if (i < lookback - 1) {
      return { [DATE]: day, [CLOSE]: round2(close[i]), [SMA]: null, [UPPER_BAND]: null, [LOWER_BAND]: null };
    }
    const span = close.slice(i - lookback + 1, i + 1);
    const mean = span.reduce((s, v) => s + v, 0) / lookback;
    const sd = Math.sqrt(span.reduce((s, v) => s + (v - mean) ** 2, 0) / lookback);
    return {
      [DATE]: day,
      [CLOSE]: round2(close[i]),
      [SMA]: round2(mean),
      [UPPER_BAND]: round2(mean + sigmas * sd),
      [LOWER_BAND]: round2(mean - sigmas * sd),
    };
  });
})();

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const n = rows.length;
const dates = rows.map((d) => new Date(`${d[DATE]}T00:00:00`));
const closes = rows.map((d) => d[CLOSE] ?? null);
const smas = rows.map((d) => d[SMA] ?? null);
const uppers = rows.map((d) => d[UPPER_BAND] ?? null);
const lowers = rows.map((d) => d[LOWER_BAND] ?? null);

// The fill between the bands is drawn for each run of consecutive days that has both bands
const bandRuns: number[][] = [];
rows.forEach((_, i) => {
  if (uppers[i] == null || lowers[i] == null) return;
  const run = bandRuns[bandRuns.length - 1];
  if (run && run[run.length - 1] === i - 1) run.push(i);
  else bandRuns.push([i]);
});

const drawn = [...closes, ...smas, ...uppers, ...lowers].filter((v) => v != null);
const yLow = Math.min(...drawn);
const yHigh = Math.max(...drawn);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

// Band width relative to the middle band; its minimum is the tightest squeeze
const widthShare = rows.map((_, i) =>
  uppers[i] != null && lowers[i] != null && smas[i] ? (uppers[i] - lowers[i]) / smas[i] : Infinity,
);
const narrowest = widthShare.indexOf(Math.min(...widthShare));

const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const squeezeNote =
  bandRuns.length > 0
    ? ` · narrowest band ${(widthShare[narrowest] * 100).toFixed(1)} % of the SMA on ${fullFormat.format(dates[narrowest])}`
    : "";

const TITLE = "indicator-bollinger · javascript · muix · anyplot.ai";
const SUBTITLE = `${n} periods, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])}${squeezeNote}`;
// The y axis carries the close, the SMA and both bands, so it is titled as the price axis
const PRICE_AXIS = "MRDN price (USD)";
const HEADER_H = 84;
const LEGEND_H = 44;
const BAND_COLOR = t.palette[2];

function BandFill() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {bandRuns.map((run) => {
        const top = run.map((i) => `${xScale(dates[i])},${yScale(uppers[i])}`);
        const bottom = [...run].reverse().map((i) => `${xScale(dates[i])},${yScale(lowers[i])}`);
        return (
          <path
            key={run[0]}
            d={`M${top.join("L")}L${bottom.join("L")}Z`}
            fill={BAND_COLOR}
            fillOpacity={BAND_FILL_OPACITY}
            stroke="none"
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
            id: "sma",
            data: smas,
            label: SMA,
            color: t.palette[1],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            type: "line",
            id: "upper",
            data: uppers,
            label: UPPER_BAND,
            color: BAND_COLOR,
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            type: "line",
            id: "lower",
            data: lowers,
            label: LOWER_BAND,
            color: BAND_COLOR,
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
            label: PRICE_AXIS,
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
              '& .MuiLineChart-line[data-series="sma"]': { strokeWidth: 2.5, strokeDasharray: "10 6" },
              '& .MuiLineChart-line[data-series="upper"], & .MuiLineChart-line[data-series="lower"]': {
                strokeWidth: 1.5,
                strokeOpacity: 0.8,
              },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <BandFill />
            <LinePlot skipAnimation />
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
