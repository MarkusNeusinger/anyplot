// anyplot.ai
// scatter-map-geographic: Scatter Map with Geographic Points
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated M5.0+ earthquake epicenters clustered along the world's major
// subduction and collision zones (Ring of Fire, Alpide belt). Longitude/
// latitude place each point on an equirectangular (plate carree) projection —
// the simplest valid map projection: lon maps linearly to x, lat to y. A
// 60 deg/30 deg graticule plus the equator and prime meridian reference lines
// stand in for a basemap (no coastline dataset ships with the community
// package and pulling one in would mean importing D3, which is out of scope
// for muix).
let seed = 8831;
const rand = () => {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
};

const FAULT_ZONES = [
  { lon: 142, lat: 38, spreadLon: 6, spreadLat: 6, count: 12, mag: [5.0, 7.2], depth: [10, 300] }, // Japan-Kuril arc
  { lon: -160, lat: 55, spreadLon: 10, spreadLat: 4, count: 8, mag: [5.0, 7.5], depth: [10, 150] }, // Aleutian-Alaska arc
  { lon: -112, lat: 24, spreadLon: 9, spreadLat: 15, count: 10, mag: [5.0, 6.9], depth: [5, 60] }, // Cascadia-Mexico coast
  { lon: -72, lat: -20, spreadLon: 3, spreadLat: 16, count: 12, mag: [5.0, 7.8], depth: [10, 600] }, // Andes subduction
  { lon: 115, lat: 2, spreadLon: 18, spreadLat: 10, count: 14, mag: [5.0, 7.6], depth: [10, 400] }, // Indonesia-Philippines arc
  { lon: 178, lat: -20, spreadLon: 4, spreadLat: 8, count: 8, mag: [5.0, 7.4], depth: [10, 600] }, // Tonga-Kermadec trench
  { lon: 30, lat: 37, spreadLon: 12, spreadLat: 5, count: 8, mag: [5.0, 6.8], depth: [5, 40] }, // Anatolia-Aegean
  { lon: 84, lat: 29, spreadLon: 10, spreadLat: 4, count: 8, mag: [5.0, 7.2], depth: [5, 40] }, // Himalayan front
];

const epicenters = FAULT_ZONES.flatMap((zone, zoneIndex) =>
  Array.from({ length: zone.count }, (_, i) => {
    const longitude = Math.max(-180, Math.min(180, zone.lon + (rand() - 0.5) * 2 * zone.spreadLon));
    const latitude = Math.max(-90, Math.min(90, zone.lat + (rand() - 0.5) * 2 * zone.spreadLat));
    const magnitude = zone.mag[0] + rand() * (zone.mag[1] - zone.mag[0]);
    const depthKm = Math.round(zone.depth[0] + rand() * (zone.depth[1] - zone.depth[0]));
    return { id: `eq-${zoneIndex}-${i}`, longitude, latitude, magnitude, depthKm };
  }),
);

const depths = epicenters.map((e) => e.depthKm);
const depthDomain = [Math.min(...depths), Math.max(...depths)];

// Magnitude tiers -> marker size. The community ScatterChart sizes markers
// per series (not per point), so a size legend for a continuous magnitude
// needs binning into a handful of series, each drawn at its own markerSize.
const MAGNITUDE_TIERS = [
  { id: "minor", label: "M 5.0-5.6", max: 5.6, markerSize: 5 },
  { id: "light", label: "M 5.6-6.3", max: 6.3, markerSize: 8 },
  { id: "strong", label: "M 6.3-7.0", max: 7.0, markerSize: 12 },
  { id: "major", label: "M 7.0+", max: Infinity, markerSize: 17 },
];

const tierSeries = MAGNITUDE_TIERS.map((tier, tierIndex) => {
  const lowerBound = tierIndex === 0 ? -Infinity : MAGNITUDE_TIERS[tierIndex - 1].max;
  const points = epicenters.filter((e) => e.magnitude > lowerBound && e.magnitude <= tier.max);
  return {
    type: "scatter",
    id: tier.id,
    label: tier.label,
    markerSize: tier.markerSize,
    color: t.palette[0],
    zAxisId: "depth",
    data: points.map((e) => ({ x: e.longitude, y: e.latitude, z: e.depthKm, id: e.id })),
    valueFormatter: (v) => `${v.x.toFixed(1)}°, ${v.y.toFixed(1)}° · depth ${v.z} km`,
  };
});

const formatLongitude = (value) => (value === 0 ? "0°" : `${Math.abs(Math.round(value))}°${value > 0 ? "E" : "W"}`);
const formatLatitude = (value) => (value === 0 ? "0°" : `${Math.abs(Math.round(value))}°${value > 0 ? "N" : "S"}`);

const TITLE = "scatter-map-geographic · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 40, bottom: 24, left: 40 };
  const titleBlockHeight = 52;
  const chartWidth = size.width - padding.left - padding.right;
  const chartHeight = size.height - padding.top - padding.bottom - titleBlockHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography sx={{ fontSize: 24, fontWeight: 600, color: "text.primary", mb: "16px", lineHeight: 1 }}>
        {TITLE}
      </Typography>
      <ScatterChart
        width={chartWidth}
        height={chartHeight}
        skipAnimation
        disableVoronoi
        series={tierSeries}
        margin={{ top: 76, right: 30, bottom: 100, left: 84 }}
        xAxis={[
          {
            id: "lon",
            min: -180,
            max: 180,
            domainLimit: "strict",
            label: "Longitude",
            tickInterval: [-180, -120, -60, 0, 60, 120, 180],
            valueFormatter: (v, ctx) => (ctx.location === "tick" ? formatLongitude(v) : `${v.toFixed(1)}°`),
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            id: "lat",
            min: -90,
            max: 90,
            domainLimit: "strict",
            label: "Latitude",
            tickInterval: [-90, -60, -30, 0, 30, 60, 90],
            valueFormatter: (v, ctx) => (ctx.location === "tick" ? formatLatitude(v) : `${v.toFixed(1)}°`),
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        zAxis={[
          {
            id: "depth",
            min: depthDomain[0],
            max: depthDomain[1],
            colorMap: { type: "continuous", min: depthDomain[0], max: depthDomain[1], color: [t.seq[0], t.seq[1]] },
          },
        ]}
        grid={{ horizontal: true, vertical: true }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "bottom", horizontal: "middle" },
            labelStyle: { fontSize: 14 },
            itemMarkWidth: 16,
            itemMarkHeight: 10,
            markGap: 6,
            itemGap: 20,
          },
        }}
        sx={{
          "& circle": { fillOpacity: 0.82, stroke: t.pageBg, strokeWidth: 1 },
          "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
        }}
      >
        <ChartsReferenceLine
          x={0}
          label="Prime Meridian"
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "2 3", strokeWidth: 1.2 }}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
        />
        <ChartsReferenceLine
          y={0}
          label="Equator"
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "2 3", strokeWidth: 1.2 }}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
        />
        <ContinuousColorLegend
          axisDirection="z"
          axisId="depth"
          direction="row"
          position={{ horizontal: "right", vertical: "top" }}
          length={180}
          thickness={12}
          minLabel={({ formattedValue }) => `${formattedValue} km shallow`}
          maxLabel={({ formattedValue }) => `${formattedValue} km deep`}
          labelStyle={{ fontSize: 13, fill: t.inkSoft }}
        />
      </ScatterChart>
    </Box>
  );
}
