// anyplot.ai
// contour-map-geographic: Contour Lines on Geographic Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Updated: 2026-09-02

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Constants
const TITLE = "contour-map-geographic · javascript · muix · anyplot.ai";
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const TARGET_CONTOUR_COUNT = 10;
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];

// Columns: set these to your data's column names
const LON = "Longitude (°)"; // role: lon
const LAT = "Latitude (°)"; // role: lat
const ELEVATION = "Elevation (m)"; // role: value

// Data: replace this block with your own records
const PEAKS = [
  { lon: -121.7603, lat: 46.8523, height: 4392, sigmaLon: 0.22, sigmaLat: 0.17, name: "Mount Rainier" },
  { lon: -121.4906, lat: 46.2024, height: 3743, sigmaLon: 0.18, sigmaLat: 0.15, name: "Mount Adams" },
  { lon: -122.1956, lat: 46.1912, height: 2549, sigmaLon: 0.16, sigmaLat: 0.13, name: "Mount St. Helens" },
];

const RIVERS = [
  {
    name: "Columbia River",
    points: [
      [-123.6, 45.62],
      [-123.1, 45.65],
      [-122.6, 45.6],
      [-122.1, 45.68],
      [-121.6, 45.72],
      [-121.1, 45.66],
      [-120.4, 45.6],
    ] as [number, number][],
  },
];

