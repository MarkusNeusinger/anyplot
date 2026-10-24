// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD_FRAC = 0.1;
const TITLE = "lollipop-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 70;

// Columns: set these to your data's column names
const CATEGORY = "Book genre"; // role: category
const VALUE = "Annual sales (millions of units)"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [CATEGORY]: "Children's", [VALUE]: 22.1 },
  { [CATEGORY]: "Romance", [VALUE]: 18.7 },
  { [CATEGORY]: "Thriller", [VALUE]: 16.3 },
  { [CATEGORY]: "Mystery", [VALUE]: 15.2 },
  { [CATEGORY]: "Fantasy", [VALUE]: 14.8 },
  { [CATEGORY]: "Sci-Fi", [VALUE]: 12.4 },
  { [CATEGORY]: "Self-Help", [VALUE]: 11.2 },
  { [CATEGORY]: "Business", [VALUE]: 10.5 },
  { [CATEGORY]: "Cooking", [VALUE]: 9.8 },
  { [CATEGORY]: "Biography", [VALUE]: 8.9 },
  { [CATEGORY]: "History", [VALUE]: 7.6 },
  { [CATEGORY]: "Literary Fiction", [VALUE]: 6.4 },
];

// Plot: reads only data and the constants above
const sortedData = [...data].sort((a, b) => Number(b[VALUE]) - Number(a[VALUE]));
const genres = sortedData.map((r) => String(r[CATEGORY]));
const salesData = sortedData.map((r) => Number(r[VALUE]));
const maxVal = Math.max(...salesData);
const xAxisMax = maxVal * (1 + X_PAD_FRAC);

function LollipopPlot() {
  const xScale = useXScale("sales") as (v: number) => number;
  const yScale = useYScale("genre") as unknown as ((v: string) => number) & {
    bandwidth: () => number;
  };
  const bw = yScale.bandwidth();
  const x0 = xScale(0);

  return (
    <g>
      {sortedData.map((row) => {
        const genre = String(row[CATEGORY]);
        const val = Number(row[VALUE]);
        const x1 = xScale(val);
        const cy = yScale(genre) + bw / 2;

        return (
          <g key={genre}>
            <line
              x1={x0}
              y1={cy}
              x2={x1}
              y2={cy}
              stroke={t.palette[0]}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <circle cx={x1} cy={cy} r={11} fill={t.palette[0]} />
            <text
              x={x1 + 16}
              y={cy + 5}
              fill={t.inkSoft}
              fontSize={14}
              fontFamily="sans-serif"
            >
              {val.toFixed(1)}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500 }}>
          {TITLE}
        </Typography>
      </Box>

      <ChartsContainer
        skipAnimation
        width={chartWidth}
        height={chartHeight}
        margin={{ top: 10, right: 85, bottom: 16, left: 24 }}
        series={[]}
        xAxis={[
          {
            id: "sales",
            scaleType: "linear",
            min: 0,
            max: xAxisMax,
            height: 54,
            label: VALUE,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "genre",
            scaleType: "band",
            data: genres,
            width: 180,
            label: CATEGORY,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeOpacity: 0.5 },
        }}
      >
        <ChartsGrid vertical />
        <LollipopPlot />
        <ChartsYAxis axisId="genre" />
        <ChartsXAxis axisId="sales" />
      </ChartsContainer>
    </Box>
  );
}
