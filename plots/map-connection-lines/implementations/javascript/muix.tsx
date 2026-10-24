// anyplot.ai
// map-connection-lines: Connection Lines Map (Origin-Destination)
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "map-connection-lines · javascript · muix · anyplot.ai";

// Constants
const ORIGIN_CODE_COL = "Origin Code" as const;
const ORIGIN_NAME_COL = "Origin City" as const;
const ORIGIN_LAT_COL = "Origin Latitude (°)" as const;
const ORIGIN_LON_COL = "Origin Longitude (°)" as const;
const DEST_CODE_COL = "Destination Code" as const;
const DEST_NAME_COL = "Destination City" as const;
const DEST_LAT_COL = "Destination Latitude (°)" as const;
const DEST_LON_COL = "Destination Longitude (°)" as const;
const PASSENGERS_COL = "Annual Passengers (thousands)" as const;

const LON_PAD_FRAC = 0.08;
const ARC_BOW_FACTOR = 0.16;
const NEIGHBOR_THRESHOLD_DEG = 15;

// Data — origin-destination flight routes with passenger volume (thousands/year)
const DATA: Array<Record<string, string | number>> = [
  { [ORIGIN_CODE_COL]: "JFK", [ORIGIN_NAME_COL]: "New York", [ORIGIN_LAT_COL]: 40.64, [ORIGIN_LON_COL]: -73.78, [DEST_CODE_COL]: "LHR", [DEST_NAME_COL]: "London", [DEST_LAT_COL]: 51.47, [DEST_LON_COL]: -0.45, [PASSENGERS_COL]: 820 },
  { [ORIGIN_CODE_COL]: "JFK", [ORIGIN_NAME_COL]: "New York", [ORIGIN_LAT_COL]: 40.64, [ORIGIN_LON_COL]: -73.78, [DEST_CODE_COL]: "CDG", [DEST_NAME_COL]: "Paris", [DEST_LAT_COL]: 49.01, [DEST_LON_COL]: 2.55, [PASSENGERS_COL]: 610 },
  { [ORIGIN_CODE_COL]: "LAX", [ORIGIN_NAME_COL]: "Los Angeles", [ORIGIN_LAT_COL]: 33.94, [ORIGIN_LON_COL]: -118.41, [DEST_CODE_COL]: "NRT", [DEST_NAME_COL]: "Tokyo", [DEST_LAT_COL]: 35.76, [DEST_LON_COL]: 140.39, [PASSENGERS_COL]: 540 },
  { [ORIGIN_CODE_COL]: "LAX", [ORIGIN_NAME_COL]: "Los Angeles", [ORIGIN_LAT_COL]: 33.94, [ORIGIN_LON_COL]: -118.41, [DEST_CODE_COL]: "SYD", [DEST_NAME_COL]: "Sydney", [DEST_LAT_COL]: -33.95, [DEST_LON_COL]: 151.18, [PASSENGERS_COL]: 310 },
  { [ORIGIN_CODE_COL]: "SFO", [ORIGIN_NAME_COL]: "San Francisco", [ORIGIN_LAT_COL]: 37.62, [ORIGIN_LON_COL]: -122.38, [DEST_CODE_COL]: "HKG", [DEST_NAME_COL]: "Hong Kong", [DEST_LAT_COL]: 22.31, [DEST_LON_COL]: 113.91, [PASSENGERS_COL]: 460 },
  { [ORIGIN_CODE_COL]: "ORD", [ORIGIN_NAME_COL]: "Chicago", [ORIGIN_LAT_COL]: 41.98, [ORIGIN_LON_COL]: -87.9, [DEST_CODE_COL]: "FRA", [DEST_NAME_COL]: "Frankfurt", [DEST_LAT_COL]: 50.03, [DEST_LON_COL]: 8.57, [PASSENGERS_COL]: 390 },
  { [ORIGIN_CODE_COL]: "DXB", [ORIGIN_NAME_COL]: "Dubai", [ORIGIN_LAT_COL]: 25.25, [ORIGIN_LON_COL]: 55.36, [DEST_CODE_COL]: "LHR", [DEST_NAME_COL]: "London", [DEST_LAT_COL]: 51.47, [DEST_LON_COL]: -0.45, [PASSENGERS_COL]: 705 },
  { [ORIGIN_CODE_COL]: "DXB", [ORIGIN_NAME_COL]: "Dubai", [ORIGIN_LAT_COL]: 25.25, [ORIGIN_LON_COL]: 55.36, [DEST_CODE_COL]: "JFK", [DEST_NAME_COL]: "New York", [DEST_LAT_COL]: 40.64, [DEST_LON_COL]: -73.78, [PASSENGERS_COL]: 480 },
  { [ORIGIN_CODE_COL]: "SIN", [ORIGIN_NAME_COL]: "Singapore", [ORIGIN_LAT_COL]: 1.35, [ORIGIN_LON_COL]: 103.99, [DEST_CODE_COL]: "SYD", [DEST_NAME_COL]: "Sydney", [DEST_LAT_COL]: -33.95, [DEST_LON_COL]: 151.18, [PASSENGERS_COL]: 520 },
  { [ORIGIN_CODE_COL]: "SIN", [ORIGIN_NAME_COL]: "Singapore", [ORIGIN_LAT_COL]: 1.35, [ORIGIN_LON_COL]: 103.99, [DEST_CODE_COL]: "NRT", [DEST_NAME_COL]: "Tokyo", [DEST_LAT_COL]: 35.76, [DEST_LON_COL]: 140.39, [PASSENGERS_COL]: 445 },
  { [ORIGIN_CODE_COL]: "GRU", [ORIGIN_NAME_COL]: "São Paulo", [ORIGIN_LAT_COL]: -23.43, [ORIGIN_LON_COL]: -46.47, [DEST_CODE_COL]: "JFK", [DEST_NAME_COL]: "New York", [DEST_LAT_COL]: 40.64, [DEST_LON_COL]: -73.78, [PASSENGERS_COL]: 385 },
  { [ORIGIN_CODE_COL]: "GRU", [ORIGIN_NAME_COL]: "São Paulo", [ORIGIN_LAT_COL]: -23.43, [ORIGIN_LON_COL]: -46.47, [DEST_CODE_COL]: "CDG", [DEST_NAME_COL]: "Paris", [DEST_LAT_COL]: 49.01, [DEST_LON_COL]: 2.55, [PASSENGERS_COL]: 260 },
  { [ORIGIN_CODE_COL]: "JNB", [ORIGIN_NAME_COL]: "Johannesburg", [ORIGIN_LAT_COL]: -26.13, [ORIGIN_LON_COL]: 28.24, [DEST_CODE_COL]: "DXB", [DEST_NAME_COL]: "Dubai", [DEST_LAT_COL]: 25.25, [DEST_LON_COL]: 55.36, [PASSENGERS_COL]: 300 },
  { [ORIGIN_CODE_COL]: "DEL", [ORIGIN_NAME_COL]: "New Delhi", [ORIGIN_LAT_COL]: 28.56, [ORIGIN_LON_COL]: 77.1, [DEST_CODE_COL]: "LHR", [DEST_NAME_COL]: "London", [DEST_LAT_COL]: 51.47, [DEST_LON_COL]: -0.45, [PASSENGERS_COL]: 560 },
  { [ORIGIN_CODE_COL]: "PEK", [ORIGIN_NAME_COL]: "Beijing", [ORIGIN_LAT_COL]: 40.08, [ORIGIN_LON_COL]: 116.58, [DEST_CODE_COL]: "LAX", [DEST_NAME_COL]: "Los Angeles", [DEST_LAT_COL]: 33.94, [DEST_LON_COL]: -118.41, [PASSENGERS_COL]: 415 },
  { [ORIGIN_CODE_COL]: "HKG", [ORIGIN_NAME_COL]: "Hong Kong", [ORIGIN_LAT_COL]: 22.31, [ORIGIN_LON_COL]: 113.91, [DEST_CODE_COL]: "SYD", [DEST_NAME_COL]: "Sydney", [DEST_LAT_COL]: -33.95, [DEST_LON_COL]: 151.18, [PASSENGERS_COL]: 330 },
];

