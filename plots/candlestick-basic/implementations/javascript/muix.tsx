// anyplot.ai
// candlestick-basic: Basic Candlestick Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.08;
const BODY_WIDTH_SHARE = 0.64;
const HEADER_H = 118;

// Columns: set these to your data's column names
const DATE = "Timestamp (UTC)"; // role: x
const OPEN = "Open price ($)"; // role: open
const HIGH = "High price ($)"; // role: high
const LOW = "Low price ($)"; // role: low
const CLOSE = "Close price ($)"; // role: close

// Data: replace this block with your own records, one object per row
const data = (() => {
  let seed = 42;
  const periods = 48;
  const start = new Date(Date.UTC(2024, 0, 8, 0, 0));
  const rows: { [key: string]: string | number }[] = [];
  let price = 42000;

  for (let i = 0; i < periods; i += 1) {
    const o = price;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u1 = seed / 0x7fffffff;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u2 = seed / 0x7fffffff;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u3 = seed / 0x7fffffff;

    const drift = (u1 - 0.5) * 260;
    const c = Math.max(1000, o + drift);
    const h = Math.max(o, c) + u2 * 140;
    const l = Math.max(Math.min(o, c) - u3 * 140, 1);

    const d = new Date(start.getTime() + i * 3600 * 1000);
    rows.push({
      [DATE]: d.toISOString(),
      [OPEN]: Math.round(o * 100) / 100,
      [HIGH]: Math.round(h * 100) / 100,
      [LOW]: Math.round(l * 100) / 100,
      [CLOSE]: Math.round(c * 100) / 100,
    });
    price = c;
  }
  return rows;
})();

// Plot: reads only data and the constants above
const sorted = [...data].sort(
  (a, b) =>
    new Date(String(a[DATE])).getTime() - new Date(String(b[DATE])).getTime(),
);

const currencyMatch = OPEN.match(/\(([^)]+)\)/);
const currencyPrefix = currencyMatch ? currencyMatch[1] : "";
const yAxisLabel = OPEN.replace(/^Open\s+/i, "").replace(
  /^([a-z])/,
  (m) => m.toUpperCase(),
);

const candles = sorted.map((r, idx) => {
  const dt = new Date(String(r[DATE]));
  const label =
    dt.getUTCHours() === 0
      ? dt.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          timeZone: "UTC",
        })
      : dt.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
          timeZone: "UTC",
        });
  return {
    idx,
    key: `${String(r[DATE])}-${idx}`,
    date: dt,
    label: `${label}#${idx}`,
    displayLabel: label,
    open: Number(r[OPEN]),
    high: Number(r[HIGH]),
    low: Number(r[LOW]),
    close: Number(r[CLOSE]),
  };
});

const dateKeys = candles.map((c) => c.label);
const displayByKey = Object.fromEntries(
  candles.map((c) => [c.label, c.displayLabel]),
);

const yMinRaw = Math.min(...candles.map((c) => c.low));
const yMaxRaw = Math.max(...candles.map((c) => c.high));
const ySpan = yMaxRaw - yMinRaw || 1;
const yMin = yMinRaw - ySpan * Y_PAD_SHARE;
const yMax = yMaxRaw + ySpan * Y_PAD_SHARE;

const bullishCount = candles.filter((c) => c.close >= c.open).length;
const bearishCount = candles.length - bullishCount;

const firstDate = candles[0]?.date;
const lastDate = candles[candles.length - 1]?.date;
const rangeText =
  firstDate && lastDate
    ? `${firstDate.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" })} – ${lastDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })}`
    : "";

const TITLE = "candlestick-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${candles.length} periods (${rangeText}) · Range ${currencyPrefix}${Math.round(yMinRaw).toLocaleString("en-US")}–${currencyPrefix}${Math.round(yMaxRaw).toLocaleString("en-US")}`;

const legendItems = [
  {
    label: `Bullish (close ≥ open, n=${bullishCount})`,
    color: t.palette[0],
  },
  {
    label: `Bearish (close < open, n=${bearishCount})`,
    color: t.palette[4],
  },
];

function CandlesticksLayer() {
  const xScale = useXScale("time") as unknown as {
    (v: string): number | undefined;
    bandwidth?: () => number;
  };
  const yScale = useYScale("price");
  if (!xScale || !yScale || !xScale.bandwidth) return null;

  const bw = xScale.bandwidth();
  const bodyWidth = bw * BODY_WIDTH_SHARE;

  return (
    <g>
      {candles.map((c) => {
        const xBand = xScale(c.label);
        const yOpen = yScale(c.open);
        const yClose = yScale(c.close);
        const yHigh = yScale(c.high);
        const yLow = yScale(c.low);
        if (
          xBand === undefined ||
          yOpen === undefined ||
          yClose === undefined ||
          yHigh === undefined ||
          yLow === undefined
        ) {
          return null;
        }
        const cx = xBand + bw / 2;
        const bullish = c.close >= c.open;
        const color = bullish ? t.palette[0] : t.palette[4];
        const bodyTop = Math.min(yOpen, yClose);
        const bodyHeight = Math.max(Math.abs(yClose - yOpen), 2);

        return (
          <g key={c.key}>
            <line
              x1={cx}
              x2={cx}
              y1={yHigh}
              y2={yLow}
              stroke={color}
              strokeWidth={1.6}
              strokeLinecap="round"
            />
            <rect
              x={cx - bodyWidth / 2}
              y={bodyTop}
              width={bodyWidth}
              height={bodyHeight}
              fill={color}
              stroke={t.ink}
              strokeOpacity={0.32}
              strokeWidth={1}
              rx={0.5}
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H;

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
          gap: 8,
          paddingTop: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            gap: 24,
            alignItems: "center",
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {legendItems.map((item) => (
            <div
              key={item.label}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  background: item.color,
                  display: "inline-block",
                }}
              />
              <span style={{ color: t.ink, fontWeight: 500 }}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        skipAnimation
        series={[]}
        margin={{ top: 20, right: 36, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "time",
            scaleType: "band",
            data: dateKeys,
            height: 64,
            label: DATE,
            valueFormatter: (v: string) => displayByKey[v] ?? v,
            tickLabelInterval: (_value: string, index: number) =>
              index % 4 === 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
          },
        ]}
        yAxis={[
          {
            id: "price",
            min: yMin,
            max: yMax,
            tickNumber: 7,
            width: 96,
            label: yAxisLabel,
            valueFormatter: (v: number) =>
              `${currencyPrefix}${Math.round(v).toLocaleString("en-US")}`,
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
        <ChartsGrid horizontal />
        <CandlesticksLayer />
        <ChartsXAxis axisId="time" />
        <ChartsYAxis axisId="price" />
      </ChartsContainer>
    </div>
  );
}
