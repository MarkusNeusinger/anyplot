// anyplot.ai
// ice-basic: Individual Conditional Expectation (ICE) Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// House price predictions from a GradientBoostingRegressor as square footage
// varies, for 70 individual houses. Each house has its own latent "quality"
// level that governs how quickly the size effect on price saturates -- higher
// quality builds keep appreciating with size, modest builds plateau sooner.
// That divergence is exactly what ICE reveals and an averaged PDP curve hides.
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const N_OBSERVATIONS = 70;
const N_GRID_POINTS = 60;
const SQFT_MIN = 800;
const SQFT_MAX = 3600;

const featureGrid = Array.from({ length: N_GRID_POINTS }, (_, i) =>
  SQFT_MIN + (i / (N_GRID_POINTS - 1)) * (SQFT_MAX - SQFT_MIN),
);

const houses = Array.from({ length: N_OBSERVATIONS }, () => ({
  basePrice: 140000 + lcg() * 60000,
  quality: lcg(),
  amplitude: 220000 + lcg() * 120000,
}));

function predictPrice(house, sqft) {
  const decay = 0.0025 - house.quality * 0.0016; // higher quality -> slower saturation
  const sizeEffect = house.amplitude * (1 - Math.exp(-decay * (sqft - SQFT_MIN)));
  return house.basePrice + sizeEffect;
}

const iceCurves = houses.map((house) => featureGrid.map((sqft) => predictPrice(house, sqft)));
const pdpCurve = featureGrid.map((_, gridIndex) => {
  const total = iceCurves.reduce((sum, curve) => sum + curve[gridIndex], 0);
  return total / iceCurves.length;
});

function hexToRgba(hex, alpha) {
  const value = parseInt(hex.slice(1), 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
const iceColor = hexToRgba(t.palette[0], 0.18);

const iceDatasets = iceCurves.map((curve, i) => ({
  label: i === 0 ? "Individual houses (ICE)" : "",
  data: curve,
  borderColor: iceColor,
  borderWidth: 1.5,
  pointRadius: 0,
  fill: false,
  tension: 0.3,
}));

const pdpDataset = {
  label: "Average effect (PDP)",
  data: pdpCurve,
  borderColor: t.ink,
  borderWidth: 4,
  pointRadius: 0,
  fill: false,
  tension: 0.3,
};

new Chart(canvas, {
  type: "line",
  data: {
    labels: featureGrid.map((sqft) => Math.round(sqft)),
    datasets: [...iceDatasets, pdpDataset],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "ice-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => item.text !== "",
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 8 },
        grid: { color: t.grid },
        title: { display: true, text: "Square Footage", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `$${(value / 1000).toFixed(0)}k`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Predicted Sale Price", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
