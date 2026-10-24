// anyplot.ai
// map-connection-lines: Connection Lines Map (Origin-Destination)
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 81/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "map-connection-lines · javascript · muix · anyplot.ai";
const LON_PAD_FRAC = 0.08;
const LAT_PAD_FRAC = 0.15;
const ARC_BOW_FACTOR = 0.16;
const NEIGHBOR_THRESHOLD_SHARE = 0.045;

// Simplified world coastlines (lon/lat vertices)
const CONTINENTS: Array<Array<[number, number]>> = [
  [
    [-165, 65], [-140, 60], [-125, 49], [-124, 40], [-117, 32], [-105, 22], [-97, 16],
    [-90, 14], [-88, 21], [-81, 25], [-80, 32], [-75, 40], [-70, 44], [-65, 47],
    [-75, 55], [-95, 62], [-110, 68], [-140, 68], [-165, 65],
  ],
  [
    [-77, 8], [-80, 0], [-81, -6], [-71, -18], [-70, -33], [-68, -45], [-68, -54],
    [-65, -52], [-58, -38], [-48, -25], [-40, -13], [-35, -6], [-50, 0], [-60, 8],
    [-72, 10], [-77, 8],
  ],
  [
    [-9, 43], [-9, 37], [3, 36], [10, 44], [15, 38], [20, 40], [28, 41], [30, 46],
    [38, 55], [30, 60], [10, 58], [5, 51], [-1, 51], [-5, 55], [-9, 43],
  ],
  [
    [-17, 21], [-17, 14], [-10, 6], [3, 6], [9, 4], [13, -6], [18, -34], [26, -33],
    [35, -20], [40, -3], [45, 11], [43, 12], [38, 15], [32, 31], [10, 37], [-6, 35],
    [-17, 21],
  ],
  [
    [27, 41], [35, 30], [42, 13], [56, 25], [61, 25], [72, 19], [77, 8], [80, 13],
    [88, 22], [96, 16], [100, 13], [104, 10], [109, 21], [121, 25], [122, 31],
    [130, 38], [140, 36], [142, 43], [135, 50], [100, 55], [60, 55], [48, 42],
    [35, 45], [27, 41],
  ],
  [
    [113, -22], [115, -32], [131, -12], [142, -11], [145, -17], [153, -28],
    [151, -34], [140, -38], [135, -35], [113, -22],
  ],
];

