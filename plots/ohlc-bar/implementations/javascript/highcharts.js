// anyplot.ai
// ohlc-bar: OHLC Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: 84/100 | Created: 2026-09-02

// The core bundle (no highcharts-more / modules/stock) has no "ohlc" series —
// that type ships in modules/ohlc.js / modules/stock.js, neither of which is
// loaded. Each bar is built from a "line" series with null-separated strokes
// (high-low range, left open tick, right close tick) drawn per point on a
// datetime x-axis — pure core series types, no add-on module, no
// cross-library workaround.
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const upColor = t.palette[0]; // #009E73 brand green — bullish (profit/up)
const downColor = t.palette[4]; // #AE3030 matte red — bearish (loss/down), finance semantic anchor

const dayMs = 24 * 3600 * 1000;
const numDays = 42;
const dates = [];
let cursor = Date.UTC(2024, 1, 1); // Thu 1 Feb 2024
while (dates.length < numDays) {
  const weekday = new Date(cursor).getUTCDay();
  if (weekday !== 0 && weekday !== 6) dates.push(cursor);
  cursor += dayMs;
}

let price = 78.4; // WTI crude oil, USD per barrel
const bars = dates.map((time) => {
  const open = price;
  const drift = (lcg() - 0.5) * 2.6;
  const close = Math.max(20, open + drift);
  const high = Math.max(open, close) + lcg() * 1.5;
  const low = Math.max(10, Math.min(open, close) - lcg() * 1.5);
  price = close;
  return {
    time,
    open: +open.toFixed(2),
    high: +high.toFixed(2),
    low: +low.toFixed(2),
    close: +close.toFixed(2),
    bullish: close >= open,
  };
});

const allLows = bars.map((b) => b.low);
const allHighs = bars.map((b) => b.high);
const pad = (Math.max(...allHighs) - Math.min(...allLows)) * 0.08;
const yMin = Math.floor(Math.min(...allLows) - pad);
const yMax = Math.ceil(Math.max(...allHighs) + pad);

// The sharpest single-day move becomes the data-storytelling focal point
// (a dashed xAxis.plotLine + label — core-bundle, no annotations module).
let sharpest = bars[0];
for (const b of bars) {
  if (Math.abs(b.close - b.open) > Math.abs(sharpest.close - sharpest.open)) sharpest = b;
}
const sharpestPct = ((sharpest.close - sharpest.open) / sharpest.open) * 100;

// Each bar draws 3 strokes: the high-low range, a left tick at open, a right
// tick at close — separated by null points so Highcharts breaks the line.
// The close tick also carries a triangle marker (▲ up / ▼ down) so direction
// reads from shape, not solely from the red/green hue.
const tickOffset = dayMs * 0.32;
function barStrokes(bar) {
  const left = bar.time - tickOffset;
  const mid = bar.time;
  const right = bar.time + tickOffset;
  const color = bar.bullish ? upColor : downColor;
  return [
    { x: mid, y: bar.low, custom: bar },
    { x: mid, y: bar.high, custom: bar },
    { x: mid, y: null },
    { x: left, y: bar.open, custom: bar },
    { x: mid, y: bar.open, custom: bar },
    { x: mid, y: null },
    { x: mid, y: bar.close, custom: bar },
    {
      x: right,
      y: bar.close,
      custom: bar,
      marker: {
        enabled: true,
        symbol: bar.bullish ? "triangle" : "triangle-down",
        radius: 5,
        fillColor: color,
        lineWidth: 0,
      },
    },
    { x: mid, y: null },
  ];
}

const upData = bars.filter((b) => b.bullish).flatMap(barStrokes);
const downData = bars.filter((b) => !b.bullish).flatMap(barStrokes);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "Crude Oil Futures · ohlc-bar · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Trading Date", style: { color: t.inkSoft, fontSize: "16px" } },
    crosshair: { width: 1, color: t.inkSoft, dashStyle: "ShortDot" },
    plotLines: [
      {
        value: sharpest.time,
        color: t.inkSoft,
        dashStyle: "Dash",
        width: 1,
        zIndex: 5,
        label: {
          text: `Sharpest move: ${sharpestPct >= 0 ? "+" : ""}${sharpestPct.toFixed(1)}%`,
          style: { color: t.inkSoft, fontSize: "13px" },
          rotation: 0,
          y: -10,
        },
      },
    ],
  },
  yAxis: {
    min: yMin,
    max: yMax,
    title: { text: "Price per Barrel (USD)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolWidth: 22,
    itemDistance: 24,
    padding: 12,
  },
  tooltip: {
    outside: false,
    formatter: function () {
      const c = this.point.custom;
      if (!c) return false;
      return (
        `<b>${Highcharts.dateFormat("%b %e, %Y", c.time)}</b><br/>` +
        `Open: $${c.open.toFixed(2)}<br/>High: $${c.high.toFixed(2)}<br/>` +
        `Low: $${c.low.toFixed(2)}<br/>Close: $${c.close.toFixed(2)}`
      );
    },
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false }, lineWidth: 3 },
  },
  series: [
    {
      name: "Up (Close ≥ Open)",
      data: upData,
      color: upColor,
      showInLegend: true,
    },
    {
      name: "Down (Close < Open)",
      data: downData,
      color: downColor,
      showInLegend: true,
    },
  ],
});
