// anyplot.ai
// area-stacked-confidence: Stacked Area Chart with Confidence Bands
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly energy mix by source, TWh. Measurement uncertainty is narrow for
// the historical quarters and widens across the forecast horizon.
const QUARTER_COUNT = 24;
const FORECAST_START = 16;

const quarters = [];
for (let idx = 0; idx < QUARTER_COUNT; idx++) {
  const year = 2020 + Math.floor(idx / 4);
  const quarter = (idx % 4) + 1;
  quarters.push(`Q${quarter} '${String(year).slice(2)}`);
}

const solarCenter = [];
const windCenter = [];
const gasCenter = [];
const uncertaintyPct = [];
for (let idx = 0; idx < QUARTER_COUNT; idx++) {
  solarCenter.push(38 + 3.4 * idx + 5 * Math.sin(idx / 3));
  windCenter.push(58 + 1.9 * idx + 6 * Math.cos(idx / 4));
  gasCenter.push(Math.max(20, 95 - 1.6 * idx));
  uncertaintyPct.push(
    idx < FORECAST_START
      ? 0.05
      : 0.05 + ((idx - (FORECAST_START - 1)) / (QUARTER_COUNT - FORECAST_START)) * 0.22
  );
}

// Cumulative baseline BELOW each series, matching the stacking order used
// for the central areas so each band wraps its own layer of the stack.
const zeroBaseline = new Array(QUARTER_COUNT).fill(0);
const windBaseline = solarCenter;
const gasBaseline = solarCenter.map((v, idx) => v + windCenter[idx]);

const absoluteBand = (center, baseline) => {
  const lower = center.map((v, idx) => baseline[idx] + v * (1 - uncertaintyPct[idx]));
  const upper = center.map((v, idx) => baseline[idx] + v * (1 + uncertaintyPct[idx]));
  const width = upper.map((v, idx) => v - lower[idx]);
  return { lower, width };
};

const seriesDefs = [
  { name: "Solar", color: t.palette[0], center: solarCenter, ...absoluteBand(solarCenter, zeroBaseline) },
  { name: "Wind", color: t.palette[1], center: windCenter, ...absoluteBand(windCenter, windBaseline) },
  { name: "Natural Gas", color: t.palette[2], center: gasCenter, ...absoluteBand(gasCenter, gasBaseline) },
];

// --- Series -------------------------------------------------------------
// Each series contributes 3 ECharts series: an invisible line pinning the
// band's lower edge, a translucent fill spanning up to the band's upper
// edge (both sharing a private stack so the fill floats at the right
// height), and the opaque central stacked area on top.
const series = [];
seriesDefs.forEach((s, idx) => {
  series.push({
    type: "line",
    stack: `band${idx}`,
    data: s.lower,
    lineStyle: { opacity: 0 },
    symbol: "none",
    silent: true,
    tooltip: { show: false },
    z: 1,
  });
  series.push({
    type: "line",
    stack: `band${idx}`,
    data: s.width,
    lineStyle: { opacity: 0 },
    symbol: "none",
    areaStyle: { color: s.color, opacity: 0.28 },
    silent: true,
    tooltip: { show: false },
    z: 1,
  });
  series.push({
    name: s.name,
    type: "line",
    stack: "total",
    data: s.center,
    symbol: "none",
    itemStyle: { color: s.color },
    lineStyle: { width: 2.5, color: s.color },
    areaStyle: { color: s.color, opacity: 0.82 },
    z: 2,
  });
});

// --- Title sizing (scales down once the string runs past the 67-char baseline) ---
const TITLE = "Energy Mix by Source · area-stacked-confidence · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * Math.min(1, 67 / TITLE.length)));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: TITLE,
    subtext: "Shaded bands show measurement uncertainty; the range widens across the forecast horizon",
    left: "center",
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  tooltip: { trigger: "axis" },
  legend: {
    data: seriesDefs.map((s) => s.name),
    top: 118,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 110, right: 60, top: 190, bottom: 90 },
  xAxis: {
    type: "category",
    data: quarters,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Energy Consumption (TWh)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series,
});
