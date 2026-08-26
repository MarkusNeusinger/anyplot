// anyplot.ai
// map-connection-lines: Connection Lines Map (Origin-Destination)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 80/100 | Created: 2026-08-26
//# anyplot-orientation: landscape
// anyplot.ai
// map-connection-lines: Connection Lines Map (Origin-Destination)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "map-connection-lines · javascript · muix · anyplot.ai";

// --- Data: major airports (in-memory, deterministic) ------------------------
const airports = {
  JFK: { name: "New York", lat: 40.64, lon: -73.78 },
  LHR: { name: "London", lat: 51.47, lon: -0.45 },
  CDG: { name: "Paris", lat: 49.01, lon: 2.55 },
  LAX: { name: "Los Angeles", lat: 33.94, lon: -118.41 },
  NRT: { name: "Tokyo", lat: 35.76, lon: 140.39 },
  SYD: { name: "Sydney", lat: -33.95, lon: 151.18 },
  SFO: { name: "San Francisco", lat: 37.62, lon: -122.38 },
  HKG: { name: "Hong Kong", lat: 22.31, lon: 113.91 },
  ORD: { name: "Chicago", lat: 41.98, lon: -87.9 },
  FRA: { name: "Frankfurt", lat: 50.03, lon: 8.57 },
  DXB: { name: "Dubai", lat: 25.25, lon: 55.36 },
  SIN: { name: "Singapore", lat: 1.35, lon: 103.99 },
  GRU: { name: "São Paulo", lat: -23.43, lon: -46.47 },
  JNB: { name: "Johannesburg", lat: -26.13, lon: 28.24 },
  DEL: { name: "New Delhi", lat: 28.56, lon: 77.1 },
  PEK: { name: "Beijing", lat: 40.08, lon: 116.58 },
};

// Flight routes: passenger volume in thousands per year (line weight)
const routes = [
  { from: "JFK", to: "LHR", passengers: 820 },
  { from: "JFK", to: "CDG", passengers: 610 },
  { from: "LAX", to: "NRT", passengers: 540 },
  { from: "LAX", to: "SYD", passengers: 310 },
  { from: "SFO", to: "HKG", passengers: 460 },
  { from: "ORD", to: "FRA", passengers: 390 },
  { from: "DXB", to: "LHR", passengers: 705 },
  { from: "DXB", to: "JFK", passengers: 480 },
  { from: "SIN", to: "SYD", passengers: 520 },
  { from: "SIN", to: "NRT", passengers: 445 },
  { from: "GRU", to: "JFK", passengers: 385 },
  { from: "GRU", to: "CDG", passengers: 260 },
  { from: "JNB", to: "DXB", passengers: 300 },
  { from: "DEL", to: "LHR", passengers: 560 },
  { from: "PEK", to: "LAX", passengers: 415 },
  { from: "HKG", to: "SYD", passengers: 330 },
];

const passengerValues = routes.map((r) => r.passengers);
const minPassengers = Math.min(...passengerValues);
const maxPassengers = Math.max(...passengerValues);

// Hub size = number of routes touching an airport
const degreeByAirport = {};
routes.forEach((r) => {
  degreeByAirport[r.from] = (degreeByAirport[r.from] || 0) + 1;
  degreeByAirport[r.to] = (degreeByAirport[r.to] || 0) + 1;
});

// Manual label nudges for the closely clustered European hubs (LHR/CDG/FRA)
// so their code labels don't collide — markers stay at true coordinates.
const labelNudge = {
  LHR: { dx: -18, dy: -8 },
  CDG: { dx: -6, dy: 22 },
  FRA: { dx: 22, dy: -2 },
};

const lons = Object.values(airports).map((a) => a.lon);
const lats = Object.values(airports).map((a) => a.lat);
const LON_MIN = Math.min(...lons) - 14;
const LON_MAX = Math.max(...lons) + 14;
const LAT_MIN = Math.min(...lats) - 8;
const LAT_MAX = Math.max(...lats) + 8;

