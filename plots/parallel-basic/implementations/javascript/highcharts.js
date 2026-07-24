// anyplot.ai
// parallel-basic: Basic Parallel Coordinates Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 83/100 | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded Math.random().
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian(mean, std) {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const dimensions = ["Price", "Rating", "Monthly Sales", "Inventory"];
const formatters = [
  (v) => `$${v.toFixed(0)}`,
  (v) => `${v.toFixed(1)}★`,
  (v) => `${Math.round(v)} units/mo`,
  (v) => `${Math.round(v)} units`,
];

// Product segments — cheaper items sell in higher volume and carry deeper
// stock, while premium items command higher price/rating but move slower.
const segments = [
  { name: "Budget", means: [25, 3.3, 850, 1200], stds: [8, 0.4, 200, 300] },
  { name: "Mid-Range", means: [75, 4.0, 420, 600], stds: [20, 0.3, 120, 150] },
  { name: "Premium", means: [220, 4.6, 95, 150], stds: [60, 0.25, 35, 50] },
];
const clampMin = [5, 1, 10, 10];
const clampMax = [Infinity, 5, Infinity, Infinity];

const samplesPerSegment = 20;
const products = [];
segments.forEach((seg, segIndex) => {
  for (let i = 0; i < samplesPerSegment; i++) {
    products.push({
      segment: seg.name,
      segIndex,
      values: seg.means.map((m, d) =>
        Math.min(clampMax[d], Math.max(clampMin[d], gaussian(m, seg.stds[d])))
      ),
    });
  }
});

// Min-max normalize each dimension to [0, 1] so all axes share one scale.
const mins = dimensions.map((_, d) => Math.min(...products.map((p) => p.values[d])));
const maxs = dimensions.map((_, d) => Math.max(...products.map((p) => p.values[d])));

const seenSegments = new Set();
const lineSeries = products.map((p) => {
  const firstOfSegment = !seenSegments.has(p.segIndex);
  seenSegments.add(p.segIndex);
  return {
    name: p.segment,
    color: t.palette[p.segIndex],
    lineWidth: 1.5,
    opacity: 0.5,
    marker: { enabled: false },
    showInLegend: firstOfSegment,
    data: p.values.map((v, d) => ({
      y: (v - mins[d]) / (maxs[d] - mins[d]),
      custom: { real: v },
    })),
  };
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "parallel-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Product segments across price, rating, sales & inventory (normalized 0–1)",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories: dimensions,
    tickmarkPlacement: "on",
    lineWidth: 0,
    gridLineWidth: 1.5,
    gridLineColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: 0,
    max: 1,
    tickInterval: 0.25,
    title: { text: "Normalized Value", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    gridLineColor: t.grid,
    gridLineWidth: 1,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter: function () {
      const dim = dimensions[this.point.index];
      const format = formatters[this.point.index];
      return `<b>${this.series.name}</b><br>${dim}: ${format(this.point.custom.real)}`;
    },
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: lineSeries,
});
