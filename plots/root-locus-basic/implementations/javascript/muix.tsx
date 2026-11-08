// anyplot.ai
// root-locus-basic: Root Locus Plot for Control Systems
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAMPING_RATIOS = [0.2, 0.4, 0.6, 0.8]; // constant-damping rays of the s-plane grid
const OMEGA_CIRCLES = 4; // about this many constant natural-frequency circles across the window
const ARROW_SHARE = 0.5; // each branch's direction arrow sits at this share of its arc length
const PAD_SHARE = 0.08; // window padding around the locus, share of its span
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 44;
const X_AXIS_H = 64;
const Y_AXIS_W = 64;
const MARGIN = { top: 16, right: 40, bottom: 8, left: 16 };

// Columns: set these to your data's column names
const BRANCH = "Branch"; // role: branch
const GAIN = "Gain K"; // role: gain
const REAL = "Real part σ (1/s)"; // role: real
const IMAGINARY = "Imaginary part ω (rad/s)"; // role: imaginary

// Data: replace this block with your own records, one object per row
// Closed-loop poles of G(s) = K / (s (s + 2) (s + 4)) for 501 gains K from 0 to 90, spaced
// quadratically so the fast-moving poles near the breakaway are sampled densely, plus the
// breakaway gain itself, where the branches from 0 and −2 meet on the real axis (s is the root
// of dK/ds = 3s² + 12s + 8 = 0 in (−2, 0), with K = −s (s + 2) (s + 4)): the real root of
// s³ + 6s² + 8s + K = 0 by Newton's method, continued from the previous gain, and the remaining
// pair from the quadratic factor; each branch is named after the open-loop pole it starts from
const data = (() => {
  const rows = [];
  const breakawayS = (-12 + Math.sqrt(12 * 12 - 4 * 3 * 8)) / (2 * 3);
  const breakawayK = -breakawayS * (breakawayS + 2) * (breakawayS + 4);
  const gains = [...Array.from({ length: 501 }, (_, i) => (i / 500) ** 2 * 90), breakawayK].sort((a, b) => a - b);
  let r3 = -4.001;
  for (const k of gains) {
    for (let it = 0; it < 80; it++) {
      const step = (r3 ** 3 + 6 * r3 ** 2 + 8 * r3 + k) / (3 * r3 ** 2 + 12 * r3 + 8);
      r3 -= step;
      if (Math.abs(step) < 1e-12) break;
    }
    const b = 6 + r3;
    const disc = b * b - 4 * (8 + r3 * b);
    const pair =
      disc >= 0
        ? [[(-b + Math.sqrt(disc)) / 2, 0], [(-b - Math.sqrt(disc)) / 2, 0]]
        : [[-b / 2, Math.sqrt(-disc) / 2], [-b / 2, -Math.sqrt(-disc) / 2]];
    [["From s = 0", ...pair[0]], ["From s = −2", ...pair[1]], ["From s = −4", r3, 0]].forEach(([branch, re, im]) =>
      rows.push({
        [BRANCH]: branch,
        [GAIN]: Math.round(k * 1000) / 1000,
        [REAL]: Math.round(re * 1e4) / 1e4,
        [IMAGINARY]: Math.round(im * 1e4) / 1e4,
      }),
    );
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Each branch in order of gain; its lowest-gain row is the open-loop pole it starts from
const branchNames = [...new Set(data.map((d) => d[BRANCH]))];
const branches = branchNames.map((name) => {
  const rows = data
    .filter((d) => d[BRANCH] === name && [d[GAIN], d[REAL], d[IMAGINARY]].every(Number.isFinite))
    .sort((a, b) => a[GAIN] - b[GAIN]);
  return { name, re: rows.map((d) => d[REAL]), im: rows.map((d) => d[IMAGINARY]), gain: rows.map((d) => d[GAIN]) };
});
const poles = branches.map((b) => ({ re: b.re[0], im: b.im[0], gain: b.gain[0] }));

// Imaginary-axis crossings: a strict sign change of the real part between two gains, interpolated
const crossings = branches.flatMap((b) =>
  b.re.slice(1).flatMap((re, j) => {
    if (b.re[j] * re >= 0) return [];
    const f = b.re[j] / (b.re[j] - re);
    return [{ im: b.im[j] + f * (b.im[j + 1] - b.im[j]), gain: b.gain[j] + f * (b.gain[j + 1] - b.gain[j]) }];
  }),
);

// Direction arrows at a share of each branch's arc length, pointing toward increasing gain
const arrows = branches.map((b) => {
  const length = [0];
  b.re.slice(1).forEach((re, j) => length.push(length[j] + Math.hypot(re - b.re[j], b.im[j + 1] - b.im[j])));
  const target = ARROW_SHARE * length[length.length - 1];
  const k = Math.min(Math.max(length.findIndex((s) => s >= target), 1), b.re.length - 2);
  return { re: b.re[k], im: b.im[k], dre: b.re[k + 1] - b.re[k - 1], dim: b.im[k + 1] - b.im[k - 1] };
});

// Window: the locus, its poles and the origin, padded, with one px-per-unit scale on both axes
const allRe = [...branches.flatMap((b) => b.re), 0];
const allIm = [...branches.flatMap((b) => b.im), 0];
const needX = (Math.max(...allRe) - Math.min(...allRe)) * (1 + 2 * PAD_SHARE);
const needY = (Math.max(...allIm) - Math.min(...allIm)) * (1 + 2 * PAD_SHARE);
const { width, height } = window.ANYPLOT_SIZE;
const chartH = height - TITLE_H - SUBTITLE_H - LEGEND_H;
const drawW = width - MARGIN.left - MARGIN.right - Y_AXIS_W;
const drawH = chartH - MARGIN.top - MARGIN.bottom - X_AXIS_H;
const pxPerUnit = Math.min(drawW / needX, drawH / needY);
const xMid = (Math.max(...allRe) + Math.min(...allRe)) / 2;
const yMid = (Math.max(...allIm) + Math.min(...allIm)) / 2;
const xRange = [xMid - drawW / pxPerUnit / 2, xMid + drawW / pxPerUnit / 2];
const yRange = [yMid - drawH / pxPerUnit / 2, yMid + drawH / pxPerUnit / 2];

// Natural-frequency circles at a 1-2-5 step that puts about OMEGA_CIRCLES rings inside the locus's
// own reach, continued out to the window's far corner
const reach = Math.max(...branches.flatMap((b) => b.re.map((re, j) => Math.hypot(re, b.im[j]))));
const corner = Math.max(...[xRange[0], xRange[1]].flatMap((x) => yRange.map((y) => Math.hypot(x, y))));
const rawStep = reach / OMEGA_CIRCLES;
const magnitude = 10 ** Math.floor(Math.log10(rawStep));
const omegaStep = [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= rawStep);
const omegas = Array.from({ length: Math.ceil(corner / omegaStep) }, (_, i) => (i + 1) * omegaStep);

const minGain = Math.min(...poles.map((p) => p.gain));
const maxGain = Math.max(...branches.map((b) => b.gain[b.gain.length - 1]));
const TITLE = "root-locus-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${branches.length} branches · ${GAIN} from ${minGain.toFixed(0)} to ${maxGain.toFixed(0)} · grid: constant damping ratio ζ and natural frequency ωn`;
const LEGEND = [
  ...branches.map((b, i) => ({ key: b.name, label: b.name, color: t.palette[i], glyph: "line" })),
  { key: "poles", label: `Open-loop pole (${GAIN} = ${minGain.toFixed(0)})`, color: t.ink, glyph: "cross" },
  ...(crossings.length > 0
    ? [{ key: "crossings", label: `Imaginary-axis crossing (${GAIN} ≈ ${crossings[0].gain.toFixed(1)})`, color: t.ink, glyph: "diamond" }]
    : []),
];

function SPlaneGrid() {
  const xScale = useXScale("re-0");
  const yScale = useYScale();
  const ox = xScale(0);
  const oy = yScale(0);
  const top = yScale(yRange[1]);
  const bottom = yScale(yRange[0]);
  const left = xScale(xRange[0]);

  return (
    <g>
      <defs>
        <clipPath id="s-plane-clip">
          <rect x={left} y={top} width={xScale(xRange[1]) - left} height={bottom - top} />
        </clipPath>
      </defs>
      <g clipPath="url(#s-plane-clip)" fill="none" stroke={t.grid} strokeWidth={1.5} strokeDasharray="6 5">
        {omegas.map((w) => (
          <path key={`w-${w}`} d={`M${ox},${oy - w * pxPerUnit} A${w * pxPerUnit},${w * pxPerUnit} 0 0 0 ${ox},${oy + w * pxPerUnit}`} />
        ))}
        {DAMPING_RATIOS.flatMap((z) =>
          [1, -1].map((side) => (
            <line
              key={`z-${z}-${side}`}
              x1={ox}
              y1={oy}
              x2={ox - z * corner * pxPerUnit}
              y2={oy - side * Math.sqrt(1 - z * z) * corner * pxPerUnit}
            />
          )),
        )}
      </g>
      <line x1={left} x2={xScale(xRange[1])} y1={oy} y2={oy} stroke={t.inkSoft} strokeWidth={1} />
      <line x1={ox} x2={ox} y1={top} y2={bottom} stroke={t.inkSoft} strokeWidth={1} />
      {DAMPING_RATIOS.map((z) => {
        // label each upper ray where it leaves the window through the top or the left edge
        const run = Math.min((top + 30 - oy) / -Math.sqrt(1 - z * z), (left + 40 - ox) / -z);
        return (
          <text
            key={`zl-${z}`}
            x={ox - z * run}
            y={oy - Math.sqrt(1 - z * z) * run}
            fontSize={14}
            fill={t.inkSoft}
            textAnchor="middle"
            stroke={t.pageBg}
            strokeWidth={4}
            paintOrder="stroke"
          >
            ζ = {z}
          </text>
        );
      })}
      {omegas
        .filter((w) => w * Math.SQRT1_2 * pxPerUnit < Math.min(ox - left, bottom - oy) - 20)
        .map((w) => (
          <text
            key={`wl-${w}`}
            x={ox - w * Math.SQRT1_2 * pxPerUnit}
            y={oy + w * Math.SQRT1_2 * pxPerUnit}
            fontSize={14}
            fill={t.inkSoft}
            textAnchor="middle"
            dominantBaseline="central"
            stroke={t.pageBg}
            strokeWidth={4}
            paintOrder="stroke"
          >
            ωn = {w}
          </text>
        ))}
    </g>
  );
}

function LocusMarks() {
  const xScale = useXScale("re-0");
  const yScale = useYScale();

  return (
    <g>
      {arrows.map((a, i) => (
        <path
          key={`arrow-${i}`}
          d="M 11 0 L -8 -8 L -8 8 Z"
          transform={`translate(${xScale(a.re)},${yScale(a.im)}) rotate(${(Math.atan2(-a.dim, a.dre) * 180) / Math.PI})`}
          fill={t.palette[i]}
        />
      ))}
      {poles.map((p, i) => (
        <g key={`pole-${i}`} transform={`translate(${xScale(p.re)},${yScale(p.im)})`} stroke={t.ink} strokeWidth={3} strokeLinecap="round">
          <line x1={-8} y1={-8} x2={8} y2={8} />
          <line x1={8} y1={-8} x2={-8} y2={8} />
        </g>
      ))}
      {crossings.map((c, i) => (
        <rect
          key={`cross-${i}`}
          x={-8}
          y={-8}
          width={16}
          height={16}
          transform={`translate(${xScale(0)},${yScale(c.im)}) rotate(45)`}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={2}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsContainer
        width={width}
        height={chartH}
        skipAnimation
        margin={MARGIN}
        series={branches.map((b, i) => ({
          type: "line",
          id: `branch-${i}`,
          label: b.name,
          xAxisId: `re-${i}`,
          data: b.im,
          color: t.palette[i],
          curve: "linear",
          showMark: false,
        }))}
        xAxis={branches.map((b, i) => ({
          id: `re-${i}`,
          scaleType: "linear",
          data: b.re,
          min: xRange[0],
          max: xRange[1],
          position: i === 0 ? "bottom" : "none",
          tickNumber: 16,
          label: REAL,
          height: X_AXIS_H,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        }))}
        yAxis={[
          {
            scaleType: "linear",
            min: yRange[0],
            max: yRange[1],
            tickNumber: 9,
            label: IMAGINARY,
            width: Y_AXIS_W,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <SPlaneGrid />
        <LinePlot skipAnimation />
        <LocusMarks />
        <ChartsXAxis axisId="re-0" />
        <ChartsYAxis />
      </ChartsContainer>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 28, fontSize: 15, color: t.ink }}>
        {LEGEND.map((item) => (
          <div key={item.key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width={24} height={18} viewBox="0 0 24 18">
              {item.glyph === "line" && <line x1={1} y1={9} x2={23} y2={9} stroke={item.color} strokeWidth={3} />}
              {item.glyph === "cross" && (
                <g stroke={item.color} strokeWidth={2.5} strokeLinecap="round">
                  <line x1={6} y1={3} x2={18} y2={15} />
                  <line x1={18} y1={3} x2={6} y2={15} />
                </g>
              )}
              {item.glyph === "diamond" && <rect x={6.5} y={3.5} width={11} height={11} transform="rotate(45 12 9)" fill={item.color} />}
            </svg>
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}
