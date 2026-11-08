// anyplot.ai
// scatter-map-geographic: Scatter Map with Geographic Points
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const WORLD = { lonMin: -180, lonMax: 180, latMin: -90, latMax: 90 }; // the whole globe, in degrees
const GRATICULE_LON_STEP = 60; // degrees between meridians
const GRATICULE_LAT_STEP = 30; // degrees between parallels
const MARKER_RADIUS = [4, 16]; // px for the smallest and the largest size value
const POINT_OPACITY = 0.82;

// Columns: set these to your data's column names
const LATITUDE = "Latitude"; // role: latitude
const LONGITUDE = "Longitude"; // role: longitude
const DEPTH = "Depth (km)"; // role: value
const MAGNITUDE = "Magnitude (Mw)"; // role: size
const ZONE = "Seismic zone"; // role: label

// Data: replace this block with your own records, one object per row
// Simplified land outlines ([lon, lat] rings) for the basemap, and simulated
// M5.0+ earthquake epicentres clustered along major subduction and collision
// zones (Ring of Fire, Alpide belt).
const LAND_OUTLINES = [
  [
    [-165, 68], [-150, 71], [-130, 70], [-95, 73], [-80, 68], [-65, 60], [-55, 52],
    [-65, 46], [-75, 36], [-81, 25], [-97, 19], [-105, 21], [-114, 31], [-124, 40],
    [-124, 49], [-130, 55], [-140, 60], [-155, 60], [-165, 68],
  ],
  [
    [-79, 9], [-77, 1], [-70, -4], [-70, -18], [-72, -30], [-70, -40], [-68, -52],
    [-65, -55], [-58, -51], [-53, -35], [-48, -24], [-40, -10], [-35, -2], [-50, 5],
    [-60, 9], [-70, 11], [-79, 9],
  ],
  [
    [-17, 15], [-16, 7], [-9, 5], [2, 6], [9, 4], [9, -5], [12, -18], [16, -28],
    [20, -34], [27, -33], [33, -26], [35, -20], [40, -15], [40, -3], [43, -1],
    [51, 10], [45, 12], [38, 15], [32, 20], [25, 30], [15, 32], [9, 36], [0, 35],
    [-8, 32], [-17, 15],
  ],
  [
    [-10, 37], [-9, 43], [-5, 48], [3, 51], [10, 54], [15, 55], [20, 54], [25, 60],
    [30, 63], [35, 66], [45, 68], [60, 70], [75, 73], [95, 75], [115, 73], [135, 70],
    [142, 60], [135, 50], [142, 45], [140, 36], [130, 32], [122, 31], [110, 20],
    [100, 10], [92, 5], [80, 8], [70, 20], [60, 25], [50, 30], [42, 37], [35, 35],
    [28, 42], [20, 40], [15, 38], [8, 36], [-10, 37],
  ],
  [
    [113, -22], [120, -17], [130, -12], [137, -12], [145, -16], [150, -24],
    [153, -28], [153, -32], [147, -38], [140, -38], [130, -32], [120, -34],
    [114, -30], [113, -22],
  ],
];

