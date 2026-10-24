// anyplot.ai
// point-and-figure-basic: Point and Figure Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "point-and-figure-basic · javascript · muix · anyplot.ai";
const X_TITLE = "Column (price reversal, not time)";
const REVERSAL_BOXES = 3;
const MIN_TREND_SPAN = 2;
const Y_PAD_BOXES = 2;
const TICK_EVERY_N_COLS = 5;

const RISING_SYMBOL = "X";
const FALLING_SYMBOL = "O";
const RISING_LABEL = "Rising column";
const FALLING_LABEL = "Falling column";
const SUPPORT_LABEL = "Support";
const RESISTANCE_LABEL = "Resistance";

// Columns: set these to your data's column names
const SESSION = "Trading session"; // role: date
const CLOSE = "Close (USD)"; // role: close

// Data: replace this block with your own records
const NUM_SESSIONS = 360;
const INITIAL_PRICE = 148;
const MIN_PRICE_FLOOR = 60;
const DRIFT_STEP = 0.01;
const VOLATILITY_STEP = 4.3;
const BOX_SIZE = 1.5;

const data: Array<Record<string, number>> = [];
let lcgState = 42 >>> 0;
let runningPrice = INITIAL_PRICE;
for (let session = 1; session <= NUM_SESSIONS; session += 1) {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  const randUnit = lcgState / 4294967296;
  runningPrice = Math.max(
    MIN_PRICE_FLOOR,
    runningPrice + DRIFT_STEP + (randUnit - 0.5) * VOLATILITY_STEP,
  );
  data.push({
    [SESSION]: session,
    [CLOSE]: Math.round(runningPrice * 100) / 100,
  });
}

// Plot: reads only data and the constants above
const sortedRows = [...data].sort((a, b) => Number(a[SESSION]) - Number(b[SESSION]));

interface PnfColumn {
  direction: string;
  boxes: number[];
}

const columns: PnfColumn[] = [];
let boxIndex = Math.round(Number(sortedRows[0][CLOSE]) / BOX_SIZE);
let direction: string | null = null;
let boxesInColumn: number[] = [boxIndex];

for (let i = 1; i < sortedRows.length; i += 1) {
  const nextBox = Math.round(Number(sortedRows[i][CLOSE]) / BOX_SIZE);
  if (direction === null) {
    if (nextBox > boxIndex) {
      direction = RISING_SYMBOL;
      for (let b = boxIndex + 1; b <= nextBox; b += 1) boxesInColumn.push(b);
      boxIndex = nextBox;
    } else if (nextBox < boxIndex) {
      direction = FALLING_SYMBOL;
      for (let b = boxIndex - 1; b >= nextBox; b -= 1) boxesInColumn.push(b);
      boxIndex = nextBox;
    }
    continue;
  }
  if (direction === RISING_SYMBOL) {
    if (nextBox > boxIndex) {
      for (let b = boxIndex + 1; b <= nextBox; b += 1) boxesInColumn.push(b);
      boxIndex = nextBox;
    } else if (nextBox <= boxIndex - REVERSAL_BOXES) {
      columns.push({ direction, boxes: boxesInColumn });
      direction = FALLING_SYMBOL;
      boxesInColumn = [];
      for (let b = boxIndex - 1; b >= nextBox; b -= 1) boxesInColumn.push(b);
      boxIndex = nextBox;
    }
  } else if (nextBox < boxIndex) {
    for (let b = boxIndex - 1; b >= nextBox; b -= 1) boxesInColumn.push(b);
    boxIndex = nextBox;
  } else if (nextBox >= boxIndex + REVERSAL_BOXES) {
    columns.push({ direction, boxes: boxesInColumn });
    direction = RISING_SYMBOL;
    boxesInColumn = [];
    for (let b = boxIndex + 1; b <= nextBox; b += 1) boxesInColumn.push(b);
    boxIndex = nextBox;
  }
}
columns.push({ direction: String(direction), boxes: boxesInColumn });

const allBoxes = columns.flatMap((column) => column.boxes);
const minBox = Math.min(...allBoxes);
const maxBox = Math.max(...allBoxes);
const yMinBox = minBox - Y_PAD_BOXES;
const yMaxBox = maxBox + Y_PAD_BOXES;
const columnIndices = columns.map((_, index) => index + 1);

// Box lattice: one horizontal rule between every pair of price rows
const gridRows: number[] = [];
for (let box = yMinBox; box < yMaxBox; box += 1) {
  gridRows.push(box + 0.5);
}

interface TrendLine {
  startIndex: number;
  startBox: number;
  endIndex: number;
  endBox: number;
}

