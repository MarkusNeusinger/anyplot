//# anyplot-orientation: landscape
// anyplot.ai
// bar-3d-categorical: 3D Bar Chart for Categorical Comparison
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-04
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Factorial-design experiment: tensile strength across alloy × heat-treatment.
const alloys = ["Al 6061", "Ti-6Al-4V", "Steel 4140", "Inconel 718", "Mg AZ31"];
// Depth order runs weakest → strongest per alloy, so the row offset (which
// pushes further rows up-and-right) always reinforces the value-driven
// height difference between neighbors instead of fighting it — that keeps
// the value labels of adjacent rows from colliding even where two treatments
// land close together (see Al 6061 / Mg AZ31 below).
const treatments = ["Annealed", "Tempered", "Quenched", "Aged"];
// tensileStrengthMPa[treatmentIndex][alloyIndex], in MPa — strictly
// increasing down each column (alloy) from Annealed to Aged.
const tensileStrengthMPa = [
  [124, 830, 655, 965, 145], // Annealed
  [200, 950, 780, 1100, 200], // Tempered
  [275, 1100, 900, 1250, 240], // Quenched
  [310, 1170, 1080, 1400, 290], // Aged
];

const MAX_STRENGTH = 1500;
const ROW_COLORS = [t.palette[0], t.palette[1], t.palette[2], t.palette[3]];

const series = treatments.map((label, i) => ({
  type: "bar",
  id: label,
  label,
  data: alloys.map((_, j) => tensileStrengthMPa[i][j]),
  color: ROW_COLORS[i],
}));

// Isometric depth vector, in CSS px within the mount's coordinate space.
// Shared by the per-bar cuboid thickness and the per-treatment stagger so the
// four rows read as one continuous grid receding into the screen, rather than
// four unrelated offsets.
const ISO_DX = 20;
const ISO_DY = -13;

const TITLE = "bar-3d-categorical · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;
const MARGIN = { top: 140, right: 230, bottom: 90, left: 120 };

function shade(hex, amount) {
  const num = parseInt(hex.slice(1), 16);
  const r = (num >> 16) & 0xff;
  const g = (num >> 8) & 0xff;
  const b = num & 0xff;
  const target = amount > 0 ? 255 : 0;
  const k = Math.abs(amount);
  const mix = (c) => Math.round(c + (target - c) * k);
  return `rgb(${mix(r)}, ${mix(g)}, ${mix(b)})`;
}

// --- Custom Y-axis title -----------------------------------------------------
// ChartsYAxis's own `label` places the rotated title at a fixed
// `tickFontSize + tickSize + 10` offset from the axis line (ChartsYAxis.js),
// which assumes short tick text; it collides with wide numeric tick labels
// like "1,500". Rendering the title separately with a hand-picked offset
// sidesteps that.
function YAxisTitle() {
  const { top, height } = useDrawingArea();
  return (
    <ChartsText
      x={38}
      y={top + height / 2}
      text="Tensile Strength (MPa)"
      style={{ fontSize: 16, fill: t.ink, fontWeight: 500, textAnchor: "middle", dominantBaseline: "auto", angle: -90 }}
    />
  );
}

// --- Custom overlay: a 2D categorical grid (alloy × treatment) rendered as
// isometric cuboids, height-encoded by value. Community `@mui/x-charts/hooks`
// (useXScale/useYScale) map data coordinates to pixels so the grid stays
// aligned with the axes at any size — the same composition pattern used for
// mohr-circle's custom geometry, applied here to a chart type (3D bars) the
// declarative BarChart can't express on its own. -----------------------------
function Bars3D() {
  const xScale = useXScale();
  const yScale = useYScale();
  const bandwidth = xScale.bandwidth();
  const barWidth = bandwidth * 0.55;
  const baseline = yScale(0);

  // Paint back row first so nearer (lower-index) rows correctly occlude it.
  const paintOrder = [...treatments.keys()].sort((a, b) => b - a);

  return (
    <>
      {paintOrder.map((row) => {
        const dx = row * ISO_DX;
        const dy = row * ISO_DY;
        const color = ROW_COLORS[row];
        const topColor = shade(color, 0.34);
        const sideColor = shade(color, -0.3);
        return (
          <g key={treatments[row]} transform={`translate(${dx}, ${dy})`}>
            {alloys.map((alloy, col) => {
              const value = tensileStrengthMPa[row][col];
              const x = xScale(alloy) + (bandwidth - barWidth) / 2;
              const y = yScale(value);
              const barHeight = baseline - y;
              const topFace = [
                `${x},${y}`,
                `${x + barWidth},${y}`,
                `${x + barWidth + ISO_DX},${y + ISO_DY}`,
                `${x + ISO_DX},${y + ISO_DY}`,
              ].join(" ");
              const sideFace = [
                `${x + barWidth},${y}`,
                `${x + barWidth},${y + barHeight}`,
                `${x + barWidth + ISO_DX},${y + barHeight + ISO_DY}`,
                `${x + barWidth + ISO_DX},${y + ISO_DY}`,
              ].join(" ");
              return (
                <g key={alloy}>
                  <rect x={x} y={y} width={barWidth} height={barHeight} fill={color} />
                  <polygon points={sideFace} fill={sideColor} />
                  <polygon points={topFace} fill={topColor} />
                  <ChartsText
                    x={x + barWidth / 2 + ISO_DX / 2}
                    y={y + ISO_DY - 8}
                    text={String(value)}
                    style={{ fontSize: 12, fill: t.ink, textAnchor: "middle", dominantBaseline: "auto" }}
                  />
                </g>
              );
            })}
          </g>
        );
      })}
    </>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
        }}
      >
        {TITLE}
      </div>
      <ChartContainer
        width={width}
        height={chartHeight}
        margin={MARGIN}
        skipAnimation
        series={series}
        xAxis={[{ scaleType: "band", data: alloys, label: "Alloy" }]}
        yAxis={[{ scaleType: "linear", min: 0, max: MAX_STRENGTH }]}
      >
        <ChartsGrid horizontal />
        <Bars3D />
        <ChartsXAxis
          labelStyle={{ fontSize: 16, fill: t.ink, fontWeight: 500 }}
          tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
          stroke={t.inkSoft}
        />
        <ChartsYAxis tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }} stroke={t.inkSoft} />
        <YAxisTitle />
        <ChartsLegend
          direction="column"
          position={{ horizontal: "right", vertical: "middle" }}
          labelStyle={{ fontSize: 15, fill: t.ink }}
        />
      </ChartContainer>
    </div>
  );
}
