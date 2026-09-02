// anyplot.ai
// map-marker-clustered: Clustered Marker Map
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const CATEGORIES = ["Flagship", "Standard", "Outlet"];

// --- Deterministic PRNG (browser has no seeded Math.random) ----------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function rand() {
    state = (1103515245 * state + 12345) >>> 0;
    return state / 4294967296;
  };
}
function gaussian(rand) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}
function pickCategory(rand, weights) {
  const r = rand();
  if (r < weights[0]) return "Flagship";
  if (r < weights[0] + weights[1]) return "Standard";
  return "Outlet";
}

// --- Data: individual store locations around metro hubs --------------------
// Each hub carries its own Flagship/Standard/Outlet mix, so different regions
// have a different dominant store type on the clustered map.
const rand = makeLcg(42);
const HUBS = [
  { lon: -122.3, lat: 47.6, weights: [0.1, 0.75, 0.15], count: 35 }, // Seattle — Standard-heavy
  { lon: -118.2, lat: 34.0, weights: [0.55, 0.35, 0.1], count: 65 }, // Los Angeles — Flagship-heavy
  { lon: -104.9, lat: 39.7, weights: [0.05, 0.35, 0.6], count: 20 }, // Denver — Outlet-heavy
  { lon: -96.8, lat: 32.8, weights: [0.1, 0.7, 0.2], count: 55 }, // Dallas — Standard-heavy
  { lon: -87.6, lat: 41.9, weights: [0.15, 0.65, 0.2], count: 70 }, // Chicago — Standard-heavy
  { lon: -84.4, lat: 33.7, weights: [0.05, 0.35, 0.6], count: 25 }, // Atlanta — Outlet-heavy
  { lon: -74.0, lat: 40.7, weights: [0.6, 0.35, 0.05], count: 80 }, // New York — Flagship-heavy
  { lon: -80.2, lat: 25.8, weights: [0.15, 0.6, 0.25], count: 40 }, // Miami — Standard-heavy
];

const stores = [];
HUBS.forEach((hub) => {
  for (let i = 0; i < hub.count; i += 1) {
    stores.push({
      lon: hub.lon + gaussian(rand) * 0.55,
      lat: hub.lat + gaussian(rand) * 0.45,
      category: pickCategory(rand, hub.weights),
    });
  }
});

// --- Cluster stores by greedy nearest-centroid grouping (current zoom level) -
// A point joins the closest existing cluster within CLUSTER_RADIUS_DEG, else it
// seeds a new one — the same distance-based grouping marker-cluster libraries
// use, re-evaluated whenever the zoom level (radius) changes.
const CLUSTER_RADIUS_DEG = 3.5;
const rawClusters = [];
stores.forEach((store) => {
  let nearest = null;
  let nearestDist = Infinity;
  rawClusters.forEach((cluster) => {
    const dLon = store.lon - cluster.lonSum / cluster.count;
    const dLat = store.lat - cluster.latSum / cluster.count;
    const dist = Math.sqrt(dLon * dLon + dLat * dLat);
    if (dist < CLUSTER_RADIUS_DEG && dist < nearestDist) {
      nearestDist = dist;
      nearest = cluster;
    }
  });
  if (!nearest) {
    nearest = { lonSum: 0, latSum: 0, count: 0, byCategory: {} };
    rawClusters.push(nearest);
  }
  nearest.lonSum += store.lon;
  nearest.latSum += store.lat;
  nearest.count += 1;
  nearest.byCategory[store.category] = (nearest.byCategory[store.category] || 0) + 1;
});

const radiusFor = (count) => Math.min(70, Math.max(10, 8 + 6 * Math.sqrt(count)));

const clusters = rawClusters.map((cell) => {
  const dominant = CATEGORIES.reduce(
    (best, cat) => ((cell.byCategory[cat] || 0) > (cell.byCategory[best] || 0) ? cat : best),
    CATEGORIES[0],
  );
  return {
    x: cell.lonSum / cell.count,
    y: cell.latSum / cell.count,
    r: radiusFor(cell.count),
    count: cell.count,
    category: dominant,
  };
});

const datasets = CATEGORIES.map((category, i) => ({
  label: category,
  data: clusters.filter((c) => c.category === category),
  backgroundColor: t.palette[i],
  borderColor: t.pageBg,
  borderWidth: 2,
}));

// --- Simplified contiguous-US outline for geographic context ---------------
const US_OUTLINE = [
  [-124.7, 48.4], [-124.2, 43.8], [-122.5, 37.8], [-117.2, 32.7],
  [-114.7, 32.5], [-111.0, 31.3], [-108.2, 31.3], [-106.5, 31.8],
  [-104.9, 29.4], [-99.5, 26.4], [-97.4, 25.9], [-97.1, 27.8],
  [-93.8, 29.7], [-89.4, 29.2], [-85.0, 29.7], [-82.7, 27.9],
  [-81.5, 25.2], [-80.1, 25.8], [-80.0, 26.7], [-81.5, 30.3],
  [-79.9, 32.8], [-77.9, 34.2], [-76.0, 36.9], [-75.5, 39.4],
  [-74.0, 40.7], [-70.3, 41.8], [-70.3, 43.7], [-67.0, 45.1],
  [-71.5, 45.0], [-79.2, 43.3], [-83.1, 42.3], [-84.5, 46.5],
  [-89.6, 48.0], [-95.2, 49.0], [-104.0, 49.0], [-114.0, 49.0],
  [-123.0, 49.0],
];

const basemapPlugin = {
  id: "basemapOutline",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.beginPath();
    US_OUTLINE.forEach(([lon, lat], i) => {
      const px = scales.x.getPixelForValue(lon);
      const py = scales.y.getPixelForValue(lat);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.closePath();
    ctx.fillStyle = t.elevatedBg;
    ctx.fill();
    ctx.globalAlpha = 0.6;
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  },
};

const clusterCountPlugin = {
  id: "clusterCount",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.font = "600 15px sans-serif";
    ctx.fillStyle = "#FFFFFF";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    chart.data.datasets.forEach((dataset) => {
      dataset.data.forEach((point) => {
        const px = scales.x.getPixelForValue(point.x);
        const py = scales.y.getPixelForValue(point.y);
        ctx.fillText(String(point.count), px, py);
      });
    });
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bubble",
  data: { datasets },
  plugins: [basemapPlugin, clusterCountPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 16 },
    plugins: {
      title: {
        display: true,
        text: "map-marker-clustered · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true, pointStyle: "circle" },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const point = ctx.raw;
            const noun = point.count === 1 ? "store" : "stores";
            return `${ctx.dataset.label}: ${point.count} ${noun}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: -128,
        max: -63,
        title: { display: true, text: "Longitude", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}°` },
        grid: { color: t.grid },
      },
      y: {
        type: "linear",
        min: 23,
        max: 50,
        title: { display: true, text: "Latitude", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}°` },
        grid: { color: t.grid },
      },
    },
  },
});