const supportLines: TrendLine[] = [];
const resistanceLines: TrendLine[] = [];
for (let i = 1; i < columns.length; i += 1) {
  const column = columns[i];
  const prevColumn = columns[i - 1];
  if (column.direction === RISING_SYMBOL && prevColumn.direction === FALLING_SYMBOL) {
    // Drawn one box below the low so the line runs through empty boxes
    const startBox = Math.min(...column.boxes) - 1;
    let endIndex = i;
    for (let j = i + 1; j < columns.length; j += 1) {
      const projected = startBox + (j - i);
      if (columns[j].direction === FALLING_SYMBOL && Math.min(...columns[j].boxes) <= projected)
        break;
      endIndex = j;
    }
    if (endIndex - i >= MIN_TREND_SPAN) {
      supportLines.push({ startIndex: i, startBox, endIndex, endBox: startBox + (endIndex - i) });
    }
  }
  if (column.direction === FALLING_SYMBOL && prevColumn.direction === RISING_SYMBOL) {
    // Drawn one box above the high so the line runs through empty boxes
    const startBox = Math.max(...column.boxes) + 1;
    let endIndex = i;
    for (let j = i + 1; j < columns.length; j += 1) {
      const projected = startBox - (j - i);
      if (columns[j].direction === RISING_SYMBOL && Math.max(...columns[j].boxes) >= projected)
        break;
      endIndex = j;
    }
    if (endIndex - i >= MIN_TREND_SPAN) {
      resistanceLines.push({
        startIndex: i,
        startBox,
        endIndex,
        endBox: startBox - (endIndex - i),
      });
    }
  }
}

const risingColor = t.palette[0];
const fallingColor = t.palette[4];

function PointAndFigureOverlay() {
  const xScale = useXScale("columns") as unknown as ((c: number) => number) & {
    bandwidth: () => number;
    range: () => [number, number];
  };
  const yScale = useYScale("price") as unknown as (v: number) => number;

  const [left, right] = xScale.range();
  const half = xScale.bandwidth() / 2;
  const rowHeight = Math.abs(yScale(1) - yScale(0));
  const glyphFontSize = Math.max(14, Math.min(xScale.bandwidth() * 0.62, rowHeight * 0.82, 22));

  return (
    <g>
      {gridRows.map((box) => (
        <line
          key={`grid-${box}`}
          x1={left}
          x2={right}
          y1={yScale(box)}
          y2={yScale(box)}
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      {supportLines.map((line, index) => (
        <line
          key={`support-${index}`}
          x1={xScale(line.startIndex + 1) + half}
          y1={yScale(line.startBox)}
          x2={xScale(line.endIndex + 1) + half}
          y2={yScale(line.endBox)}
          stroke={risingColor}
          strokeWidth={1.5}
          strokeDasharray="7 4"
          strokeOpacity={0.6}
        />
      ))}
      {resistanceLines.map((line, index) => (
        <line
          key={`resistance-${index}`}
          x1={xScale(line.startIndex + 1) + half}
          y1={yScale(line.startBox)}
          x2={xScale(line.endIndex + 1) + half}
          y2={yScale(line.endBox)}
          stroke={fallingColor}
          strokeWidth={1.5}
          strokeDasharray="7 4"
          strokeOpacity={0.6}
        />
      ))}
      <g style={{ fontWeight: 700 }}>
        {columns.map((column, columnIndex) => {
          const cx = xScale(columnIndex + 1) + half;
          const color = column.direction === RISING_SYMBOL ? risingColor : fallingColor;
          return column.boxes.map((box) => (
            <text
              key={`${columnIndex}-${box}`}
              x={cx}
              y={yScale(box)}
              fontSize={glyphFontSize}
              fill={color}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {column.direction}
            </text>
          ));
        })}
      </g>
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 44, bottom: 20, left: 16 };
  const headerHeight = 56;
  const chartWidth = size.width - padding.left - padding.right;
  const chartHeight = size.height - padding.top - padding.bottom - headerHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        backgroundColor: t.pageBg,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          mb: "18px",
        }}
      >
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1 }}>
          {TITLE}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Typography sx={{ fontSize: 16, fontWeight: 700, color: risingColor, lineHeight: 1 }}>
              {RISING_SYMBOL}
            </Typography>
            <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
              {RISING_LABEL}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Typography sx={{ fontSize: 16, fontWeight: 700, color: fallingColor, lineHeight: 1 }}>
              {FALLING_SYMBOL}
            </Typography>
            <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
              {FALLING_LABEL}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <svg width="20" height="14" aria-hidden="true">
              <line
                x1="2"
                y1="12"
                x2="18"
                y2="2"
                stroke={risingColor}
                strokeWidth={2}
                strokeDasharray="4 3"
                strokeOpacity={0.75}
              />
            </svg>
            <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
              {SUPPORT_LABEL}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <svg width="20" height="14" aria-hidden="true">
              <line
                x1="2"
                y1="2"
                x2="18"
                y2="12"
                stroke={fallingColor}
                strokeWidth={2}
                strokeDasharray="4 3"
                strokeOpacity={0.75}
              />
            </svg>
            <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
              {RESISTANCE_LABEL}
            </Typography>
          </Box>
        </Box>
      </Box>
      <ChartsContainer
        width={chartWidth}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 10, right: 16, bottom: 12, left: 12 }}
        xAxis={[
          {
            id: "columns",
            scaleType: "band",
            data: columnIndices,
            categoryGapRatio: 0.12,
            height: 56,
            label: X_TITLE,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelInterval: (_value, index) => index % TICK_EVERY_N_COLS === 0,
          },
        ]}
        yAxis={[
          {
            id: "price",
            scaleType: "linear",
            min: yMinBox,
            max: yMaxBox,
            width: 82,
            label: CLOSE,
            labelStyle: { fontSize: 15, fill: t.ink },
            valueFormatter: (boxValue: number) => (Number(boxValue) * BOX_SIZE).toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickNumber: 10,
          },
        ]}
      >
        <PointAndFigureOverlay />
        <ChartsXAxis axisId="columns" />
        <ChartsYAxis axisId="price" />
      </ChartsContainer>
    </Box>
  );
}
