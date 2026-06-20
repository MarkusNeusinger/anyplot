//# anyplot-orientation: square
// anyplot.ai
// heatmap-cohort-retention: Cohort Retention Heatmap
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-20

import React from "react";

const tok = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;   // 1200 CSS px (square mount)
const H = window.ANYPLOT_SIZE.height;  // 1200 CSS px

// Layout
const PAD_L = 158;
const PAD_T = 92;
const PAD_R = 88;
const PAD_B = 48;
const N_COHORTS = 10;
const N_PERIODS = 10;
const CELL_W = Math.floor((W - PAD_L - PAD_R) / N_PERIODS);  // ≈ 95
const CELL_H = Math.floor((H - PAD_T - PAD_B) / N_COHORTS);  // ≈ 106

// Monthly cohort metadata
const COHORTS = [
  { label: "Jan 2024", size: 4821 },
  { label: "Feb 2024", size: 3956 },
  { label: "Mar 2024", size: 5234 },
  { label: "Apr 2024", size: 4102 },
  { label: "May 2024", size: 6187 },
  { label: "Jun 2024", size: 5543 },
  { label: "Jul 2024", size: 4798 },
  { label: "Aug 2024", size: 5912 },
  { label: "Sep 2024", size: 4445 },
  { label: "Oct 2024", size: 3821 },
];

// Deterministic LCG for reproducible noise
function makeLcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}
const rng = makeLcg(42);

// Triangular retention matrix: cohort[ci] has (N_PERIODS - ci) data points
// cohort 0 (Jan) → 10 periods, cohort 9 (Oct) → 1 period
const MATRIX = COHORTS.map((_, ci) => {
  const nP = N_PERIODS - ci;
  return Array.from({ length: nP }, (_, pi) => {
    if (pi === 0) return 100;
    // Realistic decay: strong early drop-off with long-tail plateau
    const base = 100 * Math.pow(0.80, pi) + 5 / (1 + 0.4 * pi);
    const noise = (rng() - 0.5) * 10;
    return Math.max(2, Math.min(97, Math.round(base + noise)));
  });
});

// Imprint sequential colormap: seq[0]=#009E73 (green) → seq[1]=#4467A3 (blue)
function hexToRgb(hex) {
  const v = parseInt(hex.replace("#", ""), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

function seqColor(pct) {
  const t = Math.max(0, Math.min(1, pct / 100));
  const [r1, g1, b1] = hexToRgb(tok.seq[0]);
  const [r2, g2, b2] = hexToRgb(tok.seq[1]);
  return `rgb(${Math.round(r1 + t * (r2 - r1))},${Math.round(g1 + t * (g2 - g1))},${Math.round(b1 + t * (b2 - b1))})`;
}

const TITLE = "heatmap-cohort-retention · javascript · muix · anyplot.ai";
const TITLE_FS = Math.max(14, Math.round(22 * Math.min(1, 67 / TITLE.length)));

export default function Chart() {
  const GX = PAD_L;
  const GY = PAD_T;
  const GW = N_PERIODS * CELL_W;
  const GH = N_COHORTS * CELL_H;
  const CX = GX + GW + 24; // colorbar left edge

  return (
    <svg
      width={W}
      height={H}
      style={{ background: tok.pageBg, fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <defs>
        <linearGradient id="retGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={tok.seq[0]} />
          <stop offset="100%" stopColor={tok.seq[1]} />
        </linearGradient>
      </defs>

      {/* Title */}
      <text
        x={W / 2}
        y={38}
        textAnchor="middle"
        fontSize={TITLE_FS}
        fill={tok.ink}
        fontWeight="500"
      >
        {TITLE}
      </text>

      {/* X-axis label */}
      <text
        x={GX + GW / 2}
        y={62}
        textAnchor="middle"
        fontSize={14}
        fill={tok.inkSoft}
      >
        Months Since Signup
      </text>

      {/* Period column numbers */}
      {Array.from({ length: N_PERIODS }, (_, pi) => (
        <text
          key={pi}
          x={GX + pi * CELL_W + CELL_W / 2}
          y={GY - 8}
          textAnchor="middle"
          fontSize={13}
          fill={tok.inkSoft}
        >
          {pi}
        </text>
      ))}

      {/* Cohort rows */}
      {MATRIX.map((row, ci) => {
        const ry = GY + ci * CELL_H;
        const mid = ry + CELL_H / 2;
        return (
          <g key={ci}>
            {/* Cohort month label */}
            <text
              x={GX - 8}
              y={mid - 5}
              textAnchor="end"
              fontSize={14}
              fill={tok.ink}
              fontWeight="500"
            >
              {COHORTS[ci].label}
            </text>
            {/* Cohort size */}
            <text
              x={GX - 8}
              y={mid + 12}
              textAnchor="end"
              fontSize={12}
              fill={tok.inkSoft}
            >
              {`n=${COHORTS[ci].size.toLocaleString()}`}
            </text>
            {/* Retention cells */}
            {row.map((val, pi) => {
              const cx = GX + pi * CELL_W;
              return (
                <g key={pi}>
                  <rect
                    x={cx + 1}
                    y={ry + 1}
                    width={CELL_W - 2}
                    height={CELL_H - 2}
                    fill={seqColor(val)}
                    rx={3}
                  />
                  <text
                    x={cx + CELL_W / 2}
                    y={mid + 5}
                    textAnchor="middle"
                    fontSize={13}
                    fill="#FFFDF6"
                    fontWeight="600"
                  >
                    {`${val}%`}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}

      {/* Colorbar */}
      <text
        x={CX + 8}
        y={GY - 8}
        textAnchor="middle"
        fontSize={12}
        fill={tok.inkSoft}
      >
        Retention
      </text>
      <rect
        x={CX}
        y={GY}
        width={16}
        height={GH}
        fill="url(#retGrad)"
        rx={3}
      />
      {[0, 25, 50, 75, 100].map((pct) => {
        const ty = GY + GH * (1 - pct / 100);
        return (
          <g key={pct}>
            <line
              x1={CX + 16}
              y1={ty}
              x2={CX + 22}
              y2={ty}
              stroke={tok.inkSoft}
              strokeWidth={1}
            />
            <text x={CX + 26} y={ty + 4} fontSize={11} fill={tok.inkSoft}>
              {pct}%
            </text>
          </g>
        );
      })}
    </svg>
  );
}
