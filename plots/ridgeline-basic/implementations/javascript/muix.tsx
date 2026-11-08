// anyplot.ai
// ridgeline-basic: Basic Ridgeline Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-07-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const KDE_POINTS = 160; // evaluation points of each density curve
const TAIL_CUTOFF = 0.01; // a ridge ends where its density falls below this share of its peak
const PEAK_ROWS = 1.6; // ridge peak height in row spacings, so neighbours overlap by about 60 %
const BASE_PAD_ROWS = 0.25; // room below the lowest baseline, in row spacings
const TOP_PAD_ROWS = 0.15; // room above the highest peak, in row spacings
const PAD_SHARE = 0.03; // value-axis padding beyond the widest ridge, share of the span
const TITLE_H = 56;

// Columns: set these to your data's column names
const MONTH = "Month"; // role: group
const HIGH = "Daily high temperature (°C)"; // role: value

// Data: replace this block with your own records, one object per row
// Daily high temperatures in a temperate continental climate, 200 days sampled per month,
// wider spread in winter than in summer; fixed-seed LCG with Box-Muller normals
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const means = [-2, 1, 7, 14, 20, 26, 29, 28, 23, 15, 7, -1];
  const sds = [4.5, 4.5, 4.0, 3.5, 3.0, 2.5, 2.3, 2.3, 2.8, 3.3, 4.0, 4.5];
  return months.flatMap((month, i) =>
    Array.from({ length: 200 }, () => {
      const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
      return { [MONTH]: month, [HIGH]: Math.round((means[i] + sds[i] * z) * 10) / 10 };
    }),
  );
})();

// Plot: reads only data and the constants above
// Groups in order of first appearance, the first at the top; colour runs along the sequential
// ramp in that order, since the groups are ordered
const rows = data.filter((d) => Number.isFinite(d[HIGH]));
const groupNames = [...new Set(rows.map((d) => d[MONTH]))];
const n = groupNames.length;
const seqRgb = t.seq.map((hex) => [16, 8, 0].map((shift) => (parseInt(hex.slice(1), 16) >> shift) & 255));

// Per group: a Gaussian KDE with Silverman's bandwidth over the values widened by three
// bandwidths, scaled to its own peak so ridge height compares shape rather than group size
const ridges = groupNames.map((name, i) => {
  const values = rows.filter((d) => d[MONTH] === name).map((d) => d[HIGH]);
  const sorted = [...values].sort((a, b) => a - b);
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  const sd = Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / Math.max(values.length - 1, 1));
  const bandwidth = 0.9 * sd * Math.pow(values.length, -0.2);
  const lo = sorted[0] - 3 * bandwidth;
  const hi = sorted[sorted.length - 1] + 3 * bandwidth;
  const grid = Array.from({ length: KDE_POINTS }, (_, k) => lo + (k * (hi - lo)) / (KDE_POINTS - 1));
  const raw = grid.map((g) => values.reduce((s, v) => s + Math.exp(-0.5 * ((g - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  const density = raw.map((v) => v / peak);
  const first = density.findIndex((v) => v >= TAIL_CUTOFF);
  const last = density.length - 1 - [...density].reverse().findIndex((v) => v >= TAIL_CUTOFF);
  const share = n > 1 ? i / (n - 1) : 0;
  const rgb = seqRgb[0].map((c, k) => Math.round(c + (seqRgb[1][k] - c) * share));
  return {
    name,
    baseline: n - 1 - i,
    curve: grid.slice(first, last + 1).map((x, k) => [x, density[first + k]]),
    color: `rgb(${rgb.join(", ")})`,
  };
});

const extent = ridges.flatMap((r) => [r.curve[0][0], r.curve[r.curve.length - 1][0]]);
const span = Math.max(...extent) - Math.min(...extent);
const xMin = Math.min(...extent) - span * PAD_SHARE;
const xMax = Math.max(...extent) + span * PAD_SHARE;
const baselines = ridges.map((r) => r.baseline);

const TITLE = "ridgeline-basic · javascript · muix · anyplot.ai";

function Ridges() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g strokeLinejoin="round">
      {ridges.map((r) => {
        const base = yScale(r.baseline);
        const top = r.curve.map(([x, d]) => `${xScale(x)},${yScale(r.baseline + d * PEAK_ROWS)}`);
        return (
          <path
            key={r.name}
            d={`M${xScale(r.curve[0][0])},${base} L${top.join(" L")} L${xScale(r.curve[r.curve.length - 1][0])},${base} Z`}
            fill={r.color}
            fillOpacity={0.92}
            stroke={t.pageBg}
            strokeWidth={2}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 16, right: 48, bottom: 16, left: 16 }}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: HIGH,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: -BASE_PAD_ROWS,
            max: n - 1 + PEAK_ROWS + TOP_PAD_ROWS,
            tickInterval: baselines,
            valueFormatter: (v) => ridges.find((r) => r.baseline === Math.round(v))?.name ?? "",
            label: MONTH,
            width: 84,
            disableLine: true,
            disableTicks: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <Ridges />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
