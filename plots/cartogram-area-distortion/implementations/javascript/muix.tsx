// anyplot.ai
// cartogram-area-distortion: Cartogram with Area Distortion by Data Value
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-20
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_RADIUS_CAP = 64; // px ceiling for the largest circle
const GAP_SHARE = 0.06; // free space kept between the two closest circles, as a share of their distance
const PAD_SHARE = 0.12; // map padding as a share of the centroids' longitude and latitude span
const LABEL_MIN_RADIUS = 16; // px: smaller circles stay unlabeled, a 14 px abbreviation would not fit
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
// 2023 US Census population estimates for the 20 most populous states,
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
  { [STATE]: "Virginia", [ABBR]: "VA", [LON]: -78.2, [LAT]: 37.5, [POPULATION]: 8.7, [CENSUS_REGION]: "South" },
  { [STATE]: "Washington", [ABBR]: "WA", [LON]: -120.4, [LAT]: 47.0, [POPULATION]: 7.8, [CENSUS_REGION]: "West" },
  { [STATE]: "Arizona", [ABBR]: "AZ", [LON]: -111.4, [LAT]: 34.0, [POPULATION]: 7.4, [CENSUS_REGION]: "West" },
  { [STATE]: "Tennessee", [ABBR]: "TN", [LON]: -86.3, [LAT]: 35.8, [POPULATION]: 7.1, [CENSUS_REGION]: "South" },
  { [STATE]: "Massachusetts", [ABBR]: "MA", [LON]: -71.8, [LAT]: 42.3, [POPULATION]: 7.0, [CENSUS_REGION]: "Northeast" },
  { [STATE]: "Indiana", [ABBR]: "IN", [LON]: -86.1, [LAT]: 39.9, [POPULATION]: 6.8, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Missouri", [ABBR]: "MO", [LON]: -92.5, [LAT]: 38.5, [POPULATION]: 6.2, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Wisconsin", [ABBR]: "WI", [LON]: -89.6, [LAT]: 44.6, [POPULATION]: 5.9, [CENSUS_REGION]: "Midwest" },
  { [STATE]: "Colorado", [ABBR]: "CO", [LON]: -105.5, [LAT]: 39.0, [POPULATION]: 5.9, [CENSUS_REGION]: "West" },
  { [STATE]: "Minnesota", [ABBR]: "MN", [LON]: -94.3, [LAT]: 46.0, [POPULATION]: 5.7, [CENSUS_REGION]: "Midwest" },
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

// Equirectangular view at the centroids' mean latitude: px per degree of latitude is
// px per degree of longitude divided by cos(mean latitude); the padded extent grows
// along one axis until it fills the drawing area
const lons = data.map((d) => d[LON]);
const lats = data.map((d) => d[LAT]);
const lonMin = Math.min(...lons);
const lonMax = Math.max(...lons);
const latMin = Math.min(...lats);
const latMax = Math.max(...lats);
const cosMeanLat = Math.cos(((lats.reduce((s, v) => s + v, 0) / lats.length) * Math.PI) / 180);
const lonSpan0 = (lonMax - lonMin) * (1 + 2 * PAD_SHARE);
const latSpan0 = (latMax - latMin) * (1 + 2 * PAD_SHARE);
const latSpanFill = (DRAW_H * cosMeanLat * lonSpan0) / DRAW_W;
const lonSpan = latSpanFill >= latSpan0 ? lonSpan0 : (latSpan0 * DRAW_W) / (DRAW_H * cosMeanLat);
const latSpan = latSpanFill >= latSpan0 ? latSpanFill : latSpan0;
const lonCenter = (lonMin + lonMax) / 2;
const latCenter = (latMin + latMax) / 2;
const pxPerLon = DRAW_W / lonSpan;
const pxPerLat = pxPerLon / cosMeanLat;

// Dorling circles at the exact centroids: area proportional to the value, and the
// radius scale is the largest at which no two circles overlap, so nothing is moved
const maxValue = Math.max(...data.map((d) => d[POPULATION]));
const shares = data.map((d) => Math.sqrt(d[POPULATION] / maxValue));
let maxRadius = MAX_RADIUS_CAP;
for (let i = 0; i < data.length; i += 1) {
  for (let j = i + 1; j < data.length; j += 1) {
    const dx = (data[i][LON] - data[j][LON]) * pxPerLon;
    const dy = (data[i][LAT] - data[j][LAT]) * pxPerLat;
    maxRadius = Math.min(maxRadius, (Math.hypot(dx, dy) * (1 - GAP_SHARE)) / (shares[i] + shares[j]));
  }
}

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
const series = regions.map((region, i) => ({
  type: "scatter" as const,
  id: `region-${i}`,
  label: region,
  color: t.palette[i],
  sizeAxisId: "value",
  data: data
    .filter((d) => d[CENSUS_REGION] === region)
    .map((d) => ({ id: d[STATE], x: d[LON], y: d[LAT], sizeValue: d[POPULATION] })),
  valueFormatter: (v: { id: string; sizeValue: number }) => `${v.id} · ${POPULATION} ${v.sizeValue}`,
}));
const labels = data
  .map((d, i) => ({ text: d[ABBR], lon: d[LON], lat: d[LAT], r: maxRadius * shares[i], ink: labelInk[regions.indexOf(d[CENSUS_REGION])] }))
  .filter((l) => l.r >= LABEL_MIN_RADIUS);

// Size legend: three reference values, the largest rounded down to one significant digit
const magnitude = 10 ** Math.floor(Math.log10(maxValue));
const topRef = Math.floor(maxValue / magnitude) * magnitude;
const sizeRefs = [topRef / 10, topRef / 3, topRef].map((v) => Number(v.toPrecision(1)));
const sizeRefRadii = sizeRefs.map((v) => maxRadius * Math.sqrt(v / maxValue));

const TITLE = "cartogram-area-distortion · javascript · muix · anyplot.ai";
const subtitle = `Dorling cartogram of ${data.length} ${STATE.toLowerCase()}s · circle area proportional to ${POPULATION.toLowerCase()}, centered on each centroid over the true outline · color by ${CENSUS_REGION.toLowerCase()}`;

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
          xAxis={[{ min: lonCenter - lonSpan / 2, max: lonCenter + lonSpan / 2, position: "none" }]}
          yAxis={[{ min: latCenter - latSpan / 2, max: latCenter + latSpan / 2, position: "none" }]}
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
              <svg width={2 * maxRadius + 2} height={2 * sizeRefRadii[i] + 2}>
                <circle
                  cx={maxRadius + 1}
                  cy={sizeRefRadii[i] + 1}
                  r={sizeRefRadii[i]}
                  fill={t.inkSoft}
                  fillOpacity={0.3}
                  stroke={t.inkSoft}
                  strokeWidth={1.2}
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
