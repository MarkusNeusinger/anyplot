// anyplot.ai
// heatmap-geographic: Geographic Heatmap for Spatial Density
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const KM_PER_DEG = 111.32; // km per degree of latitude, and of longitude at the equator
const PAD_SHARE = 0.04; // map padding around the points, as a share of their extent
const BANDWIDTH_SHARE = 0.0625; // Gaussian kernel bandwidth as a share of the larger point extent in km
const KERNEL_CUTOFF = 3; // the kernel is truncated at this many bandwidths
const RASTER_COLS = 240; // density samples across the map width
const DENSITY_FLOOR = 0.12; // relative density below which the layer is fully transparent
const MAX_ALPHA = 0.92; // opacity of the layer at the peak density
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];
const DENSITY_LABEL = "Relative density (peak = 1)";
const TITLE = "heatmap-geographic · javascript · muix · anyplot.ai";
const TITLE_H = 92;
const MARGIN = { top: 16, right: 150, bottom: 16, left: 16 };
const X_AXIS_H = 64;
const Y_AXIS_W = 96;

// Columns: set these to your data's column names
const LATITUDE = "Latitude"; // role: latitude
const LONGITUDE = "Longitude"; // role: longitude

// Data: replace this block with your own records, one object per row, and the basemap of your region
// Retail foot-traffic check-ins across the San Francisco Bay Area: six downtown clusters plus scattered visits.
// Basemap: one simplified polygon of ocean and bay water as [longitude, latitude] pairs, and the cluster places.
const WATER = [
  [-123.2, 38.2], [-122.69, 37.91], [-122.645, 37.9], [-122.58, 37.86], [-122.56, 37.835], [-122.53, 37.816],
  [-122.495, 37.82], [-122.478, 37.826], [-122.48, 37.857], [-122.465, 37.87], [-122.45, 37.875], [-122.48, 37.91],
  [-122.5, 37.93], [-122.49, 37.945], [-122.46, 37.99], [-122.47, 38.05], [-122.36, 38.05], [-122.43, 37.965],
  [-122.42, 37.94], [-122.37, 37.91], [-122.325, 37.9], [-122.318, 37.888], [-122.315, 37.866], [-122.298, 37.842],
  [-122.315, 37.826], [-122.325, 37.802], [-122.322, 37.782], [-122.28, 37.76], [-122.25, 37.75], [-122.215, 37.712],
  [-122.185, 37.695], [-122.15, 37.64], [-122.13, 37.61], [-122.1, 37.565], [-122.075, 37.535], [-122.04, 37.51],
  [-121.99, 37.49], [-121.95, 37.465], [-121.97, 37.43], [-122.02, 37.42], [-122.07, 37.435], [-122.105, 37.455],
  [-122.13, 37.47], [-122.17, 37.49], [-122.205, 37.51], [-122.24, 37.54], [-122.255, 37.56], [-122.295, 37.575],
  [-122.325, 37.59], [-122.358, 37.605], [-122.375, 37.635], [-122.38, 37.665], [-122.385, 37.68], [-122.38, 37.71],
  [-122.358, 37.728], [-122.375, 37.745], [-122.383, 37.762], [-122.386, 37.776], [-122.388, 37.79], [-122.394, 37.8],
  [-122.405, 37.809], [-122.42, 37.81], [-122.445, 37.807], [-122.465, 37.806], [-122.477, 37.81], [-122.485, 37.793],
  [-122.512, 37.78], [-122.51, 37.76], [-122.506, 37.735], [-122.502, 37.712], [-122.496, 37.688], [-122.494, 37.665],
  [-122.493, 37.635], [-122.516, 37.592], [-122.515, 37.545], [-122.5, 37.497], [-122.455, 37.475], [-122.437, 37.44],
  [-122.41, 37.375], [-122.405, 37.32], [-122.41, 37.265], [-122.395, 37.185], [-122.33, 37.11], [-122.19, 37.01],
  [-122.19, 36.9], [-123.2, 36.9],
];
const PLACES = [
  { name: "San Francisco", lon: -122.419, lat: 37.775 },
  { name: "Oakland", lon: -122.271, lat: 37.804 },
  { name: "Berkeley", lon: -122.273, lat: 37.871 },
  { name: "Palo Alto", lon: -122.143, lat: 37.442 },
  { name: "Fremont", lon: -121.989, lat: 37.548 },
  { name: "San Jose", lon: -121.886, lat: 37.338 },
];
const data = (() => {
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
  const hotspots = [
    { lon: -122.42, lat: 37.775, weight: 1.0, sigmaKm: 2.6 },
    { lon: -122.27, lat: 37.805, weight: 0.7, sigmaKm: 3.2 },
    { lon: -122.27, lat: 37.872, weight: 0.4, sigmaKm: 2.2 },
    { lon: -121.885, lat: 37.335, weight: 0.85, sigmaKm: 3.4 },
    { lon: -122.16, lat: 37.445, weight: 0.55, sigmaKm: 2.4 },
    { lon: -121.99, lat: 37.548, weight: 0.3, sigmaKm: 2.0 },
  ];
  const rows: { [LATITUDE]: number; [LONGITUDE]: number }[] = [];
  hotspots.forEach((h) => {
    for (let i = 0; i < Math.round(h.weight * 140); i += 1) {
      const lon = h.lon + (gaussian() * h.sigmaKm) / 88;
      const lat = h.lat + (gaussian() * h.sigmaKm) / 111;
      rows.push({ [LATITUDE]: Math.round(lat * 1e5) / 1e5, [LONGITUDE]: Math.round(lon * 1e5) / 1e5 });
    }
  });
  for (let i = 0; i < 90; i += 1) {
    const lon = -122.55 + rand() * 0.8;
    const lat = 37.25 + rand() * 0.65;
    rows.push({ [LATITUDE]: Math.round(lat * 1e5) / 1e5, [LONGITUDE]: Math.round(lon * 1e5) / 1e5 });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const points = data.filter((d) => Number.isFinite(d[LATITUDE]) && Number.isFinite(d[LONGITUDE]));
const lonLo = Math.min(...points.map((d) => d[LONGITUDE]));
const lonHi = Math.max(...points.map((d) => d[LONGITUDE]));
const latLo = Math.min(...points.map((d) => d[LATITUDE]));
const latHi = Math.max(...points.map((d) => d[LATITUDE]));
const meanLat = (latLo + latHi) / 2;
const cosLat = Math.cos((meanLat * Math.PI) / 180);

// Map extent: the padded point extent, widened on the short side so px per degree of latitude
// equals px per degree of longitude divided by cos(mean latitude)
const drawW = SIZE.width - MARGIN.left - MARGIN.right - Y_AXIS_W;
const drawH = SIZE.height - TITLE_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;
const lonSpan = (lonHi - lonLo) * (1 + 2 * PAD_SHARE);
const latSpan = (latHi - latLo) * (1 + 2 * PAD_SHARE);
const lonView = Math.max(lonSpan, (latSpan * drawW) / drawH / cosLat);
const latView = Math.max(latSpan, (lonSpan * cosLat * drawH) / drawW);
const xMin = (lonLo + lonHi) / 2 - lonView / 2;
const xMax = (lonLo + lonHi) / 2 + lonView / 2;
const yMin = (latLo + latHi) / 2 - latView / 2;
const yMax = (latLo + latHi) / 2 + latView / 2;

// Gaussian kernel density in km, sampled on a raster over the map extent (row 0 at the north edge)
const kmPerDegLon = KM_PER_DEG * cosLat;
const bandwidth = BANDWIDTH_SHARE * Math.max((lonHi - lonLo) * kmPerDegLon, (latHi - latLo) * KM_PER_DEG);
const cutoffSq = (KERNEL_CUTOFF * bandwidth) ** 2;
const rasterRows = Math.round((RASTER_COLS * drawH) / drawW);
const density = new Float32Array(RASTER_COLS * rasterRows);
for (let row = 0; row < rasterRows; row += 1) {
  const lat = yMax - ((row + 0.5) / rasterRows) * (yMax - yMin);
  for (let col = 0; col < RASTER_COLS; col += 1) {
    const lon = xMin + ((col + 0.5) / RASTER_COLS) * (xMax - xMin);
    let sum = 0;
    for (const p of points) {
      const dx = (lon - p[LONGITUDE]) * kmPerDegLon;
      const dy = (lat - p[LATITUDE]) * KM_PER_DEG;
      const distSq = dx * dx + dy * dy;
      if (distSq < cutoffSq) sum += Math.exp(-distSq / (2 * bandwidth * bandwidth));
    }
    density[row * RASTER_COLS + col] = sum;
  }
}
const peak = density.reduce((m, v) => Math.max(m, v), 0);

// Imprint sequential ramp with a matching opacity ramp, painted once into an offscreen canvas
const SEQ_RGB = t.seq.map((hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
const canvas = document.createElement("canvas");
canvas.width = RASTER_COLS;
canvas.height = rasterRows;
const ctx = canvas.getContext("2d");
const pixels = ctx.createImageData(RASTER_COLS, rasterRows);
density.forEach((v, i) => {
  const z = v / peak;
  SEQ_RGB[0].forEach((c: number, k: number) => {
    pixels.data[i * 4 + k] = Math.round(c + (SEQ_RGB[1][k] - c) * z);
  });
  pixels.data[i * 4 + 3] = z <= DENSITY_FLOOR ? 0 : Math.round(((z - DENSITY_FLOOR) / (1 - DENSITY_FLOOR)) * MAX_ALPHA * 255);
});
ctx.putImageData(pixels, 0, 0);
const densityImage = canvas.toDataURL("image/png");
const floorColor = `rgb(${SEQ_RGB[0].map((c: number, k: number) => Math.round(c + (SEQ_RGB[1][k] - c) * DENSITY_FLOOR)).join(", ")})`;

const subtitle = `n = ${points.length} points · Gaussian kernel density, bandwidth ${bandwidth.toFixed(1)} km · equal ground scale at ${meanLat.toFixed(1)}° latitude`;

function WaterLayer() {
  const xScale = useXScale() as unknown as (v: number) => number;
  const yScale = useYScale() as unknown as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();
  const d = `${WATER.map(([lon, lat], i) => `${i === 0 ? "M" : "L"}${xScale(lon)},${yScale(lat)}`).join(" ")} Z`;
  return (
    <g>
      <defs>
        <clipPath id="map-clip">
          <rect x={left} y={top} width={width} height={height} />
        </clipPath>
      </defs>
      <path d={d} fill={t.grid} clipPath="url(#map-clip)" />
    </g>
  );
}

function DensityLayer() {
  const xScale = useXScale() as unknown as (v: number) => number;
  const yScale = useYScale() as unknown as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();
  const d = `${WATER.map(([lon, lat], i) => `${i === 0 ? "M" : "L"}${xScale(lon)},${yScale(lat)}`).join(" ")} Z`;
  const barX = left + width + 32;
  const barW = 22;
  return (
    <g>
      <defs>
        <linearGradient id="density-colorbar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} stopOpacity={0} />
          <stop offset={`${DENSITY_FLOOR * 100}%`} stopColor={floorColor} stopOpacity={0} />
          <stop offset="100%" stopColor={t.seq[1]} stopOpacity={MAX_ALPHA} />
        </linearGradient>
      </defs>
      <image
        href={densityImage}
        x={xScale(xMin)}
        y={yScale(yMax)}
        width={xScale(xMax) - xScale(xMin)}
        height={yScale(yMin) - yScale(yMax)}
        preserveAspectRatio="none"
      />
      <path d={d} fill="none" stroke={t.inkSoft} strokeWidth={1.25} strokeLinejoin="round" clipPath="url(#map-clip)" />
      {PLACES.filter((p) => p.lon > xMin && p.lon < xMax && p.lat > yMin && p.lat < yMax).map((p) => (
        <g key={p.name}>
          <circle cx={xScale(p.lon)} cy={yScale(p.lat)} r={3.5} fill={t.ink} />
          <text
            x={xScale(p.lon) + 8}
            y={yScale(p.lat)}
            dominantBaseline="central"
            fontSize={15}
            fontWeight={600}
            fill={t.ink}
            stroke={t.pageBg}
            strokeWidth={4}
            paintOrder="stroke"
          >
            {p.name}
          </text>
        </g>
      ))}
      <rect x={barX} y={top} width={barW} height={height} fill="url(#density-colorbar)" stroke={t.inkSoft} strokeWidth={1} />
      {COLORBAR_TICKS.map((tick) => {
        const ty = top + height * (1 - tick);
        return (
          <g key={tick}>
            <line x1={barX + barW} x2={barX + barW + 6} y1={ty} y2={ty} stroke={t.inkSoft} strokeWidth={1} />
            <text x={barX + barW + 10} y={ty} fontSize={14} fill={t.inkSoft} dominantBaseline="central">
              {tick.toFixed(2)}
            </text>
          </g>
        );
      })}
      <text
        x={barX + barW + 70}
        y={top + height / 2}
        fontSize={16}
        fill={t.ink}
        textAnchor="middle"
        transform={`rotate(-90, ${barX + barW + 70}, ${top + height / 2})`}
      >
        {DENSITY_LABEL}
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <Box sx={{ width: SIZE.width, height: SIZE.height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", px: "24px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <ChartsContainer
        width={SIZE.width}
        height={SIZE.height - TITLE_H}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: LONGITUDE,
            height: X_AXIS_H,
            tickNumber: 6,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(2)}°${v < 0 ? "W" : "E"}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            label: LATITUDE,
            width: Y_AXIS_W,
            tickNumber: 6,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(2)}°${v < 0 ? "S" : "N"}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeDasharray: "4 4" },
        }}
      >
        <WaterLayer />
        <ChartsGrid vertical horizontal />
        <DensityLayer />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
