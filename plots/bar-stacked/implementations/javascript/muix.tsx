// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly cloud infrastructure spend ($K), broken down by service. Compute
// grows fastest of the four, so its share of the stack widens month over
// month — a composition story a stacked view tells better than a line chart.
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const spendByMonth = {
  Jan: { compute: 38, storage: 14, networking: 9, database: 21 },
  Feb: { compute: 41, storage: 15, networking: 10, database: 22 },
  Mar: { compute: 44, storage: 16, networking: 10, database: 24 },
  Apr: { compute: 47, storage: 17, networking: 11, database: 25 },
  May: { compute: 52, storage: 18, networking: 12, database: 27 },
  Jun: { compute: 58, storage: 20, networking: 13, database: 29 },
};

// Stack order fixed across every bar, largest/most-volatile service first so
// it lands on Imprint position 1 (brand green).
const components = [
  { id: "compute", label: "Compute" },
  { id: "storage", label: "Storage" },
  { id: "networking", label: "Networking" },
  { id: "database", label: "Database" },
];

const series = components.map((c) => ({
  id: c.id,
  label: c.label,
  stack: "total",
  data: months.map((m) => spendByMonth[m][c.id]),
  valueFormatter: (v) => `$${v}K`,
}));

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width; // 1600 CSS px (landscape mount)
  const H = window.ANYPLOT_SIZE.height; // 900 CSS px
  const CHART_TOP = 84;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      {/* Title + subtitle */}
      <Box sx={{ position: "absolute", top: 24, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: 21, fontWeight: 500 }}>
          Cloud Costs by Service · bar-stacked · javascript · muix · anyplot.ai
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, mt: 0.5 }}>
          Compute spend nearly doubles by June, driving most of the total stack's growth
        </Typography>
      </Box>

      {/* Bar chart */}
      <Box sx={{ position: "absolute", top: CHART_TOP, left: 0, right: 0, bottom: 0 }}>
        <BarChart
          width={W}
          height={H - CHART_TOP}
          colors={t.palette}
          skipAnimation
          xAxis={[
            {
              scaleType: "band",
              data: months,
              label: "Month",
              disableTicks: true,
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              categoryGapRatio: 0.4,
            },
          ]}
          yAxis={[
            {
              label: "Spend ($K)",
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
            },
          ]}
          series={series}
          margin={{ top: 14, right: 170, bottom: 70, left: 90 }}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              position: { vertical: "middle", horizontal: "right" },
              direction: "column",
              labelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          }}
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.grid },
            "& .MuiChartsGrid-line": { stroke: t.grid },
          }}
        />
      </Box>
    </Box>
  );
}
