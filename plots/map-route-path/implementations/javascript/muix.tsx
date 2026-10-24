// anyplot.ai
// map-route-path: Route Path Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "map-route-path · javascript · muix · anyplot.ai";
const BASEMAP_CAPTION =
  "Coordinates: WGS 84 (EPSG:4326) · SVG lon/lat graticule provides spatial reference";
const TITLE_HEIGHT = 54;
const CAPTION_HEIGHT = 32;
const X_AXIS_HEIGHT = 58;
const Y_AXIS_WIDTH = 98;
const MARGIN = { top: 20, right: 260, bottom: 14, left: 16 };
const PAD_SHARE = 0.14;
const ARROW_STRIDE = 8;

// Columns: set these to your data's column names
const SEQUENCE = "Waypoint sequence"; // role: sequence
const LAT = "Latitude (°N)"; // role: lat
const LON = "Longitude (°E)"; // role: lon
const PROGRESS = "Elapsed time share"; // role: timestamp
const LANDMARK = "Landmark"; // role: label

// Data: replace this block with your own records
const KEYFRAMES: Array<[number, number, string]> = [
  [52.3731, 4.8926, "Start · Dam Square"],
  [52.3702, 4.8895, ""],
  [52.3668, 4.8838, ""],
  [52.364, 4.8815, ""],
  [52.358, 4.8686, "Vondelpark West"],
  [52.3565, 4.8755, ""],
  [52.3585, 4.8815, ""],
  [52.36, 4.8852, "Rijksmuseum"],
  [52.3635, 4.892, ""],
  [52.3662, 4.8995, ""],
  [52.3678, 4.904, "Waterlooplein"],
  [52.372, 4.9005, ""],
  [52.3755, 4.896, ""],
  [52.3765, 4.884, "Jordaan"],
  [52.3795, 4.8895, ""],
  [52.3791, 4.9003, "End · Amsterdam Centraal"],
];

const STEPS_PER_LEG = 4;
const TOTAL_WAYPOINTS = (KEYFRAMES.length - 1) * STEPS_PER_LEG + 1;
const data: Array<Record<string, string | number>> = [];

let seed = 42;
for (let leg = 0; leg < KEYFRAMES.length - 1; leg++) {
  const [lat1, lon1, name1] = KEYFRAMES[leg];
  const [lat2, lon2] = KEYFRAMES[leg + 1];
  for (let s = 0; s < STEPS_PER_LEG; s++) {
    const idx = leg * STEPS_PER_LEG + s;
    const u = s / STEPS_PER_LEG;
    seed = (seed * 1664525 + 1013904223) >>> 0;
    const r1 = seed / 0x100000000;
    seed = (seed * 1664525 + 1013904223) >>> 0;
    const r2 = seed / 0x100000000;
    const wobble = Math.sin(u * Math.PI);
    const jLat = (r1 - 0.5) * 0.0005 * wobble;
    const jLon = (r2 - 0.5) * 0.0007 * wobble;
    data.push({
      [SEQUENCE]: idx,
      [LAT]: Number((lat1 + (lat2 - lat1) * u + jLat).toFixed(6)),
      [LON]: Number((lon1 + (lon2 - lon1) * u + jLon).toFixed(6)),
      [PROGRESS]: Number((idx / (TOTAL_WAYPOINTS - 1)).toFixed(4)),
      [LANDMARK]: s === 0 ? name1 : "",
    });
  }
}
const lastKeyframe = KEYFRAMES[KEYFRAMES.length - 1];
data.push({
  [SEQUENCE]: TOTAL_WAYPOINTS - 1,
  [LAT]: lastKeyframe[0],
  [LON]: lastKeyframe[1],
  [PROGRESS]: 1,
  [LANDMARK]: lastKeyframe[2],
});

// Plot: reads only data and the constants above
const sortedRows = [...data].sort(
  (a, b) => Number(a[SEQUENCE]) - Number(b[SEQUENCE]),
);
const nWaypoints = sortedRows.length;
const lats = sortedRows.map((d) => Number(d[LAT]));
const lons = sortedRows.map((d) => Number(d[LON]));
const progressVals = sortedRows.map((d) => Number(d[PROGRESS]));
const minProgress = Math.min(...progressVals);
const maxProgress = Math.max(...progressVals);

const minLat = Math.min(...lats);
const maxLat = Math.max(...lats);
const minLon = Math.min(...lons);
const maxLon = Math.max(...lons);
const meanLatRad = (((minLat + maxLat) / 2) * Math.PI) / 180;
const cosMeanLat = Math.cos(meanLatRad);

const { width: canvasW, height: canvasH } = window.ANYPLOT_SIZE;
const chartH = canvasH - TITLE_HEIGHT - CAPTION_HEIGHT;
const drawW = canvasW - MARGIN.left - MARGIN.right - Y_AXIS_WIDTH;
const drawH = chartH - MARGIN.top - MARGIN.bottom - X_AXIS_HEIGHT;
const targetAspect = drawW / drawH;