const data = (() => {
  const sampleLonMin = -123.6;
  const sampleLonMax = -120.4;
  const sampleLatMin = 45.5;
  const sampleLatMax = 47.3;
  const sampleNLon = 101;
  const sampleNLat = 61;
  const rows: Record<string, number>[] = [];

  for (let j = 0; j < sampleNLat; j++) {
    const lat = sampleLatMin + (j * (sampleLatMax - sampleLatMin)) / (sampleNLat - 1);
    for (let i = 0; i < sampleNLon; i++) {
      const lon = sampleLonMin + (i * (sampleLonMax - sampleLonMin)) / (sampleNLon - 1);
      let elev =
        460 + 60 * Math.sin(((lon - sampleLonMin) / (sampleLonMax - sampleLonMin)) * Math.PI);
      for (const p of PEAKS) {
        const baseAtPeak =
          460 + 60 * Math.sin(((p.lon - sampleLonMin) / (sampleLonMax - sampleLonMin)) * Math.PI);
        const amp = p.height - baseAtPeak;
        const dLon = lon - p.lon;
        const dLat = lat - p.lat;
        elev +=
          amp *
          Math.exp(
            -(
              (dLon * dLon) / (2 * p.sigmaLon * p.sigmaLon) +
              (dLat * dLat) / (2 * p.sigmaLat * p.sigmaLat)
            ),
          );
      }
      rows.push({ [LON]: lon, [LAT]: lat, [ELEVATION]: elev });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const LONS = Array.from(new Set(data.map((d) => Number(d[LON])))).sort((a, b) => a - b);
const LATS = Array.from(new Set(data.map((d) => Number(d[LAT])))).sort((a, b) => a - b);
const NLON = LONS.length;
const NLAT = LATS.length;
const LON_MIN = LONS[0];
const LON_MAX = LONS[NLON - 1];
const LAT_MIN = LATS[0];
const LAT_MAX = LATS[NLAT - 1];
const MEAN_LAT_RAD = (((LAT_MIN + LAT_MAX) / 2) * Math.PI) / 180;
const LON_TO_LAT_COS = Math.cos(MEAN_LAT_RAD);

const ELEV_UNIT = ELEVATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const elevUnitSuffix = ELEV_UNIT ? ` ${ELEV_UNIT}` : "";

const lonIdxMap = new Map(LONS.map((v, i) => [v, i]));
const latIdxMap = new Map(LATS.map((v, j) => [v, j]));
const GRID: number[][] = Array.from({ length: NLAT }, () => new Array(NLON).fill(NaN));

let MIN_ELEV = Infinity;
let MAX_ELEV = -Infinity;
for (const row of data) {
  const val = Number(row[ELEVATION]);
  if (Number.isFinite(val)) {
    if (val < MIN_ELEV) MIN_ELEV = val;
    if (val > MAX_ELEV) MAX_ELEV = val;
    GRID[latIdxMap.get(Number(row[LAT]))!][lonIdxMap.get(Number(row[LON]))!] = val;
  }
}

const rawInterval = (MAX_ELEV - MIN_ELEV) / TARGET_CONTOUR_COUNT;
const intervalMag = Math.pow(10, Math.floor(Math.log10(rawInterval)));
const intervalNorm = rawInterval / intervalMag;
const CONTOUR_STEP = (intervalNorm <= 1.5 ? 1 : intervalNorm <= 3.5 ? 2 : 5) * intervalMag;
const INDEX_STEP = CONTOUR_STEP * 2;
const LEVELS: number[] = [];
for (
  let lvl = Math.ceil(MIN_ELEV / CONTOUR_STEP) * CONTOUR_STEP;
  lvl <= MAX_ELEV;
  lvl += CONTOUR_STEP
) {
  LEVELS.push(Number(lvl.toFixed(6)));
}

type Point = [number, number];
type Segment = [Point, Point];

const CONTOURS = LEVELS.map((level) => {
  const segments: Segment[] = [];
  for (let j = 0; j < NLAT - 1; j++) {
    for (let i = 0; i < NLON - 1; i++) {
      const tl = GRID[j][i];
      const tr = GRID[j][i + 1];
      const bl = GRID[j + 1][i];
      const br = GRID[j + 1][i + 1];
      if (Number.isNaN(tl) || Number.isNaN(tr) || Number.isNaN(bl) || Number.isNaN(br)) {
        continue;
      }
      const x0 = LONS[i];
      const x1 = LONS[i + 1];
      const y0 = LATS[j];
      const y1 = LATS[j + 1];
      const edges: { v0: number; v1: number; p0: Point; p1: Point }[] = [
        { v0: tl, v1: tr, p0: [x0, y0], p1: [x1, y0] },
        { v0: tr, v1: br, p0: [x1, y0], p1: [x1, y1] },
        { v0: bl, v1: br, p0: [x0, y1], p1: [x1, y1] },
        { v0: tl, v1: bl, p0: [x0, y0], p1: [x0, y1] },
      ];
      const crossings: Point[] = [];
      for (const e of edges) {
        if ((e.v0 - level) * (e.v1 - level) < 0) {
          const frac = (level - e.v0) / (e.v1 - e.v0);
          crossings.push([
            e.p0[0] + frac * (e.p1[0] - e.p0[0]),
            e.p0[1] + frac * (e.p1[1] - e.p0[1]),
          ]);
        }
      }
      if (crossings.length === 2) {
        segments.push([crossings[0], crossings[1]]);
      } else if (crossings.length === 4) {
        const meanValue = (tl + tr + bl + br) / 4;
        if (meanValue >= level) {
          segments.push([crossings[0], crossings[3]]);
          segments.push([crossings[1], crossings[2]]);
        } else {
          segments.push([crossings[0], crossings[1]]);
          segments.push([crossings[2], crossings[3]]);
        }
      }
    }
  }
  return { level, segments, isIndex: Math.abs(level % INDEX_STEP) < 1e-6 };
});

const SEQ_LOW = [
  parseInt(t.seq[0].slice(1, 3), 16),
  parseInt(t.seq[0].slice(3, 5), 16),
  parseInt(t.seq[0].slice(5, 7), 16),
];
const SEQ_HIGH = [
  parseInt(t.seq[1].slice(1, 3), 16),
  parseInt(t.seq[1].slice(3, 5), 16),
  parseInt(t.seq[1].slice(5, 7), 16),
];

const CELLS: {
  lonMin: number;
  lonMax: number;
  latMin: number;
  latMax: number;
  color: string;
}[] = [];
for (let j = 0; j < NLAT - 1; j++) {
  for (let i = 0; i < NLON - 1; i++) {
    const tl = GRID[j][i];
    const tr = GRID[j][i + 1];
    const bl = GRID[j + 1][i];
    const br = GRID[j + 1][i + 1];
    if (Number.isNaN(tl) || Number.isNaN(tr) || Number.isNaN(bl) || Number.isNaN(br)) {
      continue;
    }
    const mean = (tl + tr + bl + br) / 4;
    const frac = Math.max(0, Math.min(1, (mean - MIN_ELEV) / (MAX_ELEV - MIN_ELEV)));
    const r = Math.round(SEQ_LOW[0] + (SEQ_HIGH[0] - SEQ_LOW[0]) * frac);
    const g = Math.round(SEQ_LOW[1] + (SEQ_HIGH[1] - SEQ_LOW[1]) * frac);
    const b = Math.round(SEQ_LOW[2] + (SEQ_HIGH[2] - SEQ_LOW[2]) * frac);
    CELLS.push({
      lonMin: LONS[i],
      lonMax: LONS[i + 1],
      latMin: LATS[j],
      latMax: LATS[j + 1],
      color: `rgb(${r},${g},${b})`,
    });
  }
}

const SUBTITLE = `${NLON}×${NLAT} grid (${Math.round(MIN_ELEV)}–${Math.round(MAX_ELEV)}${elevUnitSuffix}) · index contours every ${INDEX_STEP}${elevUnitSuffix}, intermediate every ${CONTOUR_STEP}${elevUnitSuffix}`;

function ContourLayer() {
  const { left, top, width: areaW, height: areaH } = useDrawingArea();
  const lonSpan = LON_MAX - LON_MIN;
  const latSpan = LAT_MAX - LAT_MIN;

  const occupiedBoxes = PEAKS.map((p) => {
    const cx = left + ((p.lon - LON_MIN) / lonSpan) * areaW;
    const cy = top + (1 - (p.lat - LAT_MIN) / latSpan) * areaH;
    const boxW = Math.max(108, p.name.length * 8.2 + 14);
    return { x0: cx - boxW / 2 - 6, x1: cx + boxW / 2 + 6, y0: cy - 58, y1: cy - 28 };
  });

  const barX = left + areaW + 46;
  const barW = 24;
  const barTop = top + 16;
  const barBottom = top + areaH;

  return (
    <g fontFamily={FONT}>
      <defs>
        <linearGradient id="elevationRamp" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.seq[1]} />
          <stop offset="100%" stopColor={t.seq[0]} />
        </linearGradient>
      </defs>

      {CELLS.map((cell, idx) => {
        const x0 = left + ((cell.lonMin - LON_MIN) / lonSpan) * areaW;
        const x1 = left + ((cell.lonMax - LON_MIN) / lonSpan) * areaW;
        const y0 = top + (1 - (cell.latMax - LAT_MIN) / latSpan) * areaH;
        const y1 = top + (1 - (cell.latMin - LAT_MIN) / latSpan) * areaH;
        return (
          <rect
            key={idx}
            x={x0}
            y={y0}
            width={x1 - x0 + 0.5}
            height={y1 - y0 + 0.5}
            fill={cell.color}
            stroke="none"
          />
        );
      })}

      {CONTOURS.map(({ level, segments, isIndex }) => {
        const d = segments
          .map(([[lon0, lat0], [lon1, lat1]]) => {
            const px0 = left + ((lon0 - LON_MIN) / lonSpan) * areaW;
            const py0 = top + (1 - (lat0 - LAT_MIN) / latSpan) * areaH;
            const px1 = left + ((lon1 - LON_MIN) / lonSpan) * areaW;
            const py1 = top + (1 - (lat1 - LAT_MIN) / latSpan) * areaH;
            return `M${px0.toFixed(1)},${py0.toFixed(1)} L${px1.toFixed(1)},${py1.toFixed(1)}`;
          })
          .join(" ");
        return (
          <path
            key={level}
            d={d}
            fill="none"
            stroke={t.ink}
            strokeWidth={isIndex ? 2.2 : 1.0}
            strokeOpacity={isIndex ? 0.85 : 0.42}
            strokeLinecap="round"
          />
        );
      })}

      {[...CONTOURS]
        .reverse()
        .filter(({ level, isIndex }) => isIndex && level > MIN_ELEV)
        .map(({ level, segments }) => {
          if (segments.length === 0) return null;
          const mid = Math.floor(segments.length / 2);
          let chosen = segments[mid];
          let found = false;
          for (let d = 0; d < segments.length; d++) {
            for (const idx of d === 0 ? [mid] : [mid + d, mid - d]) {
              if (idx < 0 || idx >= segments.length) continue;
              const seg = segments[idx];
              const mx =
                left + (((seg[0][0] + seg[1][0]) / 2 - LON_MIN) / lonSpan) * areaW;
              const my =
                top + (1 - ((seg[0][1] + seg[1][1]) / 2 - LAT_MIN) / latSpan) * areaH;
              const clears = occupiedBoxes.every(
                (b) => mx + 36 < b.x0 || mx - 36 > b.x1 || my + 13 < b.y0 || my - 13 > b.y1,
              );
              if (clears) {
                chosen = seg;
                found = true;
                break;
              }
            }
            if (found) break;
          }
          if (!found) return null;
          const [[lon0, lat0], [lon1, lat1]] = chosen;
          const cx = left + (((lon0 + lon1) / 2 - LON_MIN) / lonSpan) * areaW;
          const cy = top + (1 - ((lat0 + lat1) / 2 - LAT_MIN) / latSpan) * areaH;
          occupiedBoxes.push({ x0: cx - 38, x1: cx + 38, y0: cy - 14, y1: cy + 14 });
          return (
            <g key={`label-${level}`}>
              <rect
                x={cx - 34}
                y={cy - 12}
                width={68}
                height={22}
                rx={4}
                fill={t.pageBg}
                opacity={0.88}
              />
              <text
                x={cx}
                y={cy + 4}
                textAnchor="middle"
                fontSize={14}
                fontWeight={600}
                fill={t.ink}
              >
                {`${level}${elevUnitSuffix}`}
              </text>
            </g>
          );
        })}

      {RIVERS.map((river) => {
        const pts = river.points
          .map(([lon, lat]) => {
            const px = left + ((lon - LON_MIN) / lonSpan) * areaW;
            const py = top + (1 - (lat - LAT_MIN) / latSpan) * areaH;
            return `${px.toFixed(1)},${py.toFixed(1)}`;
          })
          .join(" ");
        const [firstLon, firstLat] = river.points[0];
        const rx = left + ((firstLon - LON_MIN) / lonSpan) * areaW + 6;
        const ry = top + (1 - (firstLat - LAT_MIN) / latSpan) * areaH - 26;
        const boxW = Math.max(96, river.name.length * 7.8 + 14);
        return (
          <g key={river.name}>
            <polyline
              points={pts}
              fill="none"
              stroke={t.inkSoft}
              strokeWidth={3}
              strokeLinecap="round"
              strokeOpacity={0.8}
            />
            <rect
              x={rx}
              y={ry}
              width={boxW}
              height={22}
              rx={4}
              fill={t.pageBg}
              opacity={0.88}
            />
            <text
              x={rx + 6}
              y={ry + 16}
              fontSize={14}
              fontStyle="italic"
              fill={t.inkSoft}
            >
              {river.name}
            </text>
          </g>
        );
      })}

      {PEAKS.map((p) => {
        const cx = left + ((p.lon - LON_MIN) / lonSpan) * areaW;
        const cy = top + (1 - (p.lat - LAT_MIN) / latSpan) * areaH;
        const boxW = Math.max(108, p.name.length * 8.2 + 14);
        return (
          <g key={p.name}>
            <rect
              x={cx - boxW / 2}
              y={cy - 54}
              width={boxW}
              height={22}
              rx={4}
              fill={t.pageBg}
              opacity={0.88}
            />
            <text
              x={cx}
              y={cy - 38}
              textAnchor="middle"
              fontSize={14}
              fontWeight={600}
              fill={t.ink}
            >
              {p.name}
            </text>
          </g>
        );
      })}

      {/* Vertical Colorbar */}
      <text
        x={barX + barW / 2}
        y={barTop - 12}
        textAnchor="middle"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
      >
        {ELEVATION}
      </text>
      <rect
        x={barX}
        y={barTop}
        width={barW}
        height={barBottom - barTop}
        fill="url(#elevationRamp)"
        stroke={t.inkSoft}
        strokeWidth={1}
        rx={3}
      />
      {COLORBAR_TICKS.map((f) => {
        const value = Math.round(MIN_ELEV + f * (MAX_ELEV - MIN_ELEV));
        const y = barBottom - f * (barBottom - barTop);
        return (
          <g key={f}>
            <line
              x1={barX + barW}
              y1={y}
              x2={barX + barW + 6}
              y2={y}
              stroke={t.inkSoft}
              strokeWidth={1.2}
            />
            <text x={barX + barW + 12} y={y + 5} fontSize={14} fill={t.inkSoft}>
              {value}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartH = height - 108;
  const xAxisH = 60;
  const yAxisW = 92;
  const marginTop = 20;
  const marginBottom = 16;
  const marginLeft = 20;
  const marginRight = 150;
  const areaH = chartH - marginTop - marginBottom - xAxisH;
  const geoAspect = ((LON_MAX - LON_MIN) * LON_TO_LAT_COS) / (LAT_MAX - LAT_MIN);
  const areaW = Math.round(areaH * geoAspect);
  const chartW = areaW + yAxisW + marginLeft + marginRight;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: "18px",
        px: "24px",
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 700,
          color: t.ink,
          fontFamily: FONT,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        {TITLE}
      </Typography>
      <Typography
        sx={{
          fontSize: 15,
          color: t.inkSoft,
          fontFamily: FONT,
          textAlign: "center",
          mt: "4px",
          mb: "4px",
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
        width={chartW}
        height={chartH}
        series={[]}
        skipAnimation
        margin={{
          top: marginTop,
          right: marginRight,
          bottom: marginBottom,
          left: marginLeft,
        }}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: LON_MIN,
            max: LON_MAX,
            height: xAxisH,
            label: LON,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(1)}°${v < 0 ? "W" : "E"}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: LAT_MIN,
            max: LAT_MAX,
            width: yAxisW,
            label: LAT,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(1)}°${v < 0 ? "S" : "N"}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fill: t.ink, fontFamily: FONT },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ContourLayer />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </Box>
  );
}
