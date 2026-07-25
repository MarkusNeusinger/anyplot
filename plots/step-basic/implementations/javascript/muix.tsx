// anyplot.ai
// step-basic: Basic Step Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25

import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const sz = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ---------------------------------------
// Warehouse inventory level, sampled daily over a month. Stock holds
// constant between restock/shipment events, then jumps or drops on the
// event day — a textbook "stepAfter" pattern (the reported value applies
// from the current day until the next reading).
const days = Array.from({ length: 24 }, (_, i) => i + 1);
const unitsInStock = [
  500, 500, 460, 460, 460, 410, 410, 410, 680, 680, 680, 630, 630, 580, 580,
  580, 820, 820, 760, 760, 760, 700, 700, 650,
];

const margin = { top: 90, bottom: 80, left: 110, right: 60 };

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <Box sx={{ position: "relative", width: sz.width, height: sz.height }}>
      <Typography
        sx={{
          position: "absolute",
          top: 14,
          left: 0,
          right: 0,
          textAlign: "center",
          color: t.ink,
          fontSize: 22,
          fontWeight: 600,
          zIndex: 1,
          pointerEvents: "none",
        }}
      >
        step-basic · javascript · muix · anyplot.ai
      </Typography>

      {/* Rotated y-axis label, centered on the drawing area — rendered
          manually because ChartsYAxis positions its built-in `label` from
          `tickFontSize` rather than the tick labels' measured width, which
          overlaps 3-digit tick numbers at this font size. */}
      <Box
        sx={{
          position: "absolute",
          left: 4,
          top: margin.top,
          height: sz.height - margin.top - margin.bottom,
          width: 28,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
        }}
      >
        <Typography sx={{ transform: "rotate(-90deg)", whiteSpace: "nowrap", color: t.ink, fontSize: 16 }}>
          Units in Stock
        </Typography>
      </Box>

      <LineChart
        width={sz.width}
        height={sz.height}
        skipAnimation
        margin={margin}
        colors={[t.palette[0]]}
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: days,
            label: "Day of Month",
            scaleType: "linear",
            tickNumber: 12,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={[
          {
            data: unitsInStock,
            label: "Warehouse Inventory",
            curve: "stepAfter",
            showMark: true,
            area: false,
          },
        ]}
        slotProps={{ legend: { hidden: true } }}
      />
    </Box>
  );
}
