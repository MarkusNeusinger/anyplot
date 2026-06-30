// anyplot.ai
// area-mountain-panorama: Wallis Alps — Riffelberg Panorama
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-30

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { AreaPlot, LinePlot } from "@mui/x-charts/LineChart";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

const INK = THEME === "light" ? "#1A1A17" : "#F0EFE8";
const INK_SOFT = THEME === "light" ? "#4A4A44" : "#B8B7B0";
const PAGE_BG = THEME === "light" ? "#FAF8F1" : "#1A1A17";
const SKY_TOP = THEME === "light" ? "#7AAFC8" : "#05101C";
const SKY_BTM = THEME === "light" ? "#CCE8F2" : "#122030";

// Mountain silhouette — dark rock fill, theme-independent for photo-like feel
const SILHOUETTE = "#182430";
const RIDGE_COLOR = "#2C4A62";

// Wallis peaks visible from Riffelberg (3135 m), Zermatt — SW→N bearing sweep
const PEAKS = [
  { name: "Weisshorn",     angle: 211.5, elev: 4506, lw: 10, rw: 7,  off: 115 },
  { name: "Zinalrothorn",  angle: 220,   elev: 4221, lw: 6,  rw: 8,  off: 60  },
  { name: "Obergabelhorn", angle: 228,   elev: 4063, lw: 7,  rw: 6,  off: 110 },
  { name: "Dent Blanche",  angle: 237,   elev: 4358, lw: 6,  rw: 9,  off: 65  },
  { name: "Matterhorn",    angle: 253,   elev: 4478, lw: 9,  rw: 7,  off: 145 },
  { name: "Breithorn",     angle: 271,   elev: 4164, lw: 6,  rw: 5,  off: 75  },
  { name: "Castor",        angle: 279,   elev: 4223, lw: 5,  rw: 5,  off: 118 },
  { name: "Liskamm",       angle: 288,   elev: 4527, lw: 7,  rw: 8,  off: 65  },
  { name: "Dufourspitze",  angle: 299,   elev: 4634, lw: 9,  rw: 8,  off: 130 },
  { name: "Strahlhorn",    angle: 317,   elev: 4190, lw: 7,  rw: 6,  off: 75  },
  { name: "Allalinhorn",   angle: 330,   elev: 4027, lw: 6,  rw: 7,  off: 118 },
  { name: "Dom",           angle: 347,   elev: 4545, lw: 9,  rw: 7,  off: 65  },
  { name: "Täschhorn",     angle: 354,   elev: 4491, lw: 6,  rw: 9,  off: 118 },
];

const A_START = 206;
const A_END = 362;
const N = 800;
const BASE = 2700;
const Y_MIN = 2400;
const Y_MAX = 4780;

// Build ridgeline using asymmetric tent functions (triangular peaks, NOT Gaussian)
function buildProfile() {
  const xs = [];
  const ys = [];
  for (let i = 0; i < N; i++) {
    const a = A_START + (i / (N - 1)) * (A_END - A_START);
    xs.push(a);
    let e = BASE;
    for (const p of PEAKS) {
      const da = a - p.angle;
      if (da <= 0 && -da < p.lw) {
        e = Math.max(e, p.elev + (da / p.lw) * (p.elev - BASE));
      } else if (da > 0 && da < p.rw) {
        e = Math.max(e, p.elev - (da / p.rw) * (p.elev - BASE));
      }
    }
    // Superimposed high-frequency sinusoids for rocky ridge jaggedness
    const jagg =
      Math.sin(a * 5.3 + 1.1) * 38 +
      Math.sin(a * 11.7 + 2.3) * 19 +
      Math.sin(a * 23.4 + 0.7) * 10 +
      Math.sin(a * 41.2 + 1.8) * 5;
    ys.push(Math.max(Y_MIN, e + jagg));
  }
  return { xs, ys };
}

const { xs: xData, ys: yData } = buildProfile();

