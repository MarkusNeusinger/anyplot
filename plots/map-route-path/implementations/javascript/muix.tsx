// anyplot.ai
// map-route-path: Route and Path Map with Sequential Waypoints
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-19

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "map-route-path · javascript · muix · anyplot.ai";
const BASEMAP_CAPTION =
  "Coordinates: WGS 84 (EPSG:4326) · Amsterdam Centrum (Dam Square → Vondelpark → Rijksmuseum → Jordaan → Centraal)";
const TITLE_HEIGHT = 54;
const CAPTION_HEIGHT = 32;
const X_AXIS_HEIGHT = 58;
const Y_AXIS_WIDTH = 98;
const MARGIN = { top: 20, right: 260, bottom: 14, left: 16 };
const PAD_SHARE = 0.14;
const ARROW_STRIDE = 8;

// Data
const SEQ_COL = "Waypoint Sequence";
const LAT_COL = "Latitude (°N)";
const LON_COL = "Longitude (°E)";
const PROGRESS_COL = "Elapsed Time Share";
const LANDMARK_COL = "Landmark";

const KEYFRAMES: Array<[number, number, string]> = [
  [52.3731, 4.8926, "Start · Dam Square"],
  [52.3702, 4.8895, "Spui"],
  [52.3668, 4.8838, "Leidsestraat"],
  [52.364, 4.8815, "Leidseplein"],
  [52.358, 4.8686, "Vondelpark West"],
  [52.3565, 4.8755, "Vondelpark Pond"],
  [52.3585, 4.8815, "Museumplein"],
  [52.36, 4.8852, "Rijksmuseum"],
  [52.3635, 4.892, "Vijzelgracht"],
  [52.3662, 4.8995, "Rembrandtplein"],
  [52.3678, 4.904, "Waterlooplein"],
  [52.372, 4.9005, "Nieuwmarkt"],
  [52.3755, 4.896, "Oude Kerk"],
  [52.3765, 4.884, "Jordaan · Westerkerk"],
  [52.3795, 4.8895, "Haarlemmerstraat"],
  [52.3791, 4.9003, "End · Amsterdam Centraal"],
];

const STEPS_PER_LEG = 4;
const TOTAL_WAYPOINTS = (KEYFRAMES.length - 1) * STEPS_PER_LEG + 1;
const DATA: Array<Record<string, string | number>> = [];

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
    DATA.push({
      [SEQ_COL]: idx,
      [LAT_COL]: Number((lat1 + (lat2 - lat1) * u + jLat).toFixed(6)),
      [LON_COL]: Number((lon1 + (lon2 - lon1) * u + jLon).toFixed(6)),
      [PROGRESS_COL]: Number((idx / (TOTAL_WAYPOINTS - 1)).toFixed(4)),
      [LANDMARK_COL]: s === 0 ? name1 : "",
    });
  }
}
const lastKeyframe = KEYFRAMES[KEYFRAMES.length - 1];
DATA.push({
  [SEQ_COL]: TOTAL_WAYPOINTS - 1,
  [LAT_COL]: lastKeyframe[0],
  [LON_COL]: lastKeyframe[1],
  [PROGRESS_COL]: 1,
  [LANDMARK_COL]: lastKeyframe[2],
});

// Sort by sequence order before drawing path
const sortedRows = [...DATA].sort((a, b) => Number(a[SEQ_COL]) - Number(b[SEQ_COL]));
const lats = sortedRows.map((d) => Number(d[LAT_COL]));
const lons = sortedRows.map((d) => Number(d[LON_COL]));
const progressVals = sortedRows.map((d) => Number(d[PROGRESS_COL]));

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
  rawGroundAspect >= targetAspect ? rawLonSpan : (rawLatSpan * targetAspect) / cosMeanLat;
const finalLatSpan =
  rawGroundAspect >= targetAspect ? (rawLonSpan * cosMeanLat) / targetAspect : rawLatSpan;

const centerLon = (minLon + maxLon) / 2;
const centerLat = (minLat + maxLat) / 2;
const xAxisMin = centerLon - finalLonSpan / 2;
const xAxisMax = centerLon + finalLonSpan / 2;
const yAxisMin = centerLat - finalLatSpan / 2;
const yAxisMax = centerLat + finalLatSpan / 2;

// Parse sequential palette stops for smooth segment interpolation
const seqStops = t.seq.map((hex: string) => {
  const c = hex.replace("#", "");
  return [
    parseInt(c.slice(0, 2), 16),
    parseInt(c.slice(2, 4), 16),
    parseInt(c.slice(4, 6), 16),
  ];
});

