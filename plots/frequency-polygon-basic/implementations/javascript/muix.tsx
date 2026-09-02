// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const TITLE = "frequency-polygon-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic LCG — no seeded RNG in the browser) -----
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function randomNormal(rand, mean, stdDev) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

// Simple visual-stimulus reaction times (ms) across three experimental
// conditions in a psychology lab study.
const SAMPLE_SIZE = 300;
const CONDITIONS = [
  { label: "Control", mean: 320, stdDev: 40, seed: 11 },
  { label: "Caffeine", mean: 280, stdDev: 35, seed: 23 },
  { label: "Sleep-deprived", mean: 385, stdDev: 55, seed: 37 },
];
const samplesByCondition = CONDITIONS.map((condition) => {
  const rand = lcg(condition.seed);
  return Array.from({ length: SAMPLE_SIZE }, () =>
    Math.max(150, randomNormal(rand, condition.mean, condition.stdDev)),
  );
});

// Shared bin edges across all conditions so the polygons stay comparable.
const allTimes = samplesByCondition.flat();
const dataMin = Math.min(...allTimes);
const dataMax = Math.max(...allTimes);
const BIN_COUNT = 18;
const binWidth = (dataMax - dataMin) / BIN_COUNT;
const binEdges = Array.from({ length: BIN_COUNT + 1 }, (_, i) => dataMin + i * binWidth);
const binMidpoints = Array.from(
  { length: BIN_COUNT },
  (_, i) => (binEdges[i] + binEdges[i + 1]) / 2,
);

function histogram(samples) {
  const counts = new Array(BIN_COUNT).fill(0);
  samples.forEach((value) => {
    const index = Math.min(BIN_COUNT - 1, Math.floor((value - dataMin) / binWidth));
    counts[Math.max(0, index)] += 1;
  });
  return counts;
}
const countsByCondition = samplesByCondition.map(histogram);

// Extend each polygon one bin-width past the outer midpoints at zero so the
// outline closes at the baseline instead of hanging in mid-air.
const reactionTimes = [
  binMidpoints[0] - binWidth,
  ...binMidpoints,
  binMidpoints[BIN_COUNT - 1] + binWidth,
];
const frequenciesByCondition = countsByCondition.map((counts) => [0, ...counts, 0]);

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg }}>
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          px: "40px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1 }}>
          {TITLE}
        </Typography>
      </Box>
      <LineChart
        width={width}
        height={chartHeight}
        skipAnimation
        colors={t.palette.slice(0, CONDITIONS.length)}
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: reactionTimes,
            scaleType: "linear",
            label: "Reaction Time (ms)",
            valueFormatter: (v) => Math.round(v).toString(),
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: "Frequency",
          },
        ]}
        series={CONDITIONS.map((condition, index) => ({
          id: condition.label,
          data: frequenciesByCondition[index],
          label: condition.label,
          curve: "linear",
          area: true,
          showMark: false,
        }))}
        margin={{ top: 24, bottom: 90, left: 90, right: 40 }}
        sx={{
          "& .MuiAreaElement-root": { fillOpacity: 0.14 },
          "& .MuiLineElement-root": { strokeWidth: 3 },
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "15px" },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "middle" },
            itemMarkWidth: 20,
            itemMarkHeight: 4,
          },
        }}
      />
    </Box>
  );
}
