// anyplot.ai
// ridgeline-basic: Basic Ridgeline Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-07-25

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: monthly temperature distributions (seasonal pattern) ------------
// deterministic LCG (Numerical Recipes constants) — no seeded RNG in the browser
let seed = 42;
function nextUniform() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function nextNormal() {
  const u1 = Math.max(nextUniform(), 1e-9);
  const u2 = nextUniform();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthlyMeanC = [2, 3, 7, 12, 17, 21, 24, 23, 19, 13, 7, 3];
const monthlyStdC  = [4.2, 4.0, 3.6, 3.2, 2.8, 2.5, 2.3, 2.4, 2.7, 3.1, 3.6, 4.1];
const samplesPerMonth = 200;

const monthlySamples = months.map((_, i) =>
  Array.from({ length: samplesPerMonth },
    () => monthlyMeanC[i] + monthlyStdC[i] * nextNormal())
);

// --- Gaussian KDE, evaluated on a shared temperature grid -------------------
function gaussianKDE(samples, xGrid, bandwidth) {
  const norm = 1 / (samples.length * bandwidth * Math.sqrt(2 * Math.PI));
  return xGrid.map((x) => {
    let sum = 0;
    for (const s of samples) {
      const z = (x - s) / bandwidth;
      sum += Math.exp(-0.5 * z * z);
    }
    return sum * norm;
  });
}

const allSamples = monthlySamples.flat();
const xMin = Math.floor(Math.min(...allSamples) - 3);
const xMax = Math.ceil(Math.max(...allSamples) + 3);
const gridPoints = 140;
const xGrid = Array.from({ length: gridPoints },
  (_, i) => xMin + (i / (gridPoints - 1)) * (xMax - xMin));

// Silverman's rule of thumb per group keeps each ridge appropriately smooth
const bandwidths = monthlyStdC.map((std) => 1.06 * std * Math.pow(samplesPerMonth, -0.2));

// --- Stack ridges: one baseline offset per month, peaks scaled to overlap --
const rowStep = 1;
const ridgeHeight = 1.7; // ~65-70% overlap into the row(s) above
const offsets = months.map((_, i) => i * rowStep);

const ridgeColorFrom = Highcharts.color(t.seq[0]);
const ridgeColors = months.map((_, i) =>
  ridgeColorFrom.tweenTo(Highcharts.color(t.seq[1]), i / (months.length - 1))
);

const series = months.map((month, i) => {
  const density = gaussianKDE(monthlySamples[i], xGrid, bandwidths[i]);
  const peak = Math.max(...density);
  const offset = offsets[i];
  return {
    name: month,
    color: ridgeColors[i],
    fillColor: ridgeColors[i],
    fillOpacity: 0.92,
    lineWidth: 2,
    threshold: offset,
    data: xGrid.map((x, j) => [x, offset - (density[j] / peak) * ridgeHeight]),
  };
});

// Render back-to-front (Dec first, Jan last) so each ridge's peak tucks
// behind the ridge in the row above it, matching top-down chronological order.
const orderedSeries = series.slice().reverse();

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "ridgeline-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Temperature (°C)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: xMin,
    max: xMax,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: null },
    reversed: true,
    min: -ridgeHeight,
    max: offsets[offsets.length - 1] + rowStep,
    tickPositions: offsets,
    gridLineWidth: 0,
    lineWidth: 0,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return months[Math.round(this.value / rowStep)];
      },
    },
  },
  legend: { enabled: false },
  plotOptions: {
    series: {
      animation: false,
      marker: { enabled: false, states: { hover: { enabled: false } } },
      enableMouseTracking: false,
    },
    area: { threshold: undefined },
  },
  series: orderedSeries,
});
