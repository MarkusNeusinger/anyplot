// anyplot.ai
// box-grouped: Grouped Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-18
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const IQR_FENCE_MULTIPLIER = 1.5;
const Y_PAD_SHARE = 0.08;
const GROUP_WIDTH_SHARE = 0.84;
const BOX_SLOT_SHARE = 0.72;
const BOX_FILL_ALPHA = 0.32;
const BOX_STROKE_PX = 2.2;
const HEADER_H = 106;

// Columns: set these to your data's column names
const CATEGORY = "Department"; // role: category
const SUBCATEGORY = "Experience level"; // role: subcategory
const VALUE = "Productivity index (0–100)"; // role: value

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const depts = ["Engineering", "Sales", "Marketing", "Customer Support"];
  const lvls = ["Junior", "Mid-Level", "Senior"];
  const lvlParams: { [key: string]: { mean: number; std: number } } = {
    Junior: { mean: 52, std: 9 },
    "Mid-Level": { mean: 68, std: 8 },
    Senior: { mean: 82, std: 7 },
  };
  const deptOffsets: { [key: string]: number } = {
    Engineering: 5,
    Sales: -4,
    Marketing: 2,
    "Customer Support": -6,
  };
  const sampleCount = 46;
  const rows: { [key: string]: string | number }[] = [];

  for (let di = 0; di < depts.length; di += 1) {
    const dept = depts[di];
    for (let li = 0; li < lvls.length; li += 1) {
      const lvl = lvls[li];
      const { mean, std } = lvlParams[lvl];
      const offset = deptOffsets[dept];
      for (let i = 0; i < sampleCount; i += 1) {
        state = (state * 1664525 + 1013904223) >>> 0;
        const u1 = Math.max(state / 4294967296, 1e-9);
        state = (state * 1664525 + 1013904223) >>> 0;
        const u2 = state / 4294967296;
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        const val = Math.min(100, Math.max(0, mean + offset + z * std));
        rows.push({
          [CATEGORY]: dept,
          [SUBCATEGORY]: lvl,
          [VALUE]: Number(val.toFixed(2)),
        });
      }
      if ((di + li) % 2 === 0) {
        const outlierVal = Math.min(100, Math.max(0, mean + offset + 3.4 * std));
        rows.push({
          [CATEGORY]: dept,
          [SUBCATEGORY]: lvl,
          [VALUE]: Number(outlierVal.toFixed(2)),
        });
      }
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const categories: string[] = [];
const subcategories: string[] = [];
for (const row of data) {
  const c = String(row[CATEGORY]);
  const s = String(row[SUBCATEGORY]);
  if (!categories.includes(c)) categories.push(c);
  if (!subcategories.includes(s)) subcategories.push(s);
}

const boxGroups = categories.map((cat) => ({
  category: cat,
  boxes: subcategories.map((sub) => {
    const sorted = data
      .filter(
        (row) => String(row[CATEGORY]) === cat && String(row[SUBCATEGORY]) === sub,
      )
      .map((row) => Number(row[VALUE]))
      .sort((a, b) => a - b);
    const n = sorted.length;
    if (n === 0) {
      return { subcategory: sub, stats: null };
    }

    const [q1, median, q3] = [0.25, 0.5, 0.75].map((p) => {
      const pos = (n - 1) * p;
      const base = Math.floor(pos);
      return base + 1 < n
        ? sorted[base] + (pos - base) * (sorted[base + 1] - sorted[base])
        : sorted[base];
    });

    const iqr = q3 - q1;
    const lowerFence = q1 - IQR_FENCE_MULTIPLIER * iqr;
    const upperFence = q3 + IQR_FENCE_MULTIPLIER * iqr;
    const inliers = sorted.filter((v) => v >= lowerFence && v <= upperFence);
    const outliers = sorted.filter((v) => v < lowerFence || v > upperFence);

    return {
      subcategory: sub,
      stats: {
        q1,
        median,
        q3,
        whiskerMin: inliers[0],
        whiskerMax: inliers[inliers.length - 1],
        outliers,
      },
    };
  }),
}));

const allValues = data.map((row) => Number(row[VALUE]));
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const valSpan = dataMax - dataMin || 1;
const yMin = dataMin - valSpan * Y_PAD_SHARE;
const yMax = dataMax + valSpan * Y_PAD_SHARE;

const TITLE = "box-grouped · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations · ${CATEGORY}: ${categories.length} · ${SUBCATEGORY}: ${subcategories.length} · Whiskers at ${IQR_FENCE_MULTIPLIER}×IQR`;

function BoxWhiskerLayer() {
  const xScale = useXScale("dept");
  const yScale = useYScale("val");
  const bandwidth = xScale.bandwidth();
  const groupWidth = bandwidth * GROUP_WIDTH_SHARE;
  const boxSlot = groupWidth / subcategories.length;
  const boxWidth = boxSlot * BOX_SLOT_SHARE;
  const capWidth = boxWidth * 0.62;

  return (
    <g>
      {boxGroups.map((group) => {
        const groupStart = xScale(group.category) + (bandwidth - groupWidth) / 2;
        return group.boxes.map((box, subIdx) => {
          if (!box.stats) return null;
          const cx = groupStart + boxSlot * (subIdx + 0.5);
          const color = t.palette[subIdx];
          const yQ1 = yScale(box.stats.q1);
          const yQ3 = yScale(box.stats.q3);
          const yMedian = yScale(box.stats.median);
          const yWhiskerHigh = yScale(box.stats.whiskerMax);
          const yWhiskerLow = yScale(box.stats.whiskerMin);
          return (
            <g key={`${group.category}-${box.subcategory}`}>
              <line
                x1={cx}
                x2={cx}
                y1={yWhiskerHigh}
                y2={yQ3}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
              />
              <line
                x1={cx}
                x2={cx}
                y1={yQ1}
                y2={yWhiskerLow}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
              />
              <line
                x1={cx - capWidth / 2}
                x2={cx + capWidth / 2}
                y1={yWhiskerHigh}
                y2={yWhiskerHigh}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
              />
              <line
                x1={cx - capWidth / 2}
                x2={cx + capWidth / 2}
                y1={yWhiskerLow}
                y2={yWhiskerLow}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
              />
              <rect
                x={cx - boxWidth / 2}
                y={yQ3}
                width={boxWidth}
                height={Math.max(yQ1 - yQ3, 1)}
                rx={3}
                fill={color}
                fillOpacity={BOX_FILL_ALPHA}
                stroke={color}
                strokeWidth={BOX_STROKE_PX}
              />
              <line
                x1={cx - boxWidth / 2}
                x2={cx + boxWidth / 2}
                y1={yMedian}
                y2={yMedian}
                stroke={color}
                strokeWidth={3.5}
                strokeLinecap="round"
              />
              {box.stats.outliers.map((value, outlierIndex) => (
                <circle
                  key={outlierIndex}
                  cx={cx}
                  cy={yScale(value)}
                  r={5}
                  fill={t.pageBg}
                  stroke={color}
                  strokeWidth={2}
                />
              ))}
            </g>
          );
        });
      })}
    </g>
  );
}

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - HEADER_H;

  return (
    <div
      style={{
        width: chartWidth,
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
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          {subcategories.map((sub, i) => (
            <div
              key={sub}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <svg width="16" height="16" style={{ display: "inline-block" }}>
                <rect
                  x={BOX_STROKE_PX / 2}
                  y={BOX_STROKE_PX / 2}
                  width={16 - BOX_STROKE_PX}
                  height={16 - BOX_STROKE_PX}
                  rx={3}
                  fill={t.palette[i]}
                  fillOpacity={BOX_FILL_ALPHA}
                  stroke={t.palette[i]}
                  strokeWidth={BOX_STROKE_PX}
                />
              </svg>
              <span style={{ fontSize: 14, color: t.inkSoft }}>{sub}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={chartWidth}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, right: 40, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "dept",
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.36,
            height: 64,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "val",
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
        <BoxWhiskerLayer />
        <ChartsXAxis axisId="dept" />
        <ChartsYAxis axisId="val" />
      </ChartsContainer>
    </div>
  );
}
