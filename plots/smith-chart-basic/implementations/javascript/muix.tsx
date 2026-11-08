// anyplot.ai
// smith-chart-basic: Smith Chart for RF/Impedance
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const Z0 = 50; // reference impedance for normalization, ohms (the spec's default)
const RESISTANCE_CIRCLES = [0.2, 0.5, 1, 2, 5]; // normalized r of the standard grid
const REACTANCE_ARCS = [0.2, 0.5, 1, 2, 5]; // normalized |x| of the standard grid
const GAMMA_LIMIT = 1.15; // the unit disk plus room for the reactance labels
const LABEL_COUNT = 6; // frequency labels spread evenly along the sweep
const LABEL_FONT_PX = 15;
const GRID_FONT_PX = 14;
const GLYPH_EM = 0.62; // average glyph width in em, to size a label's box before it is drawn
const LABEL_GAP_PX = 14; // nearest distance from a labelled point to its label box
const LABEL_GAP_MAX_PX = 90; // farthest the search steps out along the normal
const LABEL_STEP_PX = 4;
const LABEL_CLEAR_PX = 13; // room a label box keeps from the locus, the rim and other labels
const LABEL_SAMPLE_PX = 3; // spacing of the points the clearance is measured against

// Columns: set these to your data's column names
const FREQUENCY = "Frequency (GHz)"; // role: frequency
const RESISTANCE = "Resistance (Ω)"; // role: z_real
const REACTANCE = "Reactance (Ω)"; // role: z_imag

// Data: replace this block with your own records, one object per row
// Antenna feed impedance swept 1-6 GHz: a series R-L-C model whose radiation resistance
// rises gently with frequency while the reactance swings through resonance.
const data: Record<string, number>[] = [];
for (let i = 0; i <= 40; i += 1) {
  const fGHz = 1 + i * 0.125;
  const omega = 2 * Math.PI * fGHz * 1e9;
  data.push({
    [FREQUENCY]: fGHz,
    [RESISTANCE]: Number((35 + 3 * (fGHz - 1)).toFixed(2)),
    [REACTANCE]: Number((omega * 5e-9 - 1 / (omega * 0.4e-12)).toFixed(2)),
  });
}

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const sweep = [...data].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);

// Γ = (z - 1) / (z + 1) with z = (R + jX) / Z0
const locus = sweep.map((d) => {
  const zr = d[RESISTANCE] / Z0;
  const zi = d[REACTANCE] / Z0;
  const den = (zr + 1) ** 2 + zi ** 2;
  return { f: d[FREQUENCY], re: (zr * zr + zi * zi - 1) / den, im: (2 * zi) / den };
});
const labelIdx = [...new Set(Array.from({ length: LABEL_COUNT }, (_, k) => Math.round((k * (locus.length - 1)) / (LABEL_COUNT - 1))))];
const freqUnit = FREQUENCY.match(/\(([^)]+)\)/)?.[1] ?? "";
const impedanceUnit = RESISTANCE.match(/\(([^)]+)\)/)?.[1] ?? "";

// Grid: constant-reactance arcs run from the open-circuit point (1, 0) to Γ(jx) on the boundary
const arcs = REACTANCE_ARCS.flatMap((x) => [x, -x]).map((x) => ({
  x,
  radius: 1 / Math.abs(x),
  endRe: (x * x - 1) / (x * x + 1),
  endIm: (2 * x) / (x * x + 1),
}));

// Layout: a square drawing area, so one unit of Γ is the same length on both axes
const HEADER_H = 84;
const V_MARGIN = 30;
const chartH = H - HEADER_H;
const side = Math.min(W, chartH) - 2 * V_MARGIN;
const hMargin = (W - side) / 2;
const vMargin = (chartH - side) / 2;

const title = "smith-chart-basic · javascript · muix · anyplot.ai";
const subtitle = `n = ${sweep.length} points · ${FREQUENCY} ${sweep[0][FREQUENCY]} to ${sweep[sweep.length - 1][FREQUENCY]} · impedance normalized to Z₀ = ${Z0} ${impedanceUnit}, matched point at the centre`;

