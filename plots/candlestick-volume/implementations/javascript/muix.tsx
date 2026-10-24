// anyplot.ai
// candlestick-volume: Stock Candlestick Chart with Volume
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PRICE_PAD_SHARE = 0.08;
const VOL_PAD_SHARE = 0.15;
const BODY_WIDTH_SHARE = 0.62;
const X_TICK_COUNT = 10; // about this many labelled date ticks, shared by both panes
const HEADER_H = 120;
const PANE_GAP = 10;
const PRICE_PANE_SHARE = 0.72;
const MARGIN_LEFT = 24;
const MARGIN_RIGHT = 32;
const Y_AXIS_W = 96;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const OPEN = "Open price ($)"; // role: open
const HIGH = "High price ($)"; // role: high
const LOW = "Low price ($)"; // role: low
const CLOSE = "Close price ($)"; // role: close
const VOLUME = "Volume"; // role: volume

// Data: replace this block with your own records, one object per row
const data = (() => {
  let seed = 11;
  const periods = 60;
  const day = new Date(Date.UTC(2024, 1, 1));
  const rows: { [key: string]: string | number }[] = [];
  let price = 148;

  for (let i = 0; i < periods; i += 1) {
    const o = price;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u1 = seed / 0x7fffffff;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u2 = seed / 0x7fffffff;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u3 = seed / 0x7fffffff;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u4 = seed / 0x7fffffff;

    const drift = (u1 - 0.5) * 6.2;
    const c = Math.max(20, o + drift);
    const h = Math.max(o, c) + u2 * 2.4;
    const l = Math.max(Math.min(o, c) - u3 * 2.4, 1);
    const move = Math.abs(c - o) + (h - l);
    const vol = Math.round(1.4e6 + move * 3.6e5 + u4 * 6e5);

    // Markets close on weekends: advance to the next weekday
    while (day.getUTCDay() === 0 || day.getUTCDay() === 6) {
      day.setUTCDate(day.getUTCDate() + 1);
    }
    rows.push({
      [DATE]: day.toISOString().split("T")[0],
      [OPEN]: Math.round(o * 100) / 100,
      [HIGH]: Math.round(h * 100) / 100,
      [LOW]: Math.round(l * 100) / 100,
      [CLOSE]: Math.round(c * 100) / 100,
      [VOLUME]: vol,
    });
    day.setUTCDate(day.getUTCDate() + 1);
    price = c;
  }
  return rows;
})();

// Plot: reads only data and the constants above
const sorted = [...data].sort(
  (a, b) =>
    new Date(String(a[DATE])).getTime() - new Date(String(b[DATE])).getTime(),
);

const candles = sorted.map((r, idx) => {
  const dt = new Date(`${String(r[DATE])}T00:00:00Z`);
  const shortDate = dt.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
  const fullDate = dt.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
  return {
    idx,
    key: `${String(r[DATE])}-${idx}`,
    bandKey: `${shortDate}#${idx}`,
    shortDate,
    fullDate,
    open: Number(r[OPEN]),
    high: Number(r[HIGH]),
    low: Number(r[LOW]),
    close: Number(r[CLOSE]),
    volume: Number(r[VOLUME]),
  };
});

