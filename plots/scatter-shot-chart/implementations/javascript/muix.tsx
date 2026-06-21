// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-21
//# anyplot-orientation: square
// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-21

import * as React from "react";
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;
const COURT_STROKE =
  THEME === "light" ? "rgba(26,26,23,0.40)" : "rgba(240,239,232,0.50)";

// --- Deterministic shot data (LCG seed=42) ------------------------------------
function makeLCG(seed) {
  let s = seed >>> 0;
  return function () {
    s = ((Math.imul(1664525, s) + 1013904223) >>> 0);
    return s / 4294967296;
  };
}

// NBA half-court: x ∈ [-25, 25] ft, y ∈ [0, 47] ft (y=0 baseline)
// Basket center at (0, 5.25 ft from baseline)
const BASKET_Y = 5.25;
const THREE_PT_R = 23.75;
const CORNER_X = 22;
const CORNER_TOP_Y = BASKET_Y + Math.sqrt(THREE_PT_R ** 2 - CORNER_X ** 2); // ≈ 14.2 ft

function generateShots() {
  const rng = makeLCG(42);
  const shots = [];

  for (let i = 0; i < 300; i++) {
    const zone = rng();
    let x, y, isThree;

    if (zone < 0.20) {
      // At the rim / paint close range
      const angle = rng() * Math.PI;
      const dist = rng() * 4 + 0.5;
      x = Math.cos(angle) * dist;
      y = BASKET_Y + Math.abs(Math.sin(angle)) * dist;
      isThree = false;
    } else if (zone < 0.25) {
      // Left corner three
      x = -(rng() * 2.5 + 21.5);
      y = rng() * 10 + 0.5;
      isThree = true;
    } else if (zone < 0.30) {
      // Right corner three
      x = rng() * 2.5 + 21.5;
      y = rng() * 10 + 0.5;
      isThree = true;
    } else if (zone < 0.58) {
      // Mid-range (inside three-point line)
      const angle = rng() * Math.PI;
      const dist = rng() * 8 + 9;
      x = Math.cos(angle) * dist;
      y = BASKET_Y + Math.sin(angle) * dist;
      if (y < 0.5) y = 0.5 + rng() * 2;
      const d = Math.sqrt(x ** 2 + (y - BASKET_Y) ** 2);
      if (d > 22) { x = (x / d) * 21.5; y = BASKET_Y + ((y - BASKET_Y) / d) * 21.5; }
      isThree = false;
    } else {
      // Arc three-pointers
      const angle = rng() * Math.PI;
      const dist = rng() * 4.5 + THREE_PT_R;
      x = Math.cos(angle) * dist;
      y = BASKET_Y + Math.sin(angle) * dist;
      if (y < 0.5) y = 0.5 + rng() * 2;
      if (y > 44) y = 44;
      x = Math.max(-24.5, Math.min(24.5, x));
      isThree = true;
    }

    const d = Math.sqrt(x ** 2 + (y - BASKET_Y) ** 2);
    const makePct = isThree ? 0.37 : d < 7 ? 0.60 : 0.41;
    const made = rng() < makePct;

    shots.push({ id: i, x: parseFloat(x.toFixed(2)), y: parseFloat(y.toFixed(2)), made });
  }
  return shots;
}

const allShots = generateShots();
const madeShots = allShots.filter((s) => s.made).map((s) => ({ id: s.id, x: s.x, y: s.y }));
const missedShots = allShots.filter((s) => !s.made).map((s) => ({ id: s.id, x: s.x, y: s.y }));

// Data bounds: x ∈ [-25, 25], y ∈ [0, 47]
const X_MIN = -25, X_MAX = 25, Y_MIN = 0, Y_MAX = 47;

