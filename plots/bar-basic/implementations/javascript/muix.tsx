// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-23
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
        hideLegend
        xAxis={[
          {
            scaleType: "band",
            dataKey: "country",
            label: "Country",
            height: 72,
            tickLabelStyle: { fontSize: 16 },
            labelStyle: { fontSize: 18 },
          },
        ]}
        yAxis={[
          {
            label: "Coffee Consumption (kg per capita/year)",
            width: 84,
            // headroom above the tallest bar so its outside value label is not clipped
            domainLimit: (min, max) => ({ min, max: max * 1.08 }),
            tickLabelStyle: { fontSize: 16 },
            labelStyle: { fontSize: 18 },
          },
        ]}
        series={[
          {
            dataKey: "kgPerCapita",
            label: "Coffee consumption",
            barLabel: (item) => item.value?.toFixed(1),
            barLabelPlacement: "outside",
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ top: 32, right: 32, bottom: 8, left: 16 }}
        sx={{
          "& .MuiBarChart-label": { fontSize: "16px", fontWeight: 500, fill: t.ink },
        }}
      />
    </Box>
  );
}
