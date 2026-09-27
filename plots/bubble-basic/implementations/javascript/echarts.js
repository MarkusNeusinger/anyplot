// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 93/100 | Updated: 2026-09-27

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Market analysis: R&D investment vs. revenue growth, bubble size = a relative
// market-strength index (0-100 scale, scored independently per company — not a
// literal share of one shared 100% pie). A fourth derived quantity — growth
// earned per R&D dollar — drives a continuous color encoding on top of the
// size encoding, so overlapping bubbles in the dense cluster stay visually
// separable by hue, not just by alpha blending.
const companyCount = 65;
const bubbles = [];
for (let i = 0; i < companyCount; i++) {
  const rdSpend = 5 + rand() * 95; // R&D investment, $M
  const noise = (rand() - 0.5) * 30; // wide noise band so the trend isn't a tight line
  const growthRate = Math.max(1, 3 + rdSpend * 0.18 + noise); // revenue growth, %
  const marketIndex = 8 + rand() * 92; // relative market-strength index
  const efficiency = growthRate / rdSpend; // growth % earned per R&D dollar
  bubbles.push([rdSpend, growthRate, marketIndex, efficiency]);
}

// A handful of deliberate outliers break the x/y trend, showing what the
// bubble encoding reveals that a plain 2D scatter would blur: heavy R&D spend
// doesn't guarantee growth, and a small agile spender can still break out.
bubbles[3] = [88, 5, 71, 5 / 88]; // legacy incumbent: heavy spend, weak growth
bubbles[17] = [9, 46, 24, 46 / 9]; // agile startup: tiny spend, breakout growth
bubbles[41] = [61, 3, 85, 3 / 61]; // large but stagnant market leader

const indexValues = bubbles.map((b) => b[2]);
const indexMin = Math.min(...indexValues);
const indexMax = Math.max(...indexValues);
const efficiencyValues = bubbles.map((b) => b[3]);
const efficiencyMin = Math.min(...efficiencyValues);
const efficiencyMax = Math.max(...efficiencyValues);

// Scale bubble diameter by sqrt(value) so on-screen AREA (not radius) is
// proportional to the market index.
const minDiameter = 14;
const maxDiameter = 92;
const sizeScale = maxDiameter / Math.sqrt(indexMax);
function diameterFor(value) {
  return Math.max(minDiameter, sizeScale * Math.sqrt(value));
}

// Data-storytelling focal point: the company with the best revenue growth per
// R&D dollar invested is drawn as a separate, fully-opaque, ink-outlined series
// on top of the rest so it reads as the chart's standout performer.
let standoutIdx = 0;
let bestRatio = -Infinity;
bubbles.forEach((b, i) => {
  if (b[3] > bestRatio) {
    bestRatio = b[3];
    standoutIdx = i;
  }
});
const standout = bubbles[standoutIdx];
const restBubbles = bubbles
  .filter((_, i) => i !== standoutIdx)
  // Painter's-order fix: draw the largest bubbles first and the smallest
  // last, so small bubbles in the dense low-spend cluster render on top of
  // large ones instead of disappearing underneath them.
  .slice()
  .sort((a, b) => b[2] - a[2]);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Size legend (three reference bubbles drawn as graphic elements) -------
const legendCx = size.width - 130;
const legendSamples = [
  { value: indexMin, cy: size.height * 0.26 },
  { value: (indexMin + indexMax) / 2, cy: size.height * 0.48 },
  { value: indexMax, cy: size.height * 0.72 },
];

const legendGraphics = [
  {
    type: "text",
    left: legendCx - 100,
    top: size.height * 0.14,
    style: {
      text: "Relative Market Index",
      fill: t.inkSoft,
      fontSize: 14,
      fontWeight: "bold",
    },
  },
  ...legendSamples.map((sample) => {
    const r = diameterFor(sample.value) / 2;
    return {
      type: "circle",
      shape: { cx: legendCx, cy: sample.cy, r },
      style: { fill: t.inkSoft, opacity: 0.45, stroke: t.pageBg, lineWidth: 1.5 },
    };
  }),
  ...legendSamples.map((sample) => ({
    type: "text",
    left: legendCx + maxDiameter / 2 + 14,
    top: sample.cy - 9,
    style: {
      text: `${Math.round(sample.value)}`,
      fill: t.inkSoft,
      fontSize: 14,
    },
  })),
];

// --- Option ------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bubble-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 170, right: 260, top: 110, bottom: 100 },
  xAxis: {
    type: "value",
    name: "R&D Investment ($M)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Revenue Growth Rate (%)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  // Idiomatic ECharts feature: a continuous visualMap drives the bubble-cloud
  // color from the derived efficiency dimension (index 3), giving every
  // bubble a distinct hue by growth-per-R&D-dollar instead of one flat wash —
  // this is what separates individual bubbles in the densest cluster once
  // opacity blending alone stops being enough. It targets only the main
  // cloud (seriesIndex 0); the standout series keeps its solid brand-green
  // spotlight untouched.
  // Positioned in the top portion of the left margin (well above the
  // vertically-centered y-axis name) so its side labels never collide with
  // the rotated axis title.
  visualMap: {
    type: "continuous",
    dimension: 3,
    min: efficiencyMin,
    max: efficiencyMax,
    seriesIndex: 0,
    orient: "vertical",
    left: 24,
    top: 130,
    itemHeight: 105,
    itemWidth: 16,
    calculable: false,
    hoverLink: false,
    // Reversed stop order (blue=low, green=high) so the gradient's "high" end
    // lands on brand green — matching the standout series below, which is the
    // chart's highest-efficiency point and is also drawn in brand green.
    text: ["High growth / R&D $", "Low growth / R&D $"],
    textGap: 12,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    inRange: { color: [...t.seq].reverse() },
    outOfRange: { color: [...t.seq].reverse() },
  },
  series: [
    {
      type: "scatter",
      data: restBubbles,
      symbolSize: (value) => diameterFor(value[2]),
      itemStyle: {
        opacity: 0.68,
        borderColor: t.pageBg,
        borderWidth: 1.75,
      },
    },
    {
      type: "scatter",
      data: [standout],
      symbolSize: (value) => diameterFor(value[2]),
      itemStyle: {
        color: t.palette[0],
        opacity: 0.95,
        borderColor: t.ink,
        borderWidth: 2.5,
      },
      label: {
        show: true,
        formatter: "Best growth per R&D $",
        position: "top",
        distance: 10,
        color: t.ink,
        fontSize: 13,
        fontWeight: "bold",
      },
      z: 10,
    },
  ],
  graphic: legendGraphics,
});
