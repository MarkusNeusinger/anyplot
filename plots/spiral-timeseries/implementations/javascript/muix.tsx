// anyplot.ai
// spiral-timeseries: Spiral Time Series Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-09
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAYS_PER_YEAR = 365;
const R_MAX = 1;
const R_INNER = 0.14;
const MONTH_LABELS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];
const TITLE_HEIGHT = 70;
const LEGEND_WIDTH = 150;
const BASE_MARGIN = 60;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const VALUE = "Daily Mean Temperature (°C)"; // role: value
const CYCLE_PERIOD = "year"; // role: cycle_period

// Data: replace this block with your own records
const numYearsGen = 5;
const totalDaysGen = DAYS_PER_YEAR * numYearsGen;
const startYearGen = 2020;
const baseTempC = 14;
const seasonalAmpC = 13;
const warmingPerYearC = 0.35;
const noiseAmpC = 3.5;

let lcgState = 42;
const data: Array<Record<string, string | number>> = [];
for (let day = 0; day < totalDaysGen; day++) {
  const dayOfYear = day % DAYS_PER_YEAR;
  const yearIndex = Math.floor(day / DAYS_PER_YEAR);
  const year = startYearGen + yearIndex;
  const seasonal =
    -Math.cos((2 * Math.PI * dayOfYear) / DAYS_PER_YEAR) * seasonalAmpC;
  const trend = warmingPerYearC * yearIndex;
  lcgState = (lcgState * 1103515245 + 12345) % 2147483648;
  const u = lcgState / 2147483648;
  const noise = (u - 0.5) * noiseAmpC;
  data.push({
    [DATE]: `${year}-D${String(dayOfYear + 1).padStart(3, "0")}`,
    [VALUE]: baseTempC + seasonal + trend + noise,
  });
}

// Plot: reads only data and the constants above
const cycleSpan = CYCLE_PERIOD === "year" ? DAYS_PER_YEAR : 30;
const numCycles = Math.max(1, Math.round(data.length / cycleSpan));
const revGap = (R_MAX - R_INNER) / numCycles;

const values = data.map((row) => Number(row[VALUE]));
const vMin = Math.min(...values);
const vMax = Math.max(...values);

const spiralPoints = data.map((row, idx) => {
  const value = Number(row[VALUE]);
  const revolutions = idx / cycleSpan;
  const angle = Math.PI / 2 - 2 * Math.PI * revolutions;
  const radius = R_INNER + revGap * revolutions;
  return {
    x: radius * Math.cos(angle),
    y: radius * Math.sin(angle),
    value,
    dateStr: String(row[DATE]),
  };
});

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

const cycleStartPoints = Array.from({ length: numCycles }, (_, k) => {
  const rowIdx = k * cycleSpan;
  const labelStr = String(data[rowIdx][DATE]).slice(0, 4);
  return {
    x: 0,
    y: R_INNER + revGap * k,
    id: k,
    yearLabel: labelStr,
  };
});

const cycleStartSeries = [
  {
    type: "scatter" as const,
    id: "cycle-start",
    label: "Cycle start (year)",
    color: t.ink,
    markerSize: 6,
    data: cycleStartPoints,
    valueFormatter: (point: { yearLabel?: string } | null) =>
      point?.yearLabel ? `${point.yearLabel}` : "",
  },
];

function SpiralPath() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  const segments = [];
  for (let i = 1; i < spiralPoints.length; i++) {
    const a = spiralPoints[i - 1];
    const b = spiralPoints[i];
    const segValue = (a.value + b.value) / 2;
    const ratio = Math.min(1, Math.max(0, (segValue - vMin) / (vMax - vMin)));
    const r = Math.round(seqR1 + (seqR2 - seqR1) * ratio);
    const g = Math.round(seqG1 + (seqG2 - seqG1) * ratio);
    const bl = Math.round(seqB1 + (seqB2 - seqB1) * ratio);
    const strokeW = 2 + ratio * 3.5;
    segments.push(
      <line
        key={i}
        x1={xScale(a.x)}
        y1={yScale(a.y)}
        x2={xScale(b.x)}
        y2={yScale(b.y)}
        stroke={`rgb(${r}, ${g}, ${bl})`}
        strokeWidth={strokeW}
        strokeLinecap="round"
      />,
    );
  }
  return <g>{segments}</g>;
}

