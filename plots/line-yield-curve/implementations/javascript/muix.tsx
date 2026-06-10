// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 80/100 | Created: 2026-06-10
//# anyplot-orientation: landscape
// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-10

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Maturity axis — numeric years for log-scale spacing, labels for ticks
const maturityYears = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30];
const maturityLabels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"];

// U.S. Treasury par yields (%) — three snapshots showing term structure evolution
const jan2021 = [0.05, 0.04, 0.06, 0.09, 0.12, 0.22, 0.59, 0.96, 1.08, 1.6, 1.82]; // Normal: COVID-era low rates
const oct2022 = [3.28, 3.82, 4.25, 4.55, 4.63, 4.58, 4.35, 4.25, 4.05, 4.18, 4.1]; // Near-flat: Fed hiking cycle
const jul2023 = [5.51, 5.54, 5.54, 5.36, 4.87, 4.57, 4.28, 4.22, 3.97, 4.27, 4.05]; // Inverted: recession signal

export default function Chart() {
  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* Title rendered in the chart's top margin space */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 0,
          right: 0,
          textAlign: "center",
          zIndex: 1,
          fontSize: 19,
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
        colors={[t.palette[0], t.palette[2], t.palette[4]]}
        xAxis={[
          {
            scaleType: "log",
            data: maturityYears,
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
            max: 6.5,
            valueFormatter: (v) => `${v}%`,
          },
        ]}
        series={[
          {
            data: jan2021,
            label: "Jan 2021 (Normal)",
            showMark: true,
            curve: "catmullRom",
          },
          {
            data: oct2022,
            label: "Oct 2022 (Flat)",
            showMark: true,
            curve: "catmullRom",
          },
          {
            data: jul2023,
            label: "Jul 2023 (Inverted)",
            showMark: true,
            curve: "catmullRom",
          },
        ]}
        sx={{
          "& .MuiChartsAxis-label": {
            fontSize: "16px !important",
          },
          "& .MuiChartsAxis-tickLabel": {
            fontSize: "14px !important",
          },
          "& .MuiChartsLegend-label": {
            fontSize: "15px !important",
          },
          "& .MuiLineElement-root": {
            strokeWidth: "3px",
          },
        }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "bottom", horizontal: "middle" },
          },
        }}
        margin={{ top: 60, right: 60, bottom: 80, left: 90 }}
      >
        <ChartsReferenceLine
          x={1}
          label="Inverted beyond 1Y →"
          labelAlign="start"
          lineStyle={{
            stroke: t.palette[4],
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
            strokeOpacity: 0.55,
          }}
          labelStyle={{
            fill: t.palette[4],
            fontSize: 13,
          }}
        />
      </LineChart>
    </div>
  );
}
