// anyplot.ai
// heatmap-geographic: Geographic Heatmap for Spatial Density
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (32-bit LCG, Math.imul avoids float precision loss) -
let seed = 42;
function rand() {
  seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Data: simulated incident reports across a downtown bounding box -------
const LON_MIN = -122.52;
const LON_MAX = -122.38;
const LAT_MIN = 37.73;
const LAT_MAX = 37.81;

const hotspots = [
  { lon: -122.412, lat: 37.784, weight: 0.42, spreadLon: 0.012, spreadLat: 0.01 }, // downtown core
  { lon: -122.404, lat: 37.792, weight: 0.24, spreadLon: 0.01, spreadLat: 0.008 }, // financial district
  { lon: -122.431, lat: 37.775, weight: 0.2, spreadLon: 0.014, spreadLat: 0.011 }, // tenderloin
  { lon: -122.393, lat: 37.778, weight: 0.14, spreadLon: 0.013, spreadLat: 0.01 }, // transit hub
];

const incidents = [];
for (let i = 0; i < 900; i++) {
  const r = rand();
  let acc = 0;
  let cluster = hotspots[hotspots.length - 1];
  for (const h of hotspots) {
    acc += h.weight;
    if (r <= acc) {
      cluster = h;
      break;
    }
  }
  const lon = cluster.lon + gaussian() * cluster.spreadLon;
  const lat = cluster.lat + gaussian() * cluster.spreadLat;
  if (lon < LON_MIN || lon > LON_MAX || lat < LAT_MIN || lat > LAT_MAX) continue;
  incidents.push({ lon, lat, severity: 0.6 + rand() * 0.4 });
}

// --- Kernel density estimation on a regular grid ----------------------------
const COLS = 28;
const ROWS = 16;
const bwLon = (LON_MAX - LON_MIN) / 9;
const bwLat = (LAT_MAX - LAT_MIN) / 9;

const cells = [];
let maxDensity = 0;
for (let cy = 0; cy < ROWS; cy++) {
  for (let cx = 0; cx < COLS; cx++) {
    const lon = LON_MIN + (cx + 0.5) * ((LON_MAX - LON_MIN) / COLS);
    const lat = LAT_MIN + (cy + 0.5) * ((LAT_MAX - LAT_MIN) / ROWS);
    let density = 0;
    for (const p of incidents) {
      const dx = (p.lon - lon) / bwLon;
      const dy = (p.lat - lat) / bwLat;
      density += p.severity * Math.exp(-0.5 * (dx * dx + dy * dy));
    }
    if (density > maxDensity) maxDensity = density;
    cells.push({ lon, lat, density });
  }
}

// Hide near-zero cells so the page background reads through, like a basemap.
const DENSITY_FLOOR = 0.06;
const points = cells
  .map((c) => ({ x: c.lon, y: c.lat, d: c.density / maxDensity }))
  .filter((c) => c.d > DENSITY_FLOOR);

// --- Imprint sequential colormap (brand green -> blue) ----------------------
function lerpRGB(hexA, hexB, f) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  return a.map((v, i) => Math.round(v + (b[i] - v) * f));
}
function densityColor(f, alpha) {
  const [r, g, b] = lerpRGB(t.seq[0], t.seq[1], f);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Radius approximates half the grid spacing so hotspot cells read as a
// continuous mosaic while sparse cells stay small and let the page bg show.
const CELL_RADIUS = 21;
const bubbleData = points.map((p) => ({
  x: p.x,
  y: p.y,
  r: CELL_RADIUS * (0.55 + 0.45 * p.d),
  d: p.d,
}));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bubble",
  data: {
    datasets: [
      {
        label: "Incident density",
        data: bubbleData,
        backgroundColor: bubbleData.map((p) => densityColor(p.d, 0.35 + 0.45 * p.d)),
        borderWidth: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "heatmap-geographic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        onClick: () => {},
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          usePointStyle: true,
          generateLabels: () =>
            [0.15, 0.5, 0.85].map((f, i) => ({
              text: ["Low density", "Medium density", "High density"][i],
              fillStyle: densityColor(f, 0.8),
              strokeStyle: densityColor(f, 0.8),
              pointStyle: "circle",
              hidden: false,
              index: 0,
            })),
        },
      },
    },
    scales: {
      x: {
        min: LON_MIN,
        max: LON_MAX,
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${Number(v).toFixed(2)}°` },
        grid: { color: t.grid },
        title: { display: true, text: "Longitude", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: LAT_MIN,
        max: LAT_MAX,
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${Number(v).toFixed(2)}°` },
        grid: { color: t.grid },
        title: { display: true, text: "Latitude", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
