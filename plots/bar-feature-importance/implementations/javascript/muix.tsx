// anyplot.ai
// bar-feature-importance: Feature Importance Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { BarChart } from "@mui/x-charts/BarChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Feature importances from a random forest regressor predicting wine quality
// (UCI Wine Quality dataset), sorted descending so the most influential
// feature renders first.
const features = [
  "Alcohol",
  "Sulphates",
  "Volatile Acidity",
  "Total Sulfur Dioxide",
  "Density",
  "Chlorides",
  "Citric Acid",
  "Fixed Acidity",
  "pH",
  "Free Sulfur Dioxide",
  "Residual Sugar",
];
const importance = [0.192, 0.134, 0.121, 0.095, 0.084, 0.069, 0.063, 0.058, 0.054, 0.049, 0.041];

const TITLE = "bar-feature-importance · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 40, bottom: 24, left: 40 };
  const titleBlockHeight = 56;
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
      <Typography sx={{ fontSize: 22, fontWeight: 600, color: "text.primary", mb: "20px", lineHeight: 1 }}>
        {TITLE}
      </Typography>
      <BarChart
        width={chartWidth}
        height={chartHeight}
        layout="horizontal"
        skipAnimation
        series={[
          {
            data: importance,
            label: "Feature importance",
            valueFormatter: (v) => (v === null ? "" : `${v.toFixed(3)} importance`),
          },
        ]}
        xAxis={[
          {
            min: 0,
            label: "Importance Score",
            colorMap: {
              type: "continuous",
              min: Math.min(...importance),
              max: Math.max(...importance),
              color: [t.seq[0], t.seq[1]],
            },
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: features,
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        barLabel={(item) => (item.value === null ? "" : item.value.toFixed(3))}
        grid={{ vertical: true }}
        margin={{ left: 190, right: 70, top: 16, bottom: 56 }}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiBarLabel-root": { fontSize: 13, fontWeight: 600 },
          "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
        }}
      />
    </Box>
  );
}
