// anyplot.ai
// raincloud-basic: Basic Raincloud Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "raincloud-basic · javascript · muix · anyplot.ai";
const GRID_N = 140;
const JITTER_SEED = 198472;

// Columns: set these to your data's column names
const CATEGORY = "Treatment arm"; // role: category
const VALUE = "Reaction Time (ms)"; // role: value

// Data: replace this block with your own records
const GROUP_SPECS = [
  { name: "Placebo", n: 70, meanA: 540, stdA: 55, mixProb: 1.0, meanB: 540, stdB: 55 },
  { name: "10 mg Dose", n: 70, meanA: 495, stdA: 50, mixProb: 1.0, meanB: 495, stdB: 50 },
  { name: "25 mg Dose", n: 70, meanA: 445, stdA: 48, mixProb: 1.0, meanB: 445, stdB: 48 },
  { name: "50 mg Dose", n: 70, meanA: 360, stdA: 35, mixProb: 0.55, meanB: 470, stdB: 40 },
];

let dataSeed = 42;
const data = [];
for (const group of GROUP_SPECS) {
  for (let i = 0; i < group.n; i += 1) {
    let branchProb = 0;
    if (group.mixProb < 1.0) {
      dataSeed = (dataSeed * 1664525 + 1013904223) >>> 0;
      branchProb = dataSeed / 4294967296;
    }
    dataSeed = (dataSeed * 1664525 + 1013904223) >>> 0;
    const u1 = Math.max(dataSeed / 4294967296, 1e-9);
    dataSeed = (dataSeed * 1664525 + 1013904223) >>> 0;
    const u2 = dataSeed / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const val =
      group.mixProb < 1.0 && branchProb >= group.mixProb
        ? group.meanB + group.stdB * z
        : group.meanA + group.stdA * z;
    data.push({ [CATEGORY]: group.name, [VALUE]: val });
  }
}

// Plot: reads only data and the constants above
const categories = Array.from(new Set(data.map((row) => String(row[CATEGORY]))));
const valuesByCategory = categories.map((cat) =>
  data.filter((row) => String(row[CATEGORY]) === cat).map((row) => Number(row[VALUE]))
);

let jitterState = JITTER_SEED >>> 0;
const jittersByCategory = valuesByCategory.map((values) =>
  values.map(() => {
    jitterState = (jitterState * 1664525 + 1013904223) >>> 0;
    return jitterState / 4294967296;
  })
);

const allValues = valuesByCategory.flat();
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const xPad = (dataMax - dataMin) * 0.08;
const xMin = dataMin - xPad;
const xMax = dataMax + xPad;

const statsByCategory = valuesByCategory.map((values) => {
  const sorted = [...values].sort((a, b) => a - b);
  const lastIdx = sorted.length - 1;
  const q1Pos = lastIdx * 0.25;
  const q1Base = Math.floor(q1Pos);
  const q1 =
    sorted[q1Base + 1] !== undefined
      ? sorted[q1Base] + (q1Pos - q1Base) * (sorted[q1Base + 1] - sorted[q1Base])
      : sorted[q1Base];
  const medPos = lastIdx * 0.5;
  const medBase = Math.floor(medPos);
  const median =
    sorted[medBase + 1] !== undefined
      ? sorted[medBase] + (medPos - medBase) * (sorted[medBase + 1] - sorted[medBase])
      : sorted[medBase];
  const q3Pos = lastIdx * 0.75;
  const q3Base = Math.floor(q3Pos);
  const q3 =
    sorted[q3Base + 1] !== undefined
      ? sorted[q3Base] + (q3Pos - q3Base) * (sorted[q3Base + 1] - sorted[q3Base])
      : sorted[q3Base];
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const lowerWhisker = sorted.find((v) => v >= lowerFence) ?? sorted[0];
  const upperWhisker = [...sorted].reverse().find((v) => v <= upperFence) ?? sorted[lastIdx];
  return { q1, median, q3, lowerWhisker, upperWhisker };
});