// Columns: set these to your data's column names
const ORIGIN_CODE = "Origin airport"; // role: label
const ORIGIN_LAT = "Origin latitude (°)"; // role: origin_lat
const ORIGIN_LON = "Origin longitude (°)"; // role: origin_lon
const DEST_CODE = "Destination airport"; // role: dest_label
const DEST_LAT = "Destination latitude (°)"; // role: dest_lat
const DEST_LON = "Destination longitude (°)"; // role: dest_lon
const PASSENGERS = "Annual passengers (thousands)"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [ORIGIN_CODE]: "JFK", [ORIGIN_LAT]: 40.64, [ORIGIN_LON]: -73.78, [DEST_CODE]: "LHR", [DEST_LAT]: 51.47, [DEST_LON]: -0.45, [PASSENGERS]: 820 },
  { [ORIGIN_CODE]: "JFK", [ORIGIN_LAT]: 40.64, [ORIGIN_LON]: -73.78, [DEST_CODE]: "CDG", [DEST_LAT]: 49.01, [DEST_LON]: 2.55, [PASSENGERS]: 610 },
  { [ORIGIN_CODE]: "LAX", [ORIGIN_LAT]: 33.94, [ORIGIN_LON]: -118.41, [DEST_CODE]: "NRT", [DEST_LAT]: 35.76, [DEST_LON]: 140.39, [PASSENGERS]: 540 },
  { [ORIGIN_CODE]: "LAX", [ORIGIN_LAT]: 33.94, [ORIGIN_LON]: -118.41, [DEST_CODE]: "SYD", [DEST_LAT]: -33.95, [DEST_LON]: 151.18, [PASSENGERS]: 310 },
  { [ORIGIN_CODE]: "SFO", [ORIGIN_LAT]: 37.62, [ORIGIN_LON]: -122.38, [DEST_CODE]: "HKG", [DEST_LAT]: 22.31, [DEST_LON]: 113.91, [PASSENGERS]: 460 },
  { [ORIGIN_CODE]: "ORD", [ORIGIN_LAT]: 41.98, [ORIGIN_LON]: -87.9, [DEST_CODE]: "FRA", [DEST_LAT]: 50.03, [DEST_LON]: 8.57, [PASSENGERS]: 390 },
  { [ORIGIN_CODE]: "DXB", [ORIGIN_LAT]: 25.25, [ORIGIN_LON]: 55.36, [DEST_CODE]: "LHR", [DEST_LAT]: 51.47, [DEST_LON]: -0.45, [PASSENGERS]: 705 },
  { [ORIGIN_CODE]: "DXB", [ORIGIN_LAT]: 25.25, [ORIGIN_LON]: 55.36, [DEST_CODE]: "JFK", [DEST_LAT]: 40.64, [DEST_LON]: -73.78, [PASSENGERS]: 480 },
  { [ORIGIN_CODE]: "SIN", [ORIGIN_LAT]: 1.35, [ORIGIN_LON]: 103.99, [DEST_CODE]: "SYD", [DEST_LAT]: -33.95, [DEST_LON]: 151.18, [PASSENGERS]: 520 },
  { [ORIGIN_CODE]: "SIN", [ORIGIN_LAT]: 1.35, [ORIGIN_LON]: 103.99, [DEST_CODE]: "NRT", [DEST_LAT]: 35.76, [DEST_LON]: 140.39, [PASSENGERS]: 445 },
  { [ORIGIN_CODE]: "GRU", [ORIGIN_LAT]: -23.43, [ORIGIN_LON]: -46.47, [DEST_CODE]: "JFK", [DEST_LAT]: 40.64, [DEST_LON]: -73.78, [PASSENGERS]: 385 },
  { [ORIGIN_CODE]: "GRU", [ORIGIN_LAT]: -23.43, [ORIGIN_LON]: -46.47, [DEST_CODE]: "CDG", [DEST_LAT]: 49.01, [DEST_LON]: 2.55, [PASSENGERS]: 260 },
  { [ORIGIN_CODE]: "JNB", [ORIGIN_LAT]: -26.13, [ORIGIN_LON]: 28.24, [DEST_CODE]: "DXB", [DEST_LAT]: 25.25, [DEST_LON]: 55.36, [PASSENGERS]: 300 },
  { [ORIGIN_CODE]: "DEL", [ORIGIN_LAT]: 28.56, [ORIGIN_LON]: 77.1, [DEST_CODE]: "LHR", [DEST_LAT]: 51.47, [DEST_LON]: -0.45, [PASSENGERS]: 560 },
  { [ORIGIN_CODE]: "PEK", [ORIGIN_LAT]: 40.08, [ORIGIN_LON]: 116.58, [DEST_CODE]: "LAX", [DEST_LAT]: 33.94, [DEST_LON]: -118.41, [PASSENGERS]: 415 },
  { [ORIGIN_CODE]: "HKG", [ORIGIN_LAT]: 22.31, [ORIGIN_LON]: 113.91, [DEST_CODE]: "SYD", [DEST_LAT]: -33.95, [DEST_LON]: 151.18, [PASSENGERS]: 330 },
];

// Plot: reads only data and the constants above
const airportsMap = new Map<
  string,
  { code: string; lat: number; lon: number; degree: number }
>();
for (const row of data) {
  const oCode = String(row[ORIGIN_CODE]);
  const dCode = String(row[DEST_CODE]);
  if (!airportsMap.has(oCode)) {
    airportsMap.set(oCode, {
      code: oCode,
      lat: Number(row[ORIGIN_LAT]),
      lon: Number(row[ORIGIN_LON]),
      degree: 0,
    });
  }
  if (!airportsMap.has(dCode)) {
    airportsMap.set(dCode, {
      code: dCode,
      lat: Number(row[DEST_LAT]),
      lon: Number(row[DEST_LON]),
      degree: 0,
    });
  }
  airportsMap.get(oCode)!.degree += 1;
  airportsMap.get(dCode)!.degree += 1;
}
const airportList = Array.from(airportsMap.values());

const passengerValues = data.map((r) => Number(r[PASSENGERS]));
const minPassengers = Math.min(...passengerValues);
const maxPassengers = Math.max(...passengerValues);

const lons = airportList.map((a) => a.lon);
const lats = airportList.map((a) => a.lat);
const rawLonMin = Math.min(...lons);
const rawLonMax = Math.max(...lons);
const rawLatMin = Math.min(...lats);
const rawLatMax = Math.max(...lats);

const { width: W, height: H } = window.ANYPLOT_SIZE;
const MARGIN = { top: 82, right: 56, bottom: 52, left: 22 };
const X_AXIS_H = 56;
const Y_AXIS_W = 68;
const DRAW_W = W - MARGIN.left - MARGIN.right - Y_AXIS_W;
const DRAW_H = H - MARGIN.top - MARGIN.bottom - X_AXIS_H;

