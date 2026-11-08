// anyplot.ai
// bar-feature-importance: Feature Importance Bar Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-02
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Wine Quality Random Forest · bar-feature-importance · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const PAD_SHARE = 0.1; // room beyond the longest bar for its value label
const DECIMALS = 3;

// Columns: set these to your data's column names
const FEATURE = "Feature"; // role: feature
const IMPORTANCE = "Importance (mean decrease in impurity)"; // role: importance

// Data: replace this block with your own records, one object per row
// Random forest regressor predicting wine quality (UCI Wine Quality dataset); the
// impurity-based importances of all 11 features sum to 1
const data = [
  { [FEATURE]: "Alcohol", [IMPORTANCE]: 0.2 },
  { [FEATURE]: "Sulphates", [IMPORTANCE]: 0.14 },
  { [FEATURE]: "Volatile Acidity", [IMPORTANCE]: 0.126 },
  { [FEATURE]: "Total Sulfur Dioxide", [IMPORTANCE]: 0.099 },
  { [FEATURE]: "Density", [IMPORTANCE]: 0.087 },
  { [FEATURE]: "Chlorides", [IMPORTANCE]: 0.072 },
  { [FEATURE]: "Citric Acid", [IMPORTANCE]: 0.066 },
  { [FEATURE]: "Fixed Acidity", [IMPORTANCE]: 0.06 },
  { [FEATURE]: "pH", [IMPORTANCE]: 0.056 },
  { [FEATURE]: "Free Sulfur Dioxide", [IMPORTANCE]: 0.051 },
  { [FEATURE]: "Residual Sugar", [IMPORTANCE]: 0.043 },
];

// Plot: reads only data and the constants above
// Highest importance first, so the strongest feature sits at the top
const rows = data.filter((d) => d[IMPORTANCE] != null).sort((a, b) => b[IMPORTANCE] - a[IMPORTANCE]);
const features = rows.map((d) => d[FEATURE]);
const importance = rows.map((d) => d[IMPORTANCE]);
const maxImportance = Math.max(...importance);
const minImportance = Math.min(...importance);
const fmt = (v: number) => v.toFixed(DECIMALS);

const lead = rows[0];
const runnerUp = rows[1];
const SUBTITLE = [
  `${rows.length} features, sorted by importance`,
  runnerUp && runnerUp[IMPORTANCE] > 0
    ? `${lead[FEATURE]} leads at ${fmt(lead[IMPORTANCE])}, ${(lead[IMPORTANCE] / runnerUp[IMPORTANCE]).toFixed(1)}× ${runnerUp[FEATURE]}`
    : null,
]
  .filter(Boolean)
  .join(" · ");

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <BarChart
        width={width}
        height={height - TITLE_H}
        layout="horizontal"
        skipAnimation
        hideLegend
        borderRadius={4}
        grid={{ vertical: true }}
        series={[
          {
            id: "importance",
            data: importance,
            label: IMPORTANCE,
            valueFormatter: (v: number | null) => (v == null ? null : fmt(v)),
            barLabel: (item: { value: number | null }) => (item.value == null ? null : fmt(item.value)),
            barLabelPlacement: "outside",
          },
        ]}
        xAxis={[
          {
            id: "value",
            min: 0,
            max: maxImportance * (1 + PAD_SHARE),
            label: IMPORTANCE,
            height: 64,
            tickNumber: 8,
            // The sequential Imprint ramp maps the same importance the bar length shows
            colorMap: { type: "continuous", min: minImportance, max: maxImportance, color: [t.seq[0], t.seq[1]] },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: features,
            label: FEATURE,
            width: 210,
            categoryGapRatio: 0.3,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiBarChart-label": { fill: t.ink, fontSize: 15, fontWeight: 600 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
