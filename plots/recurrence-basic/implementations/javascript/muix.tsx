//# anyplot-orientation: square
// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-10

import { ScatterChart } from "@mui/x-charts/ScatterChart";

const t = window.ANYPLOT_TOKENS;

// Logistic map — chaotic regime (r = 3.95), deterministic seed via fixed start
const N = 300;
const r = 3.95;
const ts: number[] = [0.4];
for (let i = 1; i < N; i++) {
  ts.push(r * ts[i - 1] * (1 - ts[i - 1]));
}

// Time-delay embedding: state[i] = [ts[i], ts[i + tau]] (Takens' theorem)
const tau = 5;
const M = N - tau; // 295 embedded state vectors
const states = Array.from({ length: M }, (_, i) => [ts[i], ts[i + tau]]);

// Binary recurrence: pairs (i, j) where Euclidean distance < epsilon
const epsilon = 0.15;
const recPts: { x: number; y: number; id: number }[] = [];
let ptId = 0;
for (let i = 0; i < M; i++) {
  for (let j = 0; j < M; j++) {
    const dx = states[i][0] - states[j][0];
    const dy = states[i][1] - states[j][1];
    if (dx * dx + dy * dy < epsilon * epsilon) {
      recPts.push({ x: i, y: j, id: ptId++ });
    }
  }
}

// Title layout
const TITLE_H = 52;

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const side = H - TITLE_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 18, fontWeight: 500, color: t.ink }}>
          recurrence-basic · javascript · muix · anyplot.ai
        </span>
      </div>
      <ScatterChart
        width={side}
        height={side}
        skipAnimation
        colors={[t.palette[0]]}
        margin={{ top: 25, bottom: 70, left: 75, right: 20 }}
        series={[
          {
            data: recPts,
            markerSize: 2,
            label: "Recurrent",
          },
        ]}
        xAxis={[
          {
            label: "Time Index i",
            min: 0,
            max: M - 1,
            tickLabelStyle: { fontSize: 11 },
            labelStyle: { fontSize: 13 },
          },
        ]}
        yAxis={[
          {
            label: "Time Index j",
            min: 0,
            max: M - 1,
            tickLabelStyle: { fontSize: 11 },
            labelStyle: { fontSize: 13 },
          },
        ]}
        sx={{
          "& .MuiChartsLegend-root": { display: "none" },
        }}
      />
    </div>
  );
}
