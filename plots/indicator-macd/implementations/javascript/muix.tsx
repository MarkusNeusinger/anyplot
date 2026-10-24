// anyplot.ai
// indicator-macd: MACD Technical Indicator Chart
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const DATE_COL = "Trading Date";
const CLOSE_COL = "Close Price ($)";
const MACD_COL = "MACD (12, 26)";
const SIGNAL_COL = "Signal (9)";
const HISTOGRAM_COL = "MACD Histogram";
const Y_AXIS_LABEL = "MACD Value ($)";

const PERIODS = 120;
const FAST_EMA_PERIOD = 12;
const SLOW_EMA_PERIOD = 26;
const SIGNAL_EMA_PERIOD = 9;
const Y_PAD_SHARE = 0.1;

// Data: 120 business days of synthetic closing prices and MACD(12, 26, 9)
let lcgState = 42;
const dates: Date[] = [];
const cursor = new Date(Date.UTC(2025, 0, 2));
while (dates.length < PERIODS) {
  const weekday = cursor.getUTCDay();
  if (weekday !== 0 && weekday !== 6) {
    dates.push(new Date(cursor));
  }
  cursor.setUTCDate(cursor.getUTCDate() + 1);
}

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

const rawCloses: number[] = [];
let price = 148;
for (let i = 0; i < PERIODS; i += 1) {
  const trend = 0.55 * Math.sin(i / 16) + 0.15 * Math.sin(i / 5.5);
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const r = lcgState / 4294967296;
  const noise = (r - 0.5) * 1.4;
  price += trend + noise;
  rawCloses.push(price);
}

const fastK = 2 / (FAST_EMA_PERIOD + 1);
const slowK = 2 / (SLOW_EMA_PERIOD + 1);
const sigK = 2 / (SIGNAL_EMA_PERIOD + 1);

const ema12: number[] = [rawCloses[0]];
const ema26: number[] = [rawCloses[0]];
const rawMacd: number[] = [0];
for (let i = 1; i < PERIODS; i += 1) {
  const e12 = rawCloses[i] * fastK + ema12[i - 1] * (1 - fastK);
  const e26 = rawCloses[i] * slowK + ema26[i - 1] * (1 - slowK);
  ema12.push(e12);
  ema26.push(e26);
  rawMacd.push(e12 - e26);
}

const rawSignal: number[] = [rawMacd[0]];
for (let i = 1; i < PERIODS; i += 1) {
  rawSignal.push(rawMacd[i] * sigK + rawSignal[i - 1] * (1 - sigK));
}

const DATA: Array<{
  [DATE_COL]: string;
  [CLOSE_COL]: number;
  [MACD_COL]: number;
  [SIGNAL_COL]: number;
  [HISTOGRAM_COL]: number;
}> = [];

for (let i = 0; i < PERIODS; i += 1) {
  DATA.push({
    [DATE_COL]: dateFormatter.format(dates[i]),
    [CLOSE_COL]: rawCloses[i],
    [MACD_COL]: rawMacd[i],
    [SIGNAL_COL]: rawSignal[i],
    [HISTOGRAM_COL]: Number((rawMacd[i] - rawSignal[i]).toFixed(3)),
  });
}

const dateLabels = DATA.map((row) => row[DATE_COL]);
const closes = DATA.map((row) => row[CLOSE_COL]);
const macdLine = DATA.map((row) => row[MACD_COL]);
const signalLine = DATA.map((row) => row[SIGNAL_COL]);
const histogram = DATA.map((row) => row[HISTOGRAM_COL]);

let lastCrossoverIndex: number | null = null;
let crossoverCount = 0;
for (let i = 1; i < histogram.length; i += 1) {
  if (
    Math.sign(histogram[i]) !== 0 &&
    Math.sign(histogram[i]) !== Math.sign(histogram[i - 1])
  ) {
    lastCrossoverIndex = i;
    crossoverCount += 1;
  }
}

const allValues = [...macdLine, ...signalLine, ...histogram];
const rawMax = Math.max(...allValues);
const rawMin = Math.min(...allValues);
const pad = (rawMax - rawMin) * Y_PAD_SHARE;
const Y_MAX = Math.ceil((rawMax + pad) * 2) / 2;
const Y_MIN = Math.floor((rawMin - pad) * 2) / 2;

