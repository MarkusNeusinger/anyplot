// anyplot.ai
// scatter-3d: 3D Scatter Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 90/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GROUND_ANGLE = (15 * Math.PI) / 180; // screen angle of the x and z axes below the horizontal
const HEIGHT_SHARE = 0.8; // drawn length of the y axis relative to the x and z axes
const TICK_TARGET = 5; // about this many ticks per axis
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // tick steps per power of ten
const MARKER_SIZES = [5.5, 8.5, 12]; // px per depth tertile, far to near
const DEPTH_NAMES = ["Far", "Mid", "Near"];
const MARKER_ALPHA_HEX = "D9"; // ~85 % opacity so interior points show through
const LABEL_OUT = 0.06; // tick labels sit this far outside the box, in box units
const TITLE_OUT = 0.17; // axis titles sit this far outside the box, in box units
const PAD_SHARE = 0.03; // padding around the projected box as a share of its span

// Columns: set these to your data's column names
const X = "x (nm)"; // role: x
const Y = "y (nm)"; // role: y
const Z = "z (nm)"; // role: z
const ENERGY = "Potential energy (eV)"; // role: color

// Data: replace this block with your own records, one object per row
// Simulated molecular-dynamics snapshot: three nanocluster fragments in a 100 nm cell;
// each atom's potential energy rises with its distance from its fragment's core.
const data = (() => {
  let state = 7;
  const uniform = () => {
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
  const fragments = [
    { center: [22, 74, 30], sigma: 7, count: 55 },
    { center: [78, 32, 68], sigma: 8, count: 55 },
    { center: [42, 20, 84], sigma: 6, count: 45 },
  ];
  const rows = [];
  fragments.forEach(({ center, sigma, count }) => {
    for (let i = 0; i < count; i += 1) {
      const position = center.map((c) => Math.min(99, Math.max(1, c + gaussian() * sigma)));
      const distance = Math.hypot(...position.map((p, k) => p - center[k]));
      const energy = -6.4 + 0.062 * distance + gaussian() * 0.22;
      rows.push({
        [X]: Number(position[0].toFixed(2)),
        [Y]: Number(position[1].toFixed(2)),
        [Z]: Number(position[2].toFixed(2)),
        [ENERGY]: Number(energy.toFixed(3)),
      });
    }
  });
  return rows;
})();

// Plot: reads only data and the constants above
// Each axis spans the data extent rounded out to nice ticks; box coordinates run 0 to 1
const [xAxisInfo, yAxisInfo, zAxisInfo] = [X, Y, Z].map((column) => {
  const values = data.map((d) => d[column]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const raw = (hi - lo) / TICK_TARGET;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = NICE_STEPS.find((s) => s * magnitude >= raw) * magnitude;
  const start = Math.floor(lo / step) * step;
  const end = Math.ceil(hi / step) * step;
  const ticks = Array.from({ length: Math.round((end - start) / step) + 1 }, (_, k) => Number((start + k * step).toFixed(6)));
  return { column, start, span: end - start, ticks };
});
const xTicks = xAxisInfo.ticks.map((v) => ({ v, at: (v - xAxisInfo.start) / xAxisInfo.span }));
const yTicks = yAxisInfo.ticks.map((v) => ({ v, at: (v - yAxisInfo.start) / yAxisInfo.span }));
const zTicks = zAxisInfo.ticks.map((v) => ({ v, at: (v - zAxisInfo.start) / zAxisInfo.span }));

// Fixed oblique view: box point (u, v, w) maps to chart units by this matrix; (1, 0, 1) is the nearest corner
const PROJ = [
  [Math.cos(GROUND_ANGLE), 0, -Math.cos(GROUND_ANGLE)],
  [-Math.sin(GROUND_ANGLE), HEIGHT_SHARE, -Math.sin(GROUND_ANGLE)],
];

// Back panes (floor and the two far walls) with grid lines at the ticks
const panes = [
  [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]],
  [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
  [[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]],
].map((corners) => corners.map(([u, v, w]) => PROJ.map(([a, b, c]) => a * u + b * v + c * w)));
const gridLines = [
  ...xTicks.map(({ at }) => [[at, 0, 0], [at, 0, 1]]),
  ...zTicks.map(({ at }) => [[0, 0, at], [1, 0, at]]),
  ...xTicks.map(({ at }) => [[at, 0, 0], [at, 1, 0]]),
  ...yTicks.map(({ at }) => [[0, at, 0], [1, at, 0]]),
  ...zTicks.map(({ at }) => [[0, 0, at], [0, 1, at]]),
  ...yTicks.map(({ at }) => [[0, at, 0], [0, at, 1]]),
].map((ends) => ends.map(([u, v, w]) => PROJ.map(([a, b, c]) => a * u + b * v + c * w)));
const axisEdges = [
  [[0, 0, 1], [1, 0, 1]],
  [[1, 0, 0], [1, 0, 1]],
  [[0, 0, 1], [0, 1, 1]],
].map((ends) => ends.map(([u, v, w]) => PROJ.map(([a, b, c]) => a * u + b * v + c * w)));

// Tick labels just outside the three outer edges, axis titles further out and turned along them.
// Two corners are shared: x starts where y does and z ends where x does, so the x start and the
// z end stay unlabelled and each corner label belongs to one axis only
const tickLabels = [
  ...xTicks.filter(({ at }) => at > 0).map(({ v, at }) => ({ text: `${v}`, box: [at, -LABEL_OUT, 1 + LABEL_OUT], anchor: "end" })),
  ...zTicks.filter(({ at }) => at < 1).map(({ v, at }) => ({ text: `${v}`, box: [1 + LABEL_OUT, -LABEL_OUT, at], anchor: "start" })),
  ...yTicks.map(({ v, at }) => ({ text: `${v}`, box: [-LABEL_OUT / 2, at, 1 + LABEL_OUT / 2], anchor: "end" })),
].map((label) => ({ ...label, at: PROJ.map(([a, b, c]) => a * label.box[0] + b * label.box[1] + c * label.box[2]) }));
const groundDeg = (GROUND_ANGLE * 180) / Math.PI;
const axisTitles = [
  { text: X, box: [0.5, -TITLE_OUT, 1], rotate: groundDeg },
  { text: Z, box: [1, -TITLE_OUT, 0.5], rotate: -groundDeg },
  { text: Y, box: [-TITLE_OUT / 2, 0.5, 1 + TITLE_OUT / 2], rotate: -90 },
].map((title) => ({ ...title, at: PROJ.map(([a, b, c]) => a * title.box[0] + b * title.box[1] + c * title.box[2]) }));

// Points far to near, so nearer markers paint over farther ones; marker size marks the depth tertile
const points = data
  .map((d, i) => {
    const u = (d[X] - xAxisInfo.start) / xAxisInfo.span;
    const v = (d[Y] - yAxisInfo.start) / yAxisInfo.span;
    const w = (d[Z] - zAxisInfo.start) / zAxisInfo.span;
    const [px, py] = PROJ.map(([a, b, c]) => a * u + b * v + c * w);
    return { id: i, x: px, y: py, z: d[ENERGY], depth: u + w, vx: d[X], vy: d[Y], vz: d[Z] };
  })
  .sort((a, b) => a.depth - b.depth);
const series = MARKER_SIZES.map((markerSize, tier) => ({
  type: "scatter" as const,
  id: `depth-${tier}`,
  label: DEPTH_NAMES[tier],
  markerSize,
  zAxisId: "energy",
  data: points.filter((_, i) => Math.floor((i * MARKER_SIZES.length) / points.length) === tier),
  valueFormatter: (p: any) => `${X} ${p.vx}, ${Y} ${p.vy}, ${Z} ${p.vz}; ${ENERGY} ${p.z}`,
}));

const energies = data.map((d) => d[ENERGY]);
const energyMin = Math.min(...energies);
const energyMax = Math.max(...energies);
// The size glyphs take the middle of the energy ramp at the markers' alpha, so they match the marks
const midRamp = `rgb(${[1, 3, 5]
  .map((i) => (parseInt(t.seq[0].slice(i, i + 2), 16) + parseInt(t.seq[1].slice(i, i + 2), 16)) / 2)
  .join(", ")})`;
const markerAlpha = parseInt(MARKER_ALPHA_HEX, 16) / 255;

// Chart units per px are equal on both screen axes, so the box keeps its shape
const TITLE = "scatter-3d · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${data.length} · fixed oblique view, larger markers are nearer`;
const HEADER_HEIGHT = 84;
const SIDE_WIDTH = 230;
const MARGIN = { top: 16, right: 24, bottom: 24, left: 24 };
const chartWidth = window.ANYPLOT_SIZE.width - SIDE_WIDTH;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT;
const drawRatio = (chartWidth - MARGIN.left - MARGIN.right) / (chartHeight - MARGIN.top - MARGIN.bottom);
const extentX = [...panes.flat(), ...tickLabels.map((l) => l.at), ...axisTitles.map((l) => l.at)].map((p) => p[0]);
const extentY = [...panes.flat(), ...tickLabels.map((l) => l.at), ...axisTitles.map((l) => l.at)].map((p) => p[1]);
const centerX = (Math.min(...extentX) + Math.max(...extentX)) / 2;
const centerY = (Math.min(...extentY) + Math.max(...extentY)) / 2;
const halfY =
  (Math.max(Math.max(...extentY) - Math.min(...extentY), (Math.max(...extentX) - Math.min(...extentX)) / drawRatio) *
    (1 + 2 * PAD_SHARE)) /
  2;
const halfX = halfY * drawRatio;

function BoxPanes() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {panes.map((corners, i) => (
        <polygon
          key={`pane-${i}`}
          points={corners.map(([px, py]) => `${xScale(px)},${yScale(py)}`).join(" ")}
          fill={t.elevatedBg}
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      {gridLines.map(([a, b], i) => (
        <line key={`grid-${i}`} x1={xScale(a[0])} y1={yScale(a[1])} x2={xScale(b[0])} y2={yScale(b[1])} stroke={t.grid} strokeWidth={1} />
      ))}
      {axisEdges.map(([a, b], i) => (
        <line key={`edge-${i}`} x1={xScale(a[0])} y1={yScale(a[1])} x2={xScale(b[0])} y2={yScale(b[1])} stroke={t.inkSoft} strokeWidth={1.5} />
      ))}
    </g>
  );
}

function BoxLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {tickLabels.map((label, i) => (
        <text
          key={`tick-${i}`}
          x={xScale(label.at[0])}
          y={yScale(label.at[1])}
          textAnchor={label.anchor}
          dominantBaseline="central"
          fontSize={14}
          fill={t.inkSoft}
        >
          {label.text}
        </text>
      ))}
      {axisTitles.map((title) => (
        <text
          key={`title-${title.text}`}
          transform={`translate(${xScale(title.at[0])}, ${yScale(title.at[1])}) rotate(${title.rotate})`}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={16}
          fontWeight={500}
          fill={t.ink}
        >
          {title.text}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={series}
        xAxis={[{ id: "screen-x", scaleType: "linear", min: centerX - halfX, max: centerX + halfX }]}
        yAxis={[{ id: "screen-y", scaleType: "linear", min: centerY - halfY, max: centerY + halfY }]}
        zAxis={[
          {
            id: "energy",
            colorMap: {
              type: "continuous",
              min: energyMin,
              max: energyMax,
              color: [`${t.seq[0]}${MARKER_ALPHA_HEX}`, `${t.seq[1]}${MARKER_ALPHA_HEX}`],
            },
          },
        ]}
        skipAnimation
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <ChartsSurface>
            <BoxPanes />
            <ScatterPlot />
            <BoxLabels />
          </ChartsSurface>
          <div style={{ width: SIDE_WIDTH, display: "flex", flexDirection: "column", gap: 14, paddingRight: 32 }}>
            <div style={{ fontSize: 16, fontWeight: 500, color: t.ink }}>{ENERGY}</div>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="energy"
              direction="vertical"
              labelPosition="end"
              thickness={16}
              minLabel={({ value }) => Number(value).toFixed(2)}
              maxLabel={({ value }) => Number(value).toFixed(2)}
              sx={{ height: 260, fontSize: 14, color: t.inkSoft }}
            />
            <div style={{ fontSize: 16, fontWeight: 500, color: t.ink, marginTop: 24 }}>Marker size</div>
            {DEPTH_NAMES.map((name, tier) => (
              <div key={name} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: t.inkSoft }}>
                <span style={{ width: 26, display: "flex", justifyContent: "center" }}>
                  <span
                    style={{
                      width: MARKER_SIZES[tier] * 2,
                      height: MARKER_SIZES[tier] * 2,
                      borderRadius: "50%",
                      background: midRamp,
                      opacity: markerAlpha,
                    }}
                  />
                </span>
                {name}
              </div>
            ))}
          </div>
        </div>
        <ChartsTooltip trigger="item" />
      </ChartsDataProvider>
    </div>
  );
}
