// anyplot.ai
// indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const TENKAN_PERIOD = 9;
const KIJUN_PERIOD = 26;
const SENKOU_B_PERIOD = 52;
const DISPLACEMENT = 26;
const Y_PAD_SHARE = 0.08;
const BODY_WIDTH_SHARE = 0.72;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const OPEN = "Open price (USD)"; // role: open
const HIGH = "High price (USD)"; // role: high
const LOW = "Low price (USD)"; // role: low
const CLOSE = "Close price (USD)"; // role: close
const TENKAN_SEN = "Tenkan-sen (9)"; // role: tenkan_sen
const KIJUN_SEN = "Kijun-sen (26)"; // role: kijun_sen
const SENKOU_SPAN_A = "Senkou Span A (+26)"; // role: senkou_span_a
const SENKOU_SPAN_B = "Senkou Span B (52, +26)"; // role: senkou_span_b
const CHIKOU_SPAN = "Chikou Span (-26)"; // role: chikou_span

// Data: replace this block with your own records
const HISTORY_PERIODS = 130;
const TOTAL_PERIODS = HISTORY_PERIODS + DISPLACEMENT;

let seed = 42;
const rawOpen: number[] = [];
const rawHigh: number[] = [];
const rawLow: number[] = [];
const rawClose: number[] = [];

let currentPrice = 148;
for (let i = 0; i < HISTORY_PERIODS; i += 1) {
  const o = currentPrice;
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const r1 = seed / 0x7fffffff;
  const drift = (r1 - 0.47) * 2.4;
  const c = Math.max(40, o + drift);

  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const r2 = seed / 0x7fffffff;
  const h = Math.max(o, c) + r2 * 1.6;

  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const r3 = seed / 0x7fffffff;
  const l = Math.max(Math.min(o, c) - r3 * 1.6, 1);

  rawOpen.push(o);
  rawClose.push(c);
  rawHigh.push(h);
  rawLow.push(l);
  currentPrice = c;
}

// Rolling (highest high + lowest low) / 2 over `period` bars
const rollingMidpoint = (period: number): Array<number | null> =>
  rawHigh.map((_, i) =>
    i < period - 1
      ? null
      : (Math.max(...rawHigh.slice(i - period + 1, i + 1)) +
          Math.min(...rawLow.slice(i - period + 1, i + 1))) /
        2,
  );

const tenkanRaw = rollingMidpoint(TENKAN_PERIOD);
const kijunRaw = rollingMidpoint(KIJUN_PERIOD);
const spanBRaw = rollingMidpoint(SENKOU_B_PERIOD);
const spanARaw = tenkanRaw.map((tk, i) =>
  tk !== null && kijunRaw[i] !== null ? (tk + kijunRaw[i]!) / 2 : null,
);

const isoDates: string[] = [];
let cursorMs = Date.UTC(2024, 0, 2);
while (isoDates.length < TOTAL_PERIODS) {
  const dt = new Date(cursorMs);
  const utcDay = dt.getUTCDay();
  if (utcDay !== 0 && utcDay !== 6) {
    isoDates.push(dt.toISOString().slice(0, 10));
  }
  cursorMs += 86400000;
}

const data: Array<{
  [DATE]: string;
  [OPEN]: number | null;
  [HIGH]: number | null;
  [LOW]: number | null;
  [CLOSE]: number | null;
  [TENKAN_SEN]: number | null;
  [KIJUN_SEN]: number | null;
  [SENKOU_SPAN_A]: number | null;
  [SENKOU_SPAN_B]: number | null;
  [CHIKOU_SPAN]: number | null;
}> = [];

