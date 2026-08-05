// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue (in $M) for three product lines.
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const productLines = [
  { label: "Hardware", data: [4.2, 4.8, 5.1, 6.3] },
  { label: "Software", data: [3.1, 3.9, 4.6, 5.4] },
  { label: "Services", data: [2.0, 2.3, 2.9, 3.5] },
];

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width; // 1600 CSS px (landscape mount)
  const H = window.ANYPLOT_SIZE.height; // 900 CSS px
  const CHART_TOP = 88;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      {/* Title */}
      <Box sx={{ position: "absolute", top: 24, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500 }}>
          bar-grouped · javascript · muix · anyplot.ai
        </Typography>
      </Box>

      {/* Bar chart */}
      <Box
        sx={{
          position: "absolute",
          top: CHART_TOP,
          left: 0,
          right: 0,
          bottom: 0,
        }}
      >
        <BarChart
          width={W}
          height={H - CHART_TOP}
          colors={t.palette}
          skipAnimation
          xAxis={[
            {
              scaleType: "band",
              data: quarters,
              label: "Fiscal Quarter",
              disableTicks: true,
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              categoryGapRatio: 0.35,
            },
          ]}
          yAxis={[
            {
              label: "Revenue ($M)",
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
            },
          ]}
          series={productLines.map((p) => ({
            label: p.label,
            data: p.data,
            valueFormatter: (v) => `$${v}M`,
          }))}
          margin={{ top: 20, right: 60, bottom: 90, left: 90 }}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              labelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          }}
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": { stroke: t.grid },
          }}
        />
      </Box>
    </Box>
  );
}
