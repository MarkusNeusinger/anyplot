// anyplot.ai
// root-locus-basic: Root Locus Plot for Control Systems
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-18

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const tok = window.ANYPLOT_TOKENS;

// Root locus for G(s) = K / [s(s+2)(s+4)], K ∈ [0, 90]
// Characteristic equation: s³ + 6s² + 8s + K = 0
// Open-loop poles: s = 0, −2, −4
// Asymptote centroid: −2, angles 60° / 180° / 300°
// Breakaway at s ≈ −0.845 (K ≈ 3.08); jω crossing at K = 48 (s = ±j2√2 ≈ ±j2.83)
//
// Strategy: Newton's method finds the lone real root (Branch C),
// then quadratic deflation yields the complex conjugate pair (Branches A & B).

function polyVal(r, K) {
  return r * r * r + 6 * r * r + 8 * r + K;
}

function polyDeriv(r) {
  return 3 * r * r + 12 * r + 8;
}

// Find the leftmost real root via Newton's method (Branch C: starts at −4)
function findRealRoot(K, guess) {
  let r = guess;
  for (let it = 0; it < 80; it++) {
    const f = polyVal(r, K);
    const fp = polyDeriv(r);
    if (Math.abs(fp) < 1e-15) break;
    const delta = f / fp;
    r -= delta;
    if (Math.abs(delta) < 1e-12) break;
  }
  return r;
}

// Given the real root r3, deflate: (s - r3)(s² + b·s + c) = s³ + 6s² + 8s + K
// yields  b = 6 + r3,  c = 8 + r3·b
// Roots of the quadratic are the Branches A (upper) and B (lower)
function complexPair(r3) {
  const b = 6 + r3;
  const c = 8 + r3 * b;
  const disc = b * b - 4 * c;
  if (disc >= 0) {
    const sq = Math.sqrt(disc);
    // Both real: larger (rightmost) → Branch A, smaller → Branch B
    return [
      { re: (-b + sq) / 2, im: 0 },
      { re: (-b - sq) / 2, im: 0 },
    ];
  }
  // Complex conjugate pair: upper → Branch A, lower → Branch B
  const sq = Math.sqrt(-disc);
  return [
    { re: -b / 2, im: sq / 2 },
    { re: -b / 2, im: -sq / 2 },
  ];
}

const N_K = 500;
const K_MAX = 90;

const branchA = []; // s = 0 at K=0 → upper half-plane after breakaway
const branchB = []; // s = −2 at K=0 → lower half-plane after breakaway
const branchC = []; // s = −4 at K=0 → −∞ on negative real axis

let r3 = -4.001; // track real root incrementally for fast Newton convergence

for (let i = 0; i <= N_K; i++) {
  const K = (i / N_K) * K_MAX;
  r3 = findRealRoot(K, r3);
  const pair = complexPair(r3);

  const id = i;
  branchA.push({ x: Math.round(pair[0].re * 1e4) / 1e4, y: Math.round(pair[0].im * 1e4) / 1e4, id });
  branchB.push({ x: Math.round(pair[1].re * 1e4) / 1e4, y: Math.round(pair[1].im * 1e4) / 1e4, id: id + N_K + 1 });
  branchC.push({ x: Math.round(r3 * 1e4) / 1e4, y: 0, id: id + 2 * (N_K + 1) });
}

// Open-loop poles at K = 0
const openLoopPoles = [
  { x: 0, y: 0, id: "p0" },
  { x: -2, y: 0, id: "p1" },
  { x: -4, y: 0, id: "p2" },
];

const TITLE_H = 58;

export default function Chart() {
  return (
    <Box
      sx={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography
        sx={{
          color: "text.primary",
          fontWeight: 500,
          fontSize: 22,
          textAlign: "center",
          lineHeight: `${TITLE_H}px`,
          height: TITLE_H,
          flexShrink: 0,
        }}
      >
        root-locus-basic · javascript · muix · anyplot.ai
      </Typography>
      <ScatterChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height - TITLE_H}
        skipAnimation
        series={[
          {
            label: "Branch A  (s=0 → upper half-plane)",
            data: branchA,
            color: tok.palette[0],
            markerSize: 3,
          },
          {
            label: "Branch B  (s=−2 → lower half-plane)",
            data: branchB,
            color: tok.palette[1],
            markerSize: 3,
          },
          {
            label: "Branch C  (s=−4 → −∞)",
            data: branchC,
            color: tok.palette[2],
            markerSize: 3,
          },
          {
            label: "Open-loop poles  (K=0)",
            data: openLoopPoles,
            color: tok.ink,
            markerSize: 16,
          },
        ]}
        xAxis={[
          {
            label: "Real Axis  σ",
            min: -9,
            max: 3,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            label: "Imaginary Axis  jω",
            min: -4.5,
            max: 4.5,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        slotProps={{
          legend: {
            labelStyle: { fontSize: 13 },
          },
        }}
      >
        <ChartsReferenceLine
          x={0}
          label="Stability boundary (K=48)"
          lineStyle={{
            stroke: tok.amber,
            strokeDasharray: "8 5",
            strokeWidth: 2,
          }}
          labelStyle={{ fontSize: 12, fill: tok.amber }}
        />
      </ScatterChart>
    </Box>
  );
}
