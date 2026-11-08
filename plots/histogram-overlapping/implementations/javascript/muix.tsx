// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-18
import { BarChart } from "@mui/x-charts/BarChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET_BINS = 13; // about this many bins; the width is rounded to a 1-2-2.5-5 step
const NICE_STEPS = [1, 2, 2.5, 5, 10];
const FILL_ALPHA_HEX = "8C"; // 55 % opacity, baked into the colour so the legend swatches match
const Y_HEADROOM_SHARE = 0.18; // room above the tallest bar for the mean labels

// Columns: set these to your data's column names
const SCORE = "Exam Score (0–100)"; // role: values
const GROUP = "Group"; // role: group

// Data: replace this block with your own records, one object per observation
// Exam scores of 240 students per arm of an A/B test of a new tutoring method.
const data = (() => {
  let state = 42 >>> 0;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const arms = [
    { name: "Control group", mean: 68, sd: 11 },
    { name: "Treatment group", mean: 76, sd: 9 },
  ];
  return arms.flatMap((arm) =>
    Array.from({ length: 240 }, () => ({
      [GROUP]: arm.name,
      [SCORE]: Number(Math.min(100, Math.max(0, arm.mean + arm.sd * gaussian())).toFixed(1)),
    })),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[SCORE] != null);
const groups = [...new Set(rows.map((d) => d[GROUP]))];
const values = rows.map((d) => d[SCORE]);
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
  const groupValues = rows.filter((d) => d[GROUP] === group).map((d) => d[SCORE]);
  const counts = new Array(binCount).fill(0);
  for (const v of groupValues) counts[Math.min(binCount - 1, Math.floor((v - binStart) / binWidth))] += 1;
  return { group, counts, n: groupValues.length, mean: groupValues.reduce((s, v) => s + v, 0) / groupValues.length };
});
const yMax = Math.max(...groupStats.flatMap((g) => g.counts)) * (1 + Y_HEADROOM_SHARE);
// A mean below the average of all group means is labelled left of its line, the others right
const meanOfMeans = groupStats.reduce((s, g) => s + g.mean, 0) / groupStats.length;

const TITLE = "histogram-overlapping · javascript · muix · anyplot.ai";
const SUBTITLE = `${groupStats.map((g) => `${g.group} n = ${g.n}`).join(" · ")} · shared bin width ${binWidth} · dashed lines: group means`;
const COUNT_LABEL = "Frequency (count per bin)";
const HEADER_H = 76;
const LEGEND_H = 44;

// Group means at their exact value: with contiguous bins the band axis is linear in value
function MeanLines() {
  const xScale = useXScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const { top, height } = useDrawingArea();
  const pxPerUnit = xScale.bandwidth() / binWidth;
  const x0 = xScale(binLabels[0]);
  return (
    <g>
      {groupStats.map((g, i) => {
        const x = x0 + (g.mean - binStart) * pxPerUnit;
        const flip = g.mean < meanOfMeans;
        return (
          <g key={g.group}>
            <line x1={x} x2={x} y1={top} y2={top + height} stroke={t.palette[i]} strokeWidth={2.5} strokeDasharray="7 5" />
            <text
              x={flip ? x - 8 : x + 8}
              y={top + 20 + i * 24}
              textAnchor={flip ? "end" : "start"}
              fontSize={15}
              fontWeight={600}
              fill={t.ink}
            >
              {`${g.group} mean ${g.mean.toFixed(1)}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

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
        margin={{ top: 12, right: 40, bottom: 16, left: 24 }}
        series={groupStats.map((g, i) => ({
          id: `group-${i}`,
          data: g.counts,
          label: g.group,
          color: `${t.palette[i]}${FILL_ALPHA_HEX}`,
          highlightScope: { highlight: "series", fade: "global" },
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: binLabels,
            categoryGapRatio: 0,
            // Overlap the groups instead of placing them side by side: a gap ratio
            // of -1 gives every series the full band width at the same offset
            barGapRatio: -1,
            height: 64,
            label: SCORE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: yMax,
            width: 72,
            label: COUNT_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 15, color: t.ink, pr: "40px", gap: "24px" },
          },
        }}
        sx={{ "& .MuiChartsGrid-line": { stroke: t.grid } }}
      >
        <MeanLines />
      </BarChart>
    </Box>
  );
}
