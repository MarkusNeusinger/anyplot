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
const LABEL_OFFSET_PX = 26;

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
  const locusPath = locus.map((p, i) => `${i === 0 ? "M" : "L"}${xScale(p.re)},${yScale(p.im)}`).join(" ");
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
      {RESISTANCE_CIRCLES.map((r) => (
        <text
          key={`rl-${r}`}
          x={xScale((r - 1) / (r + 1)) - 4}
          y={cy + 18}
          textAnchor="end"
          fontSize={14}
          fill={t.inkSoft}
        >
          {r}
        </text>
      ))}
      {arcs.map((a) => (
        <text
          key={`xl-${a.x}`}
          x={xScale(a.endRe * 1.07)}
          y={yScale(a.endIm * 1.07)}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={14}
          fill={t.inkSoft}
        >
          {`${a.x > 0 ? "+" : "−"}j${Math.abs(a.x)}`}
        </text>
      ))}
      <circle cx={cx} cy={cy} r={5} fill="none" stroke={t.ink} strokeWidth={2} />
      <path d={locusPath} fill="none" stroke={t.palette[0]} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />
      {labelIdx.map((i) => {
        const p = locus[i];
        const px = xScale(p.re);
        const py = yScale(p.im);
        const dist = Math.hypot(px - cx, py - cy) || 1;
        const ux = (px - cx) / dist;
        const uy = (py - cy) / dist;
        return (
          <g key={`f-${p.f}`}>
            <circle cx={px} cy={py} r={8} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={2.5} />
            <text
              x={px + ux * LABEL_OFFSET_PX}
              y={py + uy * LABEL_OFFSET_PX}
              textAnchor={ux > 0.15 ? "start" : ux < -0.15 ? "end" : "middle"}
              dominantBaseline={uy > 0.15 ? "hanging" : uy < -0.15 ? "auto" : "central"}
              fontSize={15}
              fontWeight={600}
              fill={t.ink}
              paintOrder="stroke"
              stroke={t.pageBg}
              strokeWidth={4}
              strokeLinejoin="round"
            >
              {`${p.f} ${freqUnit}`}
            </text>
          </g>
        );
      })}
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
