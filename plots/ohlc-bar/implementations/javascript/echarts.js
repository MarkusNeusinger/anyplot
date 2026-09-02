// anyplot.ai
// ohlc-bar: OHLC Bar Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const UP_COLOR = t.palette[0]; // #009E73 brand green — profit/up semantic
const DOWN_COLOR = t.palette[4]; // #AE3030 matte red — loss/down semantic

// --- Data: 45 trading days of a fictional stock's OHLC prices --------------
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const NUM_DAYS = 45;

function seededRandom(seed) {
  let s = seed;
  return function () {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}
const rand = seededRandom(42);

const dateLabels = [];
const cursor = new Date(2024, 0, 2); // Tue Jan 2 2024
while (dateLabels.length < NUM_DAYS) {
  const weekday = cursor.getDay();
  if (weekday !== 0 && weekday !== 6) {
    dateLabels.push(`${MONTHS[cursor.getMonth()]} ${cursor.getDate()}`);
  }
  cursor.setDate(cursor.getDate() + 1);
}

const ohlcRows = [];
let lastClose = 182;
for (let i = 0; i < NUM_DAYS; i++) {
  const open = lastClose + (rand() - 0.5) * 3;
  const drift = (rand() - 0.47) * 6; // slight upward drift over the period
  const close = open + drift;
  const high = Math.max(open, close) + rand() * 2.6;
  const low = Math.min(open, close) - rand() * 2.6;
  ohlcRows.push([i, +open.toFixed(2), +high.toFixed(2), +low.toFixed(2), +close.toFixed(2)]);
  lastClose = close;
}

// --- Custom render: I-beam OHLC bars ----------------------------------------
function renderOhlcBar(params, api) {
  const xIndex = api.value(0);
  const openPoint = api.coord([xIndex, api.value(1)]);
  const highPoint = api.coord([xIndex, api.value(2)]);
  const lowPoint = api.coord([xIndex, api.value(3)]);
  const closePoint = api.coord([xIndex, api.value(4)]);
  const tickLength = api.size([1, 0])[0] * 0.32;
  const isUp = api.value(4) >= api.value(1);
  const lineStyle = { stroke: isUp ? UP_COLOR : DOWN_COLOR, lineWidth: 2.6 };

  return {
    type: "group",
    children: [
      {
        type: "line",
        shape: { x1: highPoint[0], y1: highPoint[1], x2: lowPoint[0], y2: lowPoint[1] },
        style: lineStyle,
      },
      {
        type: "line",
        shape: { x1: openPoint[0] - tickLength, y1: openPoint[1], x2: openPoint[0], y2: openPoint[1] },
        style: lineStyle,
      },
      {
        type: "line",
        shape: { x1: closePoint[0], y1: closePoint[1], x2: closePoint[0] + tickLength, y2: closePoint[1] },
        style: lineStyle,
      },
    ],
  };
}

// --- Init + option -----------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Aurora Robotics · ohlc-bar · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Bullish (close > open)", "Bearish (close < open)"],
    top: 78,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    itemWidth: 26,
    itemHeight: 3,
  },
  grid: { left: 110, right: 60, top: 150, bottom: 110 },
  xAxis: {
    type: "category",
    data: dateLabels,
    boundaryGap: true,
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 3 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    scale: true,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => `$${v}` },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Bullish (close > open)",
      type: "line",
      data: [],
      symbol: "none",
      itemStyle: { color: UP_COLOR },
      lineStyle: { color: UP_COLOR, width: 2.6 },
    },
    {
      name: "Bearish (close < open)",
      type: "line",
      data: [],
      symbol: "none",
      itemStyle: { color: DOWN_COLOR },
      lineStyle: { color: DOWN_COLOR, width: 2.6 },
    },
    {
      name: "OHLC",
      type: "custom",
      renderItem: renderOhlcBar,
      encode: { x: 0, y: [1, 2, 3, 4] },
      data: ohlcRows,
    },
  ],
});
