// anyplot.ai
// heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05
//# anyplot-orientation: square
// anyplot.ai
// heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

// @mui/x-charts 7.x community has neither a polar coordinate system nor a
// Heatmap component (Heatmap ships only in the paid @mui/x-charts-pro), so the
// polar grid is composed directly on MUI X's own surface: ChartContainer draws
// the sized <svg> + drawing area, useDrawingArea() gives the plot rect the
// wedges are mapped onto, and a zAxis continuous colorMap feeds the same
// ContinuousColorLegend component ScatterChart heatmaps use elsewhere in this
// catalog — a real gradient legend, not a drawn stand-in.

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) — hourly website visits by day of week ---
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = 24;

function gauss(x, mu, sigma) {
  const d = x - mu;
  return Math.exp(-(d * d) / (2 * sigma * sigma));
}

// Distance around the 24h clock face, so a peak near midnight (hour 23 vs.
// hour 0) is treated as adjacent rather than 23 hours apart.
function cyclicDist(hour, center) {
  const d = Math.abs(hour - center);
  return Math.min(d, HOURS - d);
}

function visits(dayIdx, hour) {
  const isWeekend = dayIdx >= 5; // Sat, Sun
  const isNightlifeDay = dayIdx === 4 || dayIdx === 5; // Fri, Sat late-night crowd
  const base = 14;
  const morning = isWeekend ? 55 * gauss(hour, 10, 3.2) : 92 * gauss(hour, 8.5, 2.1);
  const evening = isWeekend ? 85 * gauss(hour, 15.5, 4.2) : 68 * gauss(hour, 19, 2.6);
  // Peaks exactly at midnight — the case a rectangular heatmap would split
  // across its first/last column instead of showing as one continuous band.
  const nightlife = isNightlifeDay ? 48 * gauss(cyclicDist(hour, 0), 0, 2.4) : 0;
  return base + morning + evening + nightlife;
}

const cells = [];
let minValue = Infinity;
let maxValue = -Infinity;
for (let day = 0; day < DAYS.length; day += 1) {
  for (let hour = 0; hour < HOURS; hour += 1) {
    const value = visits(day, hour);
    cells.push({ day, hour, value });
    minValue = Math.min(minValue, value);
    maxValue = Math.max(maxValue, value);
  }
}
const MIN_LABEL = `${Math.round(minValue)} visits/hr`;
const MAX_LABEL = `${Math.round(maxValue)} visits/hr`;

// --- Sequential Imprint color scale (imprint_seq: brand green -> blue) --------
function mixHex(hexA, hexB, ratio) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const channel = (shift) => {
    const av = (a >> shift) & 255;
    const bv = (b >> shift) & 255;
    return Math.round(av + (bv - av) * ratio);
  };
  return `#${[16, 8, 0].map((shift) => channel(shift).toString(16).padStart(2, "0")).join("")}`;
}
function seqColor(frac) {
  return mixHex(t.seq[0], t.seq[1], Math.max(0, Math.min(1, frac)));
}

// --- Title (fontsize scaled to the 67-char mandated-title baseline) ----------
const TITLE = "Website Traffic by Hour & Day · heatmap-polar · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = Math.max(15, Math.round(22 * Math.min(1, 67 / TITLE.length)));

// Angular axis: a small gap at the top (12am boundary) holds the radial-axis
// day labels so they never sit on top of a colored wedge.
const GAP_DEG = 10;
const START_ANGLE = GAP_DEG / 2;
const SWEEP_DEG = 360 - GAP_DEG;
const ANGLE_PER_HOUR = SWEEP_DEG / HOURS;
const RING_HOLE_RATIO = 0.16;
const LABEL_PAD = 40;

