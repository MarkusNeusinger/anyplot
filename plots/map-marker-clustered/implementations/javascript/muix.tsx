// anyplot.ai
// map-marker-clustered: Clustered Marker Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LAT_CELL = 0.55;
const LON_CELL = 0.75;

// Columns: set these to your data's column names
const LAT = "Latitude (°)"; // role: lat
const LON = "Longitude (°)"; // role: lon
const CATEGORY = "Store format"; // role: category

// Data: replace this block with your own records, one object per row
const data = (() => {
  let seed = 42;
  const rng = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const randomNormal = (mean: number, stdDev: number) => {
    const u1 = Math.max(rng(), 1e-9);
    const u2 = rng();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + z * stdDev;
  };

  const sampleCategories = ["Flagship", "Standard", "Kiosk"];
  const hubs = [
    { lat: 47.6062, lon: -122.3321, count: 55, spread: 0.22, categoryBias: 0 }, // Seattle
    { lat: 45.5152, lon: -122.6784, count: 42, spread: 0.2, categoryBias: 1 }, // Portland
    { lat: 47.2529, lon: -122.4443, count: 26, spread: 0.16, categoryBias: 2 }, // Tacoma
    { lat: 48.7519, lon: -122.4787, count: 18, spread: 0.14, categoryBias: 0 }, // Bellingham
    { lat: 44.0582, lon: -123.0868, count: 16, spread: 0.14, categoryBias: 1 }, // Eugene
  ];
  const ruralStoreCount = 22;
  const ruralLatRange = [43.7, 49.2];
  const ruralLonRange = [-124.6, -119.8];

  const rows: { [LAT]: number; [LON]: number; [CATEGORY]: string }[] = [];
  hubs.forEach((hub) => {
    for (let i = 0; i < hub.count; i++) {
      const categoryIndex =
        rng() < 0.65 ? hub.categoryBias : Math.floor(rng() * sampleCategories.length);
      rows.push({
        [LAT]: hub.lat + randomNormal(0, hub.spread),
        [LON]: hub.lon + randomNormal(0, hub.spread * 1.3),
        [CATEGORY]: sampleCategories[categoryIndex],
      });
    }
  });
  for (let i = 0; i < ruralStoreCount; i++) {
    rows.push({
      [LAT]: ruralLatRange[0] + rng() * (ruralLatRange[1] - ruralLatRange[0]),
      [LON]: ruralLonRange[0] + rng() * (ruralLonRange[1] - ruralLonRange[0]),
      [CATEGORY]: sampleCategories[Math.floor(rng() * sampleCategories.length)],
    });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const { width, height } = window.ANYPLOT_SIZE;
const MARGIN = { top: 24, right: 56, bottom: 20, left: 20 };
const X_AXIS_HEIGHT = 64;
const Y_AXIS_WIDTH = 76;
const TITLE_HEIGHT = 56;
const LEGEND_HEIGHT = 48;

const allLats = data.map((d) => d[LAT]);
const allLons = data.map((d) => d[LON]);
const LAT_RANGE = [
  Math.floor(Math.min(...allLats) * 2) / 2,
  Math.ceil(Math.max(...allLats) * 10) / 10,
];
const LON_RANGE = [
  Math.floor(Math.min(...allLons) * 5) / 5,
  Math.ceil(Math.max(...allLons) * 5) / 5,
];

const categories = Array.from(new Set(data.map((d) => d[CATEGORY])));
const categoryColors = categories.map((_, i) => t.palette[i % t.palette.length]);

const cells = new Map<string, typeof data>();
data.forEach((store) => {
  const key = `${Math.floor(store[LAT] / LAT_CELL)}_${Math.floor(store[LON] / LON_CELL)}`;
  if (!cells.has(key)) cells.set(key, []);
  cells.get(key)!.push(store);
});

function dominantCategory(members: typeof data) {
  const counts: Record<string, number> = {};
  members.forEach((m) => {
    counts[m[CATEGORY]] = (counts[m[CATEGORY]] || 0) + 1;
  });
  return categories.reduce(
    (best, cat) => ((counts[cat] || 0) > (counts[best] || 0) ? cat : best),
    categories[0],
  );
}

const clusters = Array.from(cells.values()).map((members, i) => ({
  id: `cluster-${i}`,
  x: members.reduce((sum, m) => sum + m[LON], 0) / members.length,
  y: members.reduce((sum, m) => sum + m[LAT], 0) / members.length,
  z: dominantCategory(members),
  count: members.length,
}));

function radiusPxFor(count: number) {
  if (count > 6) return 30;
  if (count >= 2) return 17;
  return 7;
}

const plotWidthPx = width - MARGIN.left - MARGIN.right - Y_AXIS_WIDTH;
const plotHeightPx =
  height - TITLE_HEIGHT - LEGEND_HEIGHT - MARGIN.top - MARGIN.bottom - X_AXIS_HEIGHT;
const pxPerLon = plotWidthPx / (LON_RANGE[1] - LON_RANGE[0]);
const pxPerLat = plotHeightPx / (LAT_RANGE[1] - LAT_RANGE[0]);
const MIN_GAP_PX = 8;
for (let pass = 0; pass < 40; pass++) {
  let moved = false;
  for (let i = 0; i < clusters.length; i++) {
    for (let j = i + 1; j < clusters.length; j++) {
      const a = clusters[i];
      const b = clusters[j];
      const dxPx = (b.x - a.x) * pxPerLon;
      const dyPx = (b.y - a.y) * pxPerLat;
      const distPx = Math.hypot(dxPx, dyPx) || 0.001;
      const minDistPx = radiusPxFor(a.count) + radiusPxFor(b.count) + MIN_GAP_PX;
      if (distPx < minDistPx) {
        const pushPx = (minDistPx - distPx) / 2;
        const nx = dxPx / distPx;
        const ny = dyPx / distPx;
        a.x -= (nx * pushPx) / pxPerLon;
        a.y -= (ny * pushPx) / pxPerLat;
        b.x += (nx * pushPx) / pxPerLon;
        b.y += (ny * pushPx) / pxPerLat;
        moved = true;
      }
    }
  }
  if (!moved) break;
}

const individualStores = clusters.filter((c) => c.count === 1);
const smallClusters = clusters.filter((c) => c.count >= 2 && c.count <= 6);
const largeClusters = clusters.filter((c) => c.count > 6);

const TITLE =
  "TrailBrew Coffee Co. · map-marker-clustered · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 22;
const titleFontSize =
  TITLE.length > 67 ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length)) : TITLE_FONT_DEFAULT;

const SIZE_LEGEND = [
  { label: "1 store", diameter: 7 },
  { label: "2–6 stores", diameter: 17 },
  { label: "7+ stores", diameter: 30 },
];

const PACIFIC_COAST = [
  [-124.35, LAT_RANGE[0]],
  [-124.15, 44.2],
  [-124.35, 44.9],
  [-124.4, 45.6],
  [-124.0, 46.15],
  [-124.35, 46.5],
  [-124.4, 47.3],
  [-124.45, 47.9],
  [-124.5, 48.3],
];

const PUGET_SOUND = [
  [-123.3, 48.25],
  [-122.9, 48.3],
  [-122.6, 48.1],
  [-122.4, 47.75],
  [-122.35, 47.45],
  [-122.5, 47.05],
  [-122.65, 47.15],
  [-122.55, 47.55],
  [-122.65, 47.9],
  [-122.95, 48.15],
];

const CANADA_BORDER_LAT = 49.0;
const WA_OR_BORDER_LAT = 46.0;

function GeographicBackdrop() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const project = ([lon, lat]: number[]) => `${xScale(lon)},${yScale(lat)}`;

  const oceanPoints = [
    [LON_RANGE[0], LAT_RANGE[0]],
    ...PACIFIC_COAST,
    [LON_RANGE[0], LAT_RANGE[1]],
  ]
    .map(project)
    .join(" ");

  const soundPoints = PUGET_SOUND.map(project).join(" ");
  const waterColor = t.palette[2];

  return (
    <g pointerEvents="none">
      <polygon points={oceanPoints} fill={waterColor} opacity={0.22} stroke="none" />
      <polygon points={soundPoints} fill={waterColor} opacity={0.22} stroke="none" />
      <line
        x1={xScale(LON_RANGE[0])}
        y1={yScale(CANADA_BORDER_LAT)}
        x2={xScale(LON_RANGE[1])}
        y2={yScale(CANADA_BORDER_LAT)}
        stroke={t.inkSoft}
        strokeWidth={1.25}
        strokeDasharray="6 4"
        opacity={0.5}
      />
      <line
        x1={xScale(-123.6)}
        y1={yScale(WA_OR_BORDER_LAT)}
        x2={xScale(LON_RANGE[1])}
        y2={yScale(WA_OR_BORDER_LAT)}
        stroke={t.inkSoft}
        strokeWidth={1.25}
        strokeDasharray="6 4"
        opacity={0.5}
      />
    </g>
  );
}

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
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={MARGIN}
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
            colorMap: { type: "ordinal", values: categories, colors: categoryColors },
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: LON_RANGE[0],
            max: LON_RANGE[1],
            tickMinStep: 1,
            height: X_AXIS_HEIGHT,
            label: LON,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(0)}°${v < 0 ? "W" : "E"}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: LAT_RANGE[0],
            max: LAT_RANGE[1],
            tickMinStep: 1,
            width: Y_AXIS_WIDTH,
            label: LAT,
            valueFormatter: (v: number) => `${Math.abs(v).toFixed(0)}°${v < 0 ? "S" : "N"}`,
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
        <GeographicBackdrop />
        <ChartsGrid horizontal vertical />
        <ScatterPlot skipAnimation />
        <ClusterCountLabels />
        <ChartsXAxis tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }} labelStyle={{ fontSize: 16, fill: t.ink }} />
        <ChartsYAxis tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }} labelStyle={{ fontSize: 16, fill: t.ink }} />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
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
          <span style={{ fontSize: 13, color: t.inkSoft }}>{CATEGORY}:</span>
          {categories.map((cat, i) => (
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
