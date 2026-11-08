// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot, MarkElement, MarkPlot } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // axis padding on each side as a share of the data span
const PERIOD = 10; // years per colour step along the path (decades)
// A second cue per period, in time order, so neighbouring steps of the ramp stay apart where loops cross
const PERIOD_SHAPES = ["circle", "square", "triangle", "diamond", "star", "wye", "cross"] as const;
const LABEL_GAP = 12; // px between a marker and its time label box
const LABEL_GAP_MAX = 60; // px, the farthest a label steps out when nothing nearer is clear
const LABEL_STEP = 4; // px per step outwards
const LABEL_DIRECTIONS = 16; // candidate label positions around each labelled point
const LABEL_FONT = 14;
const LABEL_HALF_H = 8; // px, half the height of a label box, halo included
const PATH_ROOM = 9; // px a label box keeps from every segment, the direction chevrons on it included
const MARKER_ROOM = 26; // px a label box keeps from any other point's marker centre
// The direction cue is an open chevron drawn on the path in the line's own stroke, well below marker
// size and unfilled, so it reads as part of the line and never as a further observation
const CHEVRON_ARM = 11; // px, the length of each arm
const CHEVRON_SPREAD = (35 * Math.PI) / 180; // the angle between each arm and the path
const LINE_WIDTH = 2.5; // px
const MARK_SCALE = 1.6; // the default mark symbol is too small a bead for a few dozen sparse points

// Columns: set these to your data's column names
const YEAR = "Year"; // role: time
const UNEMPLOYMENT = "Unemployment rate (%)"; // role: x
const INFLATION = "Inflation rate (%)"; // role: y
const LABEL = "Label"; // role: label