const data = (() => {
  let seed = 8831;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  const zones = [
    { name: "Japan-Kuril arc", lon: 142, lat: 38, spreadLon: 6, spreadLat: 6, count: 12, mag: [5.0, 7.2], depth: [10, 300] },
    { name: "Aleutian-Alaska arc", lon: -160, lat: 55, spreadLon: 10, spreadLat: 4, count: 8, mag: [5.0, 7.5], depth: [10, 150] },
    { name: "Cascadia-Mexico coast", lon: -112, lat: 24, spreadLon: 9, spreadLat: 15, count: 10, mag: [5.0, 6.9], depth: [5, 60] },
    { name: "Andes subduction", lon: -72, lat: -20, spreadLon: 3, spreadLat: 16, count: 12, mag: [5.0, 7.8], depth: [10, 600] },
    { name: "Indonesia-Philippines arc", lon: 115, lat: 2, spreadLon: 18, spreadLat: 10, count: 14, mag: [5.0, 7.6], depth: [10, 400] },
    { name: "Tonga-Kermadec trench", lon: 178, lat: -20, spreadLon: 4, spreadLat: 8, count: 8, mag: [5.0, 7.4], depth: [10, 600] },
    { name: "Anatolia-Aegean", lon: 30, lat: 37, spreadLon: 12, spreadLat: 5, count: 8, mag: [5.0, 6.8], depth: [5, 40] },
    { name: "Himalayan front", lon: 84, lat: 29, spreadLon: 10, spreadLat: 4, count: 8, mag: [5.0, 7.2], depth: [5, 40] },
  ];
  return zones.flatMap((zone) =>
    Array.from({ length: zone.count }, () => {
      const lon = zone.lon + (rand() - 0.5) * 2 * zone.spreadLon;
      const lat = zone.lat + (rand() - 0.5) * 2 * zone.spreadLat;
      const magnitude = zone.mag[0] + rand() * (zone.mag[1] - zone.mag[0]);
      const depth = zone.depth[0] + rand() * (zone.depth[1] - zone.depth[0]);
      return {
        [LATITUDE]: Number(lat.toFixed(2)),
        [LONGITUDE]: Number((((lon + 540) % 360) - 180).toFixed(2)), // wrapped across the antimeridian
        [DEPTH]: Math.round(depth),
        [MAGNITUDE]: Number(magnitude.toFixed(1)),
        [ZONE]: zone.name,
      };
    }),
  );
})();

// Plot: reads only data and the constants above
const points = data.map((d, i) => ({
  id: `p-${i}`,
  x: d[LONGITUDE],
  y: d[LATITUDE],
  z: d[DEPTH],
  sizeValue: d[MAGNITUDE],
}));
const depths = data.map((d) => d[DEPTH]);
const depthMin = Math.min(...depths);
const depthMax = Math.max(...depths);
const magnitudes = data.map((d) => d[MAGNITUDE]);
const magMin = Math.min(...magnitudes);
const magMax = Math.max(...magnitudes);
// Size legend: the smallest, middle and largest magnitude, at the radii the linear size map gives them
const sizeLegend = [magMin, (magMin + magMax) / 2, magMax].map((value) => ({
  value,
  radius: MARKER_RADIUS[0] + ((MARKER_RADIUS[1] - MARKER_RADIUS[0]) * (value - magMin)) / (magMax - magMin || 1),
}));
// The size glyphs take the middle of the depth ramp, so they share the markers' fill, edge and alpha
const midRamp = `rgb(${[1, 3, 5]
  .map((i) => (parseInt(t.seq[0].slice(i, i + 2), 16) + parseInt(t.seq[1].slice(i, i + 2), 16)) / 2)
  .join(", ")})`;

const lonTicks = Array.from(
  { length: (WORLD.lonMax - WORLD.lonMin) / GRATICULE_LON_STEP + 1 },
  (_, k) => WORLD.lonMin + k * GRATICULE_LON_STEP,
);
const latTicks = Array.from(
  { length: (WORLD.latMax - WORLD.latMin) / GRATICULE_LAT_STEP + 1 },
  (_, k) => WORLD.latMin + k * GRATICULE_LAT_STEP,
);

const TITLE = "scatter-map-geographic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} epicentres · colour: ${DEPTH} · size: ${MAGNITUDE} · equirectangular projection`;
const HEADER_HEIGHT = 70;
const LEGEND_HEIGHT = 64;
const X_AXIS_HEIGHT = 56;
const Y_AXIS_WIDTH = 72;
const chartWidth = window.ANYPLOT_SIZE.width;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT - LEGEND_HEIGHT;

// Equirectangular: px per degree of latitude = px per degree of longitude / cos(mean latitude)
const meanLatitude = ((WORLD.latMin + WORLD.latMax) / 2) * (Math.PI / 180);
const mapAspect = ((WORLD.lonMax - WORLD.lonMin) * Math.cos(meanLatitude)) / (WORLD.latMax - WORLD.latMin);
const mapHeight = Math.min(chartHeight - X_AXIS_HEIGHT - 28, (chartWidth - Y_AXIS_WIDTH - 48) / mapAspect);
const mapWidth = mapHeight * mapAspect;
const marginX = (chartWidth - Y_AXIS_WIDTH - mapWidth) / 2;
const marginY = (chartHeight - X_AXIS_HEIGHT - mapHeight) / 2;

