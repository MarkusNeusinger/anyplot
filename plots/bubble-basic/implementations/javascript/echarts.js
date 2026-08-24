// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Market analysis: R&D investment vs. revenue growth, bubble size = market share.
const companyCount = 65;
const bubbles = [];
for (let i = 0; i < companyCount; i++) {
  const rdSpend = 5 + rand() * 95; // R&D investment, $M
  const noise = (rand() - 0.5) * 14;
  const growthRate = Math.max(1, 3 + rdSpend * 0.18 + noise); // revenue growth, %
  const marketShare = 8 + rand() * 92; // market share, %
  bubbles.push([rdSpend, growthRate, marketShare]);
}

const shareValues = bubbles.map((b) => b[2]);
const shareMin = Math.min(...shareValues);
const shareMax = Math.max(...shareValues);

// Scale bubble diameter by sqrt(value) so on-screen AREA (not radius) is
// proportional to market share.
const minDiameter = 14;
const maxDiameter = 92;
const sizeScale = maxDiameter / Math.sqrt(shareMax);
function diameterFor(value) {
  return Math.max(minDiameter, sizeScale * Math.sqrt(value));
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Size legend (three reference bubbles drawn as graphic elements) -------
const legendCx = size.width - 130;
const legendSamples = [
  { value: shareMin, cy: size.height * 0.26 },
  { value: (shareMin + shareMax) / 2, cy: size.height * 0.48 },
  { value: shareMax, cy: size.height * 0.72 },
];

const legendGraphics = [
  {
    type: "text",
    left: legendCx - 100,
    top: size.height * 0.14,
    style: {
      text: "Market Share (%)",
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
      style: { fill: t.palette[0], opacity: 0.35, stroke: t.pageBg, lineWidth: 1.5 },
    };
  }),
  ...legendSamples.map((sample) => ({
    type: "text",
    left: legendCx + maxDiameter / 2 + 14,
    top: sample.cy - 8,
    style: {
      text: `${Math.round(sample.value)}%`,
      fill: t.inkSoft,
      fontSize: 13,
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
  grid: { left: 90, right: 260, top: 110, bottom: 100 },
  xAxis: {
    type: "value",
    name: "R&D Investment ($M)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
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
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "scatter",
      data: bubbles,
      symbolSize: (value) => diameterFor(value[2]),
      itemStyle: {
        color: t.palette[0],
        opacity: 0.6,
        borderColor: t.pageBg,
        borderWidth: 1.5,
      },
    },
  ],
  graphic: legendGraphics,
});