const COMPASS_TICKS = [210, 240, 270, 300, 330, 360];
const COMPASS_LABELS = { 210: "SW", 240: "WSW", 270: "W", 300: "WNW", 330: "NW", 360: "N" };

const TITLE = "Wallis Alps · area-mountain-panorama · javascript · muix · anyplot.ai";

function SkyLayer() {
  const { left, top, width, height } = useDrawingArea();
  return (
    <g>
      <defs>
        <linearGradient
          id="muixSkyGrad"
          gradientUnits="userSpaceOnUse"
          x1={left}
          y1={top}
          x2={left}
          y2={top + height}
        >
          <stop offset="0%" stopColor={SKY_TOP} />
          <stop offset="100%" stopColor={SKY_BTM} />
        </linearGradient>
      </defs>
      <rect x={left} y={top} width={width} height={height} fill="url(#muixSkyGrad)" />
    </g>
  );
}

function PeakLabels() {
  const xScale = useXScale("xAxis");
  const yScale = useYScale("yAxis");
  if (!xScale || !yScale) return null;

  return (
    <g>
      {PEAKS.map((p) => {
        const cx = xScale(p.angle);
        const cy = yScale(p.elev);
        if (cx == null || cy == null) return null;

        const labelY = cy - p.off;

        return (
          <g key={p.name}>
            <line
              x1={cx} y1={cy - 3}
              x2={cx} y2={labelY + 18}
              stroke={INK_SOFT}
              strokeWidth={0.8}
              strokeDasharray="3 2"
            />
            <text
              x={cx}
              y={labelY}
              textAnchor="middle"
              fill={INK}
              fontSize={11}
              fontWeight="600"
            >
              {p.name}
            </text>
            <text
              x={cx}
              y={labelY + 14}
              textAnchor="middle"
              fill={INK_SOFT}
              fontSize={10}
            >
              {p.elev} m
            </text>
          </g>
        );
      })}
    </g>
  );
}

function ChartTitle() {
  const { left, top, width } = useDrawingArea();
  return (
    <text
      x={left + width / 2}
      y={top - 22}
      textAnchor="middle"
      fill={INK}
      fontSize={20}
      fontWeight="500"
    >
      {TITLE}
    </text>
  );
}

export default function Chart() {
  return (
    <ChartContainer
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      skipAnimation
      series={[
        {
          type: "line",
          id: "ridgeline",
          data: yData,
          area: true,
          color: SILHOUETTE,
          showMark: false,
        },
      ]}
      xAxis={[
        {
          id: "xAxis",
          scaleType: "linear",
          data: xData,
          min: A_START,
          max: A_END,
          tickInterval: COMPASS_TICKS,
          valueFormatter: (v) => COMPASS_LABELS[v] ?? "",
        },
      ]}
      yAxis={[
        {
          id: "yAxis",
          min: Y_MIN,
          max: Y_MAX,
          tickInterval: [2500, 3000, 3500, 4000, 4500],
          valueFormatter: (v) => `${v} m`,
        },
      ]}
      margin={{ top: 80, right: 50, bottom: 60, left: 90 }}
      sx={{
        backgroundColor: PAGE_BG,
        "& .MuiAreaElement-series-ridgeline": {
          fill: SILHOUETTE,
          fillOpacity: 1,
        },
        "& .MuiLineElement-series-ridgeline": {
          stroke: RIDGE_COLOR,
          strokeWidth: 1,
        },
        "& .MuiChartsAxis-line": { stroke: INK_SOFT },
        "& .MuiChartsAxis-tick": { stroke: INK_SOFT },
      }}
    >
      <SkyLayer />
      <AreaPlot />
      <LinePlot />
      <ChartsXAxis
        axisId="xAxis"
        tickLabelStyle={{ fill: INK_SOFT, fontSize: 13 }}
      />
      <ChartsYAxis
        axisId="yAxis"
        tickLabelStyle={{ fill: INK_SOFT, fontSize: 12 }}
      />
      <PeakLabels />
      <ChartTitle />
    </ChartContainer>
  );
}