function Basemap() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {LAND_OUTLINES.map((ring, k) => (
        <path
          key={`land-${k}`}
          d={`M ${ring.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join(" L ")} Z`}
          fill={t.grid}
          stroke={t.inkSoft}
          strokeOpacity={0.45}
          strokeWidth={1}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={{ top: marginY, bottom: marginY, left: marginX, right: marginX }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "epicentres",
            label: ZONE,
            data: points,
            markerSize: MARKER_RADIUS[0],
            colorAxisId: "depth",
            sizeAxisId: "magnitude",
            valueFormatter: (v, { dataIndex }) =>
              `${data[dataIndex][ZONE]} · ${MAGNITUDE} ${data[dataIndex][MAGNITUDE]} · ${DEPTH} ${data[dataIndex][DEPTH]}`,
          },
        ]}
        xAxis={[
          {
            id: "lon",
            scaleType: "linear",
            min: WORLD.lonMin,
            max: WORLD.lonMax,
            label: LONGITUDE,
            height: X_AXIS_HEIGHT,
            tickInterval: lonTicks,
            valueFormatter: (v: number) => (v === 0 ? "0°" : `${Math.abs(v)}°${v > 0 ? "E" : "W"}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "lat",
            scaleType: "linear",
            min: WORLD.latMin,
            max: WORLD.latMax,
            label: LATITUDE,
            width: Y_AXIS_WIDTH,
            tickInterval: latTicks,
            valueFormatter: (v: number) => (v === 0 ? "0°" : `${Math.abs(v)}°${v > 0 ? "N" : "S"}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "depth",
            min: depthMin,
            max: depthMax,
            colorMap: { type: "continuous", min: depthMin, max: depthMax, color: [t.seq[0], t.seq[1]] },
          },
          {
            id: "magnitude",
            sizeMap: { type: "continuous", min: magMin, max: magMax, size: MARKER_RADIUS, interpolator: "linear" },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "bottom", horizontal: "center" }} legendDirection="horizontal">
          <div
            style={{
              gridArea: "legend",
              height: LEGEND_HEIGHT,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 72,
              color: t.inkSoft,
              fontSize: 15,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ color: t.ink, fontSize: 16 }}>{DEPTH}</span>
              <ContinuousColorLegend
                axisDirection="z"
                axisId="depth"
                direction="horizontal"
                thickness={14}
                labelPosition="end"
                sx={{ width: 300, color: t.inkSoft, fontSize: 14 }}
              />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ color: t.ink, fontSize: 16 }}>{MAGNITUDE}</span>
              {sizeLegend.map(({ value, radius }) => (
                <span key={`size-${value}`} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <svg width={2 * MARKER_RADIUS[1] + 2} height={2 * MARKER_RADIUS[1] + 2}>
                    <circle
                      cx={MARKER_RADIUS[1] + 1}
                      cy={MARKER_RADIUS[1] + 1}
                      r={radius}
                      fill={midRamp}
                      fillOpacity={POINT_OPACITY}
                      stroke={t.pageBg}
                      strokeWidth={1}
                    />
                  </svg>
                  {value.toFixed(1)}
                </span>
              ))}
            </div>
          </div>
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
            }}
          >
            <Basemap />
            <ChartsGrid horizontal vertical />
            <ChartsReferenceLine
              x={0}
              label="Prime meridian"
              labelAlign="end"
              lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.7, strokeDasharray: "6 4", strokeWidth: 1.5 }}
              labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            />
            <ChartsReferenceLine
              y={0}
              label="Equator"
              labelAlign="end"
              lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.7, strokeDasharray: "6 4", strokeWidth: 1.5 }}
              labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            />
            <ChartsXAxis />
            <ChartsYAxis />
            <ScatterPlot />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
