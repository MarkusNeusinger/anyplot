// anyplot.ai
// map-tile-background: Map with Tile Background
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// European landmarks with annual visitor counts (millions). Longitude/latitude
// double as the chart's x/y coordinates (a simple equirectangular projection),
// so Chart.js's own linear scales and gridlines become the map's graticule.
const landmarks = [
  { name: "Eiffel Tower", city: "Paris", lat: 48.858, lon: 2.294, visitorsM: 6.9 },
  { name: "British Museum", city: "London", lat: 51.519, lon: -0.127, visitorsM: 5.8 },
  { name: "Colosseum", city: "Rome", lat: 41.89, lon: 12.492, visitorsM: 7.6 },
  { name: "Sagrada Familia", city: "Barcelona", lat: 41.404, lon: 2.174, visitorsM: 4.7 },
  { name: "Anne Frank House", city: "Amsterdam", lat: 52.375, lon: 4.884, visitorsM: 1.2 },
  { name: "Brandenburg Gate", city: "Berlin", lat: 52.516, lon: 13.378, visitorsM: 3.8 },
  { name: "Acropolis", city: "Athens", lat: 37.971, lon: 23.726, visitorsM: 3.5 },
  { name: "Neuschwanstein Castle", city: "Bavaria", lat: 47.557, lon: 10.75, visitorsM: 1.5 },
  { name: "Prado Museum", city: "Madrid", lat: 40.414, lon: -3.692, visitorsM: 3.2 },
  { name: "Charles Bridge", city: "Prague", lat: 50.086, lon: 14.411, visitorsM: 4.1 },
  { name: "Edinburgh Castle", city: "Edinburgh", lat: 55.949, lon: -3.2, visitorsM: 2.2 },
  { name: "Alhambra", city: "Granada", lat: 37.176, lon: -3.588, visitorsM: 2.7 },
];
const visitorValues = landmarks.map((l) => l.visitorsM);
const minVisitors = Math.min(...visitorValues);
const maxVisitors = Math.max(...visitorValues);
const radiusFor = (v) => {
  const ratio = (v - minVisitors) / (maxVisitors - minVisitors);
  return 10 + ratio * 22; // few points -> prominent bubbles
};

// Simplified Western/Central Europe coastline (lon/lat) — stylized geographic
// context only, not survey-accurate. Used purely to pick "land" vs "sea" tile
// shading for the basemap; not itself a data series.
const EUROPE_COASTLINE = [
  [-10, 44], [-9, 38], [-6, 36.5], [-1, 36.8], [3, 39], [3, 41.5],
  [7, 43.5], [10, 44], [13, 42], [16, 40], [19, 40], [22, 37],
  [24, 37.5], [24, 40], [21, 39.5], [23, 41.5], [26, 42], [28, 41],
  [29, 41.5], [28, 45], [30, 46], [28, 46.5], [30, 49], [24, 49],
  [23, 52], [19, 54.5], [14, 54.5], [8, 53.5], [4, 51.4], [1.5, 50.9],
  [-2, 49.5], [-4.5, 48.5], [-2.5, 47.2], [-4.5, 47.9], [-1, 46.2],
  [-1.7, 43.5], [-9, 43],
];
const BRITISH_ISLES = [
  [-5.5, 50], [-3, 50.5], [1.3, 51.9], [0.5, 53.5], [-2, 55.8],
  [-3, 58.6], [-5.2, 58.5], [-6, 56], [-5, 53.4], [-6.5, 55.3],
  [-8.5, 54.5], [-10, 52], [-8, 51.5], [-5.5, 50],
];

const pointInPolygon = (lon, lat, polygon) => {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    const intersects = yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
};
const isLand = (lon, lat) =>
  pointInPolygon(lon, lat, EUROPE_COASTLINE) || pointInPolygon(lon, lat, BRITISH_ISLES);

