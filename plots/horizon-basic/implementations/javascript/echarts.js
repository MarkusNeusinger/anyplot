// anyplot.ai
// horizon-basic: Horizon Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-08-18

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic LCG) ------------------------------------
const sectorNames = [
  "Technology", "Energy", "Healthcare", "Financials", "Industrials",
  "Materials", "Utilities", "Consumer", "Real Estate", "Telecom",
];
const N = sectorNames.length;
const T = 60;

let seed = 42;
const rand = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

const seriesValues = sectorNames.map(() => {
  let value = (rand() - 0.5) * 6;
  const drift = (rand() - 0.5) * 0.15;
  const volatility = 0.8 + rand() * 1.2;
  const values = [];
  for (let i = 0; i < T; i++) {
    value += drift + (rand() - 0.5) * volatility;
    value = Math.max(-18, Math.min(18, value));
    values.push(Math.round(value * 10) / 10);
  }
  return values;
});

const startDate = new Date(2024, 0, 2);
const dayLabels = Array.from({ length: T }, (_, i) => {
  const d = new Date(startDate);
  d.setDate(d.getDate() + i);
  return `${d.getMonth() + 1}/${d.getDate()}`;
});

// --- Horizon folding: K overlapping bands per row, opacity encodes magnitude
const K = 3;
const BAND_H = 5; // percentage points per band; 3 bands saturate at +/-15
const BAND_OPACITY = [0.35, 0.65, 1.0];
const POS_COLOR = t.div[2]; // blue — above sector average
const NEG_COLOR = t.div[0]; // red — below sector average

function bandValue(v, k) {
  return Math.min(BAND_H, Math.max(0, v - k * BAND_H));
}

// --- Layout (derived from the mount size so it holds for any canvas) -------
const W = size.width;
const H = size.height;
const titleH = Math.round(H * 0.08);
const legendH = Math.round(H * 0.05);
const bottomAxisH = Math.round(H * 0.06);
const leftMargin = Math.round(W * 0.115);
const rightMargin = Math.round(W * 0.03);
const rowGap = Math.round(H * 0.009);
const rowsTop = titleH + legendH;
const rowsAvail = H - bottomAxisH - rowsTop;
const rowH = Math.floor((rowsAvail - (N - 1) * rowGap) / N);
const rowTop = (i) => rowsTop + i * (rowH + rowGap);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Grids, axes, series (one row per sector) -------------------------------
const grid = [];
const xAxis = [];
const yAxis = [];
const series = [];
const graphic = [];

for (let i = 0; i < N; i++) {
  grid.push({
    left: leftMargin,
    right: rightMargin,
    top: rowTop(i),
    height: rowH,
  });

  const isLastRow = i === N - 1;
  xAxis.push({
    type: "category",
    data: dayLabels,
    gridIndex: i,
    boundaryGap: false,
    axisLabel: {
      show: isLastRow,
      color: t.inkSoft,
      fontSize: 14,
      interval: Math.round(T / 6),
    },
    axisTick: { show: false },
    axisLine: { show: true, lineStyle: { color: t.grid } },
    splitLine: { show: false },
  });

  yAxis.push({
    type: "value",
    min: 0,
    max: BAND_H,
    gridIndex: i,
    axisLabel: { show: false },
    axisTick: { show: false },
    axisLine: { show: false },
    splitLine: { show: false },
  });

  for (let k = 0; k < K; k++) {
    series.push({
      type: "line",
      xAxisIndex: i,
      yAxisIndex: i,
      data: seriesValues[i].map((v) => bandValue(v, k)),
      showSymbol: false,
      silent: true,
      clip: true,
      lineStyle: { width: 0 },
      areaStyle: { color: POS_COLOR, opacity: BAND_OPACITY[k] },
      z: k + 1,
    });
    series.push({
      type: "line",
      xAxisIndex: i,
      yAxisIndex: i,
      data: seriesValues[i].map((v) => bandValue(-v, k)),
      showSymbol: false,
      silent: true,
      clip: true,
      lineStyle: { width: 0 },
      areaStyle: { color: NEG_COLOR, opacity: BAND_OPACITY[k] },
      z: k + 1,
    });
  }

  graphic.push({
    type: "text",
    left: 16,
    top: rowTop(i) + rowH / 2 - 8,
    style: {
      text: sectorNames[i],
      fill: t.inkSoft,
      font: "500 15px sans-serif",
    },
  });
}

// --- Diverging legend bar (top right) ---------------------------------------
const legendW = Math.round(W * 0.16);
const legendX = W - rightMargin - legendW;
const legendY = titleH + Math.round(legendH * 0.35);
graphic.push(
  {
    type: "text",
    left: legendX,
    top: titleH + 2,
    style: {
      text: "Deviation from sector avg (%)",
      fill: t.inkSoft,
      font: "12px sans-serif",
    },
  },
  {
    type: "rect",
    left: legendX,
    top: legendY,
    shape: { width: legendW, height: 12 },
    style: {
      fill: {
        type: "linear",
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: NEG_COLOR },
          { offset: 0.5, color: t.pageBg },
          { offset: 1, color: POS_COLOR },
        ],
      },
    },
  },
  {
    type: "text",
    left: legendX,
    top: legendY + 16,
    style: { text: `-${K * BAND_H}%`, fill: t.inkSoft, font: "11px sans-serif" },
  },
  {
    type: "text",
    left: legendX + legendW / 2 - 6,
    top: legendY + 16,
    style: { text: "0", fill: t.inkSoft, font: "11px sans-serif" },
  },
  {
    type: "text",
    left: legendX + legendW - 26,
    top: legendY + 16,
    style: { text: `+${K * BAND_H}%`, fill: t.inkSoft, font: "11px sans-serif" },
  },
);

// --- Option -------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Sector Return Deviation · horizon-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: Math.round(titleH * 0.28),
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  grid,
  xAxis,
  yAxis,
  series,
  graphic,
});