const meanLatDeg = (rawLatMin + rawLatMax) / 2;
const cosMeanLat = Math.cos((meanLatDeg * Math.PI) / 180);
const paddedLonSpan = (rawLonMax - rawLonMin) * (1 + 2 * LON_PAD_FRAC);
const paddedLatSpan = (rawLatMax - rawLatMin) * (1 + 2 * LAT_PAD_FRAC);
const targetAspect = DRAW_W / DRAW_H;
const groundAspect = (paddedLonSpan * cosMeanLat) / paddedLatSpan;

// Routes crossing the antimeridian need the whole globe in frame to stay whole
const wrapsAntimeridian = data.some(
  (r) => Math.abs(Number(r[DEST_LON]) - Number(r[ORIGIN_LON])) > 180,
);

// Regional data widens longitude to keep the ground aspect; a wide frame keeps
// the latitude range tight instead of padding it with empty bands
const finalLonSpan = wrapsAntimeridian
  ? 360
  : groundAspect >= targetAspect
    ? paddedLonSpan
    : (paddedLatSpan * targetAspect) / cosMeanLat;
const finalLatSpan = paddedLatSpan;

const lonCenter = wrapsAntimeridian ? 0 : (rawLonMin + rawLonMax) / 2;
const latCenter = (rawLatMin + rawLatMax) / 2;
const LON_MIN = lonCenter - finalLonSpan / 2;
const LON_MAX = lonCenter + finalLonSpan / 2;
const LAT_MIN = latCenter - finalLatSpan / 2;
const LAT_MAX = latCenter + finalLatSpan / 2;

const neighborThresholdDeg = finalLonSpan * NEIGHBOR_THRESHOLD_SHARE;
const airportLabelOffsets: Record<string, { dx: number; dy: number }> = {};
for (const a of airportList) {
  const radius = 5 + a.degree * 1.8;
  const neighbors = airportList.filter(
    (b) =>
      b.code !== a.code &&
      Math.hypot((b.lon - a.lon) * cosMeanLat, b.lat - a.lat) <
        neighborThresholdDeg,
  );
  if (neighbors.length === 0) {
    // Isolated label goes on the side away from where its routes leave
    const partnerLatShift = data.reduce((s, r) => {
      if (r[ORIGIN_CODE] === a.code) return s + Number(r[DEST_LAT]) - a.lat;
      if (r[DEST_CODE] === a.code) return s + Number(r[ORIGIN_LAT]) - a.lat;
      return s;
    }, 0);
    airportLabelOffsets[a.code] =
      partnerLatShift > 0
        ? { dx: 0, dy: radius + 20 }
        : { dx: 0, dy: -(radius + 9) };
  } else {
    const meanLon = neighbors.reduce((s, n) => s + n.lon, 0) / neighbors.length;
    const meanLat = neighbors.reduce((s, n) => s + n.lat, 0) / neighbors.length;
    const vx = (a.lon - meanLon) * cosMeanLat;
    const vy = -(a.lat - meanLat);
    const len = Math.hypot(vx, vy);
    const dist = radius + 16;
    airportLabelOffsets[a.code] = {
      dx: (vx / len) * dist * 1.25,
      dy: (vy / len) * dist + 4,
    };
  }
}

const lonUnitMatch = ORIGIN_LON.match(/\(([^)]+)\)/);
const LON_UNIT = lonUnitMatch ? lonUnitMatch[1] : "";
const latUnitMatch = ORIGIN_LAT.match(/\(([^)]+)\)/);
const LAT_UNIT = latUnitMatch ? latUnitMatch[1] : "";

