// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Fixed-seed LCG — the browser has no seeded RNG, so this stands in for
// np.random.seed(42) to keep the sample reproducible across renders.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randomNormal(mean, std) {
  const u1 = lcgRandom() || 1e-9;
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const sampleSize = 600;
const deliveryTimes = Array.from({ length: sampleSize }, () =>
  Math.max(5, randomNormal(38, 11))
);

const binCount = 18;
const minValue = Math.min(...deliveryTimes);
const maxValue = Math.max(...deliveryTimes);
const binWidth = (maxValue - minValue) / binCount;

const binCounts = new Array(binCount).fill(0);
deliveryTimes.forEach((value) => {
  const index = Math.min(binCount - 1, Math.floor((value - minValue) / binWidth));
  binCounts[index] += 1;
});

let running = 0;
const cumulativeData = binCounts.map((count, i) => {
  running += count;
  const binEdge = minValue + (i + 1) * binWidth;
  return [Math.round(binEdge * 10) / 10, running];
});
// Anchor the curve at the first bin's lower edge so the ogive starts at zero.
cumulativeData.unshift([Math.round(minValue * 10) / 10, 0]);

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "histogram-cumulative · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Delivery Time (minutes)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Cumulative Deliveries", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    min: 0,
    max: sampleSize,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.inkSoft,
    style: { color: t.ink, fontSize: "14px" },
    formatter() {
      const pct = ((this.y / sampleSize) * 100).toFixed(1);
      return `<b>&le; ${this.x} min</b><br/>Cumulative: ${this.y} deliveries (${pct}%)`;
    },
  },
  plotOptions: {
    series: { animation: false },
    area: {
      step: "left",
      lineWidth: 2.5,
      fillOpacity: 0.25,
      marker: { enabled: false },
    },
  },
  series: [
    {
      name: "Cumulative deliveries",
      data: cumulativeData,
      color: t.palette[0],
    },
  ],
});
