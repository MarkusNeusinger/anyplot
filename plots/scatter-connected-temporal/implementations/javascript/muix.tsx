// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 84/100 | Updated: 2026-06-10

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // axis padding on each side as a share of the data span
const PERIOD = 10; // years per colour step along the path (decades)
const LABEL_GAP = 12; // px between a marker and its time label
const LABEL_DIRECTIONS = 8; // candidate label positions around each labelled point
const ARROW_LENGTH = 22; // px

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
// so the path stays unbroken where the colour changes
const lineSeries = periods.map((period, k) => ({
  type: "line" as const,
  id: `path-${period}`,
  color: periodColor[k],
  curve: "linear" as const,
  showMark: false,
  data: rows.map((d, i) => (periodOf[i] === period || periodOf[i + 1] === period ? d[INFLATION] : null)),
}));
const markerSeries = periods.map((period, k) => ({
  type: "scatter" as const,
  id: `points-${period}`,
  label: `${period}s`,
  color: periodColor[k],
  markerSize: 6,
  data: rows
    .map((d, i) => ({ id: i, x: d[UNEMPLOYMENT], y: d[INFLATION], period: periodOf[i] }))
    .filter((p) => p.period === period),
  valueFormatter: (p: any) => `${rows[p.id][YEAR]}: ${UNEMPLOYMENT} ${p.x}, ${INFLATION} ${p.y}`,
}));

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

function TemporalLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const pts = rows.map((d) => [xScale(d[UNEMPLOYMENT]), yScale(d[INFLATION])]);
  const segments = pts.slice(1).map((p, i) => [pts[i], p]);

  // Each label takes the position around its point with the most room to the path, the markers
  // and the labels already placed
  const placed: { x: number; y: number; w: number; anchor: string }[] = [];
  labelled.forEach(({ i, text }) => {
    const w = text.length * 8.5 + 4;
    const options = Array.from({ length: LABEL_DIRECTIONS }, (_, k) => (2 * Math.PI * k) / LABEL_DIRECTIONS).map((a) => {
      const cos = Math.cos(a);
      const sin = Math.sin(a);
      const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
      const x = pts[i][0] + cos * (LABEL_GAP + 6);
      const y = pts[i][1] - sin * (LABEL_GAP + 8);
      const left = anchor === "start" ? x : anchor === "end" ? x - w : x - w / 2;
      const samples = [0, 0.25, 0.5, 0.75, 1].map((f) => [left + f * w, y]);
      const pathRoom = Math.min(
        ...samples.flatMap(([sx, sy]) =>
          segments.map(([[ax, ay], [bx, by]]) => {
            const len2 = (bx - ax) ** 2 + (by - ay) ** 2 || 1;
            const s = Math.max(0, Math.min(1, ((sx - ax) * (bx - ax) + (sy - ay) * (by - ay)) / len2));
            return Math.hypot(sx - ax - s * (bx - ax), sy - ay - s * (by - ay)) - 8;
          }),
        ),
      );
      const clash = placed.some((p) => {
        const pLeft = p.anchor === "start" ? p.x : p.anchor === "end" ? p.x - p.w : p.x - p.w / 2;
        return left < pLeft + p.w && pLeft < left + w && Math.abs(p.y - y) < 18;
      });
      return { x, y, w, anchor, room: clash ? -Infinity : pathRoom };
    });
    placed.push(options.reduce((best, o) => (o.room > best.room ? o : best)));
  });

  return (
    <g>
      <defs>
        {arrows.map((a, k) => (
          <marker
            key={`head-${k}`}
            id={`temporal-head-${k}`}
            viewBox="0 0 10 10"
            refX={10}
            refY={5}
            markerWidth={12}
            markerHeight={12}
            markerUnits="userSpaceOnUse"
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill={a.color} />
          </marker>
        ))}
      </defs>
      {arrows.map((a, k) => {
        const [ax, ay] = pts[a.from];
        const [bx, by] = pts[a.from + 1];
        const len = Math.hypot(bx - ax, by - ay) || 1;
        const mx = (ax + bx) / 2;
        const my = (ay + by) / 2;
        const ux = (bx - ax) / len;
        const uy = (by - ay) / len;
        return (
          <line
            key={`arrow-${k}`}
            x1={mx - (ux * ARROW_LENGTH) / 2}
            y1={my - (uy * ARROW_LENGTH) / 2}
            x2={mx + (ux * ARROW_LENGTH) / 2}
            y2={my + (uy * ARROW_LENGTH) / 2}
            stroke={a.color}
            strokeWidth={2.5}
            markerEnd={`url(#temporal-head-${k})`}
          />
        );
      })}
      {labelled.map(({ text }, k) => (
        <text
          key={`label-${text}`}
          x={placed[k].x}
          y={placed[k].y}
          textAnchor={placed[k].anchor}
          dominantBaseline="central"
          fontSize={14}
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
        series={[...lineSeries, ...markerSeries]}
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
          <ChartsLegend sx={{ fontSize: 15, color: t.ink, pr: 6 }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 2.5 },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1.5 },
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ChartsGrid horizontal vertical />
            <LinePlot skipAnimation />
            <ScatterPlot />
            <TemporalLayer />
            <ChartsXAxis axisId="unemployment" />
            <ChartsYAxis axisId="inflation" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
