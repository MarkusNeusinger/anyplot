// anyplot.ai
// indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DATE_COL = "Trading Date";
const OPEN_COL = "Open Price (USD)";
const HIGH_COL = "High Price (USD)";
const LOW_COL = "Low Price (USD)";
const CLOSE_COL = "Close Price (USD)";
const TENKAN_COL = "Tenkan-sen (9)";
const KIJUN_COL = "Kijun-sen (26)";
const SPAN_A_COL = "Senkou Span A (+26)";
const SPAN_B_COL = "Senkou Span B (52, +26)";
const CHIKOU_COL = "Chikou Span (-26)";
const Y_AXIS_LABEL = "Price (USD)";

const HISTORY_PERIODS = 130;
const TENKAN_PERIOD = 9;
const KIJUN_PERIOD = 26;
const SENKOU_B_PERIOD = 52;
const DISPLACEMENT = 26;
const TOTAL_PERIODS = HISTORY_PERIODS + DISPLACEMENT;
const Y_PAD_SHARE = 0.08;
const BODY_WIDTH_SHARE = 0.72;

// Data: deterministic LCG daily OHLC prices + standard Ichimoku (9, 26, 52)
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

const tenkanRaw: Array<number | null> = [];
const kijunRaw: Array<number | null> = [];
const spanARaw: Array<number | null> = [];
const spanBRaw: Array<number | null> = [];

for (let i = 0; i < HISTORY_PERIODS; i += 1) {
  if (i < TENKAN_PERIOD - 1) {
    tenkanRaw.push(null);
  } else {
    let hh = -Infinity;
    let ll = Infinity;
    for (let k = i - TENKAN_PERIOD + 1; k <= i; k += 1) {
      if (rawHigh[k] > hh) hh = rawHigh[k];
      if (rawLow[k] < ll) ll = rawLow[k];
    }
    tenkanRaw.push((hh + ll) / 2);
  }

  if (i < KIJUN_PERIOD - 1) {
    kijunRaw.push(null);
  } else {
    let hh = -Infinity;
    let ll = Infinity;
    for (let k = i - KIJUN_PERIOD + 1; k <= i; k += 1) {
      if (rawHigh[k] > hh) hh = rawHigh[k];
      if (rawLow[k] < ll) ll = rawLow[k];
    }
    kijunRaw.push((hh + ll) / 2);
  }

  if (tenkanRaw[i] !== null && kijunRaw[i] !== null) {
    spanARaw.push((tenkanRaw[i]! + kijunRaw[i]!) / 2);
  } else {
    spanARaw.push(null);
  }

  if (i < SENKOU_B_PERIOD - 1) {
    spanBRaw.push(null);
  } else {
    let hh = -Infinity;
    let ll = Infinity;
    for (let k = i - SENKOU_B_PERIOD + 1; k <= i; k += 1) {
      if (rawHigh[k] > hh) hh = rawHigh[k];
      if (rawLow[k] < ll) ll = rawLow[k];
    }
    spanBRaw.push((hh + ll) / 2);
  }
}

const startMs = Date.UTC(2024, 0, 2);
const dateFormat = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

const DATA: Array<{
  [DATE_COL]: string;
  [OPEN_COL]: number | null;
  [HIGH_COL]: number | null;
  [LOW_COL]: number | null;
  [CLOSE_COL]: number | null;
  [TENKAN_COL]: number | null;
  [KIJUN_COL]: number | null;
  [SPAN_A_COL]: number | null;
  [SPAN_B_COL]: number | null;
  [CHIKOU_COL]: number | null;
}> = [];

for (let i = 0; i < TOTAL_PERIODS; i += 1) {
  const d = new Date(startMs + i * 86400000);
  const label = dateFormat.format(d);
  const inHistory = i < HISTORY_PERIODS;
  const srcIdx = i - DISPLACEMENT;
  const chikouIdx = i + DISPLACEMENT;

  DATA.push({
    [DATE_COL]: label,
    [OPEN_COL]: inHistory ? rawOpen[i] : null,
    [HIGH_COL]: inHistory ? rawHigh[i] : null,
    [LOW_COL]: inHistory ? rawLow[i] : null,
    [CLOSE_COL]: inHistory ? rawClose[i] : null,
    [TENKAN_COL]: inHistory ? tenkanRaw[i] : null,
    [KIJUN_COL]: inHistory ? kijunRaw[i] : null,
    [SPAN_A_COL]:
      srcIdx >= 0 && srcIdx < HISTORY_PERIODS ? spanARaw[srcIdx] : null,
    [SPAN_B_COL]:
      srcIdx >= 0 && srcIdx < HISTORY_PERIODS ? spanBRaw[srcIdx] : null,
    [CHIKOU_COL]: chikouIdx < HISTORY_PERIODS ? rawClose[chikouIdx] : null,
  });
}

