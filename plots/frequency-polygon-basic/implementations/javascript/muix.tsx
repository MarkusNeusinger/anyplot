// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BIN_COUNT = 18; // shared bins across the pooled range of every group
const X_PAD_SHARE = 0.015; // x padding beyond the closing vertices, as a share of their span
const FREQUENCY_LABEL = "Frequency (count per bin)";
const TITLE = "frequency-polygon-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;

// Columns: set these to your data's column names
const REACTION_TIME = "Reaction time (ms)"; // role: values
const CONDITION = "Condition"; // role: group

// Data: replace this block with your own records, one object per row
// Simple visual-stimulus reaction times, 300 trials per condition in a psychology lab study;
// the sleep-deprived condition mixes in attentional lapses (microsleeps) that pull out a second mode.
const data = (() => {
  const conditions = [
    { label: "Control", seed: 11, components: [{ weight: 1, mean: 320, sd: 40 }] },
    { label: "Caffeine", seed: 23, components: [{ weight: 1, mean: 280, sd: 35 }] },
    {
      label: "Sleep-deprived",
      seed: 37,
      components: [
        { weight: 0.68, mean: 350, sd: 35 },
        { weight: 0.32, mean: 475, sd: 45 },
      ],
    },
  ];
  return conditions.flatMap((condition) => {
    let state = condition.seed;
    const rand = () => {
      state = (state * 1664525 + 1013904223) % 4294967296;
      return state / 4294967296;
    };
    return Array.from({ length: 300 }, () => {
      const pick = rand();
      let cumulative = 0;
      const component =
        condition.components.find((c) => (cumulative += c.weight) >= pick) ??
        condition.components[condition.components.length - 1];
      const u1 = Math.max(rand(), 1e-9);
      const u2 = rand();
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      return { [CONDITION]: condition.label, [REACTION_TIME]: Math.max(150, component.mean + z * component.sd) };
    });
  });
})();

// Plot: reads only data and the constants above
const observations = data.filter((d) => Number.isFinite(d[REACTION_TIME]));
const conditions = [...new Set(observations.map((d) => d[CONDITION]))];

// Bin edges shared by every group, so the vertices of all polygons sit at the same x positions
const valueMin = Math.min(...observations.map((d) => d[REACTION_TIME]));
const valueMax = Math.max(...observations.map((d) => d[REACTION_TIME]));
const binWidth = (valueMax - valueMin) / BIN_COUNT;

// One vertex per bin midpoint, plus one empty bin at each end so every polygon closes on zero
const midpoints = Array.from({ length: BIN_COUNT + 2 }, (_, i) => valueMin + (i - 0.5) * binWidth);
const frequencies = conditions.map((condition) => {
  const counts = new Array(BIN_COUNT + 2).fill(0);
  observations
    .filter((d) => d[CONDITION] === condition)
    .forEach((d) => {
      counts[1 + Math.min(BIN_COUNT - 1, Math.floor((d[REACTION_TIME] - valueMin) / binWidth))] += 1;
    });
  return counts;
});

const unit = REACTION_TIME.match(/\(([^)]+)\)/)?.[1] ?? "";
const subtitle = `n = ${observations.length} across ${conditions.length} groups · ${BIN_COUNT} shared bins of ${binWidth.toFixed(1)} ${unit}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", px: "40px", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H - 48}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        xAxis={[
          {
            data: midpoints,
            scaleType: "linear",
            min: midpoints[0] - X_PAD_SHARE * (midpoints[midpoints.length - 1] - midpoints[0]),
            max: midpoints[midpoints.length - 1] + X_PAD_SHARE * (midpoints[midpoints.length - 1] - midpoints[0]),
            label: REACTION_TIME,
            height: 68,
            tickNumber: 10,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: FREQUENCY_LABEL,
            width: 84,
            tickNumber: 8,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={conditions.map((condition, i) => ({
          id: `condition-${i}`,
          data: frequencies[i],
          label: condition,
          color: t.palette[i],
          curve: "linear",
          area: true,
          showMark: true,
          shape: "circle",
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft, mt: "8px" },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.14 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
