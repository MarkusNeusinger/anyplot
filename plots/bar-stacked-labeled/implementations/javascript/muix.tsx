// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26
import { BarChart } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Project budget breakdown by phase, three stacked cost types (Imprint palette 1-3).
const phases = ["Planning", "Design", "Development", "Testing", "Deployment"];
const costTypes = ["Labor", "Materials", "Equipment"];
const labor = [18, 32, 58, 34, 22];
const materials = [6, 14, 20, 10, 8];
const equipment = [4, 10, 16, 6, 12];
const totals = phases.map((_, i) => labor[i] + materials[i] + equipment[i]);
const maxTotal = Math.max(...totals);

const TITLE = "bar-stacked-labeled · javascript · muix · anyplot.ai";
const TITLE_H = 56;

// --- Total labels (custom overlay, positioned via chart scales) -------------
function TotalLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {phases.map((phase, i) => (
        <text
          key={phase}
          x={xScale(phase) + xScale.bandwidth() / 2}
          y={yScale(totals[i]) - 16}
          textAnchor="middle"
          fontSize={20}
          fontWeight={700}
          fill={t.ink}
        >
          {`$${totals[i]}k`}
        </text>
      ))}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          px: "40px",
          pt: "10px",
        }}
      >
        <Typography
          sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1 }}
        >
          {TITLE}
        </Typography>
      </Box>

      <BarChart
        width={width}
        height={height - TITLE_H}
        colors={t.palette}
        skipAnimation
        grid={{ horizontal: true }}
        xAxis={[
          {
            scaleType: "band",
            data: phases,
            label: "Project Phase",
          },
        ]}
        yAxis={[
          {
            label: "Cost ($ thousands)",
            max: Math.ceil((maxTotal * 1.18) / 10) * 10,
            tickFontSize: 14,
            labelFontSize: 16,
            tickSize: 8,
          },
        ]}
        series={[
          { data: labor, label: costTypes[0], stack: "total" },
          { data: materials, label: costTypes[1], stack: "total" },
          { data: equipment, label: costTypes[2], stack: "total" },
        ]}
        margin={{ top: 30, right: 32, bottom: 90, left: 90 }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "15px" },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
        slotProps={{
          legend: { position: { vertical: "bottom", horizontal: "middle" } },
        }}
      >
        <TotalLabels />
      </BarChart>
    </Box>
  );
}