const rawLonSpan = (maxLon - minLon) * (1 + 2 * PAD_SHARE);
const rawLatSpan = (maxLat - minLat) * (1 + 2 * PAD_SHARE);
const rawGroundAspect = (rawLonSpan * cosMeanLat) / rawLatSpan;

const finalLonSpan =
  rawGroundAspect >= targetAspect
    ? rawLonSpan
    : (rawLatSpan * targetAspect) / cosMeanLat;
const finalLatSpan =
  rawGroundAspect >= targetAspect
    ? (rawLonSpan * cosMeanLat) / targetAspect
    : rawLatSpan;

const centerLon = (minLon + maxLon) / 2;
const centerLat = (minLat + maxLat) / 2;
const xAxisMin = centerLon - finalLonSpan / 2;
const xAxisMax = centerLon + finalLonSpan / 2;
const yAxisMin = centerLat - finalLatSpan / 2;
const yAxisMax = centerLat + finalLatSpan / 2;

const startColor = t.palette[0];
const endColor = t.palette[4];

function RouteOverlay() {
  const { left, top, width } = useDrawingArea();
  const xScale = useXScale("lon") as (v: number) => number;
  const yScale = useYScale("lat") as (v: number) => number;
  const zColorScale = useZColorScale("seqAxis") as (v: number) => string;

  const pts = sortedRows.map((row) => ({
    x: xScale(Number(row[LON])),
    y: yScale(Number(row[LAT])),
    progress: Number(row[PROGRESS]),
    color: zColorScale(Number(row[PROGRESS])),
    landmark: String(row[LANDMARK]),
    lat: Number(row[LAT]),
    lon: Number(row[LON]),
  }));

  const startPt = pts[0];
  const endPt = pts[pts.length - 1];
  const startLabel = startPt.landmark || "Start";
  const endLabel = endPt.landmark || "End";

  // Compass rose in top-right corner of drawing area
  const roseCx = left + width - 38;
  const roseCy = top + 46;
  const roseR = 16;

  // Right-side legend panel
  const legX = left + width + 24;
  const legY = top + 16;
  const barW = 190;
  const barH = 14;

  return (
    <g>
      <defs>
        <linearGradient id="route-seq-grad" x1="0%" y1="0%" x2="100%" y2="0%">
          {t.seq.map((stop: string, idx: number) => (
            <stop
              key={stop}
              offset={`${(idx / (t.seq.length - 1)) * 100}%`}
              stopColor={stop}
            />
          ))}
        </linearGradient>
      </defs>

      {/* Halo under route path for contrast against grid */}
      <path
        d={pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
        fill="none"
        stroke={t.pageBg}
        strokeWidth={7}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Sequential color-coded route segments */}
      {pts.slice(0, -1).map((p, i) => {
        const next = pts[i + 1];
        return (
          <line
            key={`seg-${i}`}
            x1={p.x}
            y1={p.y}
            x2={next.x}
            y2={next.y}
            stroke={p.color}
            strokeWidth={4}
            strokeLinecap="round"
          />
        );
      })}

      {/* Direction chevrons along the trajectory */}
      {pts.slice(0, -1).map((p, i) => {
        if (i === 0 || i % ARROW_STRIDE !== 4) return null;
        const next = pts[i + 1];
        const mx = (p.x + next.x) / 2;
        const my = (p.y + next.y) / 2;
        const angleDeg = (Math.atan2(next.y - p.y, next.x - p.x) * 180) / Math.PI;
        return (
          <g key={`arrow-${i}`} transform={`translate(${mx}, ${my}) rotate(${angleDeg})`}>
            <polygon
              points="7,0 -6,-5.5 -3,0 -6,5.5"
              fill={p.color}
              stroke={t.pageBg}
              strokeWidth={1.5}
              strokeLinejoin="round"
            />
          </g>
        );
      })}

      {/* Waypoint dots */}
      {pts.slice(1, -1).map((p, i) => {
        const isLandmark = p.landmark !== "";
        return (
          <circle
            key={`wp-${i}`}
            cx={p.x}
            cy={p.y}
            r={isLandmark ? 4.8 : 2.8}
            fill={p.color}
            stroke={t.pageBg}
            strokeWidth={isLandmark ? 1.8 : 1}
          />
        );
      })}

      {/* Intermediate landmark labels derived from LANDMARK column */}
      {pts.slice(1, -1).map((p, i) => {
        if (!p.landmark) return null;
        const isLeftOfCenter = p.lon < centerLon;
        const dx = isLeftOfCenter ? -14 : 14;
        const dy = p.lat < centerLat ? 16 : -10;
        const anchor = isLeftOfCenter ? "end" : "start";
        return (
          <text
            key={`lm-${i}`}
            x={p.x + dx}
            y={p.y + dy}
            textAnchor={anchor}
            fontSize={14}
            fontWeight={500}
            fill={t.inkSoft}
            stroke={t.pageBg}
            strokeWidth={3.5}
            paintOrder="stroke"
          >
            {p.landmark}
          </text>
        );
      })}

      {/* Start marker (circle) and callout */}
      <circle
        cx={startPt.x}
        cy={startPt.y}
        r={9.5}
        fill={startColor}
        stroke={t.pageBg}
        strokeWidth={2.5}
      />
      <text
        x={startPt.x - 15}
        y={startPt.y + 5}
        textAnchor="end"
        fontSize={15}
        fontWeight={700}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={4}
        paintOrder="stroke"
      >
        {startLabel}
      </text>

      {/* End marker (square) and callout */}
      <rect
        x={endPt.x - 9}
        y={endPt.y - 9}
        width={18}
        height={18}
        rx={2.5}
        fill={endColor}
        stroke={t.pageBg}
        strokeWidth={2.5}
      />
      <text
        x={endPt.x + 15}
        y={endPt.y - 10}
        textAnchor="start"
        fontSize={15}
        fontWeight={700}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={4}
        paintOrder="stroke"
      >
        {endLabel}
      </text>

      {/* Geographic compass rose */}
      <g>
        <circle
          cx={roseCx}
          cy={roseCy}
          r={roseR + 4}
          fill={t.elevatedBg}
          stroke={t.grid}
          strokeWidth={1}
        />
        <polygon
          points={`${roseCx},${roseCy - roseR} ${roseCx - 5},${roseCy + 4} ${roseCx},${roseCy} ${roseCx + 5},${roseCy + 4}`}
          fill={t.ink}
        />
        <text
          x={roseCx}
          y={roseCy - roseR - 8}
          textAnchor="middle"
          fontSize={14}
          fontWeight={700}
          fill={t.ink}
        >
          N
        </text>
      </g>

      {/* Right-side legend panel */}
      <g transform={`translate(${legX}, ${legY})`}>
        <text x={0} y={14} fontSize={15} fontWeight={700} fill={t.ink}>
          Route endpoints
        </text>
        <g transform="translate(0, 34)">
          <circle cx={9} cy={0} r={8} fill={startColor} stroke={t.pageBg} strokeWidth={2} />
          <text x={26} y={5} fontSize={14} fill={t.ink}>
            {startLabel}
          </text>
        </g>
        <g transform="translate(0, 64)">
          <rect
            x={1}
            y={-8}
            width={16}
            height={16}
            rx={2}
            fill={endColor}
            stroke={t.pageBg}
            strokeWidth={2}
          />
          <text x={26} y={5} fontSize={14} fill={t.ink}>
            {endLabel}
          </text>
        </g>
        <g transform="translate(0, 94)">
          <polygon
            points="15,0 3,-5 6,0 3,5"
            fill={pts[Math.floor(pts.length / 2)].color}
          />
          <text x={26} y={5} fontSize={14} fill={t.inkSoft}>
            {`Travel direction (${nWaypoints} waypoints)`}
          </text>
        </g>

        <g transform="translate(0, 140)">
          <text x={0} y={0} fontSize={15} fontWeight={700} fill={t.ink}>
            {PROGRESS}
          </text>
          <rect
            x={0}
            y={12}
            width={barW}
            height={barH}
            rx={3}
            fill="url(#route-seq-grad)"
            stroke={t.grid}
            strokeWidth={1}
          />
          <text x={0} y={44} fontSize={14} fill={t.inkSoft}>
            {`${minProgress.toFixed(2)} (Early)`}
          </text>
          <text x={barW} y={44} textAnchor="end" fontSize={14} fill={t.inkSoft}>
            {`${maxProgress.toFixed(2)} (Late)`}
          </text>
        </g>
      </g>
    </g>
  );
}

