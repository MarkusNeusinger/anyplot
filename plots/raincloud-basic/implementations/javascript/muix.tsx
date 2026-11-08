// anyplot.ai
// raincloud-basic: Basic Raincloud Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // x padding around the observed range, share of the span
const KDE_POINTS = 160; // evaluation points of each density curve
const CLOUD_CUTOFF = 0.01; // the cloud ends where its density falls below this share of its peak
const WHISKER_IQR = 1.5; // Tukey whiskers reach the furthest value within 1.5 IQR of the box
const GOLDEN = 0.6180339887; // low-discrepancy step for the rain's vertical spread
const CLOUD_SHARE = 0.84; // cloud peak height as a share of the half band above the baseline
const RAIN_NEAR = 0.22; // rain band, as shares of the half band below the baseline
const RAIN_FAR = 0.9;
const BOX_HALF_PX = 11;
const TITLE_H = 56;

// Columns: set these to your data's column names
const ARM = "Treatment arm"; // role: category
const REACTION_TIME = "Reaction time (ms)"; // role: value

// Data: replace this block with your own records, one object per row
// Simple reaction times in a four-arm drug trial, 70 participants per arm; the 50 mg arm
// splits into fast responders and non-responders. Fixed-seed LCG with Box-Muller normals.
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const normal = () => Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
  return [
    ...Array.from({ length: 70 }, () => ({ [ARM]: "Placebo", [REACTION_TIME]: 540 + 55 * normal() })),
    ...Array.from({ length: 70 }, () => ({ [ARM]: "10 mg dose", [REACTION_TIME]: 495 + 50 * normal() })),
    ...Array.from({ length: 70 }, () => ({ [ARM]: "25 mg dose", [REACTION_TIME]: 445 + 48 * normal() })),
    ...Array.from({ length: 70 }, () => ({
      [ARM]: "50 mg dose",
      [REACTION_TIME]: uniform() < 0.55 ? 360 + 35 * normal() : 470 + 40 * normal(),
    })),
  ].map((d) => ({ ...d, [REACTION_TIME]: Math.round(d[REACTION_TIME]) }));
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[REACTION_TIME]));
const arms = [...new Set(rows.map((d) => d[ARM]))];
// Per arm: linear-interpolated quartiles, Tukey whiskers, and a Gaussian KDE with Silverman's
// bandwidth over the values widened by three bandwidths, scaled to its own peak so each cloud
// shows shape rather than group size
const groups = arms.map((arm) => {
  const values = rows.filter((d) => d[ARM] === arm).map((d) => d[REACTION_TIME]);
  const sorted = [...values].sort((a, b) => a - b);
  const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
    const pos = (sorted.length - 1) * q;
    const lo = Math.floor(pos);
    return sorted[lo] + (pos - lo) * ((sorted[lo + 1] ?? sorted[lo]) - sorted[lo]);
  });
  const iqr = q3 - q1;
  const whiskerLow = sorted.find((v) => v >= q1 - WHISKER_IQR * iqr);
  const whiskerHigh = [...sorted].reverse().find((v) => v <= q3 + WHISKER_IQR * iqr);
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  const sd = Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / Math.max(values.length - 1, 1));
  const bandwidth = 0.9 * Math.min(sd, iqr / 1.34 || sd) * Math.pow(values.length, -0.2);
  const lo = sorted[0] - 3 * bandwidth;
  const hi = sorted[sorted.length - 1] + 3 * bandwidth;
  const grid = Array.from({ length: KDE_POINTS }, (_, k) => lo + (k * (hi - lo)) / (KDE_POINTS - 1));
  const raw = grid.map((g) => values.reduce((s, v) => s + Math.exp(-0.5 * ((g - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  const density = raw.map((v) => v / peak);
  // The cloud spans the grid points where the density is still visible, so its tails end on the baseline
  const first = density.findIndex((v) => v >= CLOUD_CUTOFF);
  const last = density.length - 1 - [...density].reverse().findIndex((v) => v >= CLOUD_CUTOFF);
  const cloud = grid.slice(first, last + 1).map((x, k) => [x, density[first + k]]);
  return { arm, values, q1, median, q3, whiskerLow, whiskerHigh, cloud };
});

// The value axis covers every cloud and every raindrop
const extent = groups.flatMap((g) => [g.cloud[0][0], g.cloud[g.cloud.length - 1][0], ...g.values]);
const span = Math.max(...extent) - Math.min(...extent);
const xMin = Math.min(...extent) - span * PAD_SHARE;
const xMax = Math.max(...extent) + span * PAD_SHARE;

const TITLE = "raincloud-basic · javascript · muix · anyplot.ai";

function RaincloudLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const halfBand = yScale.bandwidth() / 2;

  return (
    <g>
      {groups.map((g, i) => {
        const color = t.palette[i];
        const base = yScale(g.arm) + halfBand;
        const cloud = g.cloud.map(([x, density]) => `${xScale(x)},${base - density * halfBand * CLOUD_SHARE}`);
        return (
          <g key={g.arm}>
            <path
              d={`M${xScale(g.cloud[0][0])},${base} L${cloud.join(" L")} L${xScale(g.cloud[g.cloud.length - 1][0])},${base} Z`}
              fill={color}
              fillOpacity={0.5}
              stroke={color}
              strokeWidth={1.5}
            />
            {g.values.map((v, j) => (
              <circle
                key={j}
                cx={xScale(v)}
                cy={base + halfBand * (RAIN_NEAR + ((j * GOLDEN) % 1) * (RAIN_FAR - RAIN_NEAR))}
                r={4}
                fill={color}
                fillOpacity={0.6}
              />
            ))}
            <line x1={xScale(g.whiskerLow)} x2={xScale(g.whiskerHigh)} y1={base} y2={base} stroke={t.ink} strokeWidth={1.5} />
            {[g.whiskerLow, g.whiskerHigh].map((w, k) => (
              <line key={k} x1={xScale(w)} x2={xScale(w)} y1={base - BOX_HALF_PX * 0.7} y2={base + BOX_HALF_PX * 0.7} stroke={t.ink} strokeWidth={1.5} />
            ))}
            <rect
              x={xScale(g.q1)}
              y={base - BOX_HALF_PX}
              width={xScale(g.q3) - xScale(g.q1)}
              height={2 * BOX_HALF_PX}
              rx={2}
              fill={t.elevatedBg}
              stroke={t.ink}
              strokeWidth={1.5}
            />
            <line x1={xScale(g.median)} x2={xScale(g.median)} y1={base - BOX_HALF_PX} y2={base + BOX_HALF_PX} stroke={t.ink} strokeWidth={2.5} />
          </g>
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
        margin={{ top: 24, right: 56, bottom: 16, left: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: REACTION_TIME,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: arms,
            categoryGapRatio: 0.3,
            label: ARM,
            width: 140,
            disableTicks: true,
            disableLine: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsGrid vertical />
        <RaincloudLayer />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
