// anyplot.ai
// candlestick-basic: Basic Candlestick Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;
const UP = t.palette[0]; // #009E73 — bullish (price up)
const DOWN = "#AE3030"; // matte red — bearish (price down), semantic finance exception

// --- Data (in-memory, deterministic) ----------------------------------------
// Small fixed-seed LCG stands in for a seeded RNG (browser has none).
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const N = 30;
const dates = [];
const cursor = new Date(2024, 0, 2);
while (dates.length < N) {
  const weekday = cursor.getDay();
  if (weekday !== 0 && weekday !== 6) {
    dates.push(`${cursor.getMonth() + 1}/${cursor.getDate()}`);
  }
  cursor.setDate(cursor.getDate() + 1);
}

let price = 148;
const ohlc = [];
for (let i = 0; i < N; i++) {
  const open = price;
  const drift = (rand() - 0.47) * 6;
  const close = Math.max(20, open + drift);
  const high = Math.max(open, close) + rand() * 2.5;
  const low = Math.min(open, close) - rand() * 2.5;
  ohlc.push([
    Number(open.toFixed(2)),
    Number(close.toFixed(2)),
    Number(low.toFixed(2)),
    Number(high.toFixed(2)),
  ]);
  price = close;
}

// 5-day simple moving average of the close price, for trend context.
const MA_PERIOD = 5;
const closes = ohlc.map((bar) => bar[1]);
const ma5 = closes.map((_, i) => {
  if (i < MA_PERIOD - 1) return null;
  let sum = 0;
  for (let j = i - MA_PERIOD + 1; j <= i; j++) sum += closes[j];
  return Number((sum / MA_PERIOD).toFixed(2));
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "candlestick-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    top: 56,
    left: "center",
    textStyle: { color: t.ink, fontSize: 14 },
    data: ["5-Day MA"],
  },
  grid: { left: 90, right: 60, top: 130, bottom: 70 },
  tooltip: { trigger: "axis" },
  xAxis: {
    type: "category",
    data: dates,
    boundaryGap: true,
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 2 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    scale: true,
    name: "Price (USD)",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "${value}" },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "candlestick",
      name: "OHLC",
      data: ohlc,
      itemStyle: {
        color: UP,
        color0: DOWN,
        borderColor: UP,
        borderColor0: DOWN,
      },
    },
    {
      type: "line",
      name: "5-Day MA",
      data: ma5,
      symbol: "none",
      lineStyle: { color: t.palette[1], width: 2 },
      itemStyle: { color: t.palette[1] },
      markPoint: {
        symbolSize: 52,
        itemStyle: { color: t.palette[1] },
        label: {
          color: t.pageBg,
          fontSize: 12,
          formatter: (p) => Math.round(p.value),
        },
        data: [
          { type: "max", name: "Peak" },
          { type: "min", name: "Trough" },
        ],
      },
    },
  ],
});
