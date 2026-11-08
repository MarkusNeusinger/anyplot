// anyplot.ai
// hexbin-map-geographic: Hexagonal Binning Map
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-25
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useDrawingArea, useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEX_RADIUS_SHARE = 0.032; // hexagon radius as a share of the projected map width
const PAD_SHARE = 0.06; // map padding around the points, as a share of their extent
const HEX_OPACITY = 0.62; // translucent cells let the base map show through
const KM_PER_DEG_LAT = 111.2; // length of one degree of latitude

// Columns: set these to your data's column names
const LON = "Longitude"; // role: lon
const LAT = "Latitude"; // role: lat

// Data: replace this block with your own records, one object per point
// Synthetic gray-whale and common-dolphin sighting reports off Southern
// California: clusters offshore of three whale-watching launch points (Santa
// Barbara Channel, Dana Point, La Jolla) plus sparse sightings up and down the
// coast, every report at least 15 km from the shore.
// Base map geometry: approximate real coastline vertices, north to south, and
// the land polygon east of it.
const COASTLINE = [
  [-120.64, 35.14], // Pismo Beach
  [-120.64, 34.9], // Point Sal
  [-120.65, 34.58], // Point Arguello
  [-120.47, 34.45], // Point Conception
  [-119.84, 34.41], // Santa Barbara
  [-119.3, 34.28], // Ventura
  [-119.1, 34.09], // Point Mugu
  [-118.8, 34.03], // Malibu
  [-118.5, 33.99], // Santa Monica
  [-118.41, 33.74], // Palos Verdes
  [-118.19, 33.75], // Long Beach
  [-117.93, 33.6], // Newport Beach
  [-117.7, 33.46], // Dana Point
  [-117.38, 33.2], // Oceanside
  [-117.27, 32.85], // La Jolla
  [-117.17, 32.72], // San Diego Bay
  [-117.13, 32.55], // Point Loma
  [-117.12, 32.53], // Tijuana
  [-117.06, 32.35], // Rosarito
  [-116.62, 31.87], // Ensenada
];
const LAND = [...COASTLINE, [-114.0, 31.87], [-114.0, 35.14]];