const dateLabels = DATA.map((row) => row[DATE_COL]);
const openArr = DATA.map((row) => row[OPEN_COL]);
const highArr = DATA.map((row) => row[HIGH_COL]);
const lowArr = DATA.map((row) => row[LOW_COL]);
const closeArr = DATA.map((row) => row[CLOSE_COL]);
const tenkanArr = DATA.map((row) => row[TENKAN_COL]);
const kijunArr = DATA.map((row) => row[KIJUN_COL]);
const spanAArr = DATA.map((row) => row[SPAN_A_COL]);
const spanBArr = DATA.map((row) => row[SPAN_B_COL]);
const chikouArr = DATA.map((row) => row[CHIKOU_COL]);

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
const yMin = Math.floor(minPrice - pricePad);
const yMax = Math.ceil(maxPrice + pricePad);

// Precompute Kumo segments with exact crossover interpolation
const kumoSegments: Array<{
  bullish: boolean;
  topPts: Array<{ idx: number; val: number }>;
  botPts: Array<{ idx: number; val: number }>;
}> = [];

let curBullish: boolean | null = null;
let curTop: Array<{ idx: number; val: number }> = [];
let curBot: Array<{ idx: number; val: number }> = [];

for (let j = 0; j < TOTAL_PERIODS; j += 1) {
  const a = spanAArr[j];
  const b = spanBArr[j];
  if (a === null || b === null) {
    if (curTop.length > 1 && curBullish !== null) {
      kumoSegments.push({
        bullish: curBullish,
        topPts: curTop,
        botPts: curBot,
      });
    }
    curBullish = null;
    curTop = [];
    curBot = [];
    continue;
  }

  const up = a >= b;
  if (curBullish === null) {
    curBullish = up;
    curTop = [{ idx: j, val: a }];
    curBot = [{ idx: j, val: b }];
  } else if (up === curBullish) {
    curTop.push({ idx: j, val: a });
    curBot.push({ idx: j, val: b });
  } else {
    const prevA = curTop[curTop.length - 1].val;
    const prevB = curBot[curBot.length - 1].val;
    const prevDiff = prevA - prevB;
    const curDiff = a - b;
    const frac =
      prevDiff - curDiff !== 0 ? prevDiff / (prevDiff - curDiff) : 0.5;
    const crossIdx = j - 1 + frac;
    const crossVal = prevA + frac * (a - prevA);

    curTop.push({ idx: crossIdx, val: crossVal });
    curBot.push({ idx: crossIdx, val: crossVal });
    kumoSegments.push({
      bullish: curBullish,
      topPts: curTop,
      botPts: curBot,
    });

    curBullish = up;
    curTop = [
      { idx: crossIdx, val: crossVal },
      { idx: j, val: a },
    ];
    curBot = [
      { idx: crossIdx, val: crossVal },
      { idx: j, val: b },
    ];
  }
}
if (curTop.length > 1 && curBullish !== null) {
  kumoSegments.push({
    bullish: curBullish,
    topPts: curTop,
    botPts: curBot,
  });
}

const BULL_COLOR = t.palette[0];
const BEAR_COLOR = t.palette[4];
const TENKAN_COLOR = t.palette[1];
const KIJUN_COLOR = t.palette[2];
const CHIKOU_COLOR = t.palette[3];