const grid = Array.from({ length: GRID_N }, (_, k) => xMin + (k * (xMax - xMin)) / (GRID_N - 1));
const densityByCategory = valuesByCategory.map((values) => {
  const n = values.length;
  const m = values.reduce((a, b) => a + b, 0) / n;
  const variance = values.reduce((a, b) => a + (b - m) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);
  const bandwidth = 0.9 * std * Math.pow(n, -0.2);
  const raw = grid.map((gx) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gx - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  return raw.map((v) => v / peak);
});

function RaincloudLayer() {
  const xScale = useXScale("value");
  const yScale = useYScale("category");
  const { left, top, width: drawW, height } = useDrawingArea();
  const ticks = xScale.ticks ? xScale.ticks(8) : [];
  const titleSize = TITLE.length > 67 ? Math.round(22 * (67 / TITLE.length)) : 22;

  return (
    <g>
      <text x={left + drawW / 2} y={top - 46} textAnchor="middle" fontSize={titleSize} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>

      {ticks.map((tick) => (
        <line key={tick} x1={xScale(tick)} x2={xScale(tick)} y1={top} y2={top + height} stroke={t.grid} strokeWidth={1} />
      ))}

      {categories.map((cat, i) => {
        const color = t.palette[i % t.palette.length];
        const bandWidth = yScale.bandwidth();
        const baselineY = yScale(cat) + bandWidth / 2;
        const halfBand = bandWidth / 2;
        const cloudPeakPx = halfBand * 0.82;
        const rainNear = halfBand * 0.2;
        const rainFar = halfBand * 0.92;
        const boxHalfHeight = Math.min(11, halfBand * 0.18);

        const density = densityByCategory[i];
        const cloudPoints = grid.map((gx, k) => `${xScale(gx)},${baselineY - density[k] * cloudPeakPx}`);
        const cloudPath = `M${xScale(grid[0])},${baselineY} L${cloudPoints.join(" L")} L${xScale(grid[GRID_N - 1])},${baselineY} Z`;

        const { q1, median, q3, lowerWhisker, upperWhisker } = statsByCategory[i];
        const boxTop = baselineY - boxHalfHeight;
        const boxBottom = baselineY + boxHalfHeight;

        return (
          <g key={cat}>
            <path d={cloudPath} fill={color} fillOpacity={0.5} stroke={color} strokeOpacity={0.7} strokeWidth={1} />
            {valuesByCategory[i].map((v, j) => (
              <circle
                key={j}
                cx={xScale(v)}
                cy={baselineY + rainNear + jittersByCategory[i][j] * (rainFar - rainNear)}
                r={4}
                fill={color}
                fillOpacity={0.55}
                stroke={t.pageBg}
                strokeWidth={0.75}
              />
            ))}
            <line x1={xScale(lowerWhisker)} x2={xScale(upperWhisker)} y1={baselineY} y2={baselineY} stroke={t.ink} strokeWidth={1.5} />
            <line
              x1={xScale(lowerWhisker)}
              x2={xScale(lowerWhisker)}
              y1={baselineY - boxHalfHeight * 0.8}
              y2={baselineY + boxHalfHeight * 0.8}
              stroke={t.ink}
              strokeWidth={1.5}
            />
            <line
              x1={xScale(upperWhisker)}
              x2={xScale(upperWhisker)}
              y1={baselineY - boxHalfHeight * 0.8}
              y2={baselineY + boxHalfHeight * 0.8}
              stroke={t.ink}
              strokeWidth={1.5}
            />
            <rect
              x={xScale(q1)}
              y={boxTop}
              width={xScale(q3) - xScale(q1)}
              height={boxHalfHeight * 2}
              fill={t.elevatedBg}
              stroke={t.ink}
              strokeWidth={1.25}
              rx={2}
            />
            <line x1={xScale(median)} x2={xScale(median)} y1={boxTop} y2={boxBottom} stroke={t.ink} strokeWidth={2.2} />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <ChartsContainer
      width={width}
      height={height}
      skipAnimation
      series={[]}
      xAxis={[
        {
          id: "value",
          scaleType: "linear",
          min: xMin,
          max: xMax,
          height: 64,
          label: VALUE,
          labelStyle: { fontSize: 16 },
          tickLabelStyle: { fontSize: 14 },
        },
      ]}
      yAxis={[
        {
          id: "category",
          scaleType: "band",
          data: categories,
          width: 120,
          categoryGapRatio: 0.35,
          tickLabelStyle: { fontSize: 15 },
        },
      ]}
      margin={{ top: 110, right: 70, bottom: 32, left: 60 }}
    >
      <RaincloudLayer />
      <ChartsXAxis axisId="value" position="bottom" />
      <ChartsYAxis axisId="category" position="left" disableTicks disableLine />
    </ChartsContainer>
  );
}