// --- Overlay: title drawn in the reserved top margin -------------------------
function MapTitle() {
  const drawingArea = useDrawingArea();
  return (
    <ChartsText
      x={drawingArea.left + drawingArea.width / 2}
      y={40}
      text={TITLE}
      textAnchor="middle"
      dominantBaseline="hanging"
      style={{ fontSize: 22, fontWeight: 500, fill: t.ink }}
    />
  );
}

// --- Overlay: geodesic-style connection arcs + endpoint markers -------------
function ConnectionOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {routes.map((route, i) => {
        const origin = airports[route.from];
        const dest = airports[route.to];
        const x1 = xScale(origin.lon);
        const y1 = yScale(origin.lat);
        const x2 = xScale(dest.lon);
        const y2 = yScale(dest.lat);

        const dx = x2 - x1;
        const dy = y2 - y1;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        // Perpendicular offset bows the line into a great-circle-like arc.
        const ux = dist === 0 ? 0 : -dy / dist;
        const uy = dist === 0 ? 0 : dx / dist;
        const bow = dist * 0.16;
        const controlX = midX + ux * bow;
        const controlY = midY + uy * bow;

        const ratio =
          (route.passengers - minPassengers) / (maxPassengers - minPassengers || 1);
        const strokeWidth = 2.5 + ratio * 6;
        const strokeOpacity = 0.35 + ratio * 0.35;

        return (
          <path
            key={`${route.from}-${route.to}-${i}`}
            d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
            fill="none"
            stroke={t.palette[0]}
            strokeWidth={strokeWidth}
            strokeOpacity={strokeOpacity}
            strokeLinecap="round"
          />
        );
      })}
      {Object.entries(airports).map(([code, airport]) => {
        const cx = xScale(airport.lon);
        const cy = yScale(airport.lat);
        const radius = 5 + (degreeByAirport[code] || 1) * 1.8;
        const nudge = labelNudge[code] || { dx: 0, dy: -(radius + 8) };
        return (
          <g key={code}>
            <circle
              cx={cx}
              cy={cy}
              r={radius}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={2}
            />
            <ChartsText
              x={cx + nudge.dx}
              y={cy + nudge.dy}
              text={code}
              textAnchor="middle"
              dominantBaseline="auto"
              style={{ fontSize: 14, fontWeight: 500, fill: t.ink }}
            />
          </g>
        );
      })}
    </g>
  );
}

// --- Overlay: caption explaining the encoding --------------------------------
function Caption() {
  const drawingArea = useDrawingArea();
  return (
    <ChartsText
      x={drawingArea.left}
      y={drawingArea.top + drawingArea.height + 74}
      text="Line thickness and opacity encode annual passenger volume (thousands)."
      textAnchor="start"
      dominantBaseline="hanging"
      style={{ fontSize: 14, fontWeight: 400, fill: t.inkSoft }}
    />
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <ChartContainer
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      margin={{ top: 90, right: 60, bottom: 100, left: 70 }}
      series={[]}
      skipAnimation
      disableAxisListener
      xAxis={[
        {
          scaleType: "linear",
          min: LON_MIN,
          max: LON_MAX,
          label: "Longitude (°)",
          valueFormatter: (v) => `${v}°`,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: LAT_MIN,
          max: LAT_MAX,
          label: "Latitude (°)",
          valueFormatter: (v) => `${v}°`,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
    >
      <ChartsGrid horizontal vertical />
      <ChartsReferenceLine
        y={0}
        label="Equator"
        labelAlign="end"
        lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 6", strokeOpacity: 0.6 }}
        labelStyle={{ fontSize: 13, fill: t.inkSoft }}
      />
      <ChartsReferenceLine
        x={0}
        label="Prime Meridian"
        labelAlign="start"
        lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 6", strokeOpacity: 0.6 }}
        labelStyle={{ fontSize: 13, fill: t.inkSoft }}
      />
      <ConnectionOverlay />
      <ChartsXAxis />
      <ChartsYAxis />
      <MapTitle />
      <Caption />
    </ChartContainer>
  );
}
