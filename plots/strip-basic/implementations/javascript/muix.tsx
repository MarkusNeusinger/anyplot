// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BASELINE = 0; // durations start at zero
const JITTER_WIDTH = 0.27; // half-width of the random sideways spread, in category slots
const POINT_ALPHA = 0.62; // points overlap often, so piled-up values read darker
const MEAN_HALF_WIDTH = 0.34; // the mean line spans slightly past the strip
const CATEGORY_PAD = 0.6; // room beside the outer strips, in category slots
const Y_PAD_SHARE = 0.05;
const JITTER_SEED = 7;

// Columns: set these to your data's column names
const GROUP = "Treatment group"; // role: category
const TIME = "Time to relief (minutes)"; // role: value

// Data: replace this block with your own records, one object per row
// Time to symptom relief after treatment, 42 patients in each of four groups
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const groups = [
    { name: "Placebo", mean: 46, std: 12 },
    { name: "Paracetamol 1 g", mean: 30, std: 10 },
    { name: "Ibuprofen 400 mg", mean: 19, std: 7 },
    { name: "Naproxen 500 mg", mean: 11, std: 5 },
  ];
  return groups.flatMap((g) =>
    Array.from({ length: 42 }, () => {
      const normal = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
      return { [GROUP]: g.name, [TIME]: Number(Math.max(2, g.mean + g.std * normal).toFixed(1)) };
    }),
  );
})();

// Plot: reads only data and the constants above
// Each group sits at its slot index; a seeded sideways jitter spreads its points, the values stay exact
const rows = data.filter((d) => d[GROUP] != null && d[TIME] != null);
const groups = [...new Set(rows.map((d) => d[GROUP] as string))];
let jitterState = JITTER_SEED;
const series = groups.map((group, i) => ({
  type: "scatter" as const,
  id: `group-${i}`,
  label: group,
  color: t.palette[i],
  markerSize: 9,
  data: rows
    .filter((d) => d[GROUP] === group)
    .map((d, k) => {
      jitterState = (1664525 * jitterState + 1013904223) >>> 0;
      return { x: i + ((jitterState / 4294967296) * 2 - 1) * JITTER_WIDTH, y: d[TIME] as number, id: `${i}-${k}` };
    }),
}));
const groupMeans = series.map((s) => s.data.reduce((acc, p) => acc + p.y, 0) / s.data.length);
const valueMax = Math.max(...rows.map((d) => d[TIME] as number));
const yMax = valueMax + (valueMax - BASELINE) * Y_PAD_SHARE;

const TITLE = "strip-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} observations in ${groups.length} groups · line: group mean`;
const HEADER_H = 76;

// A short line at each group's mean, in the group's colour
function MeanLines() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  return (
    <g>
      {groupMeans.map((mean, i) => (
        <line
          key={groups[i]}
          x1={xScale(i - MEAN_HALF_WIDTH)}
          x2={xScale(i + MEAN_HALF_WIDTH)}
          y1={yScale(mean)}
          y2={yScale(mean)}
          stroke={t.palette[i]}
          strokeWidth={3.5}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsContainer
        width={W}
        height={H - HEADER_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        series={series}
        xAxis={[
          {
            id: "group",
            min: -CATEGORY_PAD,
            max: groups.length - 1 + CATEGORY_PAD,
            tickInterval: groups.map((_, i) => i),
            valueFormatter: (v: number) => groups[Math.round(v)] ?? "",
            label: GROUP,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "time",
            min: BASELINE,
            max: yMax,
            label: TIME,
            tickNumber: 8,
            width: 72,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiScatterChart-marker": { fillOpacity: POINT_ALPHA },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <ScatterPlot />
        <MeanLines />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
