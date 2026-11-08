// anyplot.ai
// line-parametric: Parametric Curve Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

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
const LABEL_FONT = 15;
const LABEL_CHAR_EM = 0.6; // estimated width of one label character, in em, for the free-space test
const LABEL_RINGS = [30, 56, 84, 116]; // distances from its point at which a label is tried, in px
// Directions a label is tried in, preferred first: the four diagonals, then above, below, right and left
const LABEL_DIRECTIONS = [[1, -1], [-1, -1], [1, 1], [-1, 1], [0, -1], [0, 1], [1, 0], [-1, 0]];
const LABEL_CLEARANCE = 6; // px kept free between a label and the curve
const LEADER_GAP = 12; // px between a point and the start of its leader line

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

// The curve as short segments coloured by t, an arrowhead ending on the last point and a start dot.
// Each start and end label takes the nearest spot around its point whose box holds the fewest curve
// samples, inside the drawing area and clear of the label placed before it, with a leader to the point.
function CurveLayer({ panel }: { panel: (typeof panels)[number] }) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const area = useDrawingArea();
  const pts = panel.rows.map((d) => [xScale(d[X]), yScale(d[Y])]);
  const [sx, sy] = pts[0];
  const [ex, ey] = pts[pts.length - 1];
  const [px, py] = pts[pts.length - 2];
  const angle = (Math.atan2(ey - py, ex - px) * 180) / Math.PI;
  const labels = [
    { x: sx, y: sy, text: `start, ${T} = ${panel.tStart.toFixed(2)}` },
    { x: ex, y: ey, text: `end, ${T} = ${panel.tEnd.toFixed(2)}` },
  ].reduce((placed, lab) => {
    const w = lab.text.length * LABEL_FONT * LABEL_CHAR_EM;
    const h = LABEL_FONT * 1.3;
    const best = LABEL_RINGS.flatMap((r) =>
      LABEL_DIRECTIONS.map(([dx, dy]) => {
        const k = dx !== 0 && dy !== 0 ? Math.SQRT1_2 : 1;
        const ax = lab.x + dx * r * k;
        const ay = lab.y + dy * r * k;
        const x0 = dx > 0 ? ax : dx < 0 ? ax - w : ax - w / 2;
        const y0 = dy > 0 ? ay : dy < 0 ? ay - h : ay - h / 2;
        const hits = pts.filter(
          ([qx, qy]) =>
            qx > x0 - LABEL_CLEARANCE && qx < x0 + w + LABEL_CLEARANCE && qy > y0 - LABEL_CLEARANCE && qy < y0 + h + LABEL_CLEARANCE,
        ).length;
        // Curve samples within the clearance of the leader segment, from LEADER_GAP off the point to the label
        const lx = lab.x + dx * k * LEADER_GAP;
        const ly = lab.y + dy * k * LEADER_GAP;
        const len2 = (ax - lx) ** 2 + (ay - ly) ** 2;
        const crossings = pts.filter(([qx, qy]) => {
          const u = Math.max(0, Math.min(1, ((qx - lx) * (ax - lx) + (qy - ly) * (ay - ly)) / len2));
          return Math.hypot(qx - lx - u * (ax - lx), qy - ly - u * (ay - ly)) < LABEL_CLEARANCE;
        }).length;
        const outside = x0 < area.left || x0 + w > area.left + area.width || y0 < area.top || y0 + h > area.top + area.height;
        const clash = placed.some((b) => x0 < b.x0 + b.w && b.x0 < x0 + w && y0 < b.y0 + b.h && b.y0 < y0 + h);
        return { ...lab, dx, dy, k, ax, ay, x0, y0, w, h, score: hits + crossings + (outside || clash ? pts.length : 0) };
      }),
    ).reduce((a, b) => (b.score < a.score ? b : a));
    return [...placed, best];
  }, []);
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
        <g key={lab.text}>
          <line
            x1={lab.x + lab.dx * lab.k * LEADER_GAP}
            y1={lab.y + lab.dy * lab.k * LEADER_GAP}
            x2={lab.ax}
            y2={lab.ay}
            stroke={t.inkSoft}
            strokeWidth={1.5}
          />
          <text
            x={lab.dx > 0 ? lab.x0 : lab.dx < 0 ? lab.x0 + lab.w : lab.x0 + lab.w / 2}
            y={lab.y0 + lab.h / 2}
            textAnchor={lab.dx > 0 ? "start" : lab.dx < 0 ? "end" : "middle"}
            dominantBaseline="central"
            fontSize={LABEL_FONT}
            fontWeight={600}
            fill={t.ink}
            stroke={t.pageBg}
            strokeWidth={4}
            paintOrder="stroke"
          >
            {lab.text}
          </text>
        </g>
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
