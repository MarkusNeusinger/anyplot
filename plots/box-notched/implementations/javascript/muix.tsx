// anyplot.ai
// box-notched: Notched Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-18
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const IQR_FENCE_MULTIPLIER = 1.5;
const NOTCH_FACTOR = 1.57;
const Y_PAD_SHARE = 0.08;
const BOX_WIDTH_SHARE = 0.55;
const NOTCH_INSET_SHARE = 0.28;
const HEADER_H = 82;

// Columns: set these to your data's column names
const CATEGORY = "Department"; // role: category
const VALUE = "Annual salary ($k)"; // role: value

// Data: replace this block with your own records, one object per row
const data = (() => {
  let seed = 42;
  const deptSpecs = [
    { name: "Engineering", n: 55, mean: 92, sd: 14, extra: 136 },
    { name: "Finance", n: 45, mean: 88, sd: 11 },
    { name: "Sales", n: 60, mean: 74, sd: 16, extra: 31 },
    { name: "Marketing", n: 42, mean: 68, sd: 9 },
    { name: "Customer Support", n: 38, mean: 58, sd: 7, extra: 36 },
  ];
  const rows: { [key: string]: string | number }[] = [];

  for (const spec of deptSpecs) {
    for (let i = 0; i < spec.n; i += 1) {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      const u1 = Math.max(seed / 0x7fffffff, 1e-9);
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      const u2 = seed / 0x7fffffff;
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      const val = Math.max(28, spec.mean + spec.sd * z);
      rows.push({
        [CATEGORY]: spec.name,
        [VALUE]: Number(val.toFixed(2)),
      });
    }
    if (spec.extra !== undefined) {
      rows.push({ [CATEGORY]: spec.name, [VALUE]: spec.extra });
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

const salaryGroups = categories.map((name) => {
  const sorted = data
    .filter((row) => String(row[CATEGORY]) === name)
    .map((row) => Number(row[VALUE]))
    .sort((a, b) => a - b);
  const n = sorted.length;
  const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
    const p = (n - 1) * q;
    const b = Math.floor(p);
    return b + 1 < n ? sorted[b] + (p - b) * (sorted[b + 1] - sorted[b]) : sorted[b];
  });

  const iqr = q3 - q1;
  const lowerFence = q1 - IQR_FENCE_MULTIPLIER * iqr;
  const upperFence = q3 + IQR_FENCE_MULTIPLIER * iqr;
  const inliers = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  const outliers = sorted.filter((v) => v < lowerFence || v > upperFence);
  const notch = (NOTCH_FACTOR * iqr) / Math.sqrt(n);

  return {
    name,
    stats: {
      n,
      q1,
      median,
      q3,
      whiskerLow: inliers[0],
      whiskerHigh: inliers[inliers.length - 1],
      outliers,
      notch,
    },
  };
});

const allValues = data.map((row) => Number(row[VALUE]));
const minVal = Math.min(...allValues);
const maxVal = Math.max(...allValues);
const valSpan = maxVal - minVal || 1;
const yMin = minVal - valSpan * Y_PAD_SHARE;
const yMax = maxVal + valSpan * Y_PAD_SHARE;

const TITLE = "box-notched · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations · ${categories.length} groups (${CATEGORY}) · Notches at ±${NOTCH_FACTOR}×IQR/√n (95% CI around median)`;

function NotchedBoxes() {
  const xScale = useXScale("dept");
  const yScale = useYScale("salary");
  const bandwidth = xScale.bandwidth();
  const boxWidth = bandwidth * BOX_WIDTH_SHARE;
  const notchHalf = boxWidth * NOTCH_INSET_SHARE;
  const capHalf = boxWidth * 0.28;

  return (
    <g>
      {salaryGroups.map((g, i) => {
        const color = t.palette[i];
        const cx = xScale(g.name) + bandwidth / 2;
        const xLeft = cx - boxWidth / 2;
        const xRight = cx + boxWidth / 2;
        const xNotchLeft = cx - notchHalf;
        const xNotchRight = cx + notchHalf;
        const yQ3 = yScale(g.stats.q3);
        const yQ1 = yScale(g.stats.q1);
        const yMed = yScale(g.stats.median);
        const yMedTop = yScale(g.stats.median + g.stats.notch);
        const yMedBot = yScale(g.stats.median - g.stats.notch);
        const yWhiskerHigh = yScale(g.stats.whiskerHigh);
        const yWhiskerLow = yScale(g.stats.whiskerLow);

        const boxPath = [
          `M ${xLeft} ${yQ3}`,
          `L ${xRight} ${yQ3}`,
          `L ${xRight} ${yMedTop}`,
          `L ${xNotchRight} ${yMed}`,
          `L ${xRight} ${yMedBot}`,
          `L ${xRight} ${yQ1}`,
          `L ${xLeft} ${yQ1}`,
          `L ${xLeft} ${yMedBot}`,
          `L ${xNotchLeft} ${yMed}`,
          `L ${xLeft} ${yMedTop}`,
          "Z",
        ].join(" ");

        return (
          <g key={g.name}>
            <line
              x1={cx}
              y1={yWhiskerHigh}
              x2={cx}
              y2={yQ3}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={cx}
              y1={yQ1}
              x2={cx}
              y2={yWhiskerLow}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={cx - capHalf}
              y1={yWhiskerHigh}
              x2={cx + capHalf}
              y2={yWhiskerHigh}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={cx - capHalf}
              y1={yWhiskerLow}
              x2={cx + capHalf}
              y2={yWhiskerLow}
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <path
              d={boxPath}
              fill={color}
              fillOpacity={0.32}
              stroke={color}
              strokeWidth={2.5}
              strokeLinejoin="round"
            />
            <line
              x1={xNotchLeft}
              y1={yMed}
              x2={xNotchRight}
              y2={yMed}
              stroke={color}
              strokeWidth={3.5}
              strokeLinecap="round"
            />
            {g.stats.outliers.map((v, j) => (
              <circle
                key={j}
                cx={cx}
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
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H;

  return (
    <div
      style={{
        width,
        height,
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
        width={width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ left: 40, right: 40, top: 20, bottom: 20 }}
        xAxis={[
          {
            id: "dept",
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.38,
            height: 64,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "salary",
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
        <NotchedBoxes />
        <ChartsXAxis axisId="dept" />
        <ChartsYAxis axisId="salary" />
      </ChartsContainer>
    </div>
  );
}
