// anyplot.ai
// ice-basic: Individual Conditional Expectation (ICE) Plot
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-17
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
// Individual curves stay translucent so dense stretches read darker; the alpha
// (30 %) is baked into the colour so the legend swatches match the lines
const ICE_ALPHA_HEX = "4D";

// Columns: set these to your data's column names
const HOUSE = "House ID"; // role: observation_id
const SQFT = "Square Footage (sq ft)"; // role: feature_value
const PRICE = "Predicted Price (USD)"; // role: prediction
const SEGMENT = "Year built"; // role: extra

// Data: replace this block with your own records, one object per observation and grid value
// ICE curves of a gradient-boosting house-price model: for each of 70 houses the
// predicted price over 55 square-footage values, every other feature held fixed.
// About a quarter of the houses, built before 1960, show diminishing returns:
// in older stock, extra floor space adds less and less to the predicted price.
const data = (() => {
  let seed = 42;
  const rng = () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
  const gaussian = (mean: number, sd: number) =>
    mean + sd * Math.sqrt(-2 * Math.log(Math.max(rng(), 1e-9))) * Math.cos(2 * Math.PI * rng());
  const gridCount = 55;
  const sqftMin = 900;
  const sqftMax = 3800;
  const rows = [];
  for (let house = 1; house <= 70; house += 1) {
    const basePrice = gaussian(210000, 22000);
    const pricePerSqft = gaussian(145, 22);
    const older = rng() < 0.25;
    const curvature = older ? gaussian(-0.028, 0.006) : gaussian(-0.003, 0.004);
    for (let i = 0; i < gridCount; i += 1) {
      const sqft = sqftMin + (i * (sqftMax - sqftMin)) / (gridCount - 1);
      const delta = sqft - sqftMin;
      rows.push({
        [HOUSE]: house,
        [SQFT]: Math.round(sqft),
        [PRICE]: Math.round(basePrice + pricePerSqft * delta + curvature * delta * delta),
        [SEGMENT]: older ? "Before 1960" : "1960 or later",
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[SQFT] != null && d[PRICE] != null);
const grid = [...new Set(rows.map((d) => d[SQFT]))].sort((a, b) => a - b);
const segments = [...new Set(rows.map((d) => d[SEGMENT]))];
const curves = [...new Set(rows.map((d) => d[HOUSE]))].map((id) => {
  const own = rows.filter((d) => d[HOUSE] === id);
  const byX = new Map(own.map((d) => [d[SQFT], d[PRICE]]));
  return { id, segment: own[0][SEGMENT], data: grid.map((x) => byX.get(x) ?? null) };
});
// Partial dependence: the mean prediction over all observations at each grid value
const partialDependence = grid.map((_, k) => {
  const at = curves.map((c) => c.data[k]).filter((v) => v != null);
  return at.reduce((s, v) => s + v, 0) / at.length;
});
// One legend entry per segment: only the segment's first curve carries the label
const labelled = new Set(segments.map((s) => curves.find((c) => c.segment === s).id));

const TITLE = "House Price Predictions · ice-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${curves.length} ICE curves × ${grid.length} grid values · coloured by ${SEGMENT.toLowerCase()} · bold line: partial dependence`;
const PDP_LABEL = "Partial dependence (mean of all curves)";
const HEADER_H = 76;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 16, left: 24 }}
        // Individual curves first, the partial dependence line last so it draws on top
        series={[
          ...curves.map((c) => ({
            id: `obs-${c.id}`,
            data: c.data,
            color: `${t.palette[segments.indexOf(c.segment)]}${ICE_ALPHA_HEX}`,
            showMark: false,
            labelMarkType: "line",
            label: labelled.has(c.id) ? `${SEGMENT}: ${c.segment}` : undefined,
          })),
          { id: "pdp", data: partialDependence, color: t.ink, label: PDP_LABEL, showMark: false, labelMarkType: "line" },
        ]}
        xAxis={[
          {
            data: grid,
            scaleType: "linear",
            min: grid[0],
            max: grid[grid.length - 1],
            tickNumber: 12,
            height: 64,
            label: SQFT,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 84,
            label: PRICE,
            valueFormatter: (v: number) => `${(v / 1000).toFixed(0)}k`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 15, color: t.ink, pr: "40px", gap: "24px", "& .MuiChartsLegend-mark.MuiChartsLabelMark-line": { width: 30, height: 10, "& path": { strokeWidth: 6 } } },
          },
          tooltip: { trigger: "item" },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 1.5 },
          '& .MuiLineChart-line[data-series="pdp"]': { strokeWidth: 4 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