// Discover unique airports and hub degrees across both origin and destination columns
const airportsMap = new Map<
  string,
  { code: string; name: string; lat: number; lon: number; degree: number }
>();
for (const row of DATA) {
  const oCode = String(row[ORIGIN_CODE_COL]);
  const dCode = String(row[DEST_CODE_COL]);
  if (!airportsMap.has(oCode)) {
    airportsMap.set(oCode, {
      code: oCode,
      name: String(row[ORIGIN_NAME_COL]),
      lat: Number(row[ORIGIN_LAT_COL]),
      lon: Number(row[ORIGIN_LON_COL]),
      degree: 0,
    });
  }
  if (!airportsMap.has(dCode)) {
    airportsMap.set(dCode, {
      code: dCode,
      name: String(row[DEST_NAME_COL]),
      lat: Number(row[DEST_LAT_COL]),
      lon: Number(row[DEST_LON_COL]),
      degree: 0,
    });
  }
  airportsMap.get(oCode)!.degree += 1;
  airportsMap.get(dCode)!.degree += 1;
}
const airportList = Array.from(airportsMap.values());

const passengerValues = DATA.map((r) => Number(r[PASSENGERS_COL]));
const minPassengers = Math.min(...passengerValues);
const maxPassengers = Math.max(...passengerValues);

const lons = airportList.map((a) => a.lon);
const lats = airportList.map((a) => a.lat);
const rawLonMin = Math.min(...lons);
const rawLonMax = Math.max(...lons);
const rawLatMin = Math.min(...lats);
const rawLatMax = Math.max(...lats);
const lonRange = rawLonMax - rawLonMin || 1;

const LON_MIN = Math.round(rawLonMin - lonRange * LON_PAD_FRAC);
const LON_MAX = Math.round(rawLonMax + lonRange * LON_PAD_FRAC);

