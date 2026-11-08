// anyplot.ai
// cartogram-area-distortion: Cartogram with Area Distortion by Data Value
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: pending | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const AREA_SHARE = 0.45; // all circles together cover this share of the true outline's area
const GAP_SHARE = 0.03; // free space between touching circles, as a share of the largest radius
const ITERATIONS = 400; // separation steps of the Dorling layout
const PULL = 0.08; // per-step drift back toward the centroid at the first step, falling to zero by the last
const PAD_SHARE = 0.03; // map padding as a share of the span of the outline and the circles
const LABEL_MIN_RADIUS = 12; // px: smaller circles stay unlabeled, a 14 px abbreviation would not fit
const LABEL_DARK = "#1A1A17";
const LABEL_LIGHT = "#FAF8F1";

// Columns: set these to your data's column names
const STATE = "State"; // role: region
const ABBR = "Abbreviation"; // role: label
const LON = "Centroid longitude"; // role: geometry
const LAT = "Centroid latitude"; // role: geometry
const POPULATION = "Population (millions)"; // role: value
const CENSUS_REGION = "Census region"; // role: extra

// Data: replace this block with your own records, one object per row
// 2023 US Census population estimates for the 48 contiguous states,
// each at its approximate geographic centroid.
const data = [
  { [STATE]: "California", [ABBR]: "CA", [LON]: -119.4, [LAT]: 36.8, [POPULATION]: 38.9, [CENSUS_REGION]: "West" },
  { [STATE]: "Texas", [ABBR]: "TX", [LON]: -99.3, [LAT]: 31.0, [POPULATION]: 30.5, [CENSUS_REGION]: "South" },
  { [STATE]: "Florida", [ABBR]: "FL", [LON]: -81.6, [LAT]: 27.8, [POPULATION]: 22.6, [CENSUS_REGION]: "South" },
  { [STATE]: "New York", [ABBR]: "NY", [LON]: -75.5, [LAT]: 43.0, [POPULATION]: 19.6, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Pennsylvania", [ABBR]: "PA", [LON]: -77.8, [LAT]: 40.9, [POPULATION]: 13.0, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Illinois", [ABBR]: "IL", [LON]: -89.2, [LAT]: 40.0, [POPULATION]: 12.5, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Ohio", [ABBR]: "OH", [LON]: -82.8, [LAT]: 40.4, [POPULATION]: 11.8, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Georgia", [ABBR]: "GA", [LON]: -83.5, [LAT]: 32.6, [POPULATION]: 11.0, [CENSUS_REGION]: "South" },
  { [STATE]: "North Carolina", [ABBR]: "NC", [LON]: -79.4, [LAT]: 35.5, [POPULATION]: 10.8, [CENSUS_REGION]: "South" },
  { [STATE]: "Michigan", [ABBR]: "MI", [LON]: -85.0, [LAT]: 44.3, [POPULATION]: 10.0, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "New Jersey", [ABBR]: "NJ", [LON]: -74.7, [LAT]: 40.1, [POPULATION]: 9.3, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Virginia", [ABBR]: "VA", [LON]: -78.2, [LAT]: 37.5, [POPULATION]: 8.7, [CENSUS_REGION]: "South" },
  { [STATE]: "Washington", [ABBR]: "WA", [LON]: -120.4, [LAT]: 47.0, [POPULATION]: 7.8, [CENSUS_REGION]: "West" },
  { [STATE]: "Arizona", [ABBR]: "AZ", [LON]: -111.4, [LAT]: 34.0, [POPULATION]: 7.4, [CENSUS_REGION]: "West" },
  { [STATE]: "Tennessee", [ABBR]: "TN", [LON]: -86.3, [LAT]: 35.8, [POPULATION]: 7.1, [CENSUS_REGION]: "South" },
  { [STATE]: "Massachusetts", [ABBR]: "MA", [LON]: -72.0, [LAT]: 42.4, [POPULATION]: 7.0, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Indiana", [ABBR]: "IN", [LON]: -86.1, [LAT]: 39.9, [POPULATION]: 6.8, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Maryland", [ABBR]: "MD", [LON]: -76.8, [LAT]: 39.0, [POPULATION]: 6.2, [CENSUS_REGION]: "South" },
  { [STATE]: "Missouri", [ABBR]: "MO", [LON]: -92.5, [LAT]: 38.5, [POPULATION]: 6.2, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Wisconsin", [ABBR]: "WI", [LON]: -89.6, [LAT]: 44.6, [POPULATION]: 5.9, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Colorado", [ABBR]: "CO", [LON]: -105.5, [LAT]: 39.0, [POPULATION]: 5.9, [CENSUS_REGION]: "West" },
  { [STATE]: "Minnesota", [ABBR]: "MN", [LON]: -94.3, [LAT]: 46.0, [POPULATION]: 5.7, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "South Carolina", [ABBR]: "SC", [LON]: -80.9, [LAT]: 33.9, [POPULATION]: 5.4, [CENSUS_REGION]: "South" },
  { [STATE]: "Alabama", [ABBR]: "AL", [LON]: -86.8, [LAT]: 32.8, [POPULATION]: 5.1, [CENSUS_REGION]: "South" },
  { [STATE]: "Louisiana", [ABBR]: "LA", [LON]: -92.0, [LAT]: 31.0, [POPULATION]: 4.6, [CENSUS_REGION]: "South" },
  { [STATE]: "Kentucky", [ABBR]: "KY", [LON]: -85.3, [LAT]: 37.5, [POPULATION]: 4.5, [CENSUS_REGION]: "South" },
  { [STATE]: "Oregon", [ABBR]: "OR", [LON]: -120.6, [LAT]: 43.9, [POPULATION]: 4.2, [CENSUS_REGION]: "West" },
  { [STATE]: "Oklahoma", [ABBR]: "OK", [LON]: -97.5, [LAT]: 35.6, [POPULATION]: 4.1, [CENSUS_REGION]: "South" },
  { [STATE]: "Connecticut", [ABBR]: "CT", [LON]: -72.7, [LAT]: 41.6, [POPULATION]: 3.6, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Utah", [ABBR]: "UT", [LON]: -111.7, [LAT]: 39.3, [POPULATION]: 3.4, [CENSUS_REGION]: "West" },
  { [STATE]: "Iowa", [ABBR]: "IA", [LON]: -93.5, [LAT]: 42.1, [POPULATION]: 3.2, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Nevada", [ABBR]: "NV", [LON]: -116.6, [LAT]: 39.3, [POPULATION]: 3.2, [CENSUS_REGION]: "West" },
  { [STATE]: "Arkansas", [ABBR]: "AR", [LON]: -92.4, [LAT]: 34.9, [POPULATION]: 3.1, [CENSUS_REGION]: "South" },
  { [STATE]: "Mississippi", [ABBR]: "MS", [LON]: -89.7, [LAT]: 32.7, [POPULATION]: 2.9, [CENSUS_REGION]: "South" },
  { [STATE]: "Kansas", [ABBR]: "KS", [LON]: -98.4, [LAT]: 38.5, [POPULATION]: 2.9, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "New Mexico", [ABBR]: "NM", [LON]: -106.1, [LAT]: 34.4, [POPULATION]: 2.1, [CENSUS_REGION]: "West" },
  { [STATE]: "Nebraska", [ABBR]: "NE", [LON]: -99.8, [LAT]: 41.5, [POPULATION]: 2.0, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Idaho", [ABBR]: "ID", [LON]: -114.6, [LAT]: 44.4, [POPULATION]: 2.0, [CENSUS_REGION]: "West" },
  { [STATE]: "West Virginia", [ABBR]: "WV", [LON]: -80.6, [LAT]: 38.6, [POPULATION]: 1.8, [CENSUS_REGION]: "South" },
  { [STATE]: "New Hampshire", [ABBR]: "NH", [LON]: -71.6, [LAT]: 43.7, [POPULATION]: 1.4, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Maine", [ABBR]: "ME", [LON]: -69.2, [LAT]: 45.4, [POPULATION]: 1.4, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Montana", [ABBR]: "MT", [LON]: -109.6, [LAT]: 47.0, [POPULATION]: 1.1, [CENSUS_REGION]: "West" },
  { [STATE]: "Rhode Island", [ABBR]: "RI", [LON]: -71.5, [LAT]: 41.7, [POPULATION]: 1.1, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Delaware", [ABBR]: "DE", [LON]: -75.5, [LAT]: 39.0, [POPULATION]: 1.0, [CENSUS_REGION]: "South" },
  { [STATE]: "South Dakota", [ABBR]: "SD", [LON]: -100.2, [LAT]: 44.4, [POPULATION]: 0.9, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "North Dakota", [ABBR]: "ND", [LON]: -100.5, [LAT]: 47.5, [POPULATION]: 0.8, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Vermont", [ABBR]: "VT", [LON]: -72.7, [LAT]: 44.0, [POPULATION]: 0.6, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Wyoming", [ABBR]: "WY", [LON]: -107.6, [LAT]: 43.0, [POPULATION]: 0.6, [CENSUS_REGION]: "West" },
];

// Reference geography: simplified outline of the contiguous United States as a
// [longitude, latitude] ring (Canada border, Atlantic and Gulf coasts, Mexico border, Pacific coast)
const US_OUTLINE: [number, number][] = [
  [-123.3, 49], [-95.2, 49], [-89.6, 48], [-84.5, 46.5], [-82.4, 45], [-82.5, 43], [-83.1, 42], [-79, 42.8],
  [-79, 43.3], [-76.3, 44.2], [-74.7, 45], [-71.5, 45], [-70, 46.7], [-69.2, 47.4], [-68, 47.3], [-67.8, 45.7],
  [-67, 44.9], [-70, 43.5], [-70, 41.8], [-74, 40.5], [-76, 38], [-76, 35], [-78.5, 33.8], [-81, 31.5], [-80, 27],
  [-80.5, 25.2], [-82, 26.5], [-82.8, 28], [-84, 30], [-86, 30.4], [-89, 30.2], [-90, 29], [-94, 29.7],
  [-97.2, 27.5], [-97.2, 25.9], [-99.5, 27.5], [-101.4, 29.8], [-103, 29], [-104.5, 29.6], [-106.5, 31.8],
  [-108.2, 31.3], [-111, 31.3], [-114.7, 32.7], [-117.1, 32.5], [-118.5, 34], [-120.6, 34.6], [-122.5, 37.7],
  [-124, 40.4], [-124.2, 43], [-124, 46.2], [-124.7, 48.4],
];

// Plot: reads only data, the outline and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const TITLE_H = 80;
const LEGEND_H = 44; // the region legend above the map adds its own height
const SIZE_LEGEND_W = 230;
const MARGIN = { top: 16, right: 16, bottom: 24, left: 40 };
const CHART_W = W - SIZE_LEGEND_W;
const CHART_H = H - TITLE_H - LEGEND_H;
const DRAW_W = CHART_W - MARGIN.left - MARGIN.right;
const DRAW_H = CHART_H - MARGIN.top - MARGIN.bottom;

// Layout plane: equirectangular at the centroids' mean latitude, longitude scaled by
// cos(mean latitude), so one unit is one degree of latitude on both axes and areas compare
const cosMeanLat = Math.cos(((data.reduce((s, d) => s + d[LAT], 0) / data.length) * Math.PI) / 180);
const home = data.map((d) => ({ x: d[LON] * cosMeanLat, y: d[LAT] }));
const outline = US_OUTLINE.map(([lon, lat]) => ({ x: lon * cosMeanLat, y: lat }));
const outlineArea =
  Math.abs(outline.reduce((s, p, i) => s + p.x * outline[(i + 1) % outline.length].y - outline[(i + 1) % outline.length].x * p.y, 0)) / 2;

// Dorling circles: area proportional to the value, all of them together AREA_SHARE of the outline's area
const values = data.map((d) => d[POPULATION]);
const total = values.reduce((s, v) => s + v, 0);
const maxValue = Math.max(...values);
const radius = values.map((v) => Math.sqrt((AREA_SHARE * outlineArea * v) / (total * Math.PI)));
const gap = GAP_SHARE * Math.max(...radius);

// Separation pass, deterministic: each step pulls every circle back toward its centroid, with a
// strength that falls to zero, then pushes every overlapping pair apart along the line between their
// centers, the smaller circle moving more. Neighbors stay close and the last steps leave no overlap.
const pos = home.map((p) => ({ ...p }));
for (let step = 0; step < ITERATIONS; step += 1) {
  const pull = PULL * (1 - step / (ITERATIONS - 1));
  pos.forEach((p, i) => {
    p.x += (home[i].x - p.x) * pull;
    p.y += (home[i].y - p.y) * pull;
  });
  for (let i = 0; i < pos.length; i += 1) {
    for (let j = i + 1; j < pos.length; j += 1) {
      const dx = pos[j].x - pos[i].x;
      const dy = pos[j].y - pos[i].y;
      const dist = Math.hypot(dx, dy);
      const overlap = radius[i] + radius[j] + gap - dist;
      if (overlap > 0) {
        // two circles on the same spot split along a direction fixed by their indices
        const ux = dist > 0 ? dx / dist : Math.cos(i + j);
        const uy = dist > 0 ? dy / dist : Math.sin(i + j);
        const shareI = radius[j] ** 2 / (radius[i] ** 2 + radius[j] ** 2);
        pos[i].x -= ux * overlap * shareI;
        pos[i].y -= uy * overlap * shareI;
        pos[j].x += ux * overlap * (1 - shareI);
        pos[j].y += uy * overlap * (1 - shareI);
      }
    }
  }
}

// View: the padded extent of the outline and the circles, grown along one axis until it fills the
// drawing area; px per degree of latitude is px per degree of longitude divided by cos(mean latitude)
const extentX = [...outline.map((p) => p.x), ...pos.flatMap((p, i) => [p.x - radius[i], p.x + radius[i]])];
const extentY = [...outline.map((p) => p.y), ...pos.flatMap((p, i) => [p.y - radius[i], p.y + radius[i]])];
const [xMin, xMax, yMin, yMax] = [Math.min(...extentX), Math.max(...extentX), Math.min(...extentY), Math.max(...extentY)];
const spanX = Math.max(xMax - xMin, ((yMax - yMin) * DRAW_W) / DRAW_H) * (1 + 2 * PAD_SHARE);
const spanY = (spanX * DRAW_H) / DRAW_W;
const pxPerUnit = DRAW_W / spanX;
const maxRadius = Math.max(...radius) * pxPerUnit;

// Census regions in order of first appearance; each label ink is the one with the higher
// contrast against its region's color
const regions = [...new Set(data.map((d) => d[CENSUS_REGION]))];
const labelInk = regions.map((_, i) => {
  const [r, g, b] = [1, 3, 5]
    .map((k) => parseInt(t.palette[i].slice(k, k + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return (lum + 0.05) / 0.06 >= 0.98 / (lum + 0.05) ? LABEL_DARK : LABEL_LIGHT;
});
// Each circle back in longitude and latitude, the coordinates of the axes
const placed = data.map((d, i) => ({
  state: d[STATE],
  text: d[ABBR],
  region: d[CENSUS_REGION],
  value: d[POPULATION],
  lon: pos[i].x / cosMeanLat,
  lat: pos[i].y,
  r: radius[i] * pxPerUnit,
}));
const series = regions.map((region, i) => ({
  type: "scatter" as const,
  id: `region-${i}`,
  label: region,
  color: t.palette[i],
  sizeAxisId: "value",
  data: placed.filter((c) => c.region === region).map((c) => ({ id: c.state, x: c.lon, y: c.lat, sizeValue: c.value })),
  valueFormatter: (v: { id: string; sizeValue: number }) => `${v.id} · ${POPULATION} ${v.sizeValue}`,
}));
const labels = placed
  .filter((c) => c.r >= LABEL_MIN_RADIUS)
  .map((c) => ({ ...c, ink: labelInk[regions.indexOf(c.region)] }));

// Size legend: three reference values, the largest rounded down to one significant digit
const magnitude = 10 ** Math.floor(Math.log10(maxValue));
const topRef = Math.floor(maxValue / magnitude) * magnitude;
const sizeRefs = [topRef / 10, topRef / 3, topRef].map((v) => Number(v.toPrecision(1)));
const sizeRefRadii = sizeRefs.map((v) => maxRadius * Math.sqrt(v / maxValue));

const TITLE = "cartogram-area-distortion · javascript · muix · anyplot.ai";
const subtitle = `Dorling cartogram of ${data.length} ${STATE.toLowerCase()}s · circle area proportional to ${POPULATION.toLowerCase()} · circles pushed apart from their centroids until none overlap · color by ${CENSUS_REGION.toLowerCase()}`;

function ReferenceOutline() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <path
      d={`M${US_OUTLINE.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join("L")}Z`}
      fill={t.grid}
      stroke={t.inkSoft}
      strokeOpacity={0.6}
      strokeWidth={1}
    />
  );
}

function StateLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g pointerEvents="none">
      {labels.map((l) => (
        <text
          key={l.text}
          x={xScale(l.lon)}
          y={yScale(l.lat)}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={l.r >= 2 * LABEL_MIN_RADIUS ? 16 : 14}
          fontWeight={700}
          fill={l.ink}
        >
          {l.text}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "row" }}>
        <ChartsDataProvider
          width={CHART_W}
          height={CHART_H}
          margin={MARGIN}
          series={series}
          xAxis={[{ min: (xMin + xMax - spanX) / 2 / cosMeanLat, max: (xMin + xMax + spanX) / 2 / cosMeanLat, position: "none" }]}
          yAxis={[{ min: (yMin + yMax - spanY) / 2, max: (yMin + yMax + spanY) / 2, position: "none" }]}
          zAxis={[
            {
              id: "value",
              sizeMap: { type: "continuous", min: 0, max: maxValue, size: (share: number) => maxRadius * Math.sqrt(share) },
            },
          ]}
          skipAnimation
        >
          <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
            <ChartsLegend sx={{ fontSize: 15, color: t.inkSoft }} />
            <ChartsSurface sx={{ "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1.5 } }}>
              <ReferenceOutline />
              <ScatterPlot />
              <StateLabels />
            </ChartsSurface>
            <ChartsTooltip trigger="item" />
          </ChartsWrapper>
        </ChartsDataProvider>
        <div style={{ width: SIZE_LEGEND_W, display: "flex", flexDirection: "column", justifyContent: "center", paddingRight: 24, boxSizing: "border-box" }}>
          <div style={{ fontSize: 15, color: t.inkSoft, marginBottom: 14 }}>{POPULATION}</div>
          {sizeRefs.map((v, i) => (
            <div key={v} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
              <svg width={2 * sizeRefRadii[sizeRefRadii.length - 1] + 2} height={2 * sizeRefRadii[i] + 2}>
                <circle
                  cx={sizeRefRadii[sizeRefRadii.length - 1] + 1}
                  cy={sizeRefRadii[i] + 1}
                  r={sizeRefRadii[i]}
                  fill={t.inkSoft}
                  stroke={t.pageBg}
                  strokeWidth={1.5}
                />
              </svg>
              <span style={{ fontSize: 15, color: t.inkSoft }}>{v}</span>
            </div>
          ))}
          <div style={{ fontSize: 14, color: t.inkSoft, marginTop: 6 }}>Shaded outline: true geography</div>
        </div>
      </div>
    </div>
  );
}
