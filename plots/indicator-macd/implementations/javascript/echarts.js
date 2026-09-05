// anyplot.ai
// indicator-macd: MACD Technical Indicator Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG price walk) -------------------------
const FAST_PERIOD = 12;
const SLOW_PERIOD = 26;
const SIGNAL_PERIOD = 9;
const N_DAYS = 120;

let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

function ema(values, period) {
  const k = 2 / (period + 1);
  const out = [values[0]];
  for (let i = 1; i < values.length; i++) {
    out.push(values[i] * k + out[i - 1] * (1 - k));
  }
  return out;
}

function tradingDayLabels(count) {
  const labels = [];
  const start = new Date(Date.UTC(2024, 0, 2));
  const cursor = new Date(start);
  while (labels.length < count) {
    const day = cursor.getUTCDay();
    if (day !== 0 && day !== 6) {
      labels.push(cursor.toISOString().slice(0, 10));
    }
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return labels;
}

const dates = tradingDayLabels(N_DAYS);

let price = 182;
const closes = [];
for (let i = 0; i < N_DAYS; i++) {
  const drift = Math.sin(i / 14) * 0.6;
  const shock = (nextRandom() - 0.5) * 4.2;
  price = Math.max(60, price + drift + shock);
  closes.push(price);
}

const emaFast = ema(closes, FAST_PERIOD);
const emaSlow = ema(closes, SLOW_PERIOD);
const macdLine = emaFast.map((v, i) => v - emaSlow[i]);
const signalLine = ema(macdLine, SIGNAL_PERIOD);
const histogram = macdLine.map((v, i) => v - signalLine[i]);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[2], t.palette[3], t.palette[0]],
  backgroundColor: "transparent",
  title: {
    text: "indicator-macd · javascript · echarts · anyplot.ai",
    subtext: "12-day EMA − 26-day EMA, 9-day signal · MSFT daily close",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  legend: {
    data: [
      { name: "MACD", itemStyle: { color: t.palette[2] } },
      { name: "Signal", itemStyle: { color: t.palette[3] } },
      { name: "Histogram", itemStyle: { color: t.ink } },
    ],
    top: 84,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 90, right: 60, top: 150, bottom: 110 },
  xAxis: {
    type: "category",
    data: dates,
    boundaryGap: true,
    axisLabel: { color: t.inkSoft, fontSize: 13, rotate: 45, interval: 9 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "MACD value",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Histogram",
      type: "bar",
      data: histogram.map((v) => v.toFixed(4)),
      itemStyle: {
        color: (params) => (params.value >= 0 ? t.palette[0] : t.palette[4]),
      },
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        data: [{ yAxis: 0 }],
      },
      z: 1,
    },
    {
      name: "MACD",
      type: "line",
      data: macdLine.map((v) => v.toFixed(4)),
      showSymbol: false,
      lineStyle: { width: 3, color: t.palette[2] },
      z: 2,
    },
    {
      name: "Signal",
      type: "line",
      data: signalLine.map((v) => v.toFixed(4)),
      showSymbol: false,
      lineStyle: { width: 3, color: t.palette[3] },
      z: 2,
    },
  ],
});
