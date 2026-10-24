// anyplot.ai
// bifurcation-basic: Bifurcation Diagram for Dynamical Systems
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-17
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const STATE_MIN = 0;
const STATE_MAX = 1;
const POINT_ALPHA = 0.55;
const R_PAD_SHARE = 0.02;
const LABEL_DX = -8; // labels sit left of their marker line
// topShare: label height as a share of the drawing area, measured from its top
const BIFURCATION_POINTS = [
  { r: 3.0, text: "Period-2", topShare: 0.06 },
  { r: 3.449, text: "Period-4", topShare: 0.06 },
  { r: 3.544, text: "Period-8", topShare: 0.86 },
];

// Columns: set these to your data's column names
const PARAMETER = "Growth rate (r)"; // role: parameter
const STATE = "Steady-state population (x)"; // role: state

// Data: replace this block with your own records, one object per row
const data = (() => {
  const rMin = 2.5;
  const rMax = 4.0;
  const rSteps = 1000;
  const transient = 300;
  const record = 120;
  const x0 = 0.4;
  const rows: { [key: string]: number }[] = [];
  for (let i = 0; i < rSteps; i++) {
    const r = rMin + ((rMax - rMin) * i) / (rSteps - 1);
    let x = x0;
    for (let n = 0; n < transient; n++) x = r * x * (1 - x);
    for (let n = 0; n < record; n++) {
      x = r * x * (1 - x);
      rows.push({ [PARAMETER]: r, [STATE]: x });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
let rMin = Infinity;
let rMax = -Infinity;
const points = data.map((d, i) => {
  const r = d[PARAMETER];
  const x = d[STATE];
  if (r < rMin) rMin = r;
  if (r > rMax) rMax = r;
  return { x: r, y: x, id: i };
});

const rPad = (rMax - rMin) * R_PAD_SHARE;

const p0Int = parseInt(t.palette[0].slice(1), 16);
const pointColor = `rgba(${(p0Int >> 16) & 255}, ${(p0Int >> 8) & 255}, ${p0Int & 255}, ${POINT_ALPHA})`;

const TITLE = "bifurcation-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${points.length.toLocaleString("en-US")} points · ${PARAMETER}: ${rMin.toLocaleString("en-US")}–${rMax.toLocaleString("en-US")}`;
const HEADER_H = 78;

function Bifurcations() {
  const xScale = useXScale("r");
  const { top, height } = useDrawingArea();

  return (
    <g>
      {BIFURCATION_POINTS.filter((m) => m.r >= rMin && m.r <= rMax).map((m) => {
        const x = xScale(m.r);
        const labelY = top + m.topShare * height;
        const labelText = `${m.text} (r ≈ ${m.r})`;
        const pillW = labelText.length * 7.6 + 12;
        const pillX = x + LABEL_DX - pillW + 4;
        return (
          <g key={m.r}>
            <line
              x1={x}
              y1={top}
              x2={x}
              y2={top + height}
              stroke={t.amber}
              strokeWidth={1.5}
              strokeDasharray="7 5"
              opacity={0.75}
            />
            <rect
              x={pillX}
              y={labelY - 15}
              width={pillW}
              height={22}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.86}
            />
            <text
              x={x + LABEL_DX}
              y={labelY}
              fill={t.ink}
              textAnchor="end"
              style={{
                fontSize: 14,
                fontFamily: "Inter, system-ui, sans-serif",
                fontWeight: 600,
              }}
            >
              {labelText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </span>
        <span style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</span>
      </div>
      <ChartsContainer
        width={W}
        height={H - HEADER_H}
        skipAnimation
        colors={[pointColor]}
        margin={{ top: 16, bottom: 20, left: 36, right: 36 }}
        series={[
          {
            type: "scatter",
            data: points,
            markerSize: 1,
            label: STATE,
            xAxisId: "r",
            yAxisId: "x",
          },
        ]}
        xAxis={[
          {
            id: "r",
            min: rMin - rPad,
            max: rMax + rPad,
            tickNumber: 10,
            height: 64,
            label: PARAMETER,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
          },
        ]}
        yAxis={[
          {
            id: "x",
            min: STATE_MIN,
            max: STATE_MAX,
            width: 84,
            tickNumber: 11,
            label: STATE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ScatterPlot />
        <ChartsXAxis axisId="r" />
        <ChartsYAxis axisId="x" />
        <Bifurcations />
      </ChartsContainer>
    </div>
  );
}