for (let i = 0; i < TOTAL_PERIODS; i += 1) {
  const inHistory = i < HISTORY_PERIODS;
  const srcIdx = i - DISPLACEMENT;
  const chikouIdx = i + DISPLACEMENT;

  data.push({
    [DATE]: isoDates[i],
    [OPEN]: inHistory ? rawOpen[i] : null,
    [HIGH]: inHistory ? rawHigh[i] : null,
    [LOW]: inHistory ? rawLow[i] : null,
    [CLOSE]: inHistory ? rawClose[i] : null,
    [TENKAN_SEN]: inHistory ? tenkanRaw[i] : null,
    [KIJUN_SEN]: inHistory ? kijunRaw[i] : null,
    [SENKOU_SPAN_A]:
      srcIdx >= 0 && srcIdx < HISTORY_PERIODS ? spanARaw[srcIdx] : null,
    [SENKOU_SPAN_B]:
      srcIdx >= 0 && srcIdx < HISTORY_PERIODS ? spanBRaw[srcIdx] : null,
    [CHIKOU_SPAN]: chikouIdx < HISTORY_PERIODS ? rawClose[chikouIdx] : null,
  });
}

// Plot: reads only data and the constants above
const totalPeriods = data.length;
const dateFormat = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});
const formatIsoDate = (iso: string) =>
  dateFormat.format(new Date(`${iso}T00:00:00Z`));

const dateValues = data.map((row) => row[DATE]);
const openArr = data.map((row) => row[OPEN]);
const highArr = data.map((row) => row[HIGH]);
const lowArr = data.map((row) => row[LOW]);
const closeArr = data.map((row) => row[CLOSE]);
const tenkanArr = data.map((row) => row[TENKAN_SEN]);
const kijunArr = data.map((row) => row[KIJUN_SEN]);
const spanAArr = data.map((row) => row[SENKOU_SPAN_A]);
const spanBArr = data.map((row) => row[SENKOU_SPAN_B]);
const chikouArr = data.map((row) => row[CHIKOU_SPAN]);

const historyDates = data
  .filter((row) => row[CLOSE] !== null)
  .map((row) => row[DATE]);
const historyCount = historyDates.length;
const firstHistoryDate = formatIsoDate(historyDates[0]);
const lastHistoryDate = formatIsoDate(historyDates[historyCount - 1]);

const definedValues = [
  ...highArr,
  ...lowArr,
  ...spanAArr,
  ...spanBArr,
  ...tenkanArr,
  ...kijunArr,
  ...chikouArr,
].filter((v): v is number => v !== null);

const minPrice = Math.min(...definedValues);
const maxPrice = Math.max(...definedValues);
const pricePad = (maxPrice - minPrice) * Y_PAD_SHARE;
const yMin = minPrice - pricePad;
const yMax = maxPrice + pricePad;

// Precompute Kumo segments with exact crossover interpolation
const kumoSegments: Array<{
  bullish: boolean;
  spanAPts: Array<{ idx: number; val: number }>;
  spanBPts: Array<{ idx: number; val: number }>;
}> = [];

let curBullish: boolean | null = null;
let curSpanA: Array<{ idx: number; val: number }> = [];
let curSpanB: Array<{ idx: number; val: number }> = [];

for (let j = 0; j < totalPeriods; j += 1) {
  const a = spanAArr[j];
  const b = spanBArr[j];
  if (a === null || b === null) {
    if (curSpanA.length > 1 && curBullish !== null) {
      kumoSegments.push({
        bullish: curBullish,
        spanAPts: curSpanA,
        spanBPts: curSpanB,
      });
    }
    curBullish = null;
    curSpanA = [];
    curSpanB = [];
    continue;
  }

  const up = a >= b;
  if (curBullish === null) {
    curBullish = up;
    curSpanA = [{ idx: j, val: a }];
    curSpanB = [{ idx: j, val: b }];
  } else if (up === curBullish) {
    curSpanA.push({ idx: j, val: a });
    curSpanB.push({ idx: j, val: b });
  } else {
    const prevA = curSpanA[curSpanA.length - 1].val;
    const prevB = curSpanB[curSpanB.length - 1].val;
    const prevDiff = prevA - prevB;
    const curDiff = a - b;
    const frac =
      prevDiff - curDiff !== 0 ? prevDiff / (prevDiff - curDiff) : 0.5;
    const crossIdx = j - 1 + frac;
    const crossVal = prevA + frac * (a - prevA);

    curSpanA.push({ idx: crossIdx, val: crossVal });
    curSpanB.push({ idx: crossIdx, val: crossVal });
    kumoSegments.push({
      bullish: curBullish,
      spanAPts: curSpanA,
      spanBPts: curSpanB,
    });

    curBullish = up;
    curSpanA = [
      { idx: crossIdx, val: crossVal },
      { idx: j, val: a },
    ];
    curSpanB = [
      { idx: crossIdx, val: crossVal },
      { idx: j, val: b },
    ];
  }
}
if (curSpanA.length > 1 && curBullish !== null) {
  kumoSegments.push({
    bullish: curBullish,
    spanAPts: curSpanA,
    spanBPts: curSpanB,
  });
}

