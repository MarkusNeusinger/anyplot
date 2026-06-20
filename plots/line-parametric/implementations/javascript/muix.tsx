// anyplot.ai
// line-parametric: Parametric Curve Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-20

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Linear interpolation between two hex colors (Imprint sequential gradient)
function lerpColor(hex1: string, hex2: string, alpha: number): string {
  const p = (h: string, o: number) => parseInt(h.slice(o, o + 2), 16);
  const r = Math.round(p(hex1, 1) + (p(hex2, 1) - p(hex1, 1)) * alpha);
  const g = Math.round(p(hex1, 3) + (p(hex2, 3) - p(hex1, 3)) * alpha);
  const b = Math.round(p(hex1, 5) + (p(hex2, 5) - p(hex1, 5)) * alpha);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

// --- Data (deterministic, in-memory) ----------------------------------------
const N = 800;
const SEGS = 20;
const PI2 = 2 * Math.PI;

// Lissajous figure: x = sin(3t + π/4), y = sin(2t), t ∈ [0, 2π]
const lissajousPoints = Array.from({ length: N }, (_, i) => {
  const ti = (i / (N - 1)) * PI2;
  return { x: Math.sin(3 * ti + Math.PI / 4), y: Math.sin(2 * ti), id: i };
});

// Archimedean spiral: x = t·cos(t), y = t·sin(t), t ∈ [0, 4π]
const spiralPoints = Array.from({ length: N }, (_, i) => {
  const ti = (i / (N - 1)) * 4 * PI2;
  return { x: ti * Math.cos(ti), y: ti * Math.sin(ti), id: i };
});

// Segment each curve into SEGS color bands for Imprint seq gradient
// #009E73 (brand green, t=start) → #4467A3 (blue, t=end)
const SEQ_START = "#009E73";
const SEQ_END = "#4467A3";

function buildGradientSeries(points: { x: number; y: number; id: number }[]) {
  const segLen = Math.ceil(points.length / SEGS);
  return Array.from({ length: SEGS }, (_, s) => ({
    data: points.slice(s * segLen, Math.min((s + 1) * segLen + 1, points.length)),
    color: lerpColor(SEQ_START, SEQ_END, s / (SEGS - 1)),
    label: "",
    markerSize: 3.5,
    id: `seg-${s}`,
  }));
}

const lissajousSeries = buildGradientSeries(lissajousPoints);
const spiralSeries = buildGradientSeries(spiralPoints);

// --- Chart ------------------------------------------------------------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const half = Math.floor((width - 60) / 2);
  const chartH = height - 100;

  const axisLabel = { fill: t.ink, fontSize: 13 };
  const axisTick = { fill: t.inkSoft, fontSize: 11 };

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        px: 2,
        pt: 1.5,
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 20,
          fontWeight: 500,
          textAlign: "center",
          mb: 1,
          letterSpacing: 0,
        }}
      >
        line-parametric · javascript · muix · anyplot.ai
      </Typography>

      <Box sx={{ display: "flex", gap: 2, flex: 1 }}>
        {/* Lissajous figure */}
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Typography sx={{ color: t.inkSoft, fontSize: 12, mb: 0.5 }}>
            Lissajous Figure &mdash; x = sin(3t + π/4), y = sin(2t), t ∈ [0, 2π]
          </Typography>
          <ScatterChart
            width={half}
            height={chartH}
            skipAnimation
            series={lissajousSeries}
            xAxis={[{
              label: "x(t)",
              labelStyle: axisLabel,
              tickLabelStyle: axisTick,
              min: -1.25,
              max: 1.25,
            }]}
            yAxis={[{
              label: "y(t)",
              labelStyle: axisLabel,
              tickLabelStyle: axisTick,
              min: -1.25,
              max: 1.25,
            }]}
            margin={{ top: 10, bottom: 50, left: 55, right: 20 }}
            slotProps={{ legend: { hidden: true } }}
          />
        </Box>

        {/* Archimedean spiral */}
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Typography sx={{ color: t.inkSoft, fontSize: 12, mb: 0.5 }}>
            Archimedean Spiral &mdash; x = t·cos(t), y = t·sin(t), t ∈ [0, 4π]
          </Typography>
          <ScatterChart
            width={half}
            height={chartH}
            skipAnimation
            series={spiralSeries}
            xAxis={[{
              label: "x(t)",
              labelStyle: axisLabel,
              tickLabelStyle: axisTick,
            }]}
            yAxis={[{
              label: "y(t)",
              labelStyle: axisLabel,
              tickLabelStyle: axisTick,
            }]}
            margin={{ top: 10, bottom: 50, left: 55, right: 20 }}
            slotProps={{ legend: { hidden: true } }}
          />
        </Box>
      </Box>

      <Typography sx={{ color: t.inkSoft, fontSize: 11, textAlign: "center", mt: 0.5 }}>
        Color encodes direction of traversal — green (t = start) → blue (t = end)
      </Typography>
    </Box>
  );
}