function IchimokuLayer() {
  const xScale = useXScale("x") as unknown as ((v: string) => number) & {
    bandwidth: () => number;
  };
  const yScale = useYScale("y") as (v: number) => number;
  if (!xScale || !yScale) return null;

  const bw = xScale.bandwidth();
  const bodyWidth = bw * BODY_WIDTH_SHARE;
  const xZero = xScale(dateLabels[0]) + bw / 2;
  const xOne = xScale(dateLabels[1]) + bw / 2;
  const stepX = xOne - xZero;
  const isDark = window.ANYPLOT_THEME === "dark";

  const chikouPoints: string[] = [];
  for (let i = 0; i < TOTAL_PERIODS; i += 1) {
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
        const color = seg.bullish ? BULL_COLOR : BEAR_COLOR;
        const fillOpacity = seg.bullish ? 0.22 : isDark ? 0.34 : 0.24;
        const dash = seg.bullish ? undefined : "6 4";
        const topPoly = seg.topPts.map(
          (p) => `${xZero + p.idx * stepX},${yScale(p.val)}`,
        );
        const botPoly = seg.botPts
          .slice()
          .reverse()
          .map((p) => `${xZero + p.idx * stepX},${yScale(p.val)}`);
        const botLine = seg.botPts.map(
          (p) => `${xZero + p.idx * stepX},${yScale(p.val)}`,
        );

        return (
          <g key={`kumo-${s}`}>
            <polygon
              points={[...topPoly, ...botPoly].join(" ")}
              fill={color}
              fillOpacity={fillOpacity}
            />
            <polyline
              points={topPoly.join(" ")}
              fill="none"
              stroke={color}
              strokeOpacity={0.62}
              strokeWidth={1.35}
              strokeDasharray={dash}
            />
            <polyline
              points={botLine.join(" ")}
              fill="none"
              stroke={color}
              strokeOpacity={0.62}
              strokeWidth={1.35}
              strokeDasharray={dash}
            />
          </g>
        );
      })}

      {/* Candlesticks */}
      {DATA.map((row, i) => {
        const o = row[OPEN_COL];
        const h = row[HIGH_COL];
        const l = row[LOW_COL];
        const c = row[CLOSE_COL];
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
          TechCo Daily Price · indicator-ichimoku · javascript · muix ·
          anyplot.ai
        </div>
        <div
          style={{
            fontSize: 14,
            color: t.inkSoft,
            marginTop: 4,
            fontFamily: t.mono,
          }}
        >
          Ichimoku Kinko Hyo ({TENKAN_PERIOD}, {KIJUN_PERIOD}, {SENKOU_B_PERIOD}
          ) · {HISTORY_PERIODS} trading days ({dateLabels[0]} to{" "}
          {dateLabels[HISTORY_PERIODS - 1]}) + {DISPLACEMENT}-period Kumo cloud
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
            label: TENKAN_COL,
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
            label: KIJUN_COL,
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
            data: dateLabels,
            height: 58,
            label: DATE_COL,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            tickLabelInterval: (_value: string, index: number) =>
              index % 13 === 0,
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
            },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: yMin,
            max: yMax,
            width: 84,
            label: Y_AXIS_LABEL,
            labelStyle: { fontSize: 15, fill: t.ink, fontWeight: 600 },
            valueFormatter: (v: number) => `$${v.toFixed(0)}`,
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
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
          gap: 24,
          fontSize: 14,
          color: t.ink,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              background: t.pageBg,
              border: `2px solid ${BULL_COLOR}`,
              borderRadius: 2,
              display: "inline-block",
              boxSizing: "border-box",
            }}
          />
          <span>Bullish Candle</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              background: BEAR_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>Bearish Candle</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 22,
              height: 3,
              background: TENKAN_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{TENKAN_COL}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 22,
              height: 3,
              background: KIJUN_COLOR,
              borderRadius: 2,
              display: "inline-block",
            }}
          />
          <span>{KIJUN_COL}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 22,
              height: 0,
              borderTop: `2.5px dashed ${CHIKOU_COLOR}`,
              display: "inline-block",
            }}
          />
          <span>{CHIKOU_COL}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 18,
              height: 14,
              background: `${BULL_COLOR}48`,
              border: `1.5px solid ${BULL_COLOR}`,
              borderRadius: 2,
              display: "inline-block",
              boxSizing: "border-box",
            }}
          />
          <span>Kumo Bullish ({SPAN_A_COL} &gt; B)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 18,
              height: 14,
              background: `${BEAR_COLOR}48`,
              border: `1.5px dashed ${BEAR_COLOR}`,
              borderRadius: 2,
              display: "inline-block",
              boxSizing: "border-box",
            }}
          />
          <span>Kumo Bearish ({SPAN_B_COL} &gt; A)</span>
        </div>
      </div>
    </div>
  );
}