const BULL_COLOR = t.palette[0];
const BEAR_COLOR = t.palette[4];
const TENKAN_COLOR = t.palette[1];
const KIJUN_COLOR = t.palette[2];
const CHIKOU_COLOR = t.palette[3];

const lineSwatch = (color: string, thickness: number, dashed = false) => ({
  width: 20,
  height: 0,
  borderTop: `${thickness}px ${dashed ? "dashed" : "solid"} ${color}`,
});
const boxSwatch = (fill: string, border: string) => ({
  width: 14,
  height: 14,
  background: fill,
  border,
  borderRadius: 2,
});

const legendItems = [
  {
    label: "Bullish candle",
    swatch: boxSwatch(t.pageBg, `2px solid ${BULL_COLOR}`),
  },
  { label: "Bearish candle", swatch: boxSwatch(BEAR_COLOR, "none") },
  { label: TENKAN_SEN, swatch: lineSwatch(TENKAN_COLOR, 3) },
  { label: KIJUN_SEN, swatch: lineSwatch(KIJUN_COLOR, 3) },
  { label: SENKOU_SPAN_A, swatch: lineSwatch(BULL_COLOR, 2) },
  { label: SENKOU_SPAN_B, swatch: lineSwatch(BEAR_COLOR, 2, true) },
  { label: CHIKOU_SPAN, swatch: lineSwatch(CHIKOU_COLOR, 2.5, true) },
  {
    label: "Kumo bullish (A > B)",
    swatch: boxSwatch(`${BULL_COLOR}48`, `1.5px solid ${BULL_COLOR}`),
  },
  {
    label: "Kumo bearish (B > A)",
    swatch: boxSwatch(`${BEAR_COLOR}48`, `1.5px dashed ${BEAR_COLOR}`),
  },
];

