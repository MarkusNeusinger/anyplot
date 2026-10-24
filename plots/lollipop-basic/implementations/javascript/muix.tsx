// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: muix 9.x | JavaScript 22.23.0
// Quality: 90/100 | Created: 2026-07-01

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const CATEGORY_COL = "Book Genre" as const;
const VALUE_COL = "Annual Sales (millions of units)" as const;
const X_PAD_FRAC = 0.1;

// Data — annual book sales by genre (millions of units)
const DATA: Array<Record<string, string | number>> = [
  { [CATEGORY_COL]: "Children's", [VALUE_COL]: 22.1 },
  { [CATEGORY_COL]: "Romance", [VALUE_COL]: 18.7 },
  { [CATEGORY_COL]: "Thriller", [VALUE_COL]: 16.3 },
  { [CATEGORY_COL]: "Mystery", [VALUE_COL]: 15.2 },
  { [CATEGORY_COL]: "Fantasy", [VALUE_COL]: 14.8 },
  { [CATEGORY_COL]: "Sci-Fi", [VALUE_COL]: 12.4 },
  { [CATEGORY_COL]: "Self-Help", [VALUE_COL]: 11.2 },
  { [CATEGORY_COL]: "Business", [VALUE_COL]: 10.5 },
  { [CATEGORY_COL]: "Cooking", [VALUE_COL]: 9.8 },
  { [CATEGORY_COL]: "Biography", [VALUE_COL]: 8.9 },
  { [CATEGORY_COL]: "History", [VALUE_COL]: 7.6 },
  { [CATEGORY_COL]: "Literary Fiction", [VALUE_COL]: 6.4 },
];

const sortedData = [...DATA].sort((a, b) => Number(b[VALUE_COL]) - Number(a[VALUE_COL]));
const genres = sortedData.map((r) => String(r[CATEGORY_COL]));
const salesData = sortedData.map((r) => Number(r[VALUE_COL]));
const maxVal = Math.max(...salesData);
const xAxisMax = maxVal * (1 + X_PAD_FRAC);

function LollipopPlot() {
  const xScale = useXScale("sales") as (v: number) => number | undefined;
  const yScale = useYScale("genre") as {
    (v: string): number | undefined;
    bandwidth?: () => number;
  };

  if (!xScale || !yScale || typeof yScale.bandwidth !== "function") return null;
  const bw = yScale.bandwidth();

  return (
    <g>
      {sortedData.map((row) => {
        const genre = String(row[CATEGORY_COL]);
        const val = Number(row[VALUE_COL]);
        const x0 = Number(xScale(0) ?? 0);
        const x1 = Number(xScale(val) ?? 0);
        const bandTop = yScale(genre);
        if (bandTop == null || !Number.isFinite(Number(bandTop))) return null;
        const cy = Number(bandTop) + bw / 2;

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

const TITLE = "lollipop-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 70;

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
            label: VALUE_COL,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "genre",
            scaleType: "band",
            data: genres,
            width: 148,
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