// --- Custom draw plugins -----------------------------------------------------
// Chart.js has no native tile/raster basemap layer, and the offline render
// harness cannot fetch real OpenStreetMap/CartoDB/satellite tiles. This plugin
// draws a stylized tile grid directly with the canvas context, projected
// through the chart's own linear scales — land/sea tiles are shaded
// differently and a visible tile seam grid stands in for a raster slippy-map
// tileset, giving the "tile background" concept honestly without pretending
// to be live provider imagery.
const TILE_COLUMNS = 14;
const tileBasemapPlugin = {
  id: "tileBasemap",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const tileSize = chartArea.width / TILE_COLUMNS;
    const rows = Math.ceil(chartArea.height / tileSize);
    const landFill = window.ANYPLOT_THEME === "light" ? "rgba(107, 106, 99, 0.16)" : "rgba(168, 167, 159, 0.16)";
    const landFillAlt = window.ANYPLOT_THEME === "light" ? "rgba(107, 106, 99, 0.22)" : "rgba(168, 167, 159, 0.22)";
    const seaFill = window.ANYPLOT_THEME === "light" ? "rgba(68, 103, 163, 0.08)" : "rgba(68, 103, 163, 0.12)";
    const seaFillAlt = window.ANYPLOT_THEME === "light" ? "rgba(68, 103, 163, 0.13)" : "rgba(68, 103, 163, 0.18)";

    ctx.save();
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < TILE_COLUMNS; col += 1) {
        const x = chartArea.left + col * tileSize;
        const y = chartArea.top + row * tileSize;
        const w = Math.min(tileSize, chartArea.right - x);
        const h = Math.min(tileSize, chartArea.bottom - y);
        if (w <= 0 || h <= 0) continue;
        const centerLon = scales.x.getValueForPixel(x + w / 2);
        const centerLat = scales.y.getValueForPixel(y + h / 2);
        const checker = (row + col) % 2 === 0;
        const land = isLand(centerLon, centerLat);
        ctx.fillStyle = land ? (checker ? landFillAlt : landFill) : checker ? seaFillAlt : seaFill;
        ctx.fillRect(x, y, w, h);
        ctx.strokeRect(x, y, w, h);
      }
    }
    ctx.restore();
  },
};

// Small caption naming the basemap style honestly (illustrative tile grid,
// not a live tile-provider fetch), sitting in the empty Atlantic corner.
const basemapCaptionPlugin = {
  id: "basemapCaption",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    ctx.save();
    ctx.font = "12px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textAlign = "left";
    ctx.textBaseline = "bottom";
    ctx.fillText("Basemap: stylized tile grid (offline render, no live tile provider)", chartArea.left + 4, chartArea.bottom - 4);
    ctx.restore();
  },
};

const labelPlugin = {
  id: "landmarkLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.font = "13px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    landmarks.forEach((l) => {
      const x = scales.x.getPixelForValue(l.lon);
      const y = scales.y.getPixelForValue(l.lat);
      ctx.fillText(l.name, x + radiusFor(l.visitorsM) + 6, y);
    });
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Title (scale fontsize to the rendered length, see plot-generator.md) ---
const title = "European Landmark Visitors · map-tile-background · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bubble",
  data: {
    datasets: [
      {
        label: "Landmarks",
        data: landmarks.map((l) => ({ x: l.lon, y: l.lat, r: radiusFor(l.visitorsM) })),
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 1.5,
      },
    ],
  },
  plugins: [tileBasemapPlugin, basemapCaptionPlugin, labelPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 16, right: 120, bottom: 16, left: 16 } },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleFontSize, weight: "500" },
      },
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const l = landmarks[ctx.dataIndex];
            return `${l.name}, ${l.city}: ${l.visitorsM}M visitors/year`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: -12,
        max: 32,
        title: { display: true, text: "Longitude", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 4, callback: (v) => `${v}°` },
        grid: { color: t.grid },
      },
      y: {
        type: "linear",
        min: 35,
        max: 58,
        title: { display: true, text: "Latitude", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 4, callback: (v) => `${v}°` },
        grid: { color: t.grid },
      },
    },
  },
});
