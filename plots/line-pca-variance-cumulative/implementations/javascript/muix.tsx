// anyplot.ai
// line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
// Library: muix | JavaScript | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// A 16-sensor vibration/temperature/pressure array on a rotating pump feeds a
// predictive-maintenance model. PCA on the standardized sensor readings finds
// a handful of latent modes (imbalance, misalignment, bearing wear, thermal
// drift, ...) that explain most of the signal — the classic "how many
// components do we keep" question. Eigenvalues decay roughly geometrically,
// which is typical for correlated sensor arrays and produces the elbow shape
// the cumulative curve is meant to reveal.
const rawEigenvalues = [
  28, 17, 13, 9.5, 7, 5.5, 4.2, 3.2, 2.4, 1.9, 1.5, 1.2, 0.95, 0.75, 0.6, 0.5,
];
const totalVariance = rawEigenvalues.reduce((sum, v) => sum + v, 0);
const varianceRatio = rawEigenvalues.map((v) => v / totalVariance);

const cumulativeVariance = [];
varianceRatio.reduce((sum, v, i) => {
  const next = sum + v;
  cumulativeVariance[i] = next;
  return next;
}, 0);

const componentNumbers = rawEigenvalues.map((_, i) => i + 1);

// First component count whose cumulative curve reaches each guidance threshold.
const componentsFor = (threshold) => cumulativeVariance.findIndex((v) => v >= threshold) + 1;
const ninetyPctComponents = componentsFor(0.9);
const ninetyFivePctComponents = componentsFor(0.95);

const TITLE = "line-pca-variance-cumulative · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 48, bottom: 16, left: 16 };
  const titleBlockHeight = 56;
  // MUI X's y-axis `label` prop offsets itself from a hardcoded tick-width
  // guess rather than the tick labels' real measured width, so it collides
  // with the "100%"/"90%" tick text. A hand-rotated label in its own flex
  // column sidesteps that and gives predictable, collision-free spacing.
  const yLabelWidth = 32;
  const chartWidth = size.width - padding.left - padding.right - yLabelWidth;
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
      <Box sx={{ display: "flex", flexDirection: "row", height: chartHeight }}>
        <Box sx={{ width: yLabelWidth, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography
            sx={{
              fontSize: 16,
              color: "text.secondary",
              whiteSpace: "nowrap",
              transform: "rotate(-90deg)",
            }}
          >
            Explained Variance
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          series={[
            {
              id: "cumulative",
              label: "Cumulative variance explained",
              data: cumulativeVariance,
              curve: "monotoneX",
              showMark: true,
              color: t.palette[0],
              valueFormatter: (v) => `${(v * 100).toFixed(1)}%`,
            },
            {
              id: "individual",
              label: "Variance from this component",
              data: varianceRatio,
              curve: "monotoneX",
              showMark: true,
              color: t.palette[2],
              valueFormatter: (v) => `${(v * 100).toFixed(1)}%`,
            },
          ]}
          xAxis={[
            {
              data: componentNumbers,
              scaleType: "point",
              label: "Number of Principal Components",
              valueFormatter: (v) => `${v}`,
              tickLabelStyle: { fontSize: 14 },
              labelStyle: { fontSize: 16 },
            },
          ]}
          yAxis={[
            {
              min: 0,
              max: 1,
              valueFormatter: (v) => `${Math.round(v * 100)}%`,
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              direction: "row",
              labelStyle: { fontSize: 14 },
              itemMarkWidth: 18,
              itemMarkHeight: 10,
              markGap: 8,
            },
          }}
          sx={{
            "& .MuiLineElement-series-cumulative": { strokeWidth: 3 },
            "& .MuiLineElement-series-individual": { strokeWidth: 2, strokeDasharray: "6 4" },
            "& .MuiMarkElement-series-cumulative": { r: 5 },
            "& .MuiMarkElement-series-individual": { r: 4 },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        >
          <ChartsReferenceLine
            y={0.9}
            label={`90% → ${ninetyPctComponents} components`}
            labelAlign="start"
            lineStyle={{ stroke: t.amber, strokeWidth: 1.5, strokeDasharray: "8 4" }}
            labelStyle={{ fontSize: 13, fill: t.inkSoft }}
          />
          <ChartsReferenceLine
            y={0.95}
            label={`95% → ${ninetyFivePctComponents} components`}
            labelAlign="start"
            lineStyle={{ stroke: t.amber, strokeWidth: 1.5, strokeDasharray: "8 4" }}
            labelStyle={{ fontSize: 13, fill: t.inkSoft }}
          />
        </LineChart>
      </Box>
    </Box>
  );
}
