// anyplot.ai
// density-rug: Density Plot with Rug Marks
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic, LCG-seeded Box-Muller) ----------------
const makeLcg = (seed) => {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
};
const rand = makeLcg(42);
const gaussian = () => {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

// Reaction times (ms) from a lexical-decision task: a fast majority group
// plus a slower, more variable tail group — a realistic bimodal shape.
const reactionTimes = [];
for (let i = 0; i < 150; i++) {
  const isSlowGroup = rand() < 0.3;
  const mean = isSlowGroup ? 485 : 320;
  const spread = isSlowGroup ? 55 : 38;
  reactionTimes.push(Math.round(mean + gaussian() * spread));
}
reactionTimes.sort((a, b) => a - b);

// --- Kernel density estimation (Gaussian kernel, Silverman bandwidth) ------
const n = reactionTimes.length;
const mean = reactionTimes.reduce((s, v) => s + v, 0) / n;
const variance = reactionTimes.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);
const bandwidth = 1.06 * std * n ** (-1 / 5);

const gaussianKernel = (u) => Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
const densityAt = (x) =>
  reactionTimes.reduce((s, v) => s + gaussianKernel((x - v) / bandwidth), 0) / (n * bandwidth);

const gridMin = reactionTimes[0] - 3 * bandwidth;
const gridMax = reactionTimes[n - 1] + 3 * bandwidth;
const gridSteps = 200;
const densityCurve = [];
for (let i = 0; i <= gridSteps; i++) {
  const x = gridMin + ((gridMax - gridMin) * i) / gridSteps;
  densityCurve.push([x, densityAt(x)]);
}
const maxDensity = Math.max(...densityCurve.map((p) => p[1]));

// Rug ticks sit below the zero line as a thin band, separated from the fill.
const tickHeight = maxDensity * 0.12;
const rugColor = `${t.palette[0]}73`; // brand green, ~45% opacity (overlap-friendly)

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "density-rug · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Reaction Time (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: gridMin,
    max: gridMax,
  },
  yAxis: {
    title: { text: "Density", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return this.value >= 0 ? this.value.toFixed(3) : "";
      },
    },
    min: -tickHeight * 1.4,
    max: maxDensity * 1.15,
    plotLines: [{ value: 0, color: t.inkSoft, width: 1, zIndex: 3 }],
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, enableMouseTracking: false },
  },
  series: [
    {
      type: "area",
      name: "Estimated density",
      data: densityCurve,
      color: t.palette[0],
      lineWidth: 2.5,
      fillOpacity: 0.25,
      threshold: 0,
      marker: { enabled: false },
    },
    {
      type: "column",
      name: "Observations",
      data: reactionTimes.map((v) => [v, -tickHeight]),
      color: rugColor,
      borderWidth: 0,
      pointWidth: 2,
      threshold: 0,
      pointPadding: 0,
      groupPadding: 0,
    },
  ],
});
