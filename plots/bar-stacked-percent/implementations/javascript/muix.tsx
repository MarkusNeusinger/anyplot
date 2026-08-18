// anyplot.ai
// bar-stacked-percent: 100% Stacked Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-18
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Fixed (non-theme-flipping) text colors for in-bar percentage labels — the
// segment fills stay the same hex in both themes, so label contrast is chosen
// per series color rather than following t.ink/t.inkSoft.
const LABEL_ON_LIGHT_FILL = "#1A1A17"; // dark ink — for the green/lavender/ochre segments
const LABEL_ON_DARK_FILL = "#F0EFE8"; // light ink — for the darker blue segment

// --- Data (in-memory, deterministic) ----------------------------------------
// Electricity generation mix (TWh/year, illustrative) for six grids whose
// total output spans two orders of magnitude — China dwarfs Norway in raw
// terawatt-hours, which is exactly why a percent-stacked view (composition)
// tells a clearer story here than a raw stacked view (dominated by scale).
const countries = ["China", "USA", "Germany", "France", "Brazil", "Norway"];
const rawByCountry = {
  China: { renewables: 3100, nuclear: 400, gas: 300, coal: 5200 },
  USA: { renewables: 900, nuclear: 800, gas: 1700, coal: 700 },
  Germany: { renewables: 270, nuclear: 0, gas: 80, coal: 150 },
  France: { renewables: 120, nuclear: 320, gas: 30, coal: 5 },
  Brazil: { renewables: 550, nuclear: 15, gas: 60, coal: 15 },
  Norway: { renewables: 150, nuclear: 0, gas: 0.5, coal: 0.1 },
};

// Renewables listed first so it lands on Imprint position 1 (brand green) —
// a natural semantic fit (growth/nature). Order stays fixed across every bar.
const components = [
  { id: "renewables", label: "Renewables", labelFill: LABEL_ON_LIGHT_FILL },
  { id: "nuclear", label: "Nuclear", labelFill: LABEL_ON_LIGHT_FILL },
  { id: "gas", label: "Natural Gas", labelFill: LABEL_ON_DARK_FILL },
  { id: "coal", label: "Coal", labelFill: LABEL_ON_LIGHT_FILL },
];
const labelFillById = Object.fromEntries(components.map((c) => [c.id, c.labelFill]));

const totalsByCountry = countries.map((country) =>
  components.reduce((sum, c) => sum + rawByCountry[country][c.id], 0),
);
const series = components.map((c) => ({
  id: c.id,
  label: c.label,
  stack: "total",
  data: countries.map((country, i) => (rawByCountry[country][c.id] / totalsByCountry[i]) * 100),
}));

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width; // 1600 CSS px (landscape mount)
  const H = window.ANYPLOT_SIZE.height; // 900 CSS px
  const CHART_TOP = 84;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      {/* Title + subtitle */}
      <Box sx={{ position: "absolute", top: 24, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500 }}>
          bar-stacked-percent · javascript · muix · anyplot.ai
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, mt: 0.5 }}>
          Norway's grid runs almost entirely on renewables, while China still leans on coal
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
              data: countries,
              label: "Country",
              disableTicks: true,
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              categoryGapRatio: 0.35,
            },
          ]}
          yAxis={[
            {
              label: "Share (%)",
              labelStyle: { fontSize: 15, fill: t.ink },
              // tickFontSize (unlike tickLabelStyle.fontSize) drives the axis
              // label's offset from the tick labels — pushed wide to clear
              // the "100%" tick text without inflating its visual size.
              tickFontSize: 70,
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
              min: 0,
              max: 100,
              valueFormatter: (v) => `${v}%`,
            },
          ]}
          series={series.map((s) => ({
            ...s,
            valueFormatter: (v) => `${v.toFixed(1)}%`,
          }))}
          barLabel={(item) => (item.value != null && item.value >= 6 ? `${item.value.toFixed(0)}%` : null)}
          margin={{ top: 14, right: 130, bottom: 90, left: 140 }}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              position: { vertical: "middle", horizontal: "right" },
              direction: "column",
              labelStyle: { fontSize: 14, fill: t.inkSoft },
            },
            barLabel: (ownerState) => ({
              style: {
                fontSize: 13,
                fontWeight: 600,
                fill: labelFillById[ownerState.seriesId] ?? LABEL_ON_LIGHT_FILL,
              },
            }),
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
