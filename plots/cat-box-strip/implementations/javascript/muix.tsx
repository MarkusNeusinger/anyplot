// anyplot.ai
// cat-box-strip: Box Plot with Strip Overlay
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 89/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.08;
const BOX_WIDTH_SHARE = 0.36;
const JITTER_WIDTH_SHARE = 0.28;
const IQR_FENCE_MULT = 1.5;
const HEADER_H = 112;

// Columns: set these to your data's column names
const CATEGORY = "Transport mode"; // role: category
const VALUE = "Commute time (minutes)"; // role: value

// Data: replace this block with your own records, one object per row
const data = (() => {
  const nPerCategory = 45;
  const params = [
    { category: "Bike", mean: 17, sd: 4, min: 5, jamProb: 0, jamExtra: 0 },
    { category: "Walk", mean: 21, sd: 5, min: 6, jamProb: 0, jamExtra: 0 },
    { category: "Train", mean: 26, sd: 5, min: 10, jamProb: 0, jamExtra: 0 },
    { category: "Bus", mean: 31, sd: 8, min: 9, jamProb: 0, jamExtra: 0 },
    { category: "Car", mean: 24, sd: 9, min: 7, jamProb: 0.12, jamExtra: 25 },
  ];

  // One stream of uniforms (mulberry32, seed 42), consumed in order below
  let seed = 42;
  const uniforms: number[] = [];
  for (let i = 0; i < 4 * nPerCategory * params.length; i += 1) {
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    uniforms.push(((x ^ (x >>> 14)) >>> 0) / 4294967296);
  }

  let k = 0;
  const rows: { [key: string]: string | number }[] = [];
  for (const p of params) {
    for (let i = 0; i < nPerCategory; i += 1) {
      const u1 = Math.max(uniforms[k++], 1e-9);
      const u2 = uniforms[k++];
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      let v = p.mean + z * p.sd;
      // A share of car trips hits a traffic jam
      if (p.jamProb > 0 && uniforms[k++] < p.jamProb) {
        v += p.jamExtra + uniforms[k++] * p.jamExtra;
      }

      rows.push({
        [CATEGORY]: p.category,
        [VALUE]: Math.max(p.min, Math.round(v * 10) / 10),
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const categories = Array.from(new Set(data.map((d) => String(d[CATEGORY]))));

let jitterSeed = 1337;
const stats = categories.map((category, idx) => {
  const catRows = data.filter((d) => String(d[CATEGORY]) === category);
  const values = catRows.map((d) => Number(d[VALUE]));
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
    const p = (n - 1) * q;
    const b = Math.floor(p);
    return b + 1 < n ? sorted[b] + (p - b) * (sorted[b + 1] - sorted[b]) : sorted[b];
  });

  const iqr = q3 - q1;
  const lowFence = q1 - IQR_FENCE_MULT * iqr;
  const highFence = q3 + IQR_FENCE_MULT * iqr;
  const inFence = sorted.filter((v) => v >= lowFence && v <= highFence);
  const whiskerLow = inFence[0];
  const whiskerHigh = inFence[inFence.length - 1];

  const jittered = values.map((value) => {
    jitterSeed = (jitterSeed + 0x6d2b79f5) | 0;
    let jx = Math.imul(jitterSeed ^ (jitterSeed >>> 15), 1 | jitterSeed);
    jx = (jx + Math.imul(jx ^ (jx >>> 7), 61 | jx)) ^ jx;
    const u = ((jx ^ (jx >>> 14)) >>> 0) / 4294967296;
    return {
      value,
      offset: u - 0.5,
    };
  });

  return {
    category,
    color: t.palette[idx],
    jittered,
    q1,
    median,
    q3,
    whiskerLow,
    whiskerHigh,
  };
});

const allValues = data.map((d) => Number(d[VALUE]));
const rawMin = Math.min(...allValues);
const rawMax = Math.max(...allValues);
const span = rawMax - rawMin || 1;
const paddedMin = rawMin - span * Y_PAD_SHARE;
// A non-negative variable keeps its zero floor; negative data keeps its padding
const yMin = rawMin >= 0 ? Math.max(0, paddedMin) : paddedMin;
const yMax = rawMax + span * Y_PAD_SHARE;

const TITLE = "cat-box-strip · javascript · muix · anyplot.ai";
const SUBTITLE = `Box: median, Q1–Q3, whiskers to ${IQR_FENCE_MULT}×IQR · Dots: ${data.length} jittered observations · ${categories.length} groups (${CATEGORY})`;

function BoxStripLayer() {
  const xScale = useXScale("cat");
  const yScale = useYScale("val");
  const bandwidth = xScale.bandwidth();
  const boxWidth = bandwidth * BOX_WIDTH_SHARE;
  const capHalf = boxWidth * 0.32;
  const jitterSpread = bandwidth * JITTER_WIDTH_SHARE;

  return (
    <g>
      {stats.map((s) => {
        const yLow = yScale(s.whiskerLow);
        const yQ1 = yScale(s.q1);
        const yQ3 = yScale(s.q3);
        const yHigh = yScale(s.whiskerHigh);
        const yMed = yScale(s.median);
        const cx = xScale(s.category) + bandwidth / 2;

        return (
          <g key={s.category}>
            <line
              x1={cx}
              y1={yLow}
              x2={cx}
              y2={yQ1}
              stroke={s.color}
              strokeWidth={2.2}
              strokeOpacity={0.9}
            />
            <line
              x1={cx}
              y1={yQ3}
              x2={cx}
              y2={yHigh}
              stroke={s.color}
              strokeWidth={2.2}
              strokeOpacity={0.9}
            />
            <line
              x1={cx - capHalf}
              y1={yLow}
              x2={cx + capHalf}
              y2={yLow}
              stroke={s.color}
              strokeWidth={2.2}
              strokeOpacity={0.9}
            />
            <line
              x1={cx - capHalf}
              y1={yHigh}
              x2={cx + capHalf}
              y2={yHigh}
              stroke={s.color}
              strokeWidth={2.2}
              strokeOpacity={0.9}
            />
            <rect
              x={cx - boxWidth / 2}
              y={yQ3}
              width={boxWidth}
              height={Math.max(1, yQ1 - yQ3)}
              fill={s.color}
              fillOpacity={0.18}
              stroke={s.color}
              strokeWidth={2.5}
              rx={2}
            />
            <line
              x1={cx - boxWidth / 2}
              y1={yMed}
              x2={cx + boxWidth / 2}
              y2={yMed}
              stroke={t.ink}
              strokeWidth={3.2}
              strokeLinecap="round"
            />
          </g>
        );
      })}
      {stats.map((s) => {
        const cx = xScale(s.category) + bandwidth / 2;
        return s.jittered.map((p, i) => (
          <circle
            key={`${s.category}-${i}`}
            cx={cx + p.offset * jitterSpread}
            cy={yScale(p.value)}
            r={5.2}
            fill={s.color}
            fillOpacity={0.5}
            stroke={t.pageBg}
            strokeWidth={0.9}
          />
        ));
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
          gap: 8,
          paddingTop: 6,
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
        margin={{ top: 20, right: 48, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "cat",
            scaleType: "band",
            data: categories,
            height: 64,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "val",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            tickNumber: 7,
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
            opacity: 0.65,
            strokeDasharray: "3 4",
          },
        }}
      >
        <ChartsGrid horizontal />
        <BoxStripLayer />
        <ChartsXAxis axisId="cat" />
        <ChartsYAxis axisId="val" />
      </ChartsContainer>
    </div>
  );
}