// --- Basketball court SVG overlay (uses drawing area + manual scale) ----------
function BasketballCourt() {
  const { left, top, width, height } = useDrawingArea();

  // Linear scales from data coordinates to SVG pixel coordinates
  const cx = (ft) => left + ((ft - X_MIN) / (X_MAX - X_MIN)) * width;
  const cy = (ft) => top + ((Y_MAX - ft) / (Y_MAX - Y_MIN)) * height;

  // Radii in SVG pixels (using x-direction scale; ~equal to y-direction)
  const threeR_x = (THREE_PT_R / (X_MAX - X_MIN)) * width;
  const threeR_y = (THREE_PT_R / (Y_MAX - Y_MIN)) * height;
  const ftCircR = (6 / (X_MAX - X_MIN)) * width;
  const raR_x = (4 / (X_MAX - X_MIN)) * width;
  const raR_y = (4 / (Y_MAX - Y_MIN)) * height;
  const basketR = (0.75 / (X_MAX - X_MIN)) * width;

  const ls = {
    fill: "none",
    stroke: COURT_STROKE,
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  // Three-point arc: from left corner (-22, ~14.2) to right corner (22, ~14.2)
  // sweep=1 (clockwise in SVG) → arc curves toward half-court (away from basket)
  // large-arc=0 → spans ~136°, the smaller of the two arcs
  return (
    <g>
      {/* Court boundary (baseline + sidelines + half-court line) */}
      <rect
        x={cx(-25)}
        y={cy(47)}
        width={cx(25) - cx(-25)}
        height={cy(0) - cy(47)}
        style={{ ...ls, strokeWidth: 2.5 }}
      />

      {/* Paint / key area */}
      <rect
        x={cx(-8)}
        y={cy(19)}
        width={cx(8) - cx(-8)}
        height={cy(0) - cy(19)}
        style={ls}
      />

      {/* Free throw circle */}
      <ellipse
        cx={cx(0)}
        cy={cy(19)}
        rx={ftCircR}
        ry={(6 / (Y_MAX - Y_MIN)) * height}
        style={ls}
      />

      {/* Restricted area arc (semicircle above baseline) */}
      <path
        d={`M ${cx(-4)} ${cy(BASKET_Y)} A ${raR_x} ${raR_y} 0 0 1 ${cx(4)} ${cy(BASKET_Y)}`}
        style={ls}
      />

      {/* Corner three-point straight lines */}
      <line x1={cx(-CORNER_X)} y1={cy(0)} x2={cx(-CORNER_X)} y2={cy(CORNER_TOP_Y)} style={ls} />
      <line x1={cx(CORNER_X)} y1={cy(0)} x2={cx(CORNER_X)} y2={cy(CORNER_TOP_Y)} style={ls} />

      {/* Three-point arc (large-arc=0, sweep=1 → upper arc curving toward half-court) */}
      <path
        d={`M ${cx(-CORNER_X)} ${cy(CORNER_TOP_Y)} A ${threeR_x} ${threeR_y} 0 0 1 ${cx(CORNER_X)} ${cy(CORNER_TOP_Y)}`}
        style={ls}
      />

      {/* Backboard */}
      <line
        x1={cx(-3)}
        y1={cy(4)}
        x2={cx(3)}
        y2={cy(4)}
        style={{ ...ls, strokeWidth: 4 }}
      />

      {/* Basket rim */}
      <ellipse
        cx={cx(0)}
        cy={cy(BASKET_Y)}
        rx={basketR}
        ry={(0.75 / (Y_MAX - Y_MIN)) * height}
        style={{ ...ls, strokeWidth: 2.5 }}
      />
    </g>
  );
}

// --- Chart title as SVG text above the drawing area --------------------------
function ChartTitle() {
  const { left, top, width } = useDrawingArea();
  const title = "scatter-shot-chart · javascript · muix · anyplot.ai";
  return (
    <text
      x={left + width / 2}
      y={top - 24}
      textAnchor="middle"
      style={{
        fontSize: 22,
        fontFamily: "Inter, system-ui, -apple-system, sans-serif",
        fill: t.ink,
      }}
    >
      {title}
    </text>
  );
}

// --- Main chart component ----------------------------------------------------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <ChartContainer
      width={W}
      height={H}
      series={[
        {
          type: "scatter",
          id: "missed",
          label: "Missed",
          data: missedShots,
          color: "#AE3030",
          markerSize: 9,
        },
        {
          type: "scatter",
          id: "made",
          label: "Made",
          data: madeShots,
          color: "#009E73",
          markerSize: 9,
        },
      ]}
      xAxis={[{ min: X_MIN, max: X_MAX }]}
      yAxis={[{ min: Y_MIN, max: Y_MAX }]}
      margin={{ top: 70, bottom: 80, left: 42, right: 42 }}
    >
      <BasketballCourt />
      <ScatterPlot />
      <ChartsLegend
        position={{ vertical: "bottom", horizontal: "middle" }}
        slotProps={{
          legend: {
            direction: "row",
            itemMarkWidth: 20,
            itemMarkHeight: 20,
            padding: 12,
            labelStyle: {
              fontSize: 20,
              fill: t.ink,
            },
          },
        }}
      />
      <ChartTitle />
    </ChartContainer>
  );
}
