// anyplot.ai
// histogram-stacked: Stacked Histogram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
// Commute distance to work (km), binned, broken down by primary transport mode.
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function sampleNormal(rand, mean, stdDev) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const rand = makeLcg(42);

const GROUPS = [
  { label: "Car", mean: 19, stdDev: 6.5, count: 260, color: t.palette[0] },
  { label: "Public transit", mean: 13, stdDev: 5, count: 220, color: t.palette[1] },
  { label: "Bike", mean: 6, stdDev: 2.5, count: 160, color: t.palette[2] },
];

const BIN_WIDTH = 3;
const BIN_COUNT = 12;
const MAX_DISTANCE = BIN_WIDTH * BIN_COUNT;
const binLabels = Array.from(
  { length: BIN_COUNT },
  (_, i) => `${i * BIN_WIDTH}-${(i + 1) * BIN_WIDTH}`,
);

const groupCounts = GROUPS.map((group) => {
  const counts = new Array(BIN_COUNT).fill(0);
  for (let i = 0; i < group.count; i += 1) {
    const distance = Math.min(
      Math.max(sampleNormal(rand, group.mean, group.stdDev), 0),
      MAX_DISTANCE - 0.01,
    );
    counts[Math.floor(distance / BIN_WIDTH)] += 1;
  }
  return counts;
});

const dataset = binLabels.map((bin, i) => {
  const row = { bin };
  GROUPS.forEach((group, g) => {
    row[group.label] = groupCounts[g][i];
  });
  return row;
});

const TITLE_HEIGHT = 60;

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column", paddingTop: "20px" }}>
      <Typography
        sx={{ color: t.ink, fontSize: 22, fontWeight: 500, textAlign: "center", lineHeight: 1.2 }}
      >
        histogram-stacked · javascript · muix · anyplot.ai
      </Typography>
      <BarChart
        width={width}
        height={height - TITLE_HEIGHT}
        dataset={dataset}
        colors={GROUPS.map((group) => group.color)}
        skipAnimation
        xAxis={[{ scaleType: "band", dataKey: "bin", label: "Commute Distance (km)" }]}
        yAxis={[{ label: "Number of Commuters" }]}
        series={GROUPS.map((group) => ({
          dataKey: group.label,
          label: group.label,
          stack: "total",
        }))}
        grid={{ horizontal: true }}
        margin={{ top: 40, right: 40, bottom: 130, left: 100 }}
        slotProps={{
          legend: { position: { vertical: "bottom", horizontal: "middle" } },
        }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "14px" },
          "& .MuiChartsGrid-line": { opacity: 0.5 },
        }}
      />
    </Box>
  );
}
