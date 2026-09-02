// anyplot.ai
// heatmap-geographic: Geographic Heatmap for Spatial Density
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;
const TITLE =
  "Bay Area Retail Foot-Traffic Density · heatmap-geographic · javascript · muix · anyplot.ai";
// Scale the title down once it runs past the ~67-char mandated baseline
// (see prompts/plot-generator.md "Title fontsize must scale with title length").
const TITLE_FONT_SIZE = Math.max(14, Math.round(22 * Math.min(1, 67 / TITLE.length)));

// --- Deterministic PRNG (fixed-seed LCG, Box-Muller for gaussian jitter) ----
let seed = 42;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};
const gaussian = () => {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

// --- Data: retail foot-traffic check-ins across the San Francisco Bay Area --
const LON_MIN = -122.55;
const LON_MAX = -121.75;
const LAT_MIN = 37.25;
const LAT_MAX = 37.9;

// Degrees-to-km conversion at this latitude, used so the KDE bandwidth below
// reflects real city-scale distances instead of raw (anisotropic) degrees.
const KM_PER_DEG_LAT = 111;
const KM_PER_DEG_LON = 88;

const hotspots = [
  { lon: -122.42, lat: 37.775, weight: 1.0, sigmaKm: 2.6 }, // San Francisco downtown
  { lon: -122.27, lat: 37.805, weight: 0.7, sigmaKm: 3.2 }, // Oakland downtown
  { lon: -122.27, lat: 37.872, weight: 0.4, sigmaKm: 2.2 }, // Berkeley
  { lon: -121.885, lat: 37.335, weight: 0.85, sigmaKm: 3.4 }, // San Jose downtown
  { lon: -122.16, lat: 37.445, weight: 0.55, sigmaKm: 2.4 }, // Palo Alto
  { lon: -121.99, lat: 37.548, weight: 0.3, sigmaKm: 2.0 }, // Fremont
];

const visits = [];
hotspots.forEach((h) => {
  const count = Math.round(h.weight * 140);
  for (let i = 0; i < count; i += 1) {
    visits.push({
      lon: h.lon + (gaussian() * h.sigmaKm) / KM_PER_DEG_LON,
      lat: h.lat + (gaussian() * h.sigmaKm) / KM_PER_DEG_LAT,
    });
  }
});
for (let i = 0; i < 90; i += 1) {
  visits.push({
    lon: LON_MIN + rand() * (LON_MAX - LON_MIN),
    lat: LAT_MIN + rand() * (LAT_MAX - LAT_MIN),
  });
}

// --- Kernel density estimate on a coarse geographic grid --------------------
// Distances are converted to km so the kernel is isotropic in real space, and
// truncated at 3*bandwidth so far-away points can't sum into a visible tail —
// without truncation the whole region reads as one blob instead of distinct
// hotspots around each city.
const GRID_COLS = 36;
const GRID_ROWS = 22;
const BANDWIDTH_KM = 4.5;
const TRUNC_KM_SQ = (3 * BANDWIDTH_KM) ** 2;
const DENSITY_FLOOR = 0.25; // hides low-density cells so the base map reads through

const rawCells = [];
let maxDensity = 0;
for (let col = 0; col < GRID_COLS; col += 1) {
  const lon = LON_MIN + ((col + 0.5) / GRID_COLS) * (LON_MAX - LON_MIN);
  for (let row = 0; row < GRID_ROWS; row += 1) {
    const lat = LAT_MIN + ((row + 0.5) / GRID_ROWS) * (LAT_MAX - LAT_MIN);
    let density = 0;
    visits.forEach((v) => {
      const dKmLon = (lon - v.lon) * KM_PER_DEG_LON;
      const dKmLat = (lat - v.lat) * KM_PER_DEG_LAT;
      const distKmSq = dKmLon * dKmLon + dKmLat * dKmLat;
      if (distKmSq < TRUNC_KM_SQ) {
        density += Math.exp(-distKmSq / (2 * BANDWIDTH_KM * BANDWIDTH_KM));
      }
    });
    maxDensity = Math.max(maxDensity, density);
    rawCells.push({ lon, lat, density });
  }
}

const densityCells = rawCells
  .map((c) => ({ lon: c.lon, lat: c.lat, density: c.density / maxDensity }))
  .filter((c) => c.density > DENSITY_FLOOR)
  .map((c, index) => ({ id: index, x: c.lon, y: c.lat, z: c.density }));

// --- Imprint sequential colormap, translucent so the graticule shows through
const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const seqLow = hexToRgba(t.seq[0], 0.75);
const seqHigh = hexToRgba(t.seq[1], 0.88);

// --- Geographic reference graticule (basemap substitute — no map tiles are
// available in the community package, so a lon/lat grid gives spatial context)
const latLines = [37.4, 37.6, 37.8];
const lonLines = [-122.35, -122.15, -121.95];

function MapTitle() {
  const { width } = window.ANYPLOT_SIZE;
  return (
    <text
      x={width / 2}
      y={40}
      textAnchor="middle"
      dominantBaseline="hanging"
      fontSize={TITLE_FONT_SIZE}
      fontWeight={500}
      fill={t.ink}
    >
      {TITLE}
    </text>
  );
}

export default function Chart() {
  return (
    <ScatterChart
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      skipAnimation
      disableVoronoi
      margin={{ top: 90, right: 250, bottom: 90, left: 115 }}
      series={[
        {
          id: "density",
          type: "scatter",
          data: densityCells,
          markerSize: 34,
          zAxisId: "density",
          label: "Relative check-in density",
        },
      ]}
      xAxis={[
        {
          min: LON_MIN,
          max: LON_MAX,
          label: "Longitude",
          tickNumber: 4,
          valueFormatter: (v) => `${Math.abs(v).toFixed(2)}°W`,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      yAxis={[
        {
          min: LAT_MIN,
          max: LAT_MAX,
          label: "Latitude",
          tickNumber: 4,
          valueFormatter: (v) => `${v.toFixed(2)}°N`,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      zAxis={[
        {
          id: "density",
          min: 0,
          max: 1,
          // min/max must also live on colorMap itself: ContinuousColorLegend
          // reads colorMap.min/max directly (not the axis-level min/max).
          colorMap: { type: "continuous", min: 0, max: 1, color: [seqLow, seqHigh] },
        },
      ]}
      slotProps={{ legend: { hidden: true } }}
    >
      {latLines.map((lat) => (
        <ChartsReferenceLine
          key={`lat-${lat}`}
          y={lat}
          lineStyle={{ stroke: t.grid, strokeDasharray: "4 4", strokeWidth: 1 }}
          label={`${lat.toFixed(2)}°N`}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
          labelAlign="end"
        />
      ))}
      {lonLines.map((lon) => (
        <ChartsReferenceLine
          key={`lon-${lon}`}
          x={lon}
          lineStyle={{ stroke: t.grid, strokeDasharray: "4 4", strokeWidth: 1 }}
          label={`${Math.abs(lon).toFixed(2)}°W`}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
        />
      ))}
      <ContinuousColorLegend
        axisDirection="z"
        axisId="density"
        position={{ horizontal: "right", vertical: "middle" }}
        direction="column"
        length="55%"
        thickness={14}
        minLabel="Low"
        maxLabel="High"
        labelStyle={{ fontSize: 14, fill: t.inkSoft }}
      />
      <MapTitle />
    </ScatterChart>
  );
}