const segmentColors: string[] = [];
for (let i = 0; i < sortedRows.length; i++) {
  const u = Math.max(0, Math.min(1, progressVals[i]));
  const scaled = u * (seqStops.length - 1);
  const idx = Math.min(seqStops.length - 2, Math.floor(scaled));
  const frac = scaled - idx;
  const c0 = seqStops[idx];
  const c1 = seqStops[idx + 1];
  const r = Math.round(c0[0] + (c1[0] - c0[0]) * frac);
  const g = Math.round(c0[1] + (c1[1] - c0[1]) * frac);
  const b = Math.round(c0[2] + (c1[2] - c0[2]) * frac);
  segmentColors.push(`rgb(${r}, ${g}, ${b})`);
}

const startColor = t.palette[0];
const endColor = t.palette[4];

function RouteOverlay() {
  const { left, top, width, height } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();

  const pts = sortedRows.map((row) => ({
    x: Number(xScale(Number(row[LON_COL]))),
    y: Number(yScale(Number(row[LAT_COL]))),
    landmark: String(row[LANDMARK_COL]),
    lat: Number(row[LAT_COL]),
    lon: Number(row[LON_COL]),
  }));

  const startPt = pts[0];
  const endPt = pts[pts.length - 1];

  // Key intermediate landmarks to label without clutter
  const keyLandmarks = [
    { idx: 4 * STEPS_PER_LEG, label: "Vondelpark West", dx: -14, dy: -12, anchor: "end" as const },
    { idx: 7 * STEPS_PER_LEG, label: "Rijksmuseum", dx: 14, dy: 18, anchor: "start" as const },
    { idx: 10 * STEPS_PER_LEG, label: "Waterlooplein", dx: 14, dy: 6, anchor: "start" as const },
    { idx: 13 * STEPS_PER_LEG, label: "Jordaan", dx: -14, dy: -10, anchor: "end" as const },
  ];

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
            stroke={segmentColors[i]}
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
              fill={segmentColors[i]}
              stroke={t.pageBg}
              strokeWidth={1.5}
              strokeLinejoin="round"
            />
          </g>
        );
      })}

      {/* Waypoint dots */}
      {pts.slice(1, -1).map((p, i) => {
        const isKeyframe = (i + 1) % STEPS_PER_LEG === 0;
        return (
          <circle
            key={`wp-${i}`}
            cx={p.x}
            cy={p.y}
            r={isKeyframe ? 4.8 : 2.8}
            fill={segmentColors[i + 1]}
            stroke={t.pageBg}
            strokeWidth={isKeyframe ? 1.8 : 1}
          />
        );
      })}

      {/* Intermediate landmark labels */}
      {keyLandmarks.map((lm) => {
        const pt = pts[lm.idx];
        if (!pt) return null;
        return (
          <text
            key={lm.label}
            x={pt.x + lm.dx}
            y={pt.y + lm.dy}
            textAnchor={lm.anchor}
            fontSize={14}
            fontWeight={500}
            fill={t.inkSoft}
            stroke={t.pageBg}
            strokeWidth={3.5}
            paintOrder="stroke"
          >
            {lm.label}
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
        Start · Dam Square
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
        End · Amsterdam Centraal
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
          Route Endpoints
        </text>
        <g transform="translate(0, 34)">
          <circle cx={9} cy={0} r={8} fill={startColor} stroke={t.pageBg} strokeWidth={2} />
          <text x={26} y={5} fontSize={14} fill={t.ink}>
            Start · Dam Square
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
            End · Centraal Station
          </text>
        </g>
        <g transform="translate(0, 94)">
          <polygon
            points="15,0 3,-5 6,0 3,5"
            fill={seqStops ? segmentColors[Math.floor(segmentColors.length / 2)] : t.palette[0]}
          />
          <text x={26} y={5} fontSize={14} fill={t.inkSoft}>
            Travel direction ({TOTAL_WAYPOINTS} GPS pts)
          </text>
        </g>

        <g transform="translate(0, 140)">
          <text x={0} y={0} fontSize={15} fontWeight={700} fill={t.ink}>
            {PROGRESS_COL}
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
            09:00 (Early)
          </text>
          <text x={barW} y={44} textAnchor="end" fontSize={14} fill={t.inkSoft}>
            10:30 (Late)
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
            label: LON_COL,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `${v.toFixed(3)}°E`,
          },
        ]}
        yAxis={[
          {
            id: "lat",
            scaleType: "linear",
            min: yAxisMin,
            max: yAxisMax,
            width: Y_AXIS_WIDTH,
            label: LAT_COL,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `${v.toFixed(3)}°N`,
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
