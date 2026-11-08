// anyplot.ai
// ternary-basic: Basic Ternary Plot
// Library: muix 9.17.0 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-04
//# anyplot-orientation: square
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const LEVEL_SHARE = 0.2; // grid and tick step as a share of the composition total
// room beside, above and below the triangle (side 1) for the ticks and vertex names
const PAD_SIDE = 0.15;
const PAD_TOP = 0.11;
const PAD_BOTTOM = 0.08;
const TICK_LEN = 0.018; // tick mark length as a share of the side
const TICK_LABEL_OFF = 0.035; // tick label distance from its edge as a share of the side
const VERTEX_LABEL_OFF = 0.075; // vertex name distance from its vertex as a share of the side
const HEADER_H = 84;
const MARGIN = 16;

// Columns: set these to your data's column names
const SAND = "Sand (%)"; // role: component_a
const SILT = "Silt (%)"; // role: component_b
const CLAY = "Clay (%)"; // role: component_c

// Data: replace this block with your own records, one object per row
// Sand-silt-clay texture of 65 topsoil samples from a field survey
const data = (() => {
  let seed = 20260804 >>> 0;
  const rand = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  return Array.from({ length: 65 }, () => {
    const [gSand, gSilt, gClay] = [5, 2, 2].map((shape) =>
      Array.from({ length: shape }, () => -Math.log(rand() || 1e-9)).reduce((s, v) => s + v, 0),
    );
    const sum = gSand + gSilt + gClay;
    return {
      [SAND]: Number(((gSand / sum) * 100).toFixed(1)),
      [SILT]: Number(((gSilt / sum) * 100).toFixed(1)),
      [CLAY]: Number(((gClay / sum) * 100).toFixed(1)),
    };
  });
})();

// Plot: reads only data and the constants above
// Barycentric shares to the plane: the first component at the top apex, the second at
// the bottom left, the third at the bottom right, on a triangle of side 1
const COMPONENTS = [SAND, SILT, CLAY];
const SQRT3_2 = Math.sqrt(3) / 2;
const rows = data.filter(
  (d) => COMPONENTS.every((k) => Number.isFinite(d[k])) && COMPONENTS.reduce((s, k) => s + d[k], 0) > 0,
);
const rowTotals = rows.map((d) => COMPONENTS.reduce((s, k) => s + d[k], 0));
const total = rowTotals.reduce((s, v) => s + v, 0) / rows.length; // the constant sum, 100 for percentages
const points = rows.map((d, i) => ({
  id: i,
  x: d[CLAY] / rowTotals[i] + d[SAND] / rowTotals[i] / 2,
  y: (SQRT3_2 * d[SAND]) / rowTotals[i],
}));

// Lines of constant share: for component k at share f they run between the edge where
// component k + 1 takes the rest (its ticks sit there) and the edge where component k + 2 does
const levels = Array.from({ length: Math.round(1 / LEVEL_SHARE) + 1 }, (_, i) => i * LEVEL_SHARE);
const isoLines = COMPONENTS.flatMap((_, k) =>
  levels.map((f) => {
    const s1 = [0, 0, 0];
    const s2 = [0, 0, 0];
    s1[k] = f;
    s2[k] = f;
    s1[(k + 1) % 3] = 1 - f;
    s2[(k + 2) % 3] = 1 - f;
    return {
      key: `${k}-${f}`,
      k,
      f,
      x1: s1[2] + s1[0] / 2,
      y1: SQRT3_2 * s1[0],
      x2: s2[2] + s2[0] / 2,
      y2: SQRT3_2 * s2[0],
    };
  }),
);
const gridLines = isoLines.filter((l) => l.f > 1e-9 && l.f < 1 - 1e-9);
const vertices = COMPONENTS.map((_, k) => isoLines.find((l) => l.k === k && Math.abs(l.f - 1) < 1e-9)!);
// Each component's ticks point outward along its own lines; vertex names point away from the centre
// (a text's anchor and baseline follow the direction it is pushed in)
const [tickDir, vertexDir] = [
  COMPONENTS.map((_, k) => {
    const edge = isoLines.find((l) => l.k === k && l.f === 0)!;
    return { x: edge.x1 - edge.x2, y: edge.y1 - edge.y2 };
  }),
  vertices.map((v) => {
    const dx = v.x1 - 0.5;
    const dy = v.y1 - SQRT3_2 / 3;
    return { x: dx / Math.hypot(dx, dy), y: dy / Math.hypot(dx, dy) };
  }),
].map((dirs) =>
  dirs.map((d) => ({
    ...d,
    anchor: d.x < -0.3 ? "end" : d.x > 0.3 ? "start" : "middle",
    baseline: d.y > 0.3 ? "auto" : d.y < -0.3 ? "hanging" : "central",
  })),
);
const unit = SAND.match(/\(([^)]+)\)/)?.[1] ?? "";