function SmithChart() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const unit = xScale(1) - xScale(0);
  const cx = xScale(0);
  const cy = yScale(0);
  const grid = { fill: "none", stroke: t.inkSoft, strokeWidth: 1, opacity: 0.55 };
  const pts = locus.map((p) => [xScale(p.re), yScale(p.im)]);
  const locusPath = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");
  const rLabels = RESISTANCE_CIRCLES.map((r) => ({ r, x: xScale((r - 1) / (r + 1)) - 4, y: cy + 18 }));
  const xLabels = arcs.map((a) => ({
    x: a.x,
    text: `${a.x > 0 ? "+" : "−"}j${Math.abs(a.x)}`,
    px: xScale(a.endRe * 1.07),
    py: yScale(a.endIm * 1.07),
  }));

  // The locus and the rim as points a few px apart, to measure the room a label box keeps from them
  const rimSamples = Math.ceil((2 * Math.PI * unit) / LABEL_SAMPLE_PX);
  const obstacles = [
    ...pts.flatMap(([x0, y0], i) => {
      const [x1, y1] = pts[Math.min(i + 1, pts.length - 1)];
      const steps = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / LABEL_SAMPLE_PX));
      return Array.from({ length: steps }, (_, s) => [x0 + ((x1 - x0) * s) / steps, y0 + ((y1 - y0) * s) / steps]);
    }),
    ...Array.from({ length: rimSamples }, (_, k) => [
      cx + unit * Math.cos((2 * Math.PI * k) / rimSamples),
      cy + unit * Math.sin((2 * Math.PI * k) / rimSamples),
    ]),
  ];
  // Text boxes already on the chart: the grid values, then each frequency label as it is placed
  const gridHalfH = GRID_FONT_PX * 0.6;
  const boxes = [
    ...rLabels.map((l) => {
      const hw = (`${l.r}`.length * GRID_FONT_PX * GLYPH_EM) / 2;
      return { x: l.x - hw, y: l.y - GRID_FONT_PX * 0.35, hw, hh: gridHalfH };
    }),
    ...xLabels.map((l) => ({ x: l.px, y: l.py, hw: (l.text.length * GRID_FONT_PX * GLYPH_EM) / 2, hh: gridHalfH })),
  ];
  // Each frequency label sits on the locus normal at its point, on the side and at the smallest
  // distance that keep its box clear of the curve, the rim and every other label
  const freqLabels = labelIdx.map((i) => {
    const [px, py] = pts[i];
    const [ax, ay] = pts[Math.max(0, i - 1)];
    const [bx, by] = pts[Math.min(pts.length - 1, i + 1)];
    const len = Math.hypot(bx - ax, by - ay) || 1;
    const text = `${locus[i].f} ${freqUnit}`;
    const hw = (text.length * LABEL_FONT_PX * GLYPH_EM) / 2;
    const hh = LABEL_FONT_PX * 0.6;
    let best = { x: px, y: py, room: -Infinity };
    for (let gap = LABEL_GAP_PX; gap <= LABEL_GAP_MAX_PX && best.room < LABEL_CLEAR_PX; gap += LABEL_STEP_PX) {
      for (const side of [1, -1]) {
        const nx = (-(by - ay) / len) * side;
        const ny = ((bx - ax) / len) * side;
        const reach = gap + Math.abs(nx) * hw + Math.abs(ny) * hh;
        const x = px + nx * reach;
        const y = py + ny * reach;
        const room = Math.min(
          ...obstacles.map(([qx, qy]) => Math.hypot(Math.max(Math.abs(qx - x) - hw, 0), Math.max(Math.abs(qy - y) - hh, 0))),
          ...boxes.map((b) => Math.max(Math.abs(b.x - x) - b.hw - hw, Math.abs(b.y - y) - b.hh - hh)),
        );
        if (room > best.room) best = { x, y, room };
      }
    }
    boxes.push({ x: best.x, y: best.y, hw, hh });
    return { f: locus[i].f, px, py, text, x: best.x, y: best.y };
  });
  return (
    <g>
      <line x1={xScale(-1)} y1={cy} x2={xScale(1)} y2={cy} stroke={t.inkSoft} strokeWidth={1.5} />
      {RESISTANCE_CIRCLES.map((r) => (
        <circle key={`r-${r}`} cx={xScale(r / (1 + r))} cy={cy} r={unit / (1 + r)} {...grid} />
      ))}
      {arcs.map((a) => (
        <path
          key={`x-${a.x}`}
          d={`M ${xScale(1)} ${cy} A ${a.radius * unit} ${a.radius * unit} 0 0 ${a.x > 0 ? 1 : 0} ${xScale(a.endRe)} ${yScale(a.endIm)}`}
          {...grid}
        />
      ))}
      <circle cx={cx} cy={cy} r={unit} fill="none" stroke={t.ink} strokeWidth={2.5} />
      {rLabels.map((l) => (
        <text key={`rl-${l.r}`} x={l.x} y={l.y} textAnchor="end" fontSize={GRID_FONT_PX} fill={t.inkSoft}>
          {l.r}
        </text>
      ))}
      {xLabels.map((l) => (
        <text
          key={`xl-${l.x}`}
          x={l.px}
          y={l.py}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={GRID_FONT_PX}
          fill={t.inkSoft}
        >
          {l.text}
        </text>
      ))}
      <circle cx={cx} cy={cy} r={5} fill="none" stroke={t.ink} strokeWidth={2} />
      <path d={locusPath} fill="none" stroke={t.palette[0]} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />
      {freqLabels.map((l) => (
        <g key={`f-${l.f}`}>
          <circle cx={l.px} cy={l.py} r={8} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={2.5} />
          <text
            x={l.x}
            y={l.y}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={LABEL_FONT_PX}
            fontWeight={600}
            fill={t.ink}
            paintOrder="stroke"
            stroke={t.pageBg}
            strokeWidth={4}
            strokeLinejoin="round"
          >
            {l.text}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        margin={{ top: vMargin, bottom: vMargin, left: hMargin, right: hMargin }}
        series={[]}
        skipAnimation
        xAxis={[{ scaleType: "linear", min: -GAMMA_LIMIT, max: GAMMA_LIMIT, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -GAMMA_LIMIT, max: GAMMA_LIMIT, position: "none" }]}
      >
        <SmithChart />
      </ChartsContainer>
    </div>
  );
}