const data = (() => {
  let seed = 42;
  const rand = () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const minShoreKm = 15; // no report closer to the shore than this
  const cosRef = Math.cos((33.5 * Math.PI) / 180);
  // Distance from a point at sea to the coastline in km; -1 for a point on land
  const offshoreKm = (lon: number, lat: number) => {
    let coastLon = -Infinity;
    for (let i = 0; i < COASTLINE.length - 1; i += 1) {
      const [lonA, latA] = COASTLINE[i];
      const [lonB, latB] = COASTLINE[i + 1];
      if ((lat - latA) * (lat - latB) <= 0) {
        coastLon = lonA + ((lat - latA) / (latB - latA)) * (lonB - lonA);
        break;
      }
    }
    if (lon >= coastLon) return -1;
    let nearest = Infinity;
    for (let i = 0; i < COASTLINE.length - 1; i += 1) {
      const ax = COASTLINE[i][0] * cosRef;
      const ay = COASTLINE[i][1];
      const dx = COASTLINE[i + 1][0] * cosRef - ax;
      const dy = COASTLINE[i + 1][1] - ay;
      const u = Math.min(1, Math.max(0, ((lon * cosRef - ax) * dx + (lat - ay) * dy) / (dx * dx + dy * dy)));
      nearest = Math.min(nearest, Math.hypot(lon * cosRef - ax - u * dx, lat - ay - u * dy));
    }
    return nearest * KM_PER_DEG_LAT;
  };
  const inView = (lon: number, lat: number) => lon > -120.6 && lon < -117.05 && lat > 32.45 && lat < 34.55;

  const hotspots = [
    { lon: -119.72, lat: 34.16, sdLon: 0.3, sdLat: 0.09, n: 520 }, // Santa Barbara Channel
    { lon: -117.9, lat: 33.3, sdLon: 0.13, sdLat: 0.1, n: 380 }, // off Dana Point
    { lon: -117.47, lat: 32.8, sdLon: 0.1, sdLat: 0.1, n: 340 }, // off La Jolla
  ];
  const rows: { [LON]: number; [LAT]: number }[] = [];
  for (const spot of hotspots) {
    let kept = 0;
    while (kept < spot.n) {
      const lon = spot.lon + gaussian() * spot.sdLon;
      const lat = spot.lat + gaussian() * spot.sdLat;
      if (inView(lon, lat) && offshoreKm(lon, lat) >= minShoreKm) {
        rows.push({ [LON]: Number(lon.toFixed(4)), [LAT]: Number(lat.toFixed(4)) });
        kept += 1;
      }
    }
  }
  let sparse = 0;
  while (sparse < 280) {
    const lon = -120.6 + rand() * 3.55;
    const lat = 32.45 + rand() * 2.1;
    const km = offshoreKm(lon, lat);
    if (km >= minShoreKm && km <= minShoreKm + 40) {
      rows.push({ [LON]: Number(lon.toFixed(4)), [LAT]: Number(lat.toFixed(4)) });
      sparse += 1;
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const HEADER_H = 84;
const LEGEND_H = 76;
const MARGIN = { top: 16, right: 32, bottom: 12, left: 20 };
const X_AXIS_H = 60;
const Y_AXIS_W = 84;
const DRAW_W = W - MARGIN.left - MARGIN.right - Y_AXIS_W;
const DRAW_H = H - HEADER_H - LEGEND_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;

// Equirectangular projection scaled at the mid latitude: one projected unit is
// one degree of latitude, so px per degree of latitude = px per degree of
// longitude / cos(mid latitude).
const lons = data.map((d) => d[LON]);
const lats = data.map((d) => d[LAT]);
const lonLo = Math.min(...lons);
const lonHi = Math.max(...lons);
const latLo = Math.min(...lats);
const latHi = Math.max(...lats);
const lonMid = (lonLo + lonHi) / 2;
const latMid = (latLo + latHi) / 2;
const cosLat = Math.cos((latMid * Math.PI) / 180);
// Padded extent in projected units, the shorter side widened to the drawing area's aspect
const paddedX = (lonHi - lonLo) * cosLat * (1 + 2 * PAD_SHARE);
const paddedY = (latHi - latLo) * (1 + 2 * PAD_SHARE);
const spanX = Math.max(paddedX, paddedY * (DRAW_W / DRAW_H));
const spanY = spanX / (DRAW_W / DRAW_H);
const xMin = lonMid - spanX / cosLat / 2;
const xMax = lonMid + spanX / cosLat / 2;
const yMin = latMid - spanY / 2;
const yMax = latMid + spanY / 2;

// Flat-top hexagonal binning in projected units (axial coordinates, cube rounding)
const R = spanX * HEX_RADIUS_SHARE;
const binCounts = new Map<string, { q: number; r: number; count: number }>();
for (const d of data) {
  const px = d[LON] * cosLat;
  const py = d[LAT];
  const qf = ((2 / 3) * px) / R;
  const rf = ((-1 / 3) * px + (Math.sqrt(3) / 3) * py) / R;
  const sf = -qf - rf;
  let q = Math.round(qf);
  let r = Math.round(rf);
  const s = Math.round(sf);
  const dq = Math.abs(q - qf);
  const dr = Math.abs(r - rf);
  const ds = Math.abs(s - sf);
  if (dq > dr && dq > ds) q = -r - s;
  else if (dr > ds) r = -q - s;
  const key = `${q},${r}`;
  const bin = binCounts.get(key) ?? { q, r, count: 0 };
  bin.count += 1;
  binCounts.set(key, bin);
}
const bins = [...binCounts.entries()].map(([key, { q, r, count }]) => ({
  id: key,
  lon: (R * 1.5 * q) / cosLat,
  lat: R * Math.sqrt(3) * (r + q / 2),
  count,
}));
const countMin = Math.min(...bins.map((b) => b.count));
const countMax = Math.max(...bins.map((b) => b.count));
// Hexagon corners as offsets in degrees of longitude and latitude
const HEX_CORNERS = Array.from({ length: 6 }, (_, k) => [(R * Math.cos((k * Math.PI) / 3)) / cosLat, R * Math.sin((k * Math.PI) / 3)]);

const STAT_LABEL = "Count per hex cell";
const CLIP_ID = "hexbin-map-clip";
const formatLon = (v: number) => `${Math.abs(v).toFixed(1)}°${v < 0 ? "W" : "E"}`;
const formatLat = (v: number) => `${Math.abs(v).toFixed(1)}°${v < 0 ? "S" : "N"}`;
const TITLE = "Gray Whale & Dolphin Sightings · hexbin-map-geographic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length.toLocaleString("en-US")} points binned into ${bins.length} hexagons of ${(R * KM_PER_DEG_LAT).toFixed(0)} km radius · equirectangular map scaled at ${formatLat(latMid)}`;

// Base map in data coordinates: land tint and coastline, clipped to the drawing area
function BaseMap() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();
  return (
    <g>
      <defs>
        <clipPath id={CLIP_ID}>
          <rect x={left} y={top} width={width} height={height} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${CLIP_ID})`}>
        <polygon points={LAND.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join(" ")} fill={t.grid} />
        <polyline
          points={COASTLINE.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join(" ")}
          fill="none"
          stroke={t.inkSoft}
          strokeWidth={1.5}
        />
      </g>
    </g>
  );
}

// Hexagons in data coordinates, coloured by the z axis colour map
function HexCells() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const colorScale = useZColorScale() as (v: number) => string;
  return (
    <g clipPath={`url(#${CLIP_ID})`}>
      {bins.map((b) => (
        <polygon
          key={b.id}
          points={HEX_CORNERS.map(([dx, dy]) => `${xScale(b.lon + dx)},${yScale(b.lat + dy)}`).join(" ")}
          fill={colorScale(b.count)}
          fillOpacity={HEX_OPACITY}
          stroke={t.pageBg}
          strokeWidth={1.5}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "16px", px: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 21, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={W}
        height={H - HEADER_H - LEGEND_H}
        skipAnimation
        margin={MARGIN}
        // The cell centres as a scatter series: hover shows each cell's statistics
        series={[
          {
            type: "scatter",
            id: "hex-cells",
            label: STAT_LABEL,
            data: bins.map((b) => ({ id: b.id, x: b.lon, y: b.lat })),
            valueFormatter: (_v, { dataIndex }) =>
              `${bins[dataIndex].count} · ${formatLat(bins[dataIndex].lat)}, ${formatLon(bins[dataIndex].lon)}`,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: X_AXIS_H,
            label: LON,
            tickLabelMinGap: 24,
            valueFormatter: formatLon,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: Y_AXIS_W,
            label: LAT,
            valueFormatter: formatLat,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[{ colorMap: { type: "continuous", min: countMin, max: countMax, color: [t.seq[0], t.seq[1]] } }]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "bottom", horizontal: "center" }}
          legendDirection="horizontal"
          sx={{ width: W, height: H - HEADER_H }}
        >
          <Box
            sx={{
              gridArea: "legend",
              height: LEGEND_H,
              width: W * 0.45,
              display: "flex",
              flexDirection: "column",
              alignItems: "stretch",
              pt: "6px",
              boxSizing: "border-box",
            }}
          >
            <Typography sx={{ color: t.ink, fontSize: 15, textAlign: "center", mb: "4px" }}>{STAT_LABEL}</Typography>
            <ContinuousColorLegend
              direction="horizontal"
              thickness={16}
              labelPosition="end"
              minLabel={({ value }) => String(Math.round(Number(value)))}
              maxLabel={({ value }) => String(Math.round(Number(value)))}
              sx={{ color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <ChartsSurface>
            <ChartsGrid vertical horizontal sx={{ "& line": { stroke: t.grid } }} />
            <BaseMap />
            <HexCells />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