const TITLE = "Topsoil Texture · ternary-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} compositions · grid and ticks every ${Number((LEVEL_SHARE * total).toFixed(2))} ${unit}`;

function TernaryLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const side = Math.abs(xScale(1) - xScale(0)); // px per unit side, equal on both axes

  return (
    <g>
      {gridLines.map((l) => (
        <line
          key={l.key}
          x1={xScale(l.x1)}
          y1={yScale(l.y1)}
          x2={xScale(l.x2)}
          y2={yScale(l.y2)}
          stroke={t.grid}
          strokeWidth={1.5}
          strokeDasharray="6 5"
        />
      ))}
      <path
        d={`M ${vertices.map((v) => `${xScale(v.x1)} ${yScale(v.y1)}`).join(" L ")} Z`}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />
      {isoLines.map((l) => (
        <g key={`tick-${l.key}`}>
          <line
            x1={xScale(l.x1)}
            y1={yScale(l.y1)}
            x2={xScale(l.x1) + tickDir[l.k].x * TICK_LEN * side}
            y2={yScale(l.y1) - tickDir[l.k].y * TICK_LEN * side}
            stroke={t.inkSoft}
            strokeWidth={1.5}
          />
          <text
            x={xScale(l.x1) + tickDir[l.k].x * TICK_LABEL_OFF * side}
            y={yScale(l.y1) - tickDir[l.k].y * TICK_LABEL_OFF * side}
            textAnchor={tickDir[l.k].anchor}
            dominantBaseline={tickDir[l.k].baseline}
            fontSize={14}
            fill={t.inkSoft}
          >
            {Number((l.f * total).toFixed(2))}
          </text>
        </g>
      ))}
      {vertices.map((v, k) => (
        <text
          key={COMPONENTS[k]}
          x={xScale(v.x1) + vertexDir[k].x * VERTEX_LABEL_OFF * side}
          y={yScale(v.y1) - vertexDir[k].y * VERTEX_LABEL_OFF * side}
          textAnchor={vertexDir[k].anchor}
          dominantBaseline={vertexDir[k].baseline}
          fontSize={20}
          fontWeight={700}
          fill={t.ink}
        >
          {COMPONENTS[k]}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - HEADER_H;
  // equal px per unit on both axes keeps the triangle equilateral
  const drawW = width - 2 * MARGIN;
  const drawH = chartH - 2 * MARGIN;
  const k = Math.min(drawW / (1 + 2 * PAD_SIDE), drawH / (SQRT3_2 + PAD_TOP + PAD_BOTTOM));
  const yMid = (SQRT3_2 + PAD_TOP - PAD_BOTTOM) / 2;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={width}
        height={chartH}
        skipAnimation
        margin={{ top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }}
        xAxis={[{ scaleType: "linear", min: 0.5 - drawW / (2 * k), max: 0.5 + drawW / (2 * k), position: "none" }]}
        yAxis={[{ scaleType: "linear", min: yMid - drawH / (2 * k), max: yMid + drawH / (2 * k), position: "none" }]}
        series={[
          {
            type: "scatter",
            id: "compositions",
            label: COMPONENTS.join(" · "),
            color: t.palette[0],
            markerSize: 8,
            data: points,
            valueFormatter: (_value, { dataIndex }) =>
              COMPONENTS.map((name) => `${name} ${rows[dataIndex][name]}`).join(" · "),
          },
        ]}
      >
        <ChartsWrapper sx={{ width, height: chartH }}>
          <ChartsSurface sx={{ "& .MuiScatterChart-marker": { fillOpacity: 0.85 } }}>
            <TernaryLayer />
            <ScatterPlot />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
