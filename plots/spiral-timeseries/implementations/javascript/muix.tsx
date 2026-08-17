//# anyplot-orientation: square
// anyplot.ai
// spiral-timeseries: Spiral Time Series Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-17
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

const t = window.ANYPLOT_TOKENS;
const TITLE = "spiral-timeseries · javascript · muix · anyplot.ai";

// Deterministic LCG — reproducible daily noise without a seeded global RNG.
function makeLcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}
const rng = makeLcg(1729);

// --- Data (in-memory, deterministic): daily average temperature, 5 years ----
// Each full revolution of the Archimedean spiral is one calendar year, so
// the same season lands in the same angular position across every ring.
const YEARS = [2019, 2020, 2021, 2022, 2023];
const DAYS_PER_YEAR = 365;
const TOTAL_DAYS = YEARS.length * DAYS_PER_YEAR; // 1825 points, 5 cycles
const MONTHS = [
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

const rawPoints = [];
let minValue = Infinity;
let maxValue = -Infinity;
for (let i = 0; i < TOTAL_DAYS; i += 1) {
  const yearIdx = Math.floor(i / DAYS_PER_YEAR);
  const dayOfYear = i % DAYS_PER_YEAR;
  const yearFrac = i / DAYS_PER_YEAR; // continuous 0..5 — drives both angle and radius
  const seasonal = -Math.cos((2 * Math.PI * dayOfYear) / DAYS_PER_YEAR); // -1 mid-winter, +1 mid-summer
  const warmingTrend = yearIdx * 0.4; // slight year-over-year drift
  const noise = (rng() - 0.5) * 4.5;
  const value = 11 + 13 * seasonal + warmingTrend + noise;
  minValue = Math.min(minValue, value);
  maxValue = Math.max(maxValue, value);
  rawPoints.push({ yearFrac, value });
}

// 0deg = 12 o'clock, positive = clockwise (matches PieChart's own arc convention).
function polarPoint(cx, cy, radius, angleDeg) {
  const angleRad = (angleDeg * Math.PI) / 180;
  return [cx + radius * Math.sin(angleRad), cy - radius * Math.cos(angleRad)];
}

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 72;
  const legendHeight = 90;
  // The circular spiral lives in a "side"-wide square; the chart box itself
  // is taller by `legendHeight` so the continuous color legend has its own
  // reserved strip below the rings instead of overlapping the outermost year.
  const side = Math.min(width, height - titleHeight - legendHeight);
  const chartHeight = side + legendHeight;
  const boxLeft = (width - side) / 2;
  const cxGlobal = boxLeft + side / 2;
  const cyGlobal = titleHeight + side / 2;
  const cxLocal = side / 2;
  const cyLocal = side / 2;

  const outerMargin = side * 0.105; // room for month spokes + labels beyond the spiral
  const maxRadius = side / 2 - outerMargin;
  const innerRadius = maxRadius * 0.09;
  const numCycles = YEARS.length;
  const growth = (maxRadius - innerRadius) / numCycles;

  // Spiral geometry: radius and angle both grow continuously with elapsed
  // time, so consecutive points never jump at a year boundary — the spiral
  // simply keeps winding outward (Archimedean: constant spacing per turn).
  const xPixel = [];
  const scatterPoints = [];
  const lineY = [];
  rawPoints.forEach((p, i) => {
    const radius = innerRadius + growth * p.yearFrac;
    const angleDeg = 360 * (p.yearFrac - Math.floor(p.yearFrac));
    const [x, y] = polarPoint(cxLocal, cyLocal, radius, angleDeg);
    xPixel.push(x);
    lineY.push(y);
    scatterPoints.push({ id: `pt${i}`, x, y, z: p.value });
  });

  // Text alignment for labels placed around the spiral's circumference —
  // flip anchor/baseline by quadrant so labels never run back over the rings.
  function radialLabelAnchor(angleDeg) {
    const norm = ((angleDeg % 360) + 360) % 360;
    if (norm < 1 || norm > 359) return { anchor: "middle", baseline: "auto" };
    if (Math.abs(norm - 180) < 1)
      return { anchor: "middle", baseline: "hanging" };
    return {
      anchor: norm > 0 && norm < 180 ? "start" : "end",
      baseline: "middle",
    };
  }

  return (
    <div style={{ position: "relative", width, height }}>
      {/* Radial grid layer — rendered first so it sits behind the spiral data. */}
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {Array.from({ length: numCycles }, (_, k) => k + 1).map((k) => (
          <circle
            key={`ring-${k}`}
            cx={cxGlobal}
            cy={cyGlobal}
            r={innerRadius + growth * k}
            fill="none"
            stroke={t.grid}
            strokeWidth={1.25}
          />
        ))}
        {MONTHS.map((_, i) => {
          const [x2, y2] = polarPoint(cxGlobal, cyGlobal, maxRadius, i * 30);
          return (
            <line
              key={`spoke-${i}`}
              x1={cxGlobal}
              y1={cyGlobal}
              x2={x2}
              y2={y2}
              stroke={t.grid}
              strokeWidth={1}
            />
          );
        })}
      </svg>

      {/* Colored spiral: a thin neutral guide line threads the points in
          chronological order; marker color encodes the temperature value. */}
      <div style={{ position: "absolute", top: titleHeight, left: boxLeft }}>
        <ChartContainer
          width={side}
          height={chartHeight}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          skipAnimation
          series={[
            {
              id: "spiral-guide",
              type: "line",
              data: lineY,
              xAxisId: "x",
              yAxisId: "y",
              color: t.grid,
              curve: "linear",
              showMark: false,
            },
            {
              id: "spiral-points",
              type: "scatter",
              data: scatterPoints,
              xAxisId: "x",
              yAxisId: "y",
              zAxisId: "value",
              markerSize: 3.2,
            },
          ]}
          xAxis={[
            { id: "x", scaleType: "linear", min: 0, max: side, data: xPixel },
          ]}
          yAxis={[
            {
              id: "y",
              scaleType: "linear",
              min: 0,
              max: chartHeight,
              reverse: true,
            },
          ]}
          zAxis={[
            {
              id: "value",
              min: minValue,
              max: maxValue,
              colorMap: {
                type: "continuous",
                min: minValue,
                max: maxValue,
                color: [t.seq[0], t.seq[1]],
              },
            },
          ]}
        >
          <LinePlot skipAnimation slotProps={{ line: { strokeWidth: 1.5 } }} />
          <ScatterPlot />
          <ContinuousColorLegend
            axisId="value"
            axisDirection="z"
            position={{ horizontal: "middle", vertical: "bottom" }}
            direction="row"
            length="55%"
            thickness={14}
            minLabel={`${Math.round(minValue)}°C`}
            maxLabel={`${Math.round(maxValue)}°C`}
            labelStyle={{
              fontSize: 15,
              fill: t.inkSoft,
              fontFamily: "inherit",
            }}
          />
        </ChartContainer>
      </div>

      {/* Text layer — rendered last so title, month spokes and year rings
          are never hidden behind the dense scatter of colored points. */}
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <text
          x={width / 2}
          y={34}
          textAnchor="middle"
          fontSize={22}
          fontWeight={500}
          fill={t.ink}
        >
          {TITLE}
        </text>
        <text
          x={width / 2}
          y={58}
          textAnchor="middle"
          fontSize={15}
          fill={t.inkSoft}
        >
          Daily average temperature, {YEARS[0]}–{YEARS[YEARS.length - 1]} · one
          revolution = one year
        </text>

        {MONTHS.map((month, i) => {
          const angleDeg = i * 30;
          const [x, y] = polarPoint(
            cxGlobal,
            cyGlobal,
            maxRadius + 26,
            angleDeg,
          );
          const { anchor, baseline } = radialLabelAnchor(angleDeg);
          return (
            <text
              key={`month-${month}`}
              x={x}
              y={y}
              textAnchor={anchor}
              dominantBaseline={baseline}
              fontSize={15}
              fill={t.inkSoft}
            >
              {month}
            </text>
          );
        })}

        {YEARS.map((year, k) => {
          const radius = innerRadius + growth * (k + 0.5);
          const [x, y] = polarPoint(cxGlobal, cyGlobal, radius, -18);
          return (
            <text
              key={`year-${year}`}
              x={x}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {year}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
