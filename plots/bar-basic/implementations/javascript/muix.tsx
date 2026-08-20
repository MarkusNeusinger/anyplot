// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-20
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Annual coffee consumption per capita — top consuming countries (kg/person/year)
const countries = ["Finland", "Norway", "Iceland", "Denmark", "Netherlands", "Sweden", "Switzerland"];
const kgPerCapita = [12.0, 9.9, 9.0, 8.7, 8.4, 8.2, 7.9];

const dataset = countries.map((country, i) => ({ country, kgPerCapita: kgPerCapita[i] }));

const TITLE_HEIGHT = 60;

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column", paddingTop: "20px" }}>
      <Typography
        sx={{ color: t.ink, fontSize: 22, fontWeight: 500, textAlign: "center", lineHeight: 1.2 }}
      >
        bar-basic · javascript · muix · anyplot.ai
      </Typography>
      <BarChart
        width={width}
        height={height - TITLE_HEIGHT}
        dataset={dataset}
        colors={[t.palette[0]]}
        skipAnimation
        barLabel="value"
        xAxis={[{ scaleType: "band", dataKey: "country", label: "Country" }]}
        yAxis={[{ label: "Coffee Consumption (kg per capita/year)" }]}
        series={[{ dataKey: "kgPerCapita", label: "Coffee consumption" }]}
        grid={{ horizontal: true }}
        margin={{ top: 32, right: 32, bottom: 64, left: 88 }}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiBarLabel-root": { fontSize: "14px", fill: t.ink },
        }}
      />
    </Box>
  );
}
