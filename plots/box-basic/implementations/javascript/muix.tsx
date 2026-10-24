// anyplot.ai
// box-basic: Basic Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const IQR_FENCE_MULTIPLIER = 1.5;
const Y_PAD_SHARE = 0.08;
const BOX_WIDTH_SHARE = 0.5;
const HEADER_H = 82;

// Columns: set these to your data's column names
const CATEGORY = "Course section"; // role: category
const VALUE = "Exam score (%)"; // role: value

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const sections = [
    { name: "Calculus I", mean: 78, std: 7, size: 62 },
    { name: "Linear Algebra", mean: 71, std: 13, size: 58, extra: 18 },
    { name: "Probability", mean: 85, std: 5, size: 74 },
    { name: "Differential Equations", mean: 68, std: 11, size: 55, extra: 24 },
    { name: "Numerical Analysis", mean: 80, std: 9, size: 66 },
  ];
  const rows: { [key: string]: string | number }[] = [];

  for (const sec of sections) {
    for (let i = 0; i < sec.size; i += 1) {
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u1 = Math.max(state / 4294967296, 1e-9);
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u2 = state / 4294967296;
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      const score = Math.min(100, Math.max(0, sec.mean + z * sec.std));
      rows.push({ [CATEGORY]: sec.name, [VALUE]: Number(score.toFixed(2)) });
    }
    if (sec.extra !== undefined) {
      rows.push({ [CATEGORY]: sec.name, [VALUE]: sec.extra });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const categories: string[] = [];
for (const row of data) {
  const c = String(row[CATEGORY]);
  if (!categories.includes(c)) categories.push(c);
}

const boxStats = categories.map((name) => {
  const scores = data
    .filter((row) => String(row[CATEGORY]) === name)
    .map((row) => Number(row[VALUE]))
    .sort((a, b) => a - b);
  const n = scores.length;

  const [q1, median, q3] = [0.25, 0.5, 0.75].map((p) => {
    const pos = (n - 1) * p;
    const base = Math.floor(pos);
    return base + 1 < n
      ? scores[base] + (pos - base) * (scores[base + 1] - scores[base])
      : scores[base];
  });

  const iqr = q3 - q1;
  const lowerFence = q1 - IQR_FENCE_MULTIPLIER * iqr;
  const upperFence = q3 + IQR_FENCE_MULTIPLIER * iqr;
  const inliers = scores.filter((s) => s >= lowerFence && s <= upperFence);
  const outliers = scores.filter((s) => s < lowerFence || s > upperFence);

  return {
    name,
    q1,
    median,
    q3,
    whiskerLow: inliers[0],
    whiskerHigh: inliers[inliers.length - 1],
    outliers,
  };
});

const allValues = data.map((row) => Number(row[VALUE]));
const minVal = Math.min(...allValues);
const maxVal = Math.max(...allValues);
const valSpan = maxVal - minVal || 1;
const yMin = minVal - valSpan * Y_PAD_SHARE;
const yMax = maxVal + valSpan * Y_PAD_SHARE;

const totalOutliers = boxStats.reduce((sum, s) => sum + s.outliers.length, 0);
const TITLE = "box-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations · ${CATEGORY}: ${categories.length} · Whiskers at ${IQR_FENCE_MULTIPLIER}×IQR · ${totalOutliers} outliers`;

function BoxWhiskers() {
  const xScale = useXScale("classes");
  const yScale = useYScale("scores");
  const bandwidth = xScale.bandwidth();
  const boxWidth = bandwidth * BOX_WIDTH_SHARE;
  const capWidth = boxWidth * 0.65;

  return (
    <g>
      {boxStats.map((s, i) => {
        const center = xScale(s.name) + bandwidth / 2;
        const left = center - boxWidth / 2;
        const right = center + boxWidth / 2;
        const capLeft = center - capWidth / 2;
        const capRight = center + capWidth / 2;
        const color = t.palette[i];
        const yWhiskerHigh = yScale(s.whiskerHigh);
        const yWhiskerLow = yScale(s.whiskerLow);
        const yQ3 = yScale(s.q3);
        const yQ1 = yScale(s.q1);
        const yMedian = yScale(s.median);

        return (
          <g key={s.name}>
            <line
              x1={center}
              x2={center}
              y1={yWhiskerHigh}
              y2={yQ3}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={center}
              x2={center}
              y1={yQ1}
              y2={yWhiskerLow}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={capLeft}
              x2={capRight}
              y1={yWhiskerHigh}
              y2={yWhiskerHigh}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={capLeft}
              x2={capRight}
              y1={yWhiskerLow}
              y2={yWhiskerLow}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <rect
              x={left}
              y={yQ3}
              width={boxWidth}
              height={Math.max(1, yQ1 - yQ3)}
              rx={4}
              ry={4}
              fill={color}
              fillOpacity={0.3}
              stroke={color}
              strokeWidth={2.5}
            />
            <line
              x1={left}
              x2={right}
              y1={yMedian}
              y2={yMedian}
              stroke={color}
              strokeWidth={3.5}
              strokeLinecap="round"
            />
            {s.outliers.map((v, j) => (
              <circle
                key={j}
                cx={center}
                cy={yScale(v)}
                r={5.5}
                fill={t.pageBg}
                stroke={color}
                strokeWidth={2.2}
              />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - HEADER_H;

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, right: 40, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "classes",
            data: categories,
            scaleType: "band",
            height: 64,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "scores",
            min: yMin,
            max: yMax,
            tickNumber: 9,
            width: 84,
            label: VALUE,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": {
            stroke: t.grid,
            opacity: 0.7,
            strokeDasharray: "3 4",
          },
        }}
      >
        <ChartsGrid horizontal />
        <BoxWhiskers />
        <ChartsXAxis axisId="classes" />
        <ChartsYAxis axisId="scores" />
      </ChartsContainer>
    </div>
  );
}
