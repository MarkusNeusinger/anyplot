//# anyplot-orientation: square
// anyplot.ai
// nyquist-basic: Nyquist Plot for Control Systems
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-17

import { ScatterChart } from "@mui/x-charts/ScatterChart";

const t = window.ANYPLOT_TOKENS;

// Transfer function: G(s) = 1 / (s · (1+s) · (1+0.5s))
// Denominator at s=jω: d = -1.5ω² + jω(1 − 0.5ω²)
// G(jω) = conj(d) / |d|²
function gjw(omega) {
  const re = -1.5 * omega * omega;
  const im = omega * (1 - 0.5 * omega * omega);
  const m2 = re * re + im * im;
  return [re / m2, -im / m2];
}

// Nyquist curve: ω from 0.4 to 25 rad/s, 400 log-spaced points
const nyquistData = Array.from({ length: 400 }, (_, k) => {
  const omega = 0.4 * Math.pow(62.5, k / 399);
  const [x, y] = gjw(omega);
  return { x, y, id: k };
});

// Unit circle reference: 600 points for visual continuity
const circleData = Array.from({ length: 601 }, (_, k) => {
  const theta = (2 * Math.PI * k) / 600;
  return { x: Math.cos(theta), y: Math.sin(theta), id: 1000 + k };
});

// Key frequency markers: gain crossover ≈ 0.75 rad/s, phase crossover = √2 rad/s, ω = 5
const keyFreqData = [0.75, Math.SQRT2, 5].map((omega, i) => {
  const [x, y] = gjw(omega);
  return { x, y, id: 2000 + i };
});

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleH = 52;
  const chartSize = Math.min(width - 8, height - titleH - 14);

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "14px 4px 4px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          fontSize: "22px",
          fontWeight: 500,
          color: t.ink,
          marginBottom: "10px",
          textAlign: "center",
          letterSpacing: "0.01em",
        }}
      >
        nyquist-basic · javascript · muix · anyplot.ai
      </div>
      <ScatterChart
        width={chartSize}
        height={chartSize}
        skipAnimation
        series={[
          {
            data: nyquistData,
            label: "G(jω) — Open-loop Response",
            color: t.palette[0],
            markerSize: 2.5,
          },
          {
            data: circleData,
            label: "Unit Circle",
            color: t.inkSoft,
            markerSize: 2,
          },
          {
            data: keyFreqData,
            label: "Key Frequencies (ω_gc, ω_pc, ω=5)",
            color: t.palette[1],
            markerSize: 7,
          },
          {
            data: [{ x: -1, y: 0, id: 9999 }],
            label: "Critical Point (−1, 0)",
            color: "#AE3030",
            markerSize: 10,
          },
        ]}
        xAxis={[{ label: "Real", min: -2.0, max: 1.5, showGrid: true }]}
        yAxis={[{ label: "Imaginary", min: -2.0, max: 1.5, showGrid: true }]}
        margin={{ left: 80, right: 35, top: 35, bottom: 80 }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "14px" },
          "& .MuiChartsGrid-line": { stroke: t.inkSoft, strokeOpacity: 0.2 },
        }}
      />
    </div>
  );
}
