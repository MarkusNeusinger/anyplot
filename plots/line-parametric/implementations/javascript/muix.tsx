// anyplot.ai
// line-parametric: Parametric Curve Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // share of the larger span added around each curve
const LINE_WIDTH = 3.5;
const MARGIN = { top: 12, right: 28, bottom: 8, left: 8 };
const X_AXIS_H = 60;
const Y_AXIS_W = 68;
const HEADER_H = 80;
const PANEL_TITLE_H = 52;
const FOOTER_H = 56;
const SIDE_PAD = 32;
const PANEL_GAP = 32;

// Columns: set these to your data's column names
const CURVE = "Curve"; // role: extra
const T = "t"; // role: t
const X = "x(t)"; // role: x
const Y = "y(t)"; // role: y

// Data: replace this block with your own records, one object per row
// 800 samples of each curve: the Lissajous figure over one period and two turns of the spiral.
const data = [
  { name: "Lissajous figure: x = sin 3t, y = sin 2t", tEnd: 2 * Math.PI, fx: (s) => Math.sin(3 * s), fy: (s) => Math.sin(2 * s) },
  { name: "Archimedean spiral: x = t cos t, y = t sin t", tEnd: 4 * Math.PI, fx: (s) => s * Math.cos(s), fy: (s) => s * Math.sin(s) },
].flatMap((curve) =>
  Array.from({ length: 800 }, (_, i) => {
    const s = (i / 799) * curve.tEnd;
    return { [CURVE]: curve.name, [T]: s, [X]: curve.fx(s), [Y]: curve.fy(s) };
  }),
);

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const panelW = (W - 2 * SIDE_PAD - PANEL_GAP) / 2;
const panelH = H - HEADER_H - PANEL_TITLE_H - FOOTER_H;
const drawW = panelW - MARGIN.left - MARGIN.right - Y_AXIS_W;
const drawH = panelH - MARGIN.top - MARGIN.bottom - X_AXIS_H;
const seqRgb = t.seq.map((hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));

