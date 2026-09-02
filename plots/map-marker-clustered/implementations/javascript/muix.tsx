// anyplot.ai
// map-marker-clustered: Clustered Marker Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 80/100 | Created: 2026-09-02

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Reproducible LCG (seed 42) — no Math.random() in the browser harness ---
let seed = 42;
function rng() {
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}
function randomNormal(mean, stdDev) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

// --- Data: TrailBrew Coffee Co. store locations across the Pacific Northwest,
// grid-clustered the way a marker-cluster map aggregates pins at a fixed zoom
// level — dense city hubs collapse into count-labeled clusters, rural stores
// stay as individual markers. -------------------------------------------------
const CATEGORIES = ["Flagship", "Standard", "Kiosk"];

const HUBS = [
  { lat: 47.6062, lon: -122.3321, count: 55, spread: 0.22, categoryBias: 0 }, // Seattle
  { lat: 45.5152, lon: -122.6784, count: 42, spread: 0.2, categoryBias: 1 }, // Portland
  { lat: 47.2529, lon: -122.4443, count: 26, spread: 0.16, categoryBias: 2 }, // Tacoma
  { lat: 48.7519, lon: -122.4787, count: 18, spread: 0.14, categoryBias: 0 }, // Bellingham
  { lat: 44.0582, lon: -123.0868, count: 16, spread: 0.14, categoryBias: 1 }, // Eugene
];

const LAT_RANGE = [43.7, 49.2];
const LON_RANGE = [-124.6, -119.8];
const RURAL_STORE_COUNT = 22;

const stores = [];
HUBS.forEach((hub) => {
  for (let i = 0; i < hub.count; i++) {
    const categoryIndex =
      rng() < 0.65 ? hub.categoryBias : Math.floor(rng() * CATEGORIES.length);
    stores.push({
      lat: hub.lat + randomNormal(0, hub.spread),
      lon: hub.lon + randomNormal(0, hub.spread * 1.3),
      category: CATEGORIES[categoryIndex],
    });
  }
});
for (let i = 0; i < RURAL_STORE_COUNT; i++) {
  stores.push({
    lat: LAT_RANGE[0] + rng() * (LAT_RANGE[1] - LAT_RANGE[0]),
    lon: LON_RANGE[0] + rng() * (LON_RANGE[1] - LON_RANGE[0]),
    category: CATEGORIES[Math.floor(rng() * CATEGORIES.length)],
  });
}

// --- Grid-based proximity clustering (fixed zoom level) ---------------------
const LAT_CELL = 0.42;
const LON_CELL = 0.55;

const cells = new Map();
stores.forEach((store) => {
  const key = `${Math.floor(store.lat / LAT_CELL)}_${Math.floor(store.lon / LON_CELL)}`;
  if (!cells.has(key)) cells.set(key, []);
  cells.get(key).push(store);
});

function dominantCategory(members) {
  const counts = {};
  members.forEach((m) => {
    counts[m.category] = (counts[m.category] || 0) + 1;
  });
  return CATEGORIES.reduce(
    (best, cat) => ((counts[cat] || 0) > (counts[best] || 0) ? cat : best),
    CATEGORIES[0],
  );
}

const clusters = Array.from(cells.values()).map((members, i) => ({
  id: `cluster-${i}`,
  x: members.reduce((sum, m) => sum + m.lon, 0) / members.length,
  y: members.reduce((sum, m) => sum + m.lat, 0) / members.length,
  z: dominantCategory(members),
  count: members.length,
}));

const individualStores = clusters.filter((c) => c.count === 1);
const smallClusters = clusters.filter((c) => c.count >= 2 && c.count <= 6);
const largeClusters = clusters.filter((c) => c.count > 6);

// --- Chrome ------------------------------------------------------------------
const categoryColors = [t.palette[0], t.palette[1], t.palette[2]];

const TITLE =
  "TrailBrew Coffee Co. · map-marker-clustered · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 22;
const titleFontSize =
  TITLE.length > 67 ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length)) : TITLE_FONT_DEFAULT;
const TITLE_HEIGHT = 56;
const LEGEND_HEIGHT = 48;

const SIZE_LEGEND = [
  { label: "1 store", diameter: 9 },
  { label: "2–6 stores", diameter: 19 },
  { label: "7+ stores", diameter: 30 },
];

// Cluster-count labels, drawn at the live axis scale so each count sits
// exactly centered on its bubble — the honest way to show "how many
// markers this cluster represents" without faking a hover tooltip in the
// static PNG.
function ClusterCountLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  return (
    <g pointerEvents="none">
      {[...smallClusters, ...largeClusters].map((c) => (
        <text
          key={c.id}
          x={xScale(c.x)}
          y={yScale(c.y)}
          fontSize={c.count > 6 ? 13 : 11}
          fontWeight={600}
          fill={t.pageBg}
          textAnchor="middle"
          dominantBaseline="central"
        >
          {c.count}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const chartHeight = height - TITLE_HEIGHT - LEGEND_HEIGHT;

  return (
    <div style={{ width, height, backgroundColor: t.pageBg }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: titleFontSize,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartContainer
        width={width}
        height={chartHeight}
        margin={{ top: 24, right: 56, bottom: 84, left: 96 }}
        series={[
          {
            type: "scatter",
            id: "individual",
            data: individualStores,
            label: "Single location",
            markerSize: 7,
            zAxisId: "category",
          },
          {
            type: "scatter",
            id: "small-cluster",
            data: smallClusters,
            label: "Small cluster (2–6 stores)",
            markerSize: 17,
            zAxisId: "category",
          },
          {
            type: "scatter",
            id: "large-cluster",
            data: largeClusters,
            label: "Large cluster (7+ stores)",
            markerSize: 30,
            zAxisId: "category",
          },
        ]}
        zAxis={[
          {
            id: "category",
            colorMap: { type: "ordinal", values: CATEGORIES, colors: categoryColors },
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: LON_RANGE[0],
            max: LON_RANGE[1],
            label: "Longitude (°)",
            valueFormatter: (v) => `${v.toFixed(0)}°`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: LAT_RANGE[0],
            max: LAT_RANGE[1],
            label: "Latitude (°)",
            valueFormatter: (v) => `${v.toFixed(0)}°`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid horizontal vertical />
        <ScatterPlot skipAnimation />
        <ClusterCountLabels />
        <ChartsXAxis tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }} labelStyle={{ fontSize: 16, fill: t.ink }} />
        <ChartsYAxis tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }} labelStyle={{ fontSize: 16, fill: t.ink }} />
        <ChartsTooltip trigger="item" />
      </ChartContainer>
      <div
        style={{
          height: LEGEND_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 36,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 13, color: t.inkSoft }}>Store format:</span>
          {CATEGORIES.map((cat, i) => (
            <div key={cat} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  backgroundColor: categoryColors[i],
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 13, color: t.ink }}>{cat}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 13, color: t.inkSoft }}>Cluster size:</span>
          {SIZE_LEGEND.map((entry) => (
            <div key={entry.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  width: entry.diameter,
                  height: entry.diameter,
                  borderRadius: "50%",
                  backgroundColor: t.inkSoft,
                  opacity: 0.55,
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 13, color: t.ink }}>{entry.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