const MACD_COLOR = t.palette[2];
const SIGNAL_COLOR = t.palette[1];
const HIST_POS_COLOR = t.palette[0];
const HIST_NEG_COLOR = t.palette[4];

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const HEADER_H = 84;
  const LEGEND_H = 48;
  const chartH = H - HEADER_H - LEGEND_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        color: t.ink,
        fontFamily: t.sans,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          padding: "14px 44px 4px 104px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: t.ink,
            lineHeight: 1.2,
          }}
        >
          indicator-macd · javascript · muix · anyplot.ai
        </div>
        <div
          style={{
            fontSize: 14,
            color: t.inkSoft,
            marginTop: 4,
            fontFamily: t.mono,
          }}
        >
          MACD ({FAST_EMA_PERIOD}, {SLOW_EMA_PERIOD}, {SIGNAL_EMA_PERIOD}) over{" "}
          {PERIODS} trading days ({dateLabels[0]} to{" "}
          {dateLabels[dateLabels.length - 1]}, close $
          {closes[0].toFixed(1)} → ${closes[closes.length - 1].toFixed(1)}) ·{" "}
          {crossoverCount} signal crossovers
        </div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        margin={{ top: 20, right: 32, bottom: 16, left: 20 }}
        skipAnimation
        series={[
          {
            type: "bar",
            id: "histogram",
            yAxisId: "value-hist",
            data: histogram,
            label: HISTOGRAM_COL,
            color: HIST_NEG_COLOR,
          },
          {
            type: "line",
            id: "macd",
            yAxisId: "value",
            data: macdLine,
            label: MACD_COL,
            color: MACD_COLOR,
            showMark: false,
            curve: "linear",
          },
          {
            type: "line",
            id: "signal",
            yAxisId: "value",
            data: signalLine,
            label: SIGNAL_COL,
            color: SIGNAL_COLOR,
            showMark: false,
            curve: "linear",
          },
        ]}
        xAxis={[
          {
            id: "dates",
            scaleType: "band",
            data: dateLabels,
            height: 58,
            categoryGapRatio: 0.15,
            label: DATE_COL,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelInterval: (_value: string, index: number) =>
              index % 10 === 0,
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
            },
            disableLine: true,
          },
        ]}
        yAxis={[
          {
            id: "value",
            min: Y_MIN,
            max: Y_MAX,
            width: 84,
            label: Y_AXIS_LABEL,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
            },
            valueFormatter: (v: number) =>
              `${v >= 0 ? "+" : ""}${v.toFixed(1)}`,
            disableLine: true,
          },
          {
            id: "value-hist",
            min: Y_MIN,
            max: Y_MAX,
            position: "none",
            colorMap: {
              type: "piecewise",
              thresholds: [0],
              colors: [HIST_NEG_COLOR, HIST_POS_COLOR],
            },
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <BarPlot skipAnimation borderRadius={1} />
        <LinePlot skipAnimation />
        <ChartsReferenceLine
          y={0}
          axisId="value"
          lineStyle={{
            stroke: t.ink,
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
          }}
        />
        {lastCrossoverIndex !== null && (
          <ChartsReferenceLine
            x={dateLabels[lastCrossoverIndex]}
            axisId="dates"
            label={`Latest crossover (${dateLabels[lastCrossoverIndex]})`}
            labelAlign="start"
            labelStyle={{
              fontSize: 14,
              fill: t.ink,
              fontWeight: 600,
              fontFamily: t.mono,
            }}
            lineStyle={{
              stroke: t.inkSoft,
              strokeDasharray: "3 4",
              strokeWidth: 1.5,
              strokeOpacity: 0.75,
            }}
          />
        )}
        <ChartsXAxis axisId="dates" />
        <ChartsYAxis axisId="value" />
      </ChartsContainer>

      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 32,
          fontSize: 15,
          color: t.ink,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 24,
              height: 3,
              background: MACD_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{MACD_COL}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 24,
              height: 3,
              background: SIGNAL_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{SIGNAL_COL}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              background: HIST_POS_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{HISTOGRAM_COL} (&gt; 0, bullish)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              background: HIST_NEG_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{HISTOGRAM_COL} (&lt; 0, bearish)</span>
        </div>
      </div>
    </div>
  );
}