function CycleGrid() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const originX = xScale(0);
  const originY = yScale(0);

  return (
    <g>
      {MONTH_LABELS.map((label, m) => {
        const angle = Math.PI / 2 - (m / 12) * 2 * Math.PI;
        const spokeInnerX = xScale(R_INNER * 0.85 * Math.cos(angle));
        const spokeInnerY = yScale(R_INNER * 0.85 * Math.sin(angle));
        const tickOuterX = xScale(R_MAX * 1.03 * Math.cos(angle));
        const tickOuterY = yScale(R_MAX * 1.03 * Math.sin(angle));
        const labelX = xScale(R_MAX * 1.1 * Math.cos(angle));
        const labelY = yScale(R_MAX * 1.1 * Math.sin(angle));
        const dx = labelX - originX;
        const dy = labelY - originY;
        const dist = Math.hypot(dx, dy) || 1;
        const ux = dx / dist;
        const uy = dy / dist;
        return (
          <g key={label}>
            <line
              x1={spokeInnerX}
              y1={spokeInnerY}
              x2={tickOuterX}
              y2={tickOuterY}
              stroke={t.grid}
              strokeWidth={1}
              strokeDasharray="3 4"
            />
            <ChartsText
              x={labelX}
              y={labelY}
              text={label}
              style={{
                fontSize: 14,
                fill: t.inkSoft,
                textAnchor:
                  ux >= 0.3 ? "start" : ux <= -0.3 ? "end" : "middle",
                dominantBaseline:
                  uy >= 0.3 ? "hanging" : uy <= -0.3 ? "auto" : "central",
              }}
            />
          </g>
        );
      })}
    </g>
  );
}

function CycleStartLabels() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  return (
    <g>
      {cycleStartPoints.map((point) => (
        <ChartsText
          key={point.id}
          x={xScale(point.x) + 16}
          y={yScale(point.y)}
          text={point.yearLabel}
          style={{
            fontSize: 15,
            fontWeight: 600,
            fill: t.ink,
            dominantBaseline: "central",
          }}
        />
      ))}
    </g>
  );
}

function ColorLegend() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;
  const legendX = window.ANYPLOT_SIZE.width - LEGEND_WIDTH + 40;
  const legendTop = BASE_MARGIN + 20;
  const legendBottom = chartHeight - BASE_MARGIN - 20;
  const barWidth = 22;

  return (
    <g>
      <defs>
        <linearGradient id="spiralTempScale" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.seq[1]} />
          <stop offset="100%" stopColor={t.seq[0]} />
        </linearGradient>
      </defs>
      <ChartsText
        x={legendX + barWidth / 2}
        y={legendTop - 22}
        text="Avg Temp"
        style={{
          fontSize: 14,
          fontWeight: 600,
          fill: t.ink,
          textAnchor: "middle",
        }}
      />
      <rect
        x={legendX}
        y={legendTop}
        width={barWidth}
        height={legendBottom - legendTop}
        fill="url(#spiralTempScale)"
        rx={3}
      />
      <ChartsText
        x={legendX + barWidth + 10}
        y={legendTop}
        text={`${Math.round(vMax)}°C`}
        style={{ fontSize: 14, fill: t.inkSoft, dominantBaseline: "hanging" }}
      />
      <ChartsText
        x={legendX + barWidth + 10}
        y={(legendTop + legendBottom) / 2}
        text={`${Math.round((vMin + vMax) / 2)}°C`}
        style={{ fontSize: 14, fill: t.inkSoft, dominantBaseline: "central" }}
      />
      <ChartsText
        x={legendX + barWidth + 10}
        y={legendBottom}
        text={`${Math.round(vMin)}°C`}
        style={{ fontSize: 14, fill: t.inkSoft, dominantBaseline: "auto" }}
      />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;
  const availableWidth = width - LEGEND_WIDTH;
  const squareSide = chartHeight - 2 * BASE_MARGIN;
  const sideMargin = (availableWidth - squareSide) / 2;
  const margin = {
    top: BASE_MARGIN,
    bottom: BASE_MARGIN,
    left: sideMargin,
    right: sideMargin + LEGEND_WIDTH,
  };

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        Five-Year Daily Temperature Spiral · spiral-timeseries · javascript · muix · anyplot.ai
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={margin}
        series={cycleStartSeries}
        xAxis={[
          {
            scaleType: "linear",
            min: -R_MAX * 1.2,
            max: R_MAX * 1.2,
            position: "none",
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: -R_MAX * 1.2,
            max: R_MAX * 1.2,
            position: "none",
          },
        ]}
      >
        <CycleGrid />
        <SpiralPath />
        <ScatterPlot skipAnimation />
        <CycleStartLabels />
        <ColorLegend />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
    </div>
  );
}
