// anyplot.ai
// indicator-rsi: RSI Technical Indicator Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const Y_AXIS_LABEL = "Relative Strength Index (RSI)";
const LOOKBACK = 14;
const RSI_MIN = 0;
const RSI_MAX = 100;
const OVERBOUGHT_THRESHOLD = 70;
const NEUTRAL_THRESHOLD = 50;
const OVERSOLD_THRESHOLD = 30;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const CLOSE = "Close price ($)"; // role: close
const RSI = "RSI (14-period)"; // role: rsi

// Data: replace this block with your own records
const RSI_PERIODS = 120;
let lcgState = 7;
const totalDays = RSI_PERIODS + LOOKBACK;
const isoDates: string[] = [];
const cursor = new Date(Date.UTC(2025, 0, 2));
while (isoDates.length < totalDays + 1) {
  const weekday = cursor.getUTCDay();
  if (weekday !== 0 && weekday !== 6) {
    isoDates.push(cursor.toISOString().slice(0, 10));
  }
  cursor.setUTCDate(cursor.getUTCDate() + 1);
}

const allCloses: number[] = [];
let price = 62;
for (let i = 0; i <= totalDays; i += 1) {
  const trend = 0.55 * Math.sin(i / 14) + 0.18 * Math.sin(i / 4.5);
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const r = lcgState / 4294967296;
  const noise = (r - 0.5) * 1.9;
  price += trend + noise;
  allCloses.push(price);
}

const gains: number[] = [];
const losses: number[] = [];
for (let i = 1; i < allCloses.length; i += 1) {
  const change = allCloses[i] - allCloses[i - 1];
  gains.push(Math.max(change, 0));
  losses.push(Math.max(-change, 0));
}

let avgGain =
  gains.slice(0, LOOKBACK).reduce((a, b) => a + b, 0) / LOOKBACK;
let avgLoss =
  losses.slice(0, LOOKBACK).reduce((a, b) => a + b, 0) / LOOKBACK;
const rawRsi: number[] = [
  avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss),
];

for (let i = LOOKBACK; i < gains.length; i += 1) {
  avgGain = (avgGain * (LOOKBACK - 1) + gains[i]) / LOOKBACK;
  avgLoss = (avgLoss * (LOOKBACK - 1) + losses[i]) / LOOKBACK;
  rawRsi.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
}

const visibleDates = isoDates.slice(isoDates.length - RSI_PERIODS);
const visibleCloses = allCloses.slice(allCloses.length - RSI_PERIODS);
const visibleRsi = rawRsi.slice(rawRsi.length - RSI_PERIODS);

const data: Array<{
  [DATE]: string;
  [CLOSE]: number;
  [RSI]: number;
}> = [];

for (let i = 0; i < RSI_PERIODS; i += 1) {
  data.push({
    [DATE]: visibleDates[i],
    [CLOSE]: visibleCloses[i],
    [RSI]: Number(visibleRsi[i].toFixed(2)),
  });
}

// Plot: reads only data and the constants above
const nPeriods = data.length;
const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});
const formatIsoDate = (iso: string) =>
  dateFormatter.format(new Date(`${iso}T00:00:00Z`));

const unitMatch = CLOSE.match(/\(([^)]+)\)/);
const closeUnit = unitMatch ? unitMatch[1] : "";

const dateValues = data.map((row) => row[DATE]);
const closes = data.map((row) => row[CLOSE]);
const rsiValues = data.map((row) => row[RSI]);

const overboughtPeriods = rsiValues.filter(
  (v) => v >= OVERBOUGHT_THRESHOLD,
).length;
const oversoldPeriods = rsiValues.filter(
  (v) => v <= OVERSOLD_THRESHOLD,
).length;

const RSI_COLOR = t.palette[0];
const OVERBOUGHT_COLOR = t.inkSoft;
const OVERSOLD_COLOR = t.inkSoft;

