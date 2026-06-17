// anyplot.ai
// bifurcation-basic: Bifurcation Diagram for Dynamical Systems
// Library: echarts 5.5.1 | JavaScript 22
// Quality: 93/100 | Created: 2026-06-17
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const BRAND = t.palette[0]; // #009E73 — Imprint palette position 1 (first series)

// --- Data: logistic map x(n+1) = r * x(n) * (1 - x(n)) ----------------------
// For each growth rate r, iterate the map, discard the transient, and keep the
// long-term orbit. Fully deterministic — no RNG needed.
const R_MIN = 2.5;
const R_MAX = 4.0;
const R_STEPS = 1500; // parameter resolution across [2.5, 4.0]
const TRANSIENT = 300; // iterations discarded before the orbit settles
const KEEP = 100; // long-term state values recorded per r

const points = [];
for (let i = 0; i < R_STEPS; i++) {
  const r = R_MIN + ((R_MAX - R_MIN) * i) / (R_STEPS - 1);
  let x = 0.5;
  for (let n = 0; n < TRANSIENT; n++) {
    x = r * x * (1 - x);
  }
  for (let n = 0; n < KEEP; n++) {
    x = r * x * (1 - x);
    points.push([r, x]);
  }
}
// ~150,000 points — dense enough to resolve the period-doubling cascade.

// Key period-doubling thresholds on the route to chaos.
// Positions staggered (top/bottom alternating) so the three closely-spaced
// labels near chaos onset (r ≈ 3.449 / 3.544 / 3.5699) don't crowd each other.
const bifurcations = [
  { r: 3.0,    text: "period-2", position: "insideStartTop" },
  { r: 3.449,  text: "period-4", position: "insideEndBottom" },
  { r: 3.544,  text: "period-8", position: "insideStartTop" },
  { r: 3.5699, text: "chaos",    position: "insideEndBottom" },
];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bifurcation-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },
  grid: { left: 92, right: 56, top: 96, bottom: 84 },
  xAxis: {
    type: "value",
    min: R_MIN,
    max: R_MAX,
    name: "Growth rate  r",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 17 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    max: 1,
    name: "Long-term state  x",
    nameLocation: "middle",
    nameGap: 56,
    nameTextStyle: { color: t.ink, fontSize: 17 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "scatter",
      data: points,
      symbolSize: 1.1, // very small points → density-based visualization
      large: true, // optimised path for the 150k-point cloud
      largeThreshold: 2000,
      itemStyle: { color: BRAND, opacity: 0.34 },
      markLine: {
        symbol: "none",
        silent: true,
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.4, opacity: 0.7 },
        // Per-item label overrides carry the position and text; fontSize 14 gives
        // comfortable legibility at both full resolution and mobile thumbnail.
        label: { color: t.inkSoft, fontSize: 14 },
        data: bifurcations.map((b) => ({
          xAxis: b.r,
          label: { formatter: b.text, position: b.position },
        })),
      },
    },
  ],
});
