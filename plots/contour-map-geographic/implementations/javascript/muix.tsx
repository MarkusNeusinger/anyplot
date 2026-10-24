// anyplot.ai
// contour-map-geographic: Contour Lines on Geographic Map
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-24

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
const FILL_SUBSAMPLE = 12;

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

// Basemap: rivers (the Columbia is the Washington–Oregon border here), towns, states
const RIVERS: { name: string; width: number; label?: [number, number]; points: [number, number][] }[] = [
  {
    name: "Columbia River",
    width: 4,
    label: [-120.9, 45.6],
    points: [
      [-123.6, 46.25],
      [-123.38, 46.2],
      [-123.15, 46.18],
      [-122.95, 46.12],
      [-122.85, 46.01],
      [-122.8, 45.86],
      [-122.77, 45.65],
      [-122.67, 45.62],
      [-122.35, 45.58],
      [-121.95, 45.64],
      [-121.89, 45.67],
      [-121.52, 45.71],
      [-121.4, 45.69],
      [-121.18, 45.61],
      [-120.83, 45.68],
      [-120.74, 45.69],
      [-120.2, 45.72],
      [-119.7, 45.84],
      [-119.5, 45.9],
      [-119.35, 45.92],
      [-119.2, 45.95],
    ],
  },
  {
    name: "Columbia River (Hanford Reach)",
    width: 4,
    points: [
      [-119.91, 46.64],
      [-119.73, 46.64],
      [-119.5, 46.62],
      [-119.45, 46.55],
      [-119.35, 46.4],
      [-119.27, 46.28],
      [-119.2, 46.23],
    ],
  },
  {
    name: "Cowlitz River",
    width: 2.4,
    label: [-122.55, 46.62],
    points: [
      [-122.91, 46.1],
      [-122.9, 46.15],
      [-122.91, 46.28],
      [-122.85, 46.44],
      [-122.49, 46.53],
      [-121.95, 46.53],
      [-121.67, 46.6],
      [-121.6, 46.72],
    ],
  },
  {
    name: "Yakima River",
    width: 2.4,
    label: [-119.85, 46.45],
    points: [
      [-120.94, 47.19],
      [-120.55, 46.99],
      [-120.5, 46.6],
      [-120.47, 46.55],
      [-120.25, 46.4],
      [-120.0, 46.3],
      [-119.77, 46.21],
      [-119.48, 46.26],
      [-119.27, 46.28],
    ],
  },
  {
    name: "Lewis River",
    width: 1.8,
    points: [
      [-122.77, 45.88],
      [-122.5, 45.95],
      [-122.33, 45.97],
      [-122.15, 46.06],
      [-121.9, 46.13],
    ],
  },
  {
    name: "Nisqually River",
    width: 1.8,
    points: [
      [-121.75, 46.78],
      [-122.2, 46.77],
      [-122.5, 46.88],
      [-122.7, 47.08],
    ],
  },
];

const TOWNS: { name: string; lon: number; lat: number; side: "left" | "right"; dy: number }[] = [
  { name: "Portland", lon: -122.68, lat: 45.52, side: "left", dy: -14 },
  { name: "Olympia", lon: -122.9, lat: 47.04, side: "right", dy: 0 },
  { name: "Yakima", lon: -120.51, lat: 46.6, side: "right", dy: 0 },
  { name: "Ellensburg", lon: -120.55, lat: 46.99, side: "right", dy: 0 },
];

const STATES: { name: string; lon: number; lat: number }[] = [
  { name: "WASHINGTON", lon: -123.2, lat: 46.45 },
  { name: "OREGON", lon: -123.2, lat: 45.95 },
];

