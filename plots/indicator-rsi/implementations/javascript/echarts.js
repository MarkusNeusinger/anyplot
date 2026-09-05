// anyplot.ai
// indicator-rsi: RSI Technical Indicator Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Helpers -----------------------------------------------------------
function hexToRgba(hex, alpha) {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function nextTradingDay(date) {
  const next = new Date(date);
  do {
    next.setUTCDate(next.getUTCDate() + 1);
  } while (next.getUTCDay() === 0 || next.getUTCDay() === 6);
  return next;
}

function computeRsi(closes, period) {
  const rsi = new Array(closes.length).fill(null);
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = closes[i] - closes[i - 1];
    avgGain += Math.max(change, 0);
    avgLoss += Math.max(-change, 0);
  }
  avgGain /= period;
  avgLoss /= period;
  rsi[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = period + 1; i < closes.length; i += 1) {
    const change = closes[i] - closes[i - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    rsi[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return rsi;
}

// --- Data (in-memory, deterministic LCG-driven price walk) -------------
const lookback = 14;
const totalDays = 130;
const rand = lcg(42);

const dates = [new Date("2025-01-02T00:00:00Z")];
for (let i = 1; i < totalDays; i += 1) {
  dates.push(nextTradingDay(dates[i - 1]));
}

const closingPrices = [64.2];
for (let i = 1; i < totalDays; i += 1) {
  const cycle = Math.sin(i / 9) * 0.4;
  const noise = (rand() - 0.5) * 1.7;
  closingPrices.push(Math.max(10, closingPrices[i - 1] + cycle + noise));
}

const rsiValues = computeRsi(closingPrices, lookback);
const rsiSeries = [];
for (let i = lookback; i < totalDays; i += 1) {
  rsiSeries.push([dates[i].getTime(), rsiValues[i]]);
}

// --- Init ----------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: [t.palette[0]],
  title: {
    text: "indicator-rsi · javascript · echarts · anyplot.ai",
    subtext: "14-period RSI on daily closing prices · overbought > 70 · oversold < 30",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  grid: { left: 90, right: 150, top: 140, bottom: 90 },
  xAxis: {
    type: "time",
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    max: 100,
    interval: 10,
    name: "RSI",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      name: "RSI (14)",
      showSymbol: false,
      lineStyle: { width: 3, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      data: rsiSeries,
      markArea: {
        silent: true,
        data: [
          [
            { yAxis: 70, itemStyle: { color: hexToRgba(t.palette[4], 0.1) } },
            { yAxis: 100 },
          ],
          [
            { yAxis: 0, itemStyle: { color: hexToRgba(t.palette[0], 0.1) } },
            { yAxis: 30 },
          ],
        ],
      },
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { type: "dashed", color: t.inkSoft, width: 1.5 },
        label: { color: t.inkSoft, fontSize: 13, formatter: "{b}", position: "end" },
        data: [
          { yAxis: 70, name: "Overbought" },
          { yAxis: 50, name: "Neutral", lineStyle: { type: "dotted" } },
          { yAxis: 30, name: "Oversold" },
        ],
      },
    },
  ],
});