// Enforce 1 / cos(meanLat) geographic aspect ratio on the drawing area
const { width: W, height: H } = window.ANYPLOT_SIZE;
const MARGIN = { top: 82, right: 56, bottom: 52, left: 22 };
const X_AXIS_H = 56;
const Y_AXIS_W = 68;
const DRAW_W = W - MARGIN.left - MARGIN.right - Y_AXIS_W;
const DRAW_H = H - MARGIN.top - MARGIN.bottom - X_AXIS_H;

const meanLatDeg = (rawLatMin + rawLatMax) / 2;
const cosMeanLat = Math.cos((meanLatDeg * Math.PI) / 180);
const lonSpan = LON_MAX - LON_MIN;
const requiredLatSpan = (lonSpan * cosMeanLat) / (DRAW_W / DRAW_H);
const latCenter = (rawLatMin + rawLatMax) / 2;
const LAT_MIN = Math.round(latCenter - requiredLatSpan / 2);
const LAT_MAX = Math.round(latCenter + requiredLatSpan / 2);

// Data-driven label offsets so clustered airports repel away from close neighbors
const airportLabelOffsets: Record<string, { dx: number; dy: number }> = {};
for (const a of airportList) {
  const radius = 5 + a.degree * 1.8;
  const neighbors = airportList.filter(
    (b) =>
      b.code !== a.code &&
      Math.hypot((b.lon - a.lon) * cosMeanLat, b.lat - a.lat) < NEIGHBOR_THRESHOLD_DEG,
  );
  if (neighbors.length === 0) {
    airportLabelOffsets[a.code] = { dx: 0, dy: -(radius + 9) };
  } else {
    const meanLon = neighbors.reduce((s, n) => s + n.lon, 0) / neighbors.length;
    const meanLat = neighbors.reduce((s, n) => s + n.lat, 0) / neighbors.length;
    const vx = (a.lon - meanLon) * cosMeanLat;
    const vy = -(a.lat - meanLat); // SVG y is downward
    const len = Math.hypot(vx, vy) || 1;
    const dist = radius + 16;
    airportLabelOffsets[a.code] = {
      dx: (vx / len) * dist * 1.25,
      dy: (vy / len) * dist + 4,
    };
  }
}

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

const LON_UNIT = ORIGIN_LON_COL.match(/\(([^)]+)\)/)?.[1] ?? "°";
const LAT_UNIT = ORIGIN_LAT_COL.match(/\(([^)]+)\)/)?.[1] ?? "°";

function ConnectionMapLayer() {
  const xScale = useXScale("lon") as (v: number) => number | undefined;
  const yScale = useYScale("lat") as (v: number) => number | undefined;
  const drawingArea = useDrawingArea();

  const toX = (v: number) => Number(xScale(v) ?? 0);
  const toY = (v: number) => Number(yScale(v) ?? 0);

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
              .map(([lon, lat], j) => `${j === 0 ? "M" : "L"} ${toX(lon)},${toY(lat)}`)
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
      </g>

      {/* Geodesic-style connection arcs */}
      {DATA.map((row, i) => {
        const x1 = toX(Number(row[ORIGIN_LON_COL]));
        const y1 = toY(Number(row[ORIGIN_LAT_COL]));
        const x2 = toX(Number(row[DEST_LON_COL]));
        const y2 = toY(Number(row[DEST_LAT_COL]));

        const dx = x2 - x1;
        const dy = y2 - y1;
        const dist = Math.hypot(dx, dy);
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        const ux = dist === 0 ? 0 : -dy / dist;
        const uy = dist === 0 ? 0 : dx / dist;
        const bow = dist * ARC_BOW_FACTOR;
        const controlX = midX + ux * bow;
        const controlY = midY + uy * bow;

        const pax = Number(row[PASSENGERS_COL]);
        const ratio = (pax - minPassengers) / (maxPassengers - minPassengers || 1);
        const strokeWidth = 2.5 + ratio * 6;
        const strokeOpacity = 0.3 + ratio * 0.3;

        return (
          <path
            key={`${row[ORIGIN_CODE_COL]}-${row[DEST_CODE_COL]}-${i}`}
            d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
            fill="none"
            stroke={t.palette[0]}
            strokeWidth={strokeWidth}
            strokeOpacity={strokeOpacity}
            strokeLinecap="round"
          />
        );
      })}

      {/* Airport endpoint markers and collision-avoiding labels */}
      {airportList.map((airport) => {
        const cx = toX(airport.lon);
        const cy = toY(airport.lat);
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
        {`Line thickness and opacity encode ${PASSENGERS_COL.toLowerCase()}; marker size encodes route degree.`}
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
            label: `Longitude (${LON_UNIT})`,
            valueFormatter: (v: number | null) => `${v ?? ""}${LON_UNIT}`,
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
            valueFormatter: (v: number | null) => `${v ?? ""}${LAT_UNIT}`,
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