function RsiZonesLayer() {
  const { left, width } = useDrawingArea();
  const yScale = useYScale("rsi-axis") as (v: number) => number;

  const y100 = yScale(RSI_MAX);
  const y70 = yScale(OVERBOUGHT_THRESHOLD);
  const y30 = yScale(OVERSOLD_THRESHOLD);
  const y0 = yScale(RSI_MIN);

  return (
    <g>
      <rect
        x={left}
        y={y100}
        width={width}
        height={Math.max(0, y70 - y100)}
        fill={OVERBOUGHT_COLOR}
        fillOpacity={0.12}
      />
      <rect
        x={left}
        y={y30}
        width={width}
        height={Math.max(0, y0 - y30)}
        fill={OVERSOLD_COLOR}
        fillOpacity={0.12}
      />
    </g>
  );
}

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
        fontFamily: FONT,
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
          indicator-rsi · javascript · muix · anyplot.ai
        </div>
        <div
          style={{
            fontSize: 14,
            color: t.inkSoft,
            marginTop: 4,
            fontFamily: MONO,
          }}
        >
          Wilder&apos;s {LOOKBACK}-period RSI over {nPeriods} periods (
          {formatIsoDate(dateValues[0])} to{" "}
          {formatIsoDate(dateValues[dateValues.length - 1])}, close {closeUnit}
          {closes[0].toFixed(1)} → {closeUnit}
          {closes[closes.length - 1].toFixed(1)}) · {overboughtPeriods}{" "}
          overbought (&ge;{OVERBOUGHT_THRESHOLD}) &amp; {oversoldPeriods}{" "}
          oversold (&le;{OVERSOLD_THRESHOLD}) periods
        </div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        margin={{ top: 20, right: 32, bottom: 16, left: 20 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "rsi",
            yAxisId: "rsi-axis",
            data: rsiValues,
            label: RSI,
            color: RSI_COLOR,
            showMark: false,
            curve: "linear",
          },
        ]}
        xAxis={[
          {
            id: "dates",
            scaleType: "band",
            data: dateValues,
            height: 58,
            categoryGapRatio: 0.15,
            label: DATE,
            valueFormatter: (v: string) => formatIsoDate(v),
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelInterval: (_value: string, index: number) =>
              index % 10 === 0,
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            disableLine: true,
          },
        ]}
        yAxis={[
          {
            id: "rsi-axis",
            min: RSI_MIN,
            max: RSI_MAX,
            width: 84,
            tickNumber: 6,
            label: Y_AXIS_LABEL,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            disableLine: true,
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <RsiZonesLayer />
        <ChartsGrid horizontal />
        <LinePlot skipAnimation />
        <ChartsReferenceLine
          y={OVERBOUGHT_THRESHOLD}
          axisId="rsi-axis"
          label={`Overbought (${OVERBOUGHT_THRESHOLD})`}
          labelAlign="end"
          labelStyle={{
            fontSize: 14,
            fill: t.ink,
            fontWeight: 600,
            fontFamily: MONO,
          }}
          lineStyle={{
            stroke: OVERBOUGHT_COLOR,
            strokeWidth: 1.75,
            strokeDasharray: "6 4",
          }}
        />
        <ChartsReferenceLine
          y={NEUTRAL_THRESHOLD}
          axisId="rsi-axis"
          label={`Neutral (${NEUTRAL_THRESHOLD})`}
          labelAlign="end"
          labelStyle={{
            fontSize: 14,
            fill: t.inkSoft,
            fontWeight: 600,
            fontFamily: MONO,
          }}
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "4 4",
            strokeOpacity: 0.65,
          }}
        />
        <ChartsReferenceLine
          y={OVERSOLD_THRESHOLD}
          axisId="rsi-axis"
          label={`Oversold (${OVERSOLD_THRESHOLD})`}
          labelAlign="end"
          labelStyle={{
            fontSize: 14,
            fill: t.ink,
            fontWeight: 600,
            fontFamily: MONO,
          }}
          lineStyle={{
            stroke: OVERSOLD_COLOR,
            strokeWidth: 1.75,
            strokeDasharray: "6 4",
          }}
        />
        <ChartsXAxis axisId="dates" />
        <ChartsYAxis axisId="rsi-axis" />
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
              background: RSI_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{RSI}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 16,
              height: 14,
              background: `${OVERBOUGHT_COLOR}48`,
              border: `1.5px dashed ${OVERBOUGHT_COLOR}`,
              borderRadius: 2,
              display: "inline-block",
              boxSizing: "border-box",
            }}
          />
          <span>Overbought zone (&gt; {OVERBOUGHT_THRESHOLD})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 16,
              height: 14,
              background: `${OVERSOLD_COLOR}48`,
              border: `1.5px dashed ${OVERSOLD_COLOR}`,
              borderRadius: 2,
              display: "inline-block",
              boxSizing: "border-box",
            }}
          />
          <span>Oversold zone (&lt; {OVERSOLD_THRESHOLD})</span>
        </div>
      </div>
    </div>
  );
}