// One panel per curve, its rows in order of t. Both axes get the same units per pixel
// (equal aspect), centred on the curve, with the larger span setting the scale.
const panels = [...new Set(data.map((d) => d[CURVE]))].map((name) => {
  const rows = data.filter((d) => d[CURVE] === name).sort((a, b) => a[T] - b[T]);
  const xs = rows.map((d) => d[X]);
  const ys = rows.map((d) => d[Y]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const unitsPerPx = Math.max((x1 - x0) / drawW, (y1 - y0) / drawH) * (1 + 2 * PAD_SHARE);
  const tStart = rows[0][T];
  const tEnd = rows[rows.length - 1][T];
  return {
    name,
    rows,
    tStart,
    tEnd,
    xDomain: [(x0 + x1) / 2 - (unitsPerPx * drawW) / 2, (x0 + x1) / 2 + (unitsPerPx * drawW) / 2],
    yDomain: [(y0 + y1) / 2 - (unitsPerPx * drawH) / 2, (y0 + y1) / 2 + (unitsPerPx * drawH) / 2],
    // Imprint sequential ramp along increasing t: green at the start, blue at the end
    colors: rows.map((d) => {
      const f = tEnd > tStart ? (d[T] - tStart) / (tEnd - tStart) : 0;
      return `rgb(${seqRgb[0].map((c: number, k: number) => Math.round(c + (seqRgb[1][k] - c) * f)).join(", ")})`;
    }),
  };
});

const TITLE = "line-parametric · javascript · muix · anyplot.ai";
const SUBTITLE = `${panels.length} curves · ${data.length.toLocaleString("en-US")} samples · equal aspect ratio in each panel`;

// The curve as short segments coloured by t, an arrowhead ending on the last point and a start dot
function CurveLayer({ panel }: { panel: (typeof panels)[number] }) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const pts = panel.rows.map((d) => [xScale(d[X]), yScale(d[Y])]);
  const [sx, sy] = pts[0];
  const [ex, ey] = pts[pts.length - 1];
  const [px, py] = pts[pts.length - 2];
  const angle = (Math.atan2(ey - py, ex - px) * 180) / Math.PI;
  const midX = (xScale(panel.xDomain[0]) + xScale(panel.xDomain[1])) / 2;
  const labels = [
    { x: sx, y: sy - 18, text: `start, ${T} = ${panel.tStart.toFixed(2)}` },
    { x: ex, y: ey + 30, text: `end, ${T} = ${panel.tEnd.toFixed(2)}` },
  ];
  return (
    <g>
      {pts.slice(1).map(([x2, y2], i) => (
        <line
          key={i}
          x1={pts[i][0]}
          y1={pts[i][1]}
          x2={x2}
          y2={y2}
          stroke={panel.colors[i + 1]}
          strokeWidth={LINE_WIDTH}
          strokeLinecap="round"
        />
      ))}
      {/* Arrow tip on the last point; the start dot comes after it so a closed curve shows both */}
      <path
        d="M 0 0 L -24 -10 L -24 10 Z"
        transform={`translate(${ex}, ${ey}) rotate(${angle})`}
        fill={panel.colors[panel.colors.length - 1]}
        stroke={t.pageBg}
        strokeWidth={2}
      />
      <circle cx={sx} cy={sy} r={8} fill={panel.colors[0]} stroke={t.pageBg} strokeWidth={2.5} />
      {labels.map((lab) => (
        <text
          key={lab.text}
          x={lab.x + (lab.x > midX ? -14 : 14)}
          y={lab.y}
          textAnchor={lab.x > midX ? "end" : "start"}
          fontSize={15}
          fontWeight={600}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={4}
          paintOrder="stroke"
        >
          {lab.text}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: `16px ${SIDE_PAD}px 0 ${SIDE_PAD + 8}px`, boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <div style={{ display: "flex", gap: PANEL_GAP, padding: `0 ${SIDE_PAD}px` }}>
        {panels.map((panel) => (
          <div key={panel.name} style={{ width: panelW, display: "flex", flexDirection: "column" }}>
            <div style={{ height: PANEL_TITLE_H, paddingLeft: MARGIN.left + Y_AXIS_W, boxSizing: "border-box" }}>
              <div style={{ fontSize: 17, fontWeight: 600, color: t.ink }}>{panel.name}</div>
              <div style={{ fontSize: 14, color: t.inkSoft, marginTop: 4 }}>
                {panel.rows.length} samples, {T} from {panel.tStart.toFixed(2)} to {panel.tEnd.toFixed(2)}
              </div>
            </div>
            <ChartsContainer
              width={panelW}
              height={panelH}
              margin={MARGIN}
              skipAnimation
              series={[]}
              xAxis={[
                {
                  scaleType: "linear",
                  min: panel.xDomain[0],
                  max: panel.xDomain[1],
                  domainLimit: "strict",
                  label: X,
                  height: X_AXIS_H,
                  tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
                  labelStyle: { fontSize: 16, fill: t.ink },
                },
              ]}
              yAxis={[
                {
                  scaleType: "linear",
                  min: panel.yDomain[0],
                  max: panel.yDomain[1],
                  domainLimit: "strict",
                  label: Y,
                  width: Y_AXIS_W,
                  tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
                  labelStyle: { fontSize: 16, fill: t.ink },
                },
              ]}
              sx={{
                "& .MuiChartsAxis-line": { stroke: t.inkSoft },
                "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
                "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              }}
            >
              <ChartsGrid horizontal vertical />
              <CurveLayer panel={panel} />
              <ChartsXAxis />
              <ChartsYAxis />
            </ChartsContainer>
          </div>
        ))}
      </div>
      <div
        style={{
          height: FOOTER_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 12,
          fontSize: 15,
          color: t.inkSoft,
        }}
      >
        <span>Colour along each curve: {T} at the start</span>
        <span
          style={{
            width: 260,
            height: 14,
            borderRadius: 7,
            background: `linear-gradient(90deg, ${t.seq[0]}, ${t.seq[1]})`,
            display: "inline-block",
          }}
        />
        <span>{T} at the end</span>
      </div>
    </div>
  );
}