// Data: replace this block with your own records, one object per row
// US Phillips curve, 1970–2009: annual unemployment against annual CPI inflation;
// the decade boundaries and the 1973 oil shock and 2008 crisis carry a label.
const data = (() => {
  const unemployment = [
    4.9, 5.9, 5.6, 4.9, 5.6, 8.5, 7.7, 7.1, 6.1, 5.8, 7.1, 7.6, 9.7, 9.6, 7.5, 7.2, 7.0, 6.2, 5.5, 5.3,
    5.6, 6.8, 7.5, 6.9, 6.1, 5.6, 5.4, 4.9, 4.5, 4.2, 4.0, 4.7, 5.8, 6.0, 5.5, 5.1, 4.6, 4.6, 5.8, 9.3,
  ];
  const inflation = [
    5.7, 4.4, 3.2, 6.2, 11.0, 9.1, 5.8, 6.5, 7.6, 11.3, 13.5, 10.3, 6.2, 3.2, 4.3, 3.6, 1.9, 3.6, 4.1, 4.8,
    5.4, 4.2, 3.0, 3.0, 2.6, 2.8, 3.0, 2.3, 1.6, 2.2, 3.4, 2.8, 1.6, 2.3, 2.7, 3.4, 3.2, 2.9, 3.8, -0.4,
  ];
  const labelled = new Set([1970, 1973, 1979, 1980, 1989, 1990, 1999, 2000, 2008, 2009]);
  return unemployment.map((u, i) => ({
    [YEAR]: 1970 + i,
    [UNEMPLOYMENT]: u,
    [INFLATION]: inflation[i],
    [LABEL]: labelled.has(1970 + i) ? `${1970 + i}` : "",
  }));
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[YEAR] - b[YEAR]);
const periodOf = rows.map((d) => Math.floor(d[YEAR] / PERIOD) * PERIOD);
const periods = [...new Set(periodOf)];

// Periods are ordered, so they take steps of the Imprint sequential ramp in time order
const rampStart = parseInt(t.seq[0].slice(1), 16);
const rampEnd = parseInt(t.seq[1].slice(1), 16);
const periodColor = periods.map((_, k) => {
  const share = periods.length > 1 ? k / (periods.length - 1) : 0;
  return `#${[16, 8, 0]
    .map((shift) => {
      const a = (rampStart >> shift) & 255;
      const b = (rampEnd >> shift) & 255;
      return Math.round(a + (b - a) * share).toString(16).padStart(2, "0");
    })
    .join("")}`;
});

// One line series per period; each also holds the last point of the period before it,
// so the path stays unbroken where the colour changes, and marks only its own points
const lineSeries = periods.map((period, k) => ({
  type: "line" as const,
  id: `path-${period}`,
  label: `${period}s`,
  color: periodColor[k],
  curve: "linear" as const,
  shape: PERIOD_SHAPES[k],
  showMark: ({ index }) => periodOf[index] === period,
  labelMarkType: "line+mark" as const,
  data: rows.map((d, i) => (periodOf[i] === period || periodOf[i + 1] === period ? d[INFLATION] : null)),
}));
// Marks, on the plot and in the legend, are filled with their period's colour; both default to hollow
const markFills = Object.fromEntries(
  periods.flatMap((period, k) => [
    [`& [data-series="path-${period}"] .MuiLineChart-mark`, { fill: periodColor[k] }],
    [`& [data-series="path-${period}"] .MuiChartsLabelMark-root path:last-of-type`, { fill: periodColor[k] }],
  ]),
);

// One arrow per period, on the segment that leaves the period's middle point
const arrows = periods
  .map((period, k) => {
    const members = rows.map((_, i) => i).filter((i) => periodOf[i] === period && i + 1 < rows.length);
    return { from: members[Math.floor((members.length - 1) / 2)], color: periodColor[k] };
  })
  .filter((a) => a.from !== undefined);
const labelled = rows.map((d, i) => ({ i, text: `${d[LABEL]}` })).filter((l) => l.text !== "");

const xs = rows.map((d) => d[UNEMPLOYMENT]);
const ys = rows.map((d) => d[INFLATION]);
const xPad = (Math.max(...xs) - Math.min(...xs)) * PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * PAD_SHARE;

const TITLE = "scatter-connected-temporal · javascript · muix · anyplot.ai";
const SUBTITLE = `${INFLATION} against ${UNEMPLOYMENT}, ${rows[0][YEAR]}–${rows[rows.length - 1][YEAR]}, joined in time order`;
const HEADER_HEIGHT = 84;
const LEGEND_HEIGHT = 40;

// MarkElement takes no size and positions itself by its transform, so the mark slot draws it at the
// origin of a group that is moved to the point and scaled there
function LargeMark({ x, y, ...props }) {
  return (
    <g transform={`translate(${x},${y}) scale(${MARK_SCALE})`}>
      <MarkElement {...props} x={0} y={0} />
    </g>
  );
}

function TemporalLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();
  const pts = rows.map((d) => [xScale(d[UNEMPLOYMENT]), yScale(d[INFLATION])]);
  const segments = pts.slice(1).map((p, i) => [pts[i], p]);

  // Each label takes the nearest position around its point, stepping outwards ring by ring, whose
  // whole text box keeps its room from every segment, every other marker (a label beside another
  // point's marker reads as belonging to it), the labels already placed and the plot edge; where no
  // ring is clear, the position with the most room wins
  const placed: { x: number; y: number; hw: number; room: number }[] = [];
  labelled.forEach(({ i, text }) => {
    const hw = (text.length * LABEL_FONT * 0.6 + 4) / 2;
    let best = { x: pts[i][0], y: pts[i][1], hw, room: -Infinity };
    for (let gap = LABEL_GAP; gap <= LABEL_GAP_MAX && best.room < 0; gap += LABEL_STEP) {
      for (let k = 0; k < LABEL_DIRECTIONS; k += 1) {
        const cos = Math.cos((2 * Math.PI * k) / LABEL_DIRECTIONS);
        const sin = Math.sin((2 * Math.PI * k) / LABEL_DIRECTIONS);
        const reach = gap + Math.abs(cos) * hw + Math.abs(sin) * LABEL_HALF_H;
        const x = pts[i][0] + cos * reach;
        const y = pts[i][1] - sin * reach;
        const outline: number[][] = [];
        for (let s = -hw; s <= hw; s += LABEL_STEP) outline.push([x + s, y - LABEL_HALF_H], [x + s, y + LABEL_HALF_H]);
        for (let s = -LABEL_HALF_H; s <= LABEL_HALF_H; s += LABEL_STEP) outline.push([x - hw, y + s], [x + hw, y + s]);
        const pathRoom =
          Math.min(
            ...outline.flatMap(([sx, sy]) =>
              segments.map(([[ax, ay], [bx, by]]) => {
                const len2 = (bx - ax) ** 2 + (by - ay) ** 2 || 1;
                const s = Math.max(0, Math.min(1, ((sx - ax) * (bx - ax) + (sy - ay) * (by - ay)) / len2));
                return Math.hypot(sx - ax - s * (bx - ax), sy - ay - s * (by - ay));
              }),
            ),
          ) - PATH_ROOM;
        const markerRoom =
          Math.min(
            ...pts
              .filter((_, j) => j !== i)
              .map(([px, py]) => Math.hypot(Math.max(Math.abs(px - x) - hw, 0), Math.max(Math.abs(py - y) - LABEL_HALF_H, 0))),
          ) - MARKER_ROOM;
        const labelRoom = Math.min(
          Infinity,
          ...placed.map((p) => Math.max(Math.abs(p.x - x) - p.hw - hw, Math.abs(p.y - y) - 2 * LABEL_HALF_H) - LABEL_STEP),
        );
        const edgeRoom = Math.min(x - hw - left, left + width - x - hw, y - LABEL_HALF_H - top, top + height - y - LABEL_HALF_H);
        const room = Math.min(pathRoom, markerRoom, labelRoom, edgeRoom);
        if (room > best.room) best = { x, y, hw, room };
      }
    }
    placed.push(best);
  });

  return (
    <g>
      {arrows.map((a, k) => {
        const [ax, ay] = pts[a.from];
        const [bx, by] = pts[a.from + 1];
        const len = Math.hypot(bx - ax, by - ay) || 1;
        const ux = (bx - ax) / len;
        const uy = (by - ay) / len;
        // The tip sits half the chevron's depth past the segment's midpoint, so the chevron is centred on it;
        // each arm runs back from the tip, turned off the path by the spread to either side
        const back = CHEVRON_ARM * Math.cos(CHEVRON_SPREAD);
        const side = CHEVRON_ARM * Math.sin(CHEVRON_SPREAD);
        const tipX = (ax + bx) / 2 + (ux * back) / 2;
        const tipY = (ay + by) / 2 + (uy * back) / 2;
        return (
          <path
            key={`chevron-${k}`}
            d={`M ${tipX - ux * back - uy * side},${tipY - uy * back + ux * side} L ${tipX},${tipY} L ${tipX - ux * back + uy * side},${tipY - uy * back - ux * side}`}
            fill="none"
            stroke={a.color}
            strokeWidth={LINE_WIDTH}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
      {labelled.map(({ text }, k) => (
        <text
          key={`label-${text}`}
          x={placed[k].x}
          y={placed[k].y}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={LABEL_FONT}
          fontWeight={500}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={3}
          paintOrder="stroke"
        >
          {text}
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
        width={width}
        height={height - HEADER_HEIGHT - LEGEND_HEIGHT}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        skipAnimation
        series={lineSeries}
        xAxis={[
          {
            id: "unemployment",
            scaleType: "linear",
            data: xs,
            min: Math.min(...xs) - xPad,
            max: Math.max(...xs) + xPad,
            label: UNEMPLOYMENT,
            tickNumber: 8,
            height: 72,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "inflation",
            min: Math.min(...ys) - yPad,
            max: Math.max(...ys) + yPad,
            label: INFLATION,
            tickNumber: 8,
            width: 72,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "end" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 15,
              color: t.ink,
              pr: 6,
              "& .MuiChartsLabelMark-root": { width: 24, height: 24 },
              "& .MuiChartsLabelMark-root path:last-of-type": { stroke: t.pageBg, strokeWidth: 1 },
              ...markFills,
            }}
          />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: LINE_WIDTH },
              "& .MuiLineChart-mark": { stroke: t.pageBg, strokeWidth: 1 },
              ...markFills,
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ChartsGrid horizontal vertical />
            <LinePlot skipAnimation />
            <MarkPlot skipAnimation slots={{ mark: LargeMark }} />
            <TemporalLayer />
            <ChartsXAxis axisId="unemployment" />
            <ChartsYAxis axisId="inflation" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
