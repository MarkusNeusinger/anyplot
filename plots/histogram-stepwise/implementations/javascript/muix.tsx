// anyplot.ai
// histogram-stepwise: Step Histogram
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BIN_COUNT = 26; // shared bins across the pooled range of all groups
const Y_HEADROOM_SHARE = 0.16; // room above the tallest step for the peak labels

// Columns: set these to your data's column names
const LATENCY = "Response latency (ms)"; // role: values
const VERSION = "API version"; // role: group

// Data: replace this block with your own records, one object per observation
// Response latency of 800 requests each before (v1) and after (v2) an
// optimisation pass of the same API endpoint.
const data = (() => {
  let state = 42 >>> 0;
  const rng = () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const versions = [
    { name: "API v1", mean: 118, sd: 22 },
    { name: "API v2", mean: 92, sd: 16 },
  ];
  return versions.flatMap((v) =>
    Array.from({ length: 800 }, () => {
      const z = Math.sqrt(-2 * Math.log(Math.max(rng(), 1e-9))) * Math.cos(2 * Math.PI * rng());
      return { [VERSION]: v.name, [LATENCY]: Number(Math.max(8, v.mean + z * v.sd).toFixed(1)) };
    }),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[LATENCY] != null);
const groups = [...new Set(rows.map((d) => d[VERSION]))];
const values = rows.map((d) => d[LATENCY]);
const minValue = Math.min(...values);
const maxValue = Math.max(...values);
const binWidth = (maxValue - minValue) / BIN_COUNT;
const edges = Array.from({ length: BIN_COUNT + 1 }, (_, i) => minValue + i * binWidth);

const groupStats = groups.map((group) => {
  const counts = new Array(BIN_COUNT).fill(0);
  const groupValues = rows.filter((d) => d[VERSION] === group).map((d) => d[LATENCY]);
  for (const v of groupValues) counts[Math.min(BIN_COUNT - 1, Math.floor((v - minValue) / binWidth))] += 1;
  const peakIndex = counts.indexOf(Math.max(...counts));
  return { group, counts, n: groupValues.length, peak: (edges[peakIndex] + edges[peakIndex + 1]) / 2 };
});
// One x per bin edge with curve "stepAfter": the doubled first edge lifts the outline
// from zero, and the trailing 0 closes it back to the axis at the last edge
const stepX = [edges[0], ...edges];
const yMax = Math.max(...groupStats.flatMap((g) => g.counts)) * (1 + Y_HEADROOM_SHARE);
// A peak below the average of all peaks is labelled left of its line, the others right
const meanPeak = groupStats.reduce((s, g) => s + g.peak, 0) / groupStats.length;

const unit = LATENCY.match(/\(([^)]+)\)/)?.[1] ?? "";
const unitSuffix = unit ? ` ${unit}` : "";
const TITLE = "histogram-stepwise · javascript · muix · anyplot.ai";
const SUBTITLE = `${groupStats.map((g) => `${g.group} n = ${g.n}`).join(" · ")} · ${BIN_COUNT} shared bins of ${binWidth.toFixed(1)}${unitSuffix} · dashed lines: centre of each tallest bin`;
const COUNT_LABEL = "Frequency (count per bin)";
const HEADER_H = 76;
const LEGEND_H = 44;

// Peak markers at the centre of each group's tallest bin
function PeakLines() {
  const xScale = useXScale() as (v: number) => number;
  const { top, height } = useDrawingArea();
  return (
    <g>
      {groupStats.map((g, i) => {
        const x = xScale(g.peak);
        const leftSide = g.peak < meanPeak;
        return (
          <g key={g.group}>
            <line x1={x} x2={x} y1={top} y2={top + height} stroke={t.palette[i]} strokeWidth={2} strokeDasharray="6 4" />
            <text
              x={leftSide ? x - 8 : x + 8}
              y={top + 20 + i * 24}
              textAnchor={leftSide ? "end" : "start"}
              fontSize={15}
              fontWeight={600}
              fill={t.ink}
            >
              {`${g.group} peak ${g.peak.toFixed(0)}${unitSuffix}`}
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
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 16, left: 24 }}
        series={groupStats.map((g, i) => ({
          id: `group-${i}`,
          data: [0, ...g.counts, 0],
          label: g.group,
          color: t.palette[i],
          curve: "stepAfter",
          showMark: false,
        }))}
        xAxis={[
          {
            data: stepX,
            scaleType: "linear",
            min: edges[0],
            max: edges[edges.length - 1],
            tickNumber: 12,
            height: 64,
            label: LATENCY,
            valueFormatter: (v: number) => v.toFixed(0),
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
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <PeakLines />
      </LineChart>
    </Box>
  );
}