const bandKeys = candles.map((c) => c.bandKey);
const shortDateByBand = Object.fromEntries(
  candles.map((c) => [c.bandKey, c.shortDate]),
);
const tickEvery = Math.ceil(candles.length / X_TICK_COUNT);
const showTick = (_v: string, idx: number) => idx % tickEvery === 0;
const formatPrice = (v: number) => v.toFixed(2);
const formatVolume = (v: number) =>
  v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${Math.round(v / 1e3)}K`;

const priceMinRaw = Math.min(...candles.map((c) => c.low));
const priceMaxRaw = Math.max(...candles.map((c) => c.high));
const priceSpan = priceMaxRaw - priceMinRaw || 1;
const priceMin = priceMinRaw - priceSpan * PRICE_PAD_SHARE;
const priceMax = priceMaxRaw + priceSpan * PRICE_PAD_SHARE;

const volumeMaxRaw = Math.max(...candles.map((c) => c.volume)) || 1;
const volumeMax = volumeMaxRaw * (1 + VOL_PAD_SHARE);

const bullishCount = candles.filter((c) => c.close >= c.open).length;
const bearishCount = candles.length - bullishCount;

const TITLE = "candlestick-volume · javascript · muix · anyplot.ai";
const SUBTITLE = `${candles.length} periods (${candles[0].shortDate} – ${candles[candles.length - 1].fullDate}) · Price ${formatPrice(priceMinRaw)}–${formatPrice(priceMaxRaw)}`;
const BEAR_HATCH = `repeating-linear-gradient(135deg, color-mix(in srgb, ${t.ink} 38%, transparent) 0 1.5px, transparent 1.5px 5px)`;

function CandlesticksLayer({ activeIdx }: { activeIdx: number | null }) {
  const xScale = useXScale("xPrice");
  const yScale = useYScale("yPrice");
  const { top, height } = useDrawingArea();
  const bw = xScale.bandwidth();
  const bodyWidth = bw * BODY_WIDTH_SHARE;

  return (
    <g>
      <defs>
        <pattern
          id="candle-bear-hatch"
          width={5}
          height={5}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <line
            x1={0}
            y1={0}
            x2={0}
            y2={5}
            stroke={t.ink}
            strokeOpacity={0.38}
            strokeWidth={1.5}
          />
        </pattern>
      </defs>
      {activeIdx !== null && (
        <line
          x1={xScale(candles[activeIdx].bandKey) + bw / 2}
          x2={xScale(candles[activeIdx].bandKey) + bw / 2}
          y1={top}
          y2={top + height}
          stroke={t.inkSoft}
          strokeWidth={1.5}
          strokeDasharray="4 4"
          opacity={0.75}
        />
      )}
      {candles.map((c) => {
        const yOpen = yScale(c.open);
        const yClose = yScale(c.close);
        const cx = xScale(c.bandKey) + bw / 2;
        const bullish = c.close >= c.open;
        const color = bullish ? t.palette[0] : t.palette[4];
        const bodyTop = Math.min(yOpen, yClose);
        const bodyHeight = Math.max(Math.abs(yClose - yOpen), 2);
        return (
          <g key={c.key}>
            <line
              x1={cx}
              x2={cx}
              y1={yScale(c.high)}
              y2={yScale(c.low)}
              stroke={color}
              strokeWidth={1.5}
              strokeLinecap="round"
            />
            <rect
              x={cx - bodyWidth / 2}
              y={bodyTop}
              width={bodyWidth}
              height={bodyHeight}
              fill={color}
              stroke={t.ink}
              strokeOpacity={bullish ? 0.3 : 0.55}
              strokeWidth={bullish ? 1 : 1.6}
            />
            {!bullish && (
              <rect
                x={cx - bodyWidth / 2}
                y={bodyTop}
                width={bodyWidth}
                height={bodyHeight}
                fill="url(#candle-bear-hatch)"
                pointerEvents="none"
              />
            )}
          </g>
        );
      })}
    </g>
  );
}

function VolumeBarsLayer({ activeIdx }: { activeIdx: number | null }) {
  const xScale = useXScale("xVolume");
  const yScale = useYScale("yVolume");
  const { top, height } = useDrawingArea();
  const bw = xScale.bandwidth();
  const barWidth = bw * BODY_WIDTH_SHARE;
  const yZero = yScale(0);

  return (
    <g>
      <defs>
        <pattern
          id="volume-bear-hatch"
          width={5}
          height={5}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <line
            x1={0}
            y1={0}
            x2={0}
            y2={5}
            stroke={t.ink}
            strokeOpacity={0.38}
            strokeWidth={1.5}
          />
        </pattern>
      </defs>
      {activeIdx !== null && (
        <line
          x1={xScale(candles[activeIdx].bandKey) + bw / 2}
          x2={xScale(candles[activeIdx].bandKey) + bw / 2}
          y1={top}
          y2={top + height}
          stroke={t.inkSoft}
          strokeWidth={1.5}
          strokeDasharray="4 4"
          opacity={0.75}
        />
      )}
      {candles.map((c) => {
        const yTop = yScale(c.volume);
        const bullish = c.close >= c.open;
        const color = bullish ? t.palette[0] : t.palette[4];
        const cx = xScale(c.bandKey) + bw / 2;
        const barHeight = Math.max(yZero - yTop, 1.5);
        return (
          <g key={c.key}>
            <rect
              x={cx - barWidth / 2}
              y={yTop}
              width={barWidth}
              height={barHeight}
              fill={color}
              fillOpacity={0.78}
              stroke={bullish ? "none" : t.ink}
              strokeOpacity={bullish ? 0 : 0.48}
              strokeWidth={bullish ? 0 : 1.3}
            />
            {!bullish && (
              <rect
                x={cx - barWidth / 2}
                y={yTop}
                width={barWidth}
                height={barHeight}
                fill="url(#volume-bear-hatch)"
                pointerEvents="none"
              />
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  // Cross-pane cursor and OHLCV readout: live while hovering in the HTML,
  // absent from the static PNG, where nothing hovers.
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const { width, height } = window.ANYPLOT_SIZE;
  const chartsHeight = height - HEADER_H;
  const priceHeight = Math.round(chartsHeight * PRICE_PANE_SHARE);
  const volumeHeight = chartsHeight - PANE_GAP - priceHeight;

  const plotLeft = MARGIN_LEFT + Y_AXIS_W;
  const plotWidth = width - plotLeft - MARGIN_RIGHT;
  const bandStep = plotWidth / candles.length;
  const active = hoverIdx === null ? null : candles[hoverIdx];
  const cursorX = hoverIdx === null ? 0 : plotLeft + (hoverIdx + 0.5) * bandStep;
  const readoutOnRight = cursorX < plotLeft + plotWidth / 2;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          paddingTop: 4,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 20,
            alignItems: "center",
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: 3,
                background: t.palette[0],
                display: "inline-block",
              }}
            />
            <span style={{ color: t.ink, fontWeight: 500 }}>
              Bullish (close ≥ open, n={bullishCount})
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: 3,
                backgroundColor: t.palette[4],
                backgroundImage: BEAR_HATCH,
                border: `1.5px solid ${t.ink}`,
                display: "inline-block",
              }}
            />
            <span style={{ color: t.ink, fontWeight: 500 }}>
              Bearish (close &lt; open, n={bearishCount})
            </span>
          </div>
        </div>
      </div>

      <div
        style={{ position: "relative" }}
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          const idx = Math.floor((event.clientX - rect.left - plotLeft) / bandStep);
          setHoverIdx(idx >= 0 && idx < candles.length ? idx : null);
        }}
        onMouseLeave={() => setHoverIdx(null)}
      >
        <ChartsContainer
          width={width}
          height={priceHeight}
          skipAnimation
          series={[]}
          margin={{
            top: 16,
            bottom: 6,
            left: MARGIN_LEFT,
            right: MARGIN_RIGHT,
          }}
          xAxis={[
            {
              id: "xPrice",
              scaleType: "band",
              data: bandKeys,
              position: "none",
              tickInterval: showTick,
            },
          ]}
          yAxis={[
            {
              id: "yPrice",
              min: priceMin,
              max: priceMax,
              tickNumber: 6,
              width: Y_AXIS_W,
              label: CLOSE,
              valueFormatter: (v: number) => v.toFixed(0),
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            },
          ]}
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": {
              stroke: t.grid,
              opacity: 0.65,
              strokeDasharray: "3 4",
            },
          }}
        >
          <ChartsGrid horizontal vertical />
          <CandlesticksLayer activeIdx={hoverIdx} />
          <ChartsYAxis axisId="yPrice" />
        </ChartsContainer>

        <div
          style={{
            height: PANE_GAP,
            display: "flex",
            alignItems: "center",
            marginLeft: plotLeft,
            marginRight: MARGIN_RIGHT,
          }}
        >
          <div style={{ flex: 1, height: 1, background: t.grid }} />
        </div>

        <ChartsContainer
          width={width}
          height={volumeHeight}
          skipAnimation
          series={[]}
          margin={{
            top: 6,
            bottom: 16,
            left: MARGIN_LEFT,
            right: MARGIN_RIGHT,
          }}
          xAxis={[
            {
              id: "xVolume",
              scaleType: "band",
              data: bandKeys,
              height: 60,
              label: DATE,
              valueFormatter: (v: string) => shortDateByBand[v],
              tickInterval: showTick,
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            },
          ]}
          yAxis={[
            {
              id: "yVolume",
              min: 0,
              max: volumeMax,
              tickNumber: 4,
              width: Y_AXIS_W,
              label: VOLUME,
              valueFormatter: formatVolume,
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            },
          ]}
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": {
              stroke: t.grid,
              opacity: 0.65,
              strokeDasharray: "3 4",
            },
          }}
        >
          <ChartsGrid horizontal vertical />
          <VolumeBarsLayer activeIdx={hoverIdx} />
          <ChartsXAxis axisId="xVolume" />
          <ChartsYAxis axisId="yVolume" />
        </ChartsContainer>

        {active && (
          <div
            style={{
              position: "absolute",
              top: 8,
              left: readoutOnRight ? cursorX + 12 : undefined,
              right: readoutOnRight ? undefined : width - cursorX + 12,
              padding: "6px 12px",
              borderRadius: 6,
              background: t.elevatedBg,
              border: `1px solid ${t.grid}`,
              color: t.ink,
              fontSize: 14,
              whiteSpace: "nowrap",
              pointerEvents: "none",
            }}
          >
            <strong>{active.fullDate}</strong> · O {formatPrice(active.open)} · H{" "}
            {formatPrice(active.high)} · L {formatPrice(active.low)} · C{" "}
            {formatPrice(active.close)} · Vol {formatVolume(active.volume)}
          </div>
        )}
      </div>
    </div>
  );
}
