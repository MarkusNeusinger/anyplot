// anyplot.ai
// box-horizontal: Horizontal Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const IQR_FENCE_MULTIPLIER = 1.5;
const X_PAD_SHARE = 0.08;
const BOX_HEIGHT_SHARE = 0.56;
const HEADER_H = 82;

// Columns: set these to your data's column names
const CATEGORIES = "Job title"; // role: categories
const VALUES = "Annual base salary ($k)"; // role: values

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const roles = [
    { title: "Senior Software Engineer", mean: 152, std: 16, size: 13, extra: 206 },
    { title: "Data Scientist", mean: 138, std: 15, size: 12 },
    { title: "Product Manager", mean: 134, std: 19, size: 11 },
    { title: "DevOps Engineer", mean: 121, std: 13, size: 12 },
    { title: "UX/UI Designer", mean: 104, std: 14, size: 11 },
    { title: "Marketing Analyst", mean: 79, std: 11, size: 11, extra: 43 },
    { title: "Customer Success Manager", mean: 73, std: 9, size: 11 },
  ];
  const rows: { [key: string]: string | number }[] = [];

  for (const role of roles) {
    for (let i = 0; i < role.size; i += 1) {
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u1 = Math.max(state / 4294967296, 1e-9);
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u2 = state / 4294967296;
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      const salary = Math.max(28, role.mean + z * role.std);
      rows.push({
        [CATEGORIES]: role.title,
        [VALUES]: Number(salary.toFixed(1)),
      });
    }
    if (role.extra !== undefined) {
      rows.push({ [CATEGORIES]: role.title, [VALUES]: role.extra });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const rawCategories: string[] = [];
for (const row of data) {
  const c = String(row[CATEGORIES]);
  if (!rawCategories.includes(c)) rawCategories.push(c);
}

const boxStats = rawCategories
  .map((title) => {
    const salaries = data
      .filter((row) => String(row[CATEGORIES]) === title)
      .map((row) => Number(row[VALUES]))
      .sort((a, b) => a - b);
    const n = salaries.length;
    const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
      const p = (n - 1) * q;
      const b = Math.floor(p);
      return b + 1 < n ? salaries[b] + (p - b) * (salaries[b + 1] - salaries[b]) : salaries[b];
    });

    const iqr = q3 - q1;
    const lowerFence = q1 - IQR_FENCE_MULTIPLIER * iqr;
    const upperFence = q3 + IQR_FENCE_MULTIPLIER * iqr;
    const inliers = salaries.filter((v) => v >= lowerFence && v <= upperFence);
    const outliers = salaries.filter((v) => v < lowerFence || v > upperFence);

    return {
      title,
      q1,
      median,
      q3,
      whiskerLow: inliers[0],
      whiskerHigh: inliers[inliers.length - 1],
      outliers,
    };
  })
  .sort((a, b) => b.median - a.median);

const categories = boxStats.map((s) => s.title);
const allValues = data.map((row) => Number(row[VALUES]));
const minVal = Math.min(...allValues);
const maxVal = Math.max(...allValues);
const valSpan = maxVal - minVal || 1;
const valueMin = minVal - valSpan * X_PAD_SHARE;
const valueMax = maxVal + valSpan * X_PAD_SHARE;

const TITLE = "box-horizontal · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations · ${categories.length} groups (${CATEGORIES}), sorted by median · Whiskers at ${IQR_FENCE_MULTIPLIER}×IQR`;

function BoxWhiskers() {
  const xScale = useXScale("salary");
  const yScale = useYScale("role");
  const bandwidth = yScale.bandwidth();
  const boxHeight = bandwidth * BOX_HEIGHT_SHARE;
  const capHeight = boxHeight * 0.65;

  return (
    <g>
      {boxStats.map((s, i) => {
        const center = yScale(s.title) + bandwidth / 2;
        const top = center - boxHeight / 2;
        const bottom = center + boxHeight / 2;
        const capTop = center - capHeight / 2;
        const capBottom = center + capHeight / 2;
        const color = t.palette[i];
        const xWhiskerLow = xScale(s.whiskerLow);
        const xWhiskerHigh = xScale(s.whiskerHigh);
        const xQ1 = xScale(s.q1);
        const xQ3 = xScale(s.q3);
        const xMedian = xScale(s.median);

        return (
          <g key={s.title}>
            <line
              x1={xWhiskerLow}
              x2={xQ1}
              y1={center}
              y2={center}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={xQ3}
              x2={xWhiskerHigh}
              y1={center}
              y2={center}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={xWhiskerLow}
              x2={xWhiskerLow}
              y1={capTop}
              y2={capBottom}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={xWhiskerHigh}
              x2={xWhiskerHigh}
              y1={capTop}
              y2={capBottom}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <rect
              x={xQ1}
              y={top}
              width={Math.max(1, xQ3 - xQ1)}
              height={boxHeight}
              rx={4}
              ry={4}
              fill={color}
              fillOpacity={0.3}
              stroke={color}
              strokeWidth={2.5}
            />
            <line
              x1={xMedian}
              x2={xMedian}
              y1={top}
              y2={bottom}
              stroke={color}
              strokeWidth={3.5}
              strokeLinecap="round"
            />
            {s.outliers.map((v, j) => (
              <circle
                key={j}
                cx={xScale(v)}
                cy={center}
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
        margin={{ top: 20, right: 48, bottom: 20, left: 36 }}
        xAxis={[
          {
            id: "salary",
            scaleType: "linear",
            min: valueMin,
            max: valueMax,
            tickNumber: 9,
            height: 64,
            label: VALUES,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "role",
            scaleType: "band",
            data: categories,
            width: 240,
            label: CATEGORIES,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": {
            stroke: t.grid,
            opacity: 0.65,
            strokeDasharray: "3 4",
          },
        }}
      >
        <ChartsGrid vertical />
        <BoxWhiskers />
        <ChartsXAxis axisId="salary" />
        <ChartsYAxis axisId="role" />
      </ChartsContainer>
    </div>
  );
}