export default function Chart() {
  return (
    <div
      style={{
        width: canvasW,
        height: canvasH,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={canvasW}
        height={chartH}
        margin={MARGIN}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "lon",
            scaleType: "linear",
            min: xAxisMin,
            max: xAxisMax,
            height: X_AXIS_HEIGHT,
            label: LON,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `${v.toFixed(3)}°`,
          },
        ]}
        yAxis={[
          {
            id: "lat",
            scaleType: "linear",
            min: yAxisMin,
            max: yAxisMax,
            width: Y_AXIS_WIDTH,
            label: LAT,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `${v.toFixed(3)}°`,
          },
        ]}
        zAxis={[
          {
            id: "seqAxis",
            min: minProgress,
            max: maxProgress,
            colorMap: {
              type: "continuous",
              color: [t.seq[0], t.seq[t.seq.length - 1]],
            },
          },
        ]}
      >
        <ChartsGrid horizontal vertical />
        <RouteOverlay />
        <ChartsXAxis axisId="lon" />
        <ChartsYAxis axisId="lat" />
      </ChartsContainer>
      <div
        style={{
          height: CAPTION_HEIGHT,
          paddingLeft: MARGIN.left + Y_AXIS_WIDTH,
          display: "flex",
          alignItems: "center",
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        {BASEMAP_CAPTION}
      </div>
    </div>
  );
}
