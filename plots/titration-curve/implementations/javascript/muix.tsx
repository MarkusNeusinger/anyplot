// anyplot.ai
// titration-curve: Acid-Base Titration Curve
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-24

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH -----------------
const N = 201;
const VOL_MAX = 50;
const EQ_VOL = 25;

function phAt(V) {
  // Exact equivalence point
  if (Math.abs(V - EQ_VOL) < 1e-4) return 7.0;
  if (V < EQ_VOL) {
    // Excess HCl region
    const excessH = 0.0025 - V * 1e-4;
    return Math.max(0, -Math.log10(excessH / ((25 + V) / 1000)));
  }
  // Excess NaOH region
  const excessOH = (V - EQ_VOL) * 1e-4;
  const pOH = -Math.log10(excessOH / ((25 + V) / 1000));
  return Math.min(14, 14 - pOH);
}

// 201 evenly-spaced volume points (0–50 mL); index 100 = 25.00 mL exactly
const volumes = Array.from({ length: N }, (_, i) =>
  parseFloat(((i / (N - 1)) * VOL_MAX).toFixed(2))
);
const phData = volumes.map((v) => parseFloat(phAt(v).toFixed(3)));

// Central-difference derivative dpH/dV — peaks at the equivalence point
const derivData = volumes.map((_, i) => {
  if (i === 0 || i === N - 1) return 0;
  const dv = volumes[i + 1] - volumes[i - 1];
  const dph = phData[i + 1] - phData[i - 1];
  return parseFloat((dph / dv).toFixed(3));
});

const maxDeriv = Math.max(...derivData); // ≈ 14.8 at equivalence

// --- Chart ---------------------------------------------------------------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const TITLE_H = 60;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Chart title */}
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center" }}>
        <Typography
          sx={{
            fontSize: 22,
            fontWeight: 500,
            color: t.ink,
            letterSpacing: 0.3,
          }}
        >
          titration-curve · javascript · muix · anyplot.ai
        </Typography>
      </Box>

      <LineChart
        width={W}
        height={H - TITLE_H}
        skipAnimation
        colors={[t.palette[0], t.palette[1]]}
        xAxis={[
          {
            id: "vol",
            data: volumes,
            scaleType: "linear",
            label: "Volume of NaOH added (mL)",
            min: 0,
            max: VOL_MAX,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            id: "ph",
            min: 0,
            max: 14,
            label: "pH",
            tickNumber: 8,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
          {
            id: "deriv",
            position: "right",
            min: 0,
            max: Math.ceil(maxDeriv * 1.2),
            label: "dpH/dV (mL⁻¹)",
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        series={[
          {
            data: phData,
            label: "pH",
            yAxisId: "ph",
            showMark: false,
            curve: "monotoneX",
            strokeWidth: 3,
          },
          {
            data: derivData,
            label: "dpH/dV",
            yAxisId: "deriv",
            showMark: false,
            curve: "monotoneX",
            strokeWidth: 2,
          },
        ]}
        margin={{ top: 30, bottom: 90, left: 90, right: 120 }}
        slotProps={{
          legend: {
            position: { vertical: "top", horizontal: "right" },
            itemMarkWidth: 18,
            itemMarkHeight: 3,
            labelStyle: { fontSize: 14 },
          },
        }}
      >
        <ChartsReferenceLine
          x={EQ_VOL}
          lineStyle={{
            strokeDasharray: "8 5",
            stroke: t.inkSoft,
            strokeWidth: 1.5,
          }}
          label="Equivalence Point — 25 mL, pH 7"
          labelAlign="start"
          labelStyle={{ fontSize: 13, fill: t.inkSoft }}
        />
      </LineChart>
    </Box>
  );
}
