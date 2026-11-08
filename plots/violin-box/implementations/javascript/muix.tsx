// anyplot.ai
// violin-box: Violin Plot with Embedded Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-09
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GRID_N = 140; // KDE evaluation points per violin
const TAIL_BANDWIDTHS = 1.5; // the density falls below ~4 % of its peak this far past the data
const WHISKER_IQR = 1.5; // Tukey whiskers: the last points within 1.5 × IQR of the box
const Y_PAD = 0.04; // share of the value range added above and below
const TITLE = "violin-box · javascript · muix · anyplot.ai";
const TITLE_H = 80;

// Columns: set these to your data's column names
const DOSE = "Caffeine dose"; // role: group
const REACTION = "Reaction time (ms)"; // role: value

// Data: replace this block with your own records, one object per row
// Simple reaction times of 240 trials per caffeine dose. Placebo carries a
// slow "attention lapse" tail, 200 mg is the tight optimum and 300 mg turns
// bimodal (impulsive-fast vs. normal latency), the overstimulation pattern
// of the Yerkes-Dodson law.
const data = (() => {
  let state = 7;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const normal = (mean, sd) => mean + sd * Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const doses = [
    { dose: "0 mg (placebo)", mean: 515, sd: 52, lapse: 0.06 },
    { dose: "100 mg", mean: 468, sd: 40, lapse: 0.03 },
    { dose: "200 mg", mean: 408, sd: 26, lapse: 0.01 },
    { dose: "300 mg", mean: 465, sd: 34, lapse: 0, fastShare: 0.35, fastMean: 350, fastSd: 22 },
  ];
  return doses.flatMap((g) =>
    Array.from({ length: 240 }, () => {
      let v = g.fastShare && rand() < g.fastShare ? normal(g.fastMean, g.fastSd) : normal(g.mean, g.sd);
      if (g.lapse > 0 && rand() < g.lapse) v += 130 + rand() * 110;
      return { [DOSE]: g.dose, [REACTION]: Math.round(Math.max(220, v)) };
    }),
  );
})();

// Plot: reads only data and the constants above
const categories = [...new Set(data.map((d) => d[DOSE]))];

// Per group: Tukey box statistics with the outliers beyond the whiskers, and a
// Gaussian KDE (Silverman bandwidth) normalized to its own peak. The grid ends
// a short way past the data, so each violin tapers just beyond its values.
const violins = categories.map((cat) => {
  const values = data
    .filter((d) => d[DOSE] === cat && d[REACTION] != null)
    .map((d) => d[REACTION])
    .sort((a, b) => a - b);
  const n = values.length;
  const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
    const pos = (n - 1) * q;
    const base = Math.floor(pos);
    return values[base] + (pos - base) * ((values[base + 1] ?? values[base]) - values[base]);
  });
  const fenceLow = q1 - WHISKER_IQR * (q3 - q1);
  const fenceHigh = q3 + WHISKER_IQR * (q3 - q1);
  const inliers = values.filter((v) => v >= fenceLow && v <= fenceHigh);

  const mean = values.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
  const bandwidth = 0.9 * sd * Math.pow(n, -0.2);
  const lo = values[0] - TAIL_BANDWIDTHS * bandwidth;
  const hi = values[n - 1] + TAIL_BANDWIDTHS * bandwidth;
  const grid = Array.from({ length: GRID_N }, (_, k) => lo + (k * (hi - lo)) / (GRID_N - 1));
  const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);

  return {
    cat,
    n,
    q1,
    median,
    q3,
    whiskerLow: inliers[0],
    whiskerHigh: inliers[inliers.length - 1],
    outliers: values.filter((v) => v < fenceLow || v > fenceHigh),
    grid,
    density: raw.map((v) => v / peak),
  };
});

// The doses are ordered, so the violins take steps of the sequential ramp in their order
const [seqA, seqB] = [t.seq[0], t.seq[1]].map((hex) => [16, 8, 0].map((s) => (parseInt(hex.slice(1), 16) >> s) & 255));
const groupColor = categories.map((_, i) => {
  const f = categories.length > 1 ? i / (categories.length - 1) : 0;
  return `rgb(${seqA.map((v, c) => Math.round(v + (seqB[c] - v) * f)).join(",")})`;
});

const gridMin = Math.min(...violins.map((v) => v.grid[0]));
const gridMax = Math.max(...violins.map((v) => v.grid[GRID_N - 1]));
const yPad = (gridMax - gridMin) * Y_PAD;
const SUBTITLE = `${data.length} measurements in ${categories.length} groups · box Q1–Q3 with median, whiskers to ${WHISKER_IQR} × IQR, open circles beyond`;

// The community package has no violin or box component: a custom SVG layer
// draws both through the chart's own band and linear scales.
function ViolinBoxes() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = xScale.bandwidth();
  const violinHalfWidth = band * 0.42;
  const boxHalfWidth = Math.min(16, band * 0.09);

  return (
    <g>
      {violins.map(({ cat, grid, density, q1, median, q3, whiskerLow, whiskerHigh, outliers }, i) => {
        const color = groupColor[i];
        const center = xScale(cat) + band / 2;
        const leftSide = grid.map((gy, k) => `${center - density[k] * violinHalfWidth},${yScale(gy)}`);
        const rightSide = grid.map((gy, k) => `${center + density[k] * violinHalfWidth},${yScale(gy)}`).reverse();
        const bottomTip = `${center},${yScale(grid[0])}`;
        const topTip = `${center},${yScale(grid[GRID_N - 1])}`;
        const violinPath = `M${bottomTip} L${leftSide.join(" L")} L${topTip} L${rightSide.join(" L")} Z`;

        return (
          <g key={cat}>
            <path d={violinPath} fill={color} fillOpacity={0.45} stroke={color} strokeWidth={2} strokeLinejoin="round" />
            <line x1={center} x2={center} y1={yScale(whiskerLow)} y2={yScale(whiskerHigh)} stroke={t.ink} strokeWidth={1.75} />
            {[whiskerLow, whiskerHigh].map((w, k) => (
              <line key={`cap-${k}`} x1={center - boxHalfWidth * 0.6} x2={center + boxHalfWidth * 0.6} y1={yScale(w)} y2={yScale(w)} stroke={t.ink} strokeWidth={1.75} />
            ))}
            <rect
              x={center - boxHalfWidth}
              y={yScale(q3)}
              width={boxHalfWidth * 2}
              height={Math.max(1, yScale(q1) - yScale(q3))}
              fill={t.ink}
              rx={3}
            />
            <line x1={center - boxHalfWidth} x2={center + boxHalfWidth} y1={yScale(median)} y2={yScale(median)} stroke={t.pageBg} strokeWidth={2.5} />
            {outliers.map((v, j) => (
              <circle key={`out-${j}`} cx={center} cy={yScale(v)} r={4.5} fill="none" stroke={t.ink} strokeWidth={1.5} />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 12, left: 24 }}
        xAxis={[
          {
            id: "groups",
            data: categories,
            scaleType: "band",
            height: 72,
            label: DOSE,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "values",
            min: gridMin - yPad,
            max: gridMax + yPad,
            width: 84,
            label: REACTION,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid horizontal />
        <ViolinBoxes />
        <ChartsXAxis axisId="groups" disableTicks />
        <ChartsYAxis axisId="values" />
      </ChartsContainer>
    </div>
  );
}