function ConnectionMapLayer() {
  const xScale = useXScale("lon") as (v: number) => number;
  const yScale = useYScale("lat") as (v: number) => number;
  const drawingArea = useDrawingArea();

  return (
    <g>
      <defs>
        <clipPath id="worldClip">
          <rect
            x={drawingArea.left}
            y={drawingArea.top}
            width={drawingArea.width}
            height={drawingArea.height}
          />
        </clipPath>
      </defs>

      {/* Simplified land masses */}
      <g clipPath="url(#worldClip)">
        {CONTINENTS.map((points, i) => {
          const d =
            points
              .map(
                ([lon, lat], j) =>
                  `${j === 0 ? "M" : "L"} ${xScale(lon)},${yScale(lat)}`,
              )
              .join(" ") + " Z";
          return (
            <path
              key={i}
              d={d}
              fill={t.grid}
              fillOpacity={0.6}
              stroke={t.inkSoft}
              strokeWidth={1}
              strokeOpacity={0.5}
            />
          );
        })}

        {/* Geodesic-style connection arcs (splitting trans-antimeridian routes) */}
        {data.map((row, i) => {
          const lon1 = Number(row[ORIGIN_LON]);
          const lat1 = Number(row[ORIGIN_LAT]);
          const lon2 = Number(row[DEST_LON]);
          const lat2 = Number(row[DEST_LAT]);

          const pax = Number(row[PASSENGERS]);
          const ratio =
            (pax - minPassengers) / (maxPassengers - minPassengers);
          const strokeWidth = 3 + ratio * 6;
          const strokeOpacity = 0.45 + ratio * 0.25;

          const segments: Array<[number, number, number, number]> = [];
          if (Math.abs(lon2 - lon1) <= 180) {
            segments.push([lon1, lat1, lon2, lat2]);
          } else {
            const lon2Unwrapped = lon2 > lon1 ? lon2 - 360 : lon2 + 360;
            const edgeLon1 = lon1 < 0 ? -180 : 180;
            const edgeLon2 = -edgeLon1;
            const frac = (edgeLon1 - lon1) / (lon2Unwrapped - lon1);
            const crossLat = lat1 + frac * (lat2 - lat1);
            segments.push([lon1, lat1, edgeLon1, crossLat]);
            segments.push([edgeLon2, crossLat, lon2, lat2]);
          }

          return (
            <g key={`${row[ORIGIN_CODE]}-${row[DEST_CODE]}-${i}`}>
              {segments.map(([sLon1, sLat1, sLon2, sLat2], sIdx) => {
                const x1 = xScale(sLon1);
                const y1 = yScale(sLat1);
                const x2 = xScale(sLon2);
                const y2 = yScale(sLat2);
                const dx = x2 - x1;
                const dy = y2 - y1;
                const dist = Math.hypot(dx, dy);
                const midX = (x1 + x2) / 2;
                const midY = (y1 + y2) / 2;
                const bowSign = y1 + y2 < yScale(0) * 2 ? -1 : 1;
                const bow = dist * ARC_BOW_FACTOR * bowSign;
                const controlX = midX;
                const controlY = midY + bow;
                return (
                  <path
                    key={sIdx}
                    d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
                    fill="none"
                    stroke={t.palette[0]}
                    strokeWidth={strokeWidth}
                    strokeOpacity={strokeOpacity}
                    strokeLinecap="round"
                  />
                );
              })}
            </g>
          );
        })}
      </g>

      {/* Airport endpoint markers and collision-avoiding labels */}
      {airportList.map((airport) => {
        const cx = xScale(airport.lon);
        const cy = yScale(airport.lat);
        const radius = 5 + airport.degree * 1.8;
        const nudge = airportLabelOffsets[airport.code];
        return (
          <g key={airport.code}>
            <circle
              cx={cx}
              cy={cy}
              r={radius}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={2}
            />
            <text
              x={cx + nudge.dx}
              y={cy + nudge.dy}
              textAnchor="middle"
              fontSize={14}
              fontWeight={500}
              fill={t.ink}
            >
              {airport.code}
            </text>
          </g>
        );
      })}

      {/* Title */}
      <text
        x={W / 2}
        y={36}
        textAnchor="middle"
        dominantBaseline="hanging"
        fontSize={22}
        fontWeight={500}
        fill={t.ink}
      >
        {TITLE}
      </text>

      {/* Encoding caption */}
      <text
        x={drawingArea.left}
        y={drawingArea.top + drawingArea.height + 68}
        textAnchor="start"
        dominantBaseline="hanging"
        fontSize={14}
        fontWeight={400}
        fill={t.inkSoft}
      >
        {`Line thickness and opacity encode ${PASSENGERS}; marker size encodes route degree.`}
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, backgroundColor: t.pageBg }}>
      <ChartsContainer
        width={W}
        height={H}
        margin={MARGIN}
        series={[]}
        skipAnimation
        disableAxisListener
        xAxis={[
          {
            id: "lon",
            scaleType: "linear",
            min: LON_MIN,
            max: LON_MAX,
            height: X_AXIS_H,
            label: `Longitude (${LON_UNIT})`,            valueFormatter: (v: number | null) =>
              v === null ? "" : `${Math.round(v)}${LON_UNIT}`,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "lat",
            scaleType: "linear",
            min: LAT_MIN,
            max: LAT_MAX,
            width: Y_AXIS_W,
            label: `Latitude (${LAT_UNIT})`,
            valueFormatter: (v: number | null) =>
              v === null ? "" : `${Math.round(v)}${LAT_UNIT}`,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsGrid horizontal vertical />
        <ChartsReferenceLine
          y={0}
          axisId="lat"
          label="Equator"
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 6", strokeOpacity: 0.6 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
        />
        <ChartsReferenceLine
          x={0}
          axisId="lon"
          label="Prime Meridian"
          labelAlign="start"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 6", strokeOpacity: 0.6 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
        />
        <ConnectionMapLayer />
        <ChartsXAxis axisId="lon" />
        <ChartsYAxis axisId="lat" />
      </ChartsContainer>
    </div>
  );
}