const data = (() => {
  const sampleLonMin = -123.6;
  const sampleLonMax = -119.2;
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

// Filled bands between the contour levels: one imprint_seq step per band
const hexToRgb = (hex: string) => [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16));
const SEQ_LOW = hexToRgb(t.seq[0]);
const SEQ_HIGH = hexToRgb(t.seq[1]);
const BAND_EDGES = [MIN_ELEV, ...LEVELS, MAX_ELEV];
const N_BANDS = BAND_EDGES.length - 1;
const BAND_RGB = Array.from({ length: N_BANDS }, (_, k) =>
  SEQ_LOW.map((c, ch) => Math.round(c + ((SEQ_HIGH[ch] - c) * k) / (N_BANDS - 1))),
);
const bandOf = (v: number) => LEVELS.filter((l) => l <= v).length;

// Rasterize the banded field (bilinear within each grid cell, so band edges follow the isolines)
const FILL_URL = (() => {
  const w = (NLON - 1) * FILL_SUBSAMPLE;
  const h = (NLAT - 1) * FILL_SUBSAMPLE;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const img = ctx.createImageData(w, h);
  for (let py = 0; py < h; py++) {
    const gy = NLAT - 1 - (py + 0.5) / FILL_SUBSAMPLE;
    const j = Math.min(NLAT - 2, Math.floor(gy));
    const fy = gy - j;
    for (let px = 0; px < w; px++) {
      const gx = (px + 0.5) / FILL_SUBSAMPLE;
      const i = Math.min(NLON - 2, Math.floor(gx));
      const fx = gx - i;
      const v =
        GRID[j][i] * (1 - fx) * (1 - fy) +
        GRID[j][i + 1] * fx * (1 - fy) +
        GRID[j + 1][i] * (1 - fx) * fy +
        GRID[j + 1][i + 1] * fx * fy;
      if (Number.isNaN(v)) continue;
      const [r, g, b] = BAND_RGB[bandOf(v)];
      const o = (py * w + px) * 4;
      img.data[o] = r;
      img.data[o + 1] = g;
      img.data[o + 2] = b;
      img.data[o + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL();
})();

const SUBTITLE = `${NLON}×${NLAT} grid (${Math.round(MIN_ELEV)}–${Math.round(MAX_ELEV)}${elevUnitSuffix}) · index contours every ${INDEX_STEP}${elevUnitSuffix}, intermediate every ${CONTOUR_STEP}${elevUnitSuffix}`;

function ContourLayer() {
  const { left, top, width: areaW, height: areaH } = useDrawingArea();
  const lonSpan = LON_MAX - LON_MIN;
  const latSpan = LAT_MAX - LAT_MIN;
  const projX = (lon: number) => left + ((lon - LON_MIN) / lonSpan) * areaW;
  const projY = (lat: number) => top + (1 - (lat - LAT_MIN) / latSpan) * areaH;

  const peakLabels = PEAKS.map((p) => {
    const cx = projX(p.lon);
    const cy = projY(p.lat);
    const boxW = Math.max(108, p.name.length * 8.2 + 14);
    return { key: p.name, text: p.name, x: cx - boxW / 2, y: cy - 54, w: boxW };
  });
  const riverLabels = RIVERS.filter((r) => r.label).map((r) => {
    const boxW = r.name.length * 7.4 + 14;
    return {
      key: r.name,
      text: r.name,
      x: projX(r.label![0]) - boxW / 2,
      y: projY(r.label![1]) - 11,
      w: boxW,
    };
  });
  const townLabels = TOWNS.map((town) => {
    const boxW = town.name.length * 7.6 + 12;
    const cx = projX(town.lon);
    return {
      key: town.name,
      text: town.name,
      cx,
      cy: projY(town.lat),
      x: town.side === "right" ? cx + 8 : cx - 8 - boxW,
      y: projY(town.lat) - 11 + town.dy,
      w: boxW,
    };
  });
  const stateLabels = STATES.map((s) => {
    const boxW = s.name.length * 13 + 16;
    return { key: s.name, text: s.name, x: projX(s.lon) - boxW / 2, y: projY(s.lat) - 11, w: boxW };
  });
  const occupiedBoxes = [...peakLabels, ...riverLabels, ...townLabels, ...stateLabels].map(
    (b) => ({ x0: b.x - 6, x1: b.x + b.w + 6, y0: b.y - 4, y1: b.y + 26 }),
  );

  const barX = left + areaW + 46;
  const barW = 24;
  const barTop = top + 16;
  const barBottom = top + areaH;
  const barY = (v: number) =>
    barBottom - ((v - MIN_ELEV) / (MAX_ELEV - MIN_ELEV)) * (barBottom - barTop);

  return (
    <g fontFamily={FONT}>
      <defs>
        <clipPath id="mapClip">
          <rect x={left} y={top} width={areaW} height={areaH} />
        </clipPath>
      </defs>

      <image
        href={FILL_URL}
        x={left}
        y={top}
        width={areaW}
        height={areaH}
        preserveAspectRatio="none"
      />

      {/* Basemap: rivers in the page color, beneath the contours */}
      <g clipPath="url(#mapClip)">
        {RIVERS.map((river) => (
          <polyline
            key={river.name}
            points={river.points
              .map(([lon, lat]) => `${projX(lon).toFixed(1)},${projY(lat).toFixed(1)}`)
              .join(" ")}
            fill="none"
            stroke={t.pageBg}
            strokeWidth={river.width}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeOpacity={0.9}
          />
        ))}
      </g>

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

      {townLabels.map((town) => (
        <circle
          key={`dot-${town.key}`}
          cx={town.cx}
          cy={town.cy}
          r={4.5}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={1.5}
        />
      ))}

      {[
        ...stateLabels.map((b) => ({ ...b, color: t.inkSoft, weight: 600, italic: false, spacing: 3 })),
        ...riverLabels.map((b) => ({ ...b, color: t.inkSoft, weight: 400, italic: true, spacing: 0 })),
        ...townLabels.map((b) => ({ ...b, color: t.ink, weight: 400, italic: false, spacing: 0 })),
        ...peakLabels.map((b) => ({ ...b, color: t.ink, weight: 600, italic: false, spacing: 0 })),
      ].map((b) => (
        <g key={`text-${b.key}`}>
          <rect x={b.x} y={b.y} width={b.w} height={22} rx={4} fill={t.pageBg} opacity={0.88} />
          <text
            x={b.x + b.w / 2}
            y={b.y + 16}
            textAnchor="middle"
            fontSize={14}
            fontWeight={b.weight}
            fontStyle={b.italic ? "italic" : "normal"}
            letterSpacing={b.spacing}
            fill={b.color}
          >
            {b.text}
          </text>
        </g>
      ))}

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
      {BAND_RGB.map(([r, g, b], k) => (
        <rect
          key={`band-${k}`}
          x={barX}
          y={barY(BAND_EDGES[k + 1])}
          width={barW}
          height={barY(BAND_EDGES[k]) - barY(BAND_EDGES[k + 1])}
          fill={`rgb(${r},${g},${b})`}
        />
      ))}
      <rect
        x={barX}
        y={barTop}
        width={barW}
        height={barBottom - barTop}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={1}
      />
      {LEVELS.map((level) => {
        const y = barY(level);
        const isIndex = Math.abs(level % INDEX_STEP) < 1e-6;
        return (
          <g key={`tick-${level}`}>
            <line
              x1={barX}
              y1={y}
              x2={barX + barW + 6}
              y2={y}
              stroke={t.inkSoft}
              strokeWidth={isIndex ? 1.4 : 0.8}
            />
            <text
              x={barX + barW + 12}
              y={y + 5}
              fontSize={14}
              fontWeight={isIndex ? 600 : 400}
              fill={t.inkSoft}
            >
              {level}
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
