// anyplot.ai
// histogram-stacked: Stacked Histogram
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET_BINS = 15; // about this many bins; the width is rounded to a 1-2-2.5-5 step
const NICE_STEPS = [1, 2, 2.5, 5, 10];

// Columns: set these to your data's column names
const DISTANCE = "Commute Distance (km)"; // role: values
const MODE = "Transport mode"; // role: group

// Data: replace this block with your own records, one object per observation
// One-way commute distance of 640 employees by their primary transport mode.
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const modes = [
    { name: "Car", mean: 19, sd: 6.5, n: 260 },
    { name: "Public transit", mean: 13, sd: 5, n: 220 },
    { name: "Bike", mean: 6, sd: 2.5, n: 160 },
  ];
  return modes.flatMap((mode) =>
    Array.from({ length: mode.n }, () => {
      const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
      return { [MODE]: mode.name, [DISTANCE]: Number(Math.min(Math.max(mode.mean + z * mode.sd, 0), 35.99).toFixed(2)) };
    }),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[DISTANCE] != null);
const groups = [...new Set(rows.map((d) => d[MODE]))];
const values = rows.map((d) => d[DISTANCE]);
const minValue = Math.min(...values);
const maxValue = Math.max(...values);
const rawWidth = (maxValue - minValue) / TARGET_BINS;
const magnitude = 10 ** Math.floor(Math.log10(rawWidth));
const binWidth = NICE_STEPS.map((s) => s * magnitude).find((w) => w >= rawWidth);
const binStart = Math.floor(minValue / binWidth) * binWidth;
const binCount = Math.max(1, Math.ceil((maxValue - binStart) / binWidth));
// Bin edges shared by every group; bins [edge, edge + width), the last one closed
const edges = Array.from({ length: binCount + 1 }, (_, i) => Number((binStart + i * binWidth).toPrecision(12)));
const binLabels = edges.slice(0, -1).map((lo, i) => `${lo}–${edges[i + 1]}`);

const groupStats = groups.map((group) => {
  const groupValues = rows.filter((d) => d[MODE] === group).map((d) => d[DISTANCE]);
  const counts = new Array(binCount).fill(0);
  for (const v of groupValues) counts[Math.min(binCount - 1, Math.floor((v - binStart) / binWidth))] += 1;
  return { group, counts, n: groupValues.length };
});

const unit = DISTANCE.match(/\(([^)]+)\)/)?.[1] ?? "";
const TITLE = "histogram-stacked · javascript · muix · anyplot.ai";
const SUBTITLE = `${MODE}: ${groupStats.map((g) => `${g.group} n = ${g.n}`).join(" · ")} · bin width ${binWidth}${unit ? ` ${unit}` : ""}`;
const COUNT_LABEL = "Frequency (count per bin)";
const HEADER_H = 76;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <BarChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        borderRadius={0}
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 8, left: 24 }}
        // Stacked in the data's group order, the same in every bin
        series={groupStats.map((g, i) => ({
          id: `group-${i}`,
          data: g.counts,
          label: g.group,
          color: t.palette[i],
          stack: "total",
          highlightScope: { highlight: "series", fade: "global" },
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: binLabels,
            // Contiguous bins: the segment stroke marks bin and group edges
            categoryGapRatio: 0,
            height: 64,
            label: DISTANCE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            width: 72,
            label: COUNT_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink, gap: "28px" },
          },
        }}
        sx={{
          "& .MuiBarChart-element": { stroke: t.pageBg, strokeWidth: 1.5 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
