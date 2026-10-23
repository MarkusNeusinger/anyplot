// anyplot.ai
// map-marker-clustered: Clustered Marker Map
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-23
//# anyplot-orientation: square

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
const EXTENT_PAD_DEG = 0.25; // degrees added around the data extent

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
const MARGIN = { top: 24, right: 40, bottom: 20, left: 20 };
const X_AXIS_HEIGHT = 64;
const Y_AXIS_WIDTH = 76;
const TITLE_HEIGHT = 56;
const LEGEND_HEIGHT = 56;

// Equal-distance framing: one degree of longitude is cos(latitude) of a degree of
// latitude, so the data extent is fitted into the plot box at that ratio and the
// looser dimension is widened around the data center to fill the box.
const allLats = data.map((d) => d[LAT]);
const allLons = data.map((d) => d[LON]);
const latMin = Math.min(...allLats) - EXTENT_PAD_DEG;
const latMax = Math.max(...allLats) + EXTENT_PAD_DEG;
const lonMin = Math.min(...allLons) - EXTENT_PAD_DEG;
const lonMax = Math.max(...allLons) + EXTENT_PAD_DEG;
const lonShrink = Math.cos((((latMin + latMax) / 2) * Math.PI) / 180);
const plotWidthPx = width - MARGIN.left - MARGIN.right - Y_AXIS_WIDTH;
const plotHeightPx =
  height - TITLE_HEIGHT - LEGEND_HEIGHT - MARGIN.top - MARGIN.bottom - X_AXIS_HEIGHT;
const pxPerLat = Math.min(
  plotHeightPx / (latMax - latMin),
  plotWidthPx / ((lonMax - lonMin) * lonShrink),
);
const latHalfSpan = plotHeightPx / pxPerLat / 2;
const lonHalfSpan = plotWidthPx / (pxPerLat * lonShrink) / 2;
const LAT_RANGE = [(latMin + latMax) / 2 - latHalfSpan, (latMin + latMax) / 2 + latHalfSpan];
const LON_RANGE = [(lonMin + lonMax) / 2 - lonHalfSpan, (lonMin + lonMax) / 2 + lonHalfSpan];

const categories = Array.from(new Set(data.map((d) => d[CATEGORY])));
const categoryColors = categories.map((_, i) => t.palette[i]);
// Count text: dark or light ink, whichever contrasts more with the marker fill
const countInk = Object.fromEntries(
  categories.map((cat, i) => {
    const [r, g, b] = [1, 3, 5].map((k) => {
      const c = parseInt(categoryColors[i].slice(k, k + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    return [cat, luminance > 0.18 ? "#1A1A17" : "#FAF8F1"];
  }),
);

const cells = new Map<string, typeof data>();
data.forEach((store) => {
  const key = `${Math.floor(store[LAT] / LAT_CELL)}_${Math.floor(store[LON] / LON_CELL)}`;
  if (!cells.has(key)) cells.set(key, []);
  cells.get(key)!.push(store);
});

const clusters = Array.from(cells.values()).map((members, i) => {
  const counts: Record<string, number> = {};
  members.forEach((m) => {
    counts[m[CATEGORY]] = (counts[m[CATEGORY]] || 0) + 1;
  });
  return {
    id: `cluster-${i}`,
    x: members.reduce((sum, m) => sum + m[LON], 0) / members.length,
    y: members.reduce((sum, m) => sum + m[LAT], 0) / members.length,
    z: categories.reduce((best, cat) => ((counts[cat] || 0) > (counts[best] || 0) ? cat : best)),
    count: members.length,
  };
});

const individualStores = clusters.filter((c) => c.count === 1);
const smallClusters = clusters.filter((c) => c.count >= 2 && c.count <= 6);
const largeClusters = clusters.filter((c) => c.count > 6);

const TITLE = "TrailBrew Coffee Co. · map-marker-clustered · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 22;
const titleFontSize =
  TITLE.length > 67 ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length)) : TITLE_FONT_DEFAULT;

const MARKER_SIZE = { single: 6, small: 17, large: 27 };
const SIZE_LEGEND = [
  { label: "1 store", diameter: 2 * MARKER_SIZE.single },
  { label: "2–6 stores", diameter: 2 * MARKER_SIZE.small },
  { label: "7+ stores", diameter: 2 * MARKER_SIZE.large },
];

const PACIFIC_COAST = [
  [-124.2, 42.0],
  [-124.15, 44.2],
  [-124.35, 44.9],
  [-124.4, 45.6],
  [-124.0, 46.15],
  [-124.35, 46.5],
  [-124.4, 47.3],
  [-124.45, 47.9],
  [-124.7, 48.4],
  [-124.7, 50.0],
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

  // Clamp to the axis ranges so the water stays inside the plot area
  const project = ([lon, lat]: number[]) =>
    `${xScale(Math.max(lon, LON_RANGE[0]))},${yScale(Math.min(Math.max(lat, LAT_RANGE[0]), LAT_RANGE[1]))}`;
  const oceanPoints = [[LON_RANGE[0], 42.0], ...PACIFIC_COAST, [LON_RANGE[0], 50.0]]
    .map(project)
    .join(" ");
  const soundPoints = PUGET_SOUND.map(project).join(" ");
  const border = { stroke: t.inkSoft, strokeWidth: 1.25, strokeDasharray: "6 4", opacity: 0.5 };

  return (
    <g pointerEvents="none">
      <polygon points={oceanPoints} fill={t.inkSoft} opacity={0.1} />
      <polygon points={soundPoints} fill={t.inkSoft} opacity={0.1} />
      <line
        x1={xScale(-123.3)}
        y1={yScale(CANADA_BORDER_LAT)}
        x2={xScale(LON_RANGE[1])}
        y2={yScale(CANADA_BORDER_LAT)}
        {...border}
      />
      <line
        x1={xScale(-124.0)}
        y1={yScale(WA_OR_BORDER_LAT)}
        x2={xScale(LON_RANGE[1])}
        y2={yScale(WA_OR_BORDER_LAT)}
        {...border}
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
          fontSize={c.count > 6 ? 16 : 13}
          fontWeight={700}
          fill={countInk[c.z]}
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
        height={height - TITLE_HEIGHT - LEGEND_HEIGHT}
        margin={MARGIN}
        series={[
          {
            type: "scatter",
            id: "individual",
            data: individualStores,
            label: "Single location",
            markerSize: MARKER_SIZE.single,
            zAxisId: "category",
          },
          {
            type: "scatter",
            id: "small-cluster",
            data: smallClusters,
            label: "Small cluster (2–6 stores)",
            markerSize: MARKER_SIZE.small,
            zAxisId: "category",
          },
          {
            type: "scatter",
            id: "large-cluster",
            data: largeClusters,
            label: "Large cluster (7+ stores)",
            markerSize: MARKER_SIZE.large,
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
        <ChartsXAxis />
        <ChartsYAxis />
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
          <span style={{ fontSize: 14, color: t.inkSoft }}>{CATEGORY}:</span>
          {categories.map((cat, i) => (
            <div key={cat} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: categoryColors[i],
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 14, color: t.ink }}>{cat}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 14, color: t.inkSoft }}>Cluster size:</span>
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
              <span style={{ fontSize: 14, color: t.ink }}>{entry.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
