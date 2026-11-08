// anyplot.ai
// depth-order-book: Order Book Depth Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-15
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const BID = "bid"; // side values the spec defines
const ASK = "ask";
const SIDE_COLOR = { [BID]: t.palette[0], [ASK]: t.palette[4] }; // green bids, red asks, as the Notes ask
const SIDE_LABEL = { [BID]: "Bids (buy orders)", [ASK]: "Asks (sell orders)" };
const X_PAD = 0.02; // share of the half-range added on both sides of the outermost levels
const TITLE_H = 84;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const PRICE = "Price (USD)"; // role: price
const QUANTITY = "Quantity (BTC)"; // role: quantity
const SIDE = "Side"; // role: side
const SYMBOL = "Symbol"; // role: extra

// Data: replace this block with your own records, one object per row
// One BTC/USD order-book snapshot: 50 bid levels below and 50 ask levels above the spread, 5 USD apart,
// with two large resting "walls" per side
const data = (() => {
  let s = 42;
  const rng = () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967296;
  };
  const levels = 50;
  const rows = [];
  for (let i = 0; i < levels; i += 1) {
    const base = 0.4 + rng() * 2.0;
    const wall = i === 14 || i === 31 ? rng() * 35 + 18 : 0;
    rows.push({ [PRICE]: 59995 - i * 5, [QUANTITY]: +(base + wall).toFixed(3), [SIDE]: "bid", [SYMBOL]: "BTC/USD" });
  }
  for (let i = 0; i < levels; i += 1) {
    const base = 0.4 + rng() * 2.0;
    const wall = i === 11 || i === 37 ? rng() * 35 + 18 : 0;
    rows.push({ [PRICE]: 60005 + i * 5, [QUANTITY]: +(base + wall).toFixed(3), [SIDE]: "ask", [SYMBOL]: "BTC/USD" });
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Cumulative quantity per side, accumulated from the best price outward
const bids = data.filter((d) => d[SIDE] === BID).sort((a, b) => b[PRICE] - a[PRICE]);
const asks = data.filter((d) => d[SIDE] === ASK).sort((a, b) => a[PRICE] - b[PRICE]);
let bidRun = 0;
const bidDepth = new Map(bids.map((d) => [d[PRICE], (bidRun += d[QUANTITY])]));
let askRun = 0;
const askDepth = new Map(asks.map((d) => [d[PRICE], (askRun += d[QUANTITY])]));

const prices = [...bids, ...asks].map((d) => d[PRICE]).sort((a, b) => a - b);
const bidSeries = prices.map((p) => bidDepth.get(p) ?? null);
const askSeries = prices.map((p) => askDepth.get(p) ?? null);

const bestBid = bids[0][PRICE];
const bestAsk = asks[0][PRICE];
const mid = (bestBid + bestAsk) / 2;
const spread = bestAsk - bestBid;
// x axis centred on the mid price so the two areas mirror each other
const halfRange = Math.max(mid - prices[0], prices[prices.length - 1] - mid) * (1 + X_PAD);

const priceUnit = PRICE.match(/\(([^)]+)\)/)?.[1] ?? "";
const quantityUnit = QUANTITY.match(/\(([^)]+)\)/)?.[1] ?? "";
const fmtPrice = (v) => v.toLocaleString("en-US", { maximumFractionDigits: 2 });
const title = `${data[0][SYMBOL]} Order Book · depth-order-book · javascript · muix · anyplot.ai`;
const subtitle = `${bids.length} bid and ${asks.length} ask levels · bid depth ${bidRun.toFixed(1)} ${quantityUnit} · ask depth ${askRun.toFixed(1)} ${quantityUnit}`;
const midLabel = `Mid ${fmtPrice(mid)} ${priceUnit} · spread ${fmtPrice(spread)} ${priceUnit}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "22px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{subtitle}</div>
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        xAxis={[
          {
            data: prices,
            scaleType: "linear",
            min: mid - halfRange,
            max: mid + halfRange,
            label: PRICE,
            height: 68,
            tickNumber: 10,
            valueFormatter: fmtPrice,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: `${QUANTITY}, cumulative from the mid price`,
            width: 84,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "bids",
            data: bidSeries,
            label: SIDE_LABEL[BID] ?? BID,
            color: SIDE_COLOR[BID],
            area: true,
            // depth at a price between two bid levels is the depth of the higher level
            curve: "stepBefore",
            connectNulls: false,
            showMark: false,
          },
          {
            id: "asks",
            data: askSeries,
            label: SIDE_LABEL[ASK] ?? ASK,
            color: SIDE_COLOR[ASK],
            area: true,
            // depth at a price between two ask levels is the depth of the lower level
            curve: "stepAfter",
            connectNulls: false,
            showMark: false,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.3 },
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine
          x={mid}
          label={midLabel}
          labelAlign="start"
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
        />
      </LineChart>
    </div>
  );
}
