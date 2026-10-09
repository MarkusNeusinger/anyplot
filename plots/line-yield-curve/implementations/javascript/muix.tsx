//# anyplot-orientation: landscape
// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-10

import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Maturity axis — numeric years for log-scale spacing, labels for ticks
const maturityYears = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30];
const maturityLabels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"];

// Approximate U.S. Treasury par yields (%) — three eras of the term structure
const jun1993 = [3.0, 3.1, 3.2, 3.4, 3.9, 4.4, 5.2, 5.8, 5.9, 6.6, 6.8]; // Normal: early-1990s recovery
const mar2000 = [5.7, 5.9, 6.1, 6.3, 6.5, 6.4, 6.3, 6.3, 6.2, 6.3, 5.9]; // Humped: dot-com peak
const jan2007 = [5.2, 5.2, 5.1, 5.0, 4.8, 4.7, 4.7, 4.8, 4.8, 5.0, 4.9]; // Inverted: pre-crisis

// Shaded band over the maturities where the Jan 2007 short end sits above its 5Y yield
function InversionBand() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  const x0 = xScale(maturityYears[0]);
  const x1 = xScale(5);
  return (
    <g pointerEvents="none">
      <rect x={x0} y={top} width={x1 - x0} height={height} fill={t.palette[4]} fillOpacity={0.1} />
      <text x={(x0 + x1) / 2} y={top + 24} textAnchor="middle" fontSize={15} fontWeight={500} fill={t.ink}>
        Inversion: short-term yields above long-term
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 0,
          right: 0,
          textAlign: "center",
          zIndex: 1,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          pointerEvents: "none",
          fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
        }}
      >
        U.S. Treasury Yield Curves · line-yield-curve · javascript · muix · anyplot.ai
      </div>

      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height}
        skipAnimation
        grid={{ horizontal: true }}
        colors={[t.palette[0], t.palette[1], t.palette[4]]}
        xAxis={[
          {
            scaleType: "log",
            data: maturityYears,
            tickInterval: maturityYears,
            min: 0.06,
            max: 40,
            valueFormatter: (v) => {
              const idx = maturityYears.findIndex((y) => Math.abs(y - v) < 0.005);
              return idx >= 0 ? maturityLabels[idx] : "";
            },
            label: "Maturity",
          },
        ]}
        yAxis={[
          {
            label: "Yield (%)",
            min: 0,
            max: 7.5,
            tickMinStep: 1,
            valueFormatter: (v) => `${v}%`,
          },
        ]}
        series={[
          { data: jun1993, label: "Jun 1993 (Normal)", showMark: true, curve: "linear" },
          { data: mar2000, label: "Mar 2000 (Humped)", showMark: true, curve: "linear" },
          { data: jan2007, label: "Jan 2007 (Inverted)", showMark: true, curve: "linear" },
        ]}
        sx={{
          "& .MuiChartsAxis-label": { fontSize: "16px !important" },
          "& .MuiChartsAxis-left .MuiChartsAxis-label": { transform: "translateX(-24px)" },
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px !important" },
          "& .MuiChartsLegend-label": { fontSize: "15px !important" },
          "& .MuiChartsGrid-line": { strokeOpacity: 0.25 },
          "& .MuiLineElement-root": { strokeWidth: "3px" },
        }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "bottom", horizontal: "middle" },
          },
        }}
        margin={{ top: 60, right: 60, bottom: 80, left: 110 }}
      >
        <InversionBand />
      </LineChart>
    </div>
  );
}