function IchimokuLayer() {
  const xScale = useXScale("x") as unknown as ((v: string) => number) & {
    bandwidth: () => number;
  };
  const yScale = useYScale("y") as (v: number) => number;

  const bw = xScale.bandwidth();
  const bodyWidth = bw * BODY_WIDTH_SHARE;
  const xZero = xScale(dateValues[0]) + bw / 2;
  const xOne = xScale(dateValues[1]) + bw / 2;
  const stepX = xOne - xZero;
  const isDark = window.ANYPLOT_THEME === "dark";

  const chikouPoints: string[] = [];
  for (let i = 0; i < totalPeriods; i += 1) {
    if (chikouArr[i] !== null) {
      chikouPoints.push(
        `${xZero + i * stepX},${yScale(chikouArr[i]!)}`,
      );
    }
  }

  return (
    <g>
      {/* Kumo cloud */}
      {kumoSegments.map((seg, s) => {
        const fillColor = seg.bullish ? BULL_COLOR : BEAR_COLOR;
        const fillOpacity = seg.bullish ? 0.22 : isDark ? 0.34 : 0.24;
        const spanALine = seg.spanAPts.map(
          (p) => `${xZero + p.idx * stepX},${yScale(p.val)}`,
        );
        const spanBPolyRev = seg.spanBPts
          .slice()
          .reverse()
          .map((p) => `${xZero + p.idx * stepX},${yScale(p.val)}`);
        const spanBLine = seg.spanBPts.map(
          (p) => `${xZero + p.idx * stepX},${yScale(p.val)}`,
        );

        return (
          <g key={`kumo-${s}`}>
            <polygon
              points={[...spanALine, ...spanBPolyRev].join(" ")}
              fill={fillColor}
              fillOpacity={fillOpacity}
            />
            <polyline
              points={spanALine.join(" ")}
              fill="none"
              stroke={BULL_COLOR}
              strokeOpacity={0.85}
              strokeWidth={1.6}
            />
            <polyline
              points={spanBLine.join(" ")}
              fill="none"
              stroke={BEAR_COLOR}
              strokeOpacity={0.85}
              strokeWidth={1.6}
              strokeDasharray="6 4"
            />
          </g>
        );
      })}

      {/* Candlesticks */}
      {data.map((row, i) => {
        const o = row[OPEN];
        const h = row[HIGH];
        const l = row[LOW];
        const c = row[CLOSE];
        if (o === null || h === null || l === null || c === null) return null;

        const cx = xZero + i * stepX;
        const bullish = c >= o;
        const color = bullish ? BULL_COLOR : BEAR_COLOR;
        const yO = yScale(o);
        const yC = yScale(c);
        const bodyTop = Math.min(yO, yC);
        const bodyHeight = Math.max(Math.abs(yC - yO), 1.5);

        return (
          <g key={`candle-${i}`}>
            <line
              x1={cx}
              x2={cx}
              y1={yScale(h)}
              y2={yScale(l)}
              stroke={color}
              strokeWidth={1.5}
            />
            <rect
              x={cx - bodyWidth / 2}
              y={bodyTop}
              width={bodyWidth}
              height={bodyHeight}
              fill={bullish ? t.pageBg : color}
              stroke={color}
              strokeWidth={bullish ? 2 : 0}
            />
          </g>
        );
      })}

      {/* Dashed Chikou Span (-26 periods) */}
      <polyline
        points={chikouPoints.join(" ")}
        fill="none"
        stroke={CHIKOU_COLOR}
        strokeWidth={2.4}
        strokeDasharray="7 5"
      />
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const HEADER_H = 84;
  const LEGEND_H = 54;
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
          indicator-ichimoku · javascript · muix · anyplot.ai
        </div>
        <div
          style={{
            fontSize: 14,
            color: t.inkSoft,
            marginTop: 4,
            fontFamily: MONO,
          }}
        >
          Ichimoku Kinko Hyo ({TENKAN_PERIOD}, {KIJUN_PERIOD}, {SENKOU_B_PERIOD}
          ) · {historyCount} trading periods ({firstHistoryDate} to{" "}
          {lastHistoryDate}) + {totalPeriods - historyCount}-period Kumo cloud
          projection
        </div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        margin={{ top: 16, right: 32, bottom: 16, left: 20 }}
        series={[
          {
            type: "line",
            id: "tenkan",
            xAxisId: "x",
            yAxisId: "y",
            data: tenkanArr,
            label: TENKAN_SEN,
            color: TENKAN_COLOR,
            showMark: false,
            curve: "linear",
            connectNulls: false,
          },
          {
            type: "line",
            id: "kijun",
            xAxisId: "x",
            yAxisId: "y",
            data: kijunArr,
            label: KIJUN_SEN,
            color: KIJUN_COLOR,
            showMark: false,
            curve: "linear",
            connectNulls: false,
          },
        ]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: dateValues,
            height: 58,
            label: DATE,
            valueFormatter: (v: string) => formatIsoDate(v),
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelInterval: (_value: string, index: number) =>
              index % 13 === 0,
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: yMin,
            max: yMax,
            width: 84,
            label: CLOSE,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <IchimokuLayer />
        <LinePlot skipAnimation />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>

      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 18,
          fontSize: 13,
          color: t.ink,
          flexWrap: "wrap",
          padding: "0 20px",
          boxSizing: "border-box",
        }}
      >
        {legendItems.map((item) => (
          <div
            key={item.label}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <span
              style={{
                ...item.swatch,
                display: "inline-block",
                boxSizing: "border-box",
              }}
            />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
