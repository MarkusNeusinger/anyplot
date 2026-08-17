// anyplot.ai
// ice-basic: Individual Conditional Expectation (ICE) Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-17

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const N_HOUSES = 90;
const N_GRID = 60;
const SQFT_MIN = 800;
const SQFT_MAX = 3200;

const grid = Array.from(
  { length: N_GRID },
  (_, i) => SQFT_MIN + (i / (N_GRID - 1)) * (SQFT_MAX - SQFT_MIN)
);

// Each house gets its own base price, slope and curvature — a stand-in for a
// GradientBoostingRegressor's individual conditional expectation curve.
const iceCurves = [];
const observedSqft = [];
for (let h = 0; h < N_HOUSES; h++) {
  const basePrice = 140000 + rand() * 90000;
  const pricePerSqft = 90 + rand() * 60;
  const curvature = -6 + rand() * 12; // diminishing vs. accelerating returns
  const noise = (rand() - 0.5) * 12000;
  observedSqft.push(SQFT_MIN + rand() * (SQFT_MAX - SQFT_MIN));

  const curve = grid.map((sqft) => {
    const dx = sqft - SQFT_MIN;
    const price = basePrice + pricePerSqft * dx + curvature * 0.001 * dx * dx + noise;
    return [sqft, Math.round(price)];
  });
  iceCurves.push(curve);
}

// Partial dependence (PDP) — the average of all ICE curves at each grid point.
const pdp = grid.map((sqft, gi) => {
  const avg = iceCurves.reduce((sum, curve) => sum + curve[gi][1], 0) / N_HOUSES;
  return [sqft, Math.round(avg)];
});

const allPrices = iceCurves.flat().map((p) => p[1]);
const priceMin = Math.min(...allPrices);
const priceMax = Math.max(...allPrices);
const rugY = priceMin - (priceMax - priceMin) * 0.03;
const rug = observedSqft.map((sqft) => [sqft, rugY]);

// --- Custom marker: a short vertical tick for the rug plot ------------------
Highcharts.SVGRenderer.prototype.symbols.rugtick = (x, y, w, h) => [
  "M", x + w / 2, y,
  "L", x + w / 2, y + h,
];

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
    text: "ice-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Predicted price vs. square footage — one curve per house, average in bold",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Square Footage", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: SQFT_MIN,
    max: SQFT_MAX,
  },
  yAxis: {
    title: { text: "Predicted House Price", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return "$" + Math.round(this.value / 1000) + "k";
      },
    },
    min: priceMin - (priceMax - priceMin) * 0.08,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    style: { color: t.ink },
    formatter() {
      return `${Math.round(this.x)} sq ft<br/><b>$${Math.round(this.y).toLocaleString()}</b>`;
    },
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
    line: { enableMouseTracking: false },
  },
  series: [
    ...iceCurves.map((curve, i) => ({
      type: "line",
      name: i === 0 ? "Individual houses (ICE)" : undefined,
      showInLegend: i === 0,
      data: curve,
      color: "rgba(0, 158, 115, 0.18)",
      lineWidth: 1.25,
    })),
    {
      type: "line",
      name: "Average effect (PDP)",
      data: pdp,
      color: t.ink,
      lineWidth: 4,
      enableMouseTracking: true,
      zIndex: 5,
    },
    {
      type: "scatter",
      name: "Observed sq ft (rug)",
      data: rug,
      color: t.inkSoft,
      marker: {
        enabled: true,
        symbol: "rugtick",
        radius: 7,
        fillColor: "none",
        lineColor: t.inkSoft,
        lineWidth: 2,
      },
      enableMouseTracking: false,
    },
  ],
});