// --- Polar heatmap layer: rendered as children inside MUI X's ChartsSurface ---
function PolarHeatmapLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const outerR = Math.min(area.width, area.height) / 2 - LABEL_PAD;
  const innerR = outerR * RING_HOLE_RATIO;
  const ringThickness = (outerR - innerR) / DAYS.length;

  // angle 0 = straight up (12am gap), increasing clockwise — matches a clock face.
  const polarPoint = (angleDeg, r) => {
    const rad = (angleDeg * Math.PI) / 180;
    return [cx + r * Math.sin(rad), cy - r * Math.cos(rad)];
  };

  const wedgePath = (r0, r1, a0, a1) => {
    const [x0, y0] = polarPoint(a0, r1);
    const [x1, y1] = polarPoint(a1, r1);
    const [x2, y2] = polarPoint(a1, r0);
    const [x3, y3] = polarPoint(a0, r0);
    return `M ${x0} ${y0} A ${r1} ${r1} 0 0 1 ${x1} ${y1} L ${x2} ${y2} A ${r0} ${r0} 0 0 0 ${x3} ${y3} Z`;
  };

  const hourMarks = [
    { hour: 0, label: "12am" },
    { hour: 6, label: "6am" },
    { hour: 12, label: "12pm" },
    { hour: 18, label: "6pm" },
  ];

  return (
    <g>
      {cells.map((cell) => {
        const r0 = innerR + cell.day * ringThickness;
        const r1 = r0 + ringThickness;
        const a0 = START_ANGLE + cell.hour * ANGLE_PER_HOUR;
        const a1 = a0 + ANGLE_PER_HOUR;
        const frac = (cell.value - minValue) / (maxValue - minValue);
        return (
          <path
            key={`${cell.day}-${cell.hour}`}
            d={wedgePath(r0, r1, a0, a1)}
            fill={seqColor(frac)}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
        );
      })}

      {hourMarks.map(({ hour, label }) => {
        const angle = START_ANGLE + (hour + 0.5) * ANGLE_PER_HOUR;
        const [lx, ly] = polarPoint(angle, outerR + 24);
        const dx = lx - cx;
        const dy = ly - cy;
        const anchor = dx > 8 ? "start" : dx < -8 ? "end" : "middle";
        const baseline = dy > 8 ? "hanging" : dy < -8 ? "auto" : "central";
        return (
          <text
            key={`hour-${hour}`}
            x={lx}
            y={ly}
            fill={t.inkSoft}
            fontSize={16}
            textAnchor={anchor}
            dominantBaseline={baseline}
          >
            {label}
          </text>
        );
      })}

      {DAYS.map((day, i) => {
        const r = innerR + (i + 0.5) * ringThickness;
        const [lx, ly] = polarPoint(0, r);
        return (
          <text
            key={`day-${day}`}
            x={lx}
            y={ly}
            fill={t.ink}
            fontSize={14}
            fontWeight={600}
            textAnchor="middle"
            dominantBaseline="central"
          >
            {day}
          </text>
        );
      })}
    </g>
  );
}

function Title() {
  return (
    <text x={size.width / 2} y={64} fill={t.ink} fontSize={TITLE_FONT_SIZE} fontWeight={500} textAnchor="middle">
      {TITLE}
    </text>
  );
}

// --- Chart (default-exported component — the harness mounts it) --------------
export default function Chart() {
  return (
    <ChartContainer
      width={size.width}
      height={size.height}
      series={[]}
      zAxis={[
        {
          id: "visits",
          min: minValue,
          max: maxValue,
          colorMap: { type: "continuous", min: minValue, max: maxValue, color: seqColor },
        },
      ]}
      margin={{ top: 130, bottom: 130, left: 70, right: 70 }}
      skipAnimation
    >
      <Title />
      <PolarHeatmapLayer />
      <ContinuousColorLegend
        axisId="visits"
        axisDirection="z"
        position={{ horizontal: "middle", vertical: "bottom" }}
        length="45%"
        thickness={16}
        minLabel={MIN_LABEL}
        maxLabel={MAX_LABEL}
        labelStyle={{ fontSize: 14, fill: t.inkSoft, fontFamily: "inherit" }}
      />
    </ChartContainer>
  );
}
