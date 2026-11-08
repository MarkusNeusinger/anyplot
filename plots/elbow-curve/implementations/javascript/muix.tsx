// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 92/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD = 0.04; // share of the k range added on both sides so the outermost markers sit inside the plot
const Y_PAD = 0.08; // share of the largest inertia left free above it
const ELBOW_R = 11; // px radius of the highlighted elbow marker
const TITLE = "elbow-curve · javascript · muix · anyplot.ai";
const HEADER_H = 84;

// Columns: set these to your data's column names
const K = "Number of clusters (k)"; // role: k_values
const INERTIA = "Inertia (within-cluster sum of squares)"; // role: inertia

// Data: replace this block with your own records, one object per row
// K-means inertia for a customer segmentation model, k = 1 to 10
const data = [
  { [K]: 1, [INERTIA]: 1250 },
  { [K]: 2, [INERTIA]: 690 },
  { [K]: 3, [INERTIA]: 410 },
  { [K]: 4, [INERTIA]: 260 },
  { [K]: 5, [INERTIA]: 195 },
  { [K]: 6, [INERTIA]: 165 },
  { [K]: 7, [INERTIA]: 145 },
  { [K]: 8, [INERTIA]: 130 },
  { [K]: 9, [INERTIA]: 118 },
  { [K]: 10, [INERTIA]: 108 },
];

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[INERTIA])).sort((a, b) => a[K] - b[K]);
const ks = rows.map((d) => d[K]);
const inertia = rows.map((d) => d[INERTIA]);
const kLo = ks[0];
const kHi = ks[ks.length - 1];
const yLo = Math.min(...inertia);
const yHi = Math.max(...inertia);

// Elbow: the point farthest from the straight line joining the first and last points,
// both axes scaled to 0-1 so k and inertia weigh equally
const chordDistance = rows.map((d) => 1 - (d[K] - kLo) / (kHi - kLo) - (d[INERTIA] - yLo) / (yHi - yLo));
const elbowIdx = chordDistance.indexOf(Math.max(...chordDistance));
const elbowK = ks[elbowIdx];
const elbowSeries = inertia.map((v, i) => (i === elbowIdx ? v : null));
const dropToElbow = (1 - inertia[elbowIdx] / inertia[0]) * 100;
const dropAfter = (1 - inertia[inertia.length - 1] / inertia[elbowIdx]) * 100;
const subtitle = `k = ${kLo} to ${kHi} · elbow at k = ${elbowK}, the point farthest from the line joining the first and last k · inertia falls ${dropToElbow.toFixed(0)}% up to the elbow and ${dropAfter.toFixed(0)}% after it`;

// Dashed guide from the top of the plot down to the elbow marker, with the label beside it
function ElbowGuide() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { top } = useDrawingArea();
  const x = xScale(elbowK);
  const y = yScale(inertia[elbowIdx]);
  return (
    <g>
      <line x1={x} x2={x} y1={top} y2={y - ELBOW_R - 6} stroke={t.inkSoft} strokeWidth={2} strokeDasharray="6 6" />
      <text x={x + 12} y={top + 18} fontSize={16} fontWeight={600} fill={t.ink}>
        {`Elbow at k = ${elbowK}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "22px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{subtitle}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 24, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: ks,
            scaleType: "linear",
            min: kLo - (kHi - kLo) * X_PAD,
            max: kHi + (kHi - kLo) * X_PAD,
            tickMinStep: 1,
            valueFormatter: (v) => v.toFixed(0),
            label: K,
            height: 68,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: yHi * (1 + Y_PAD),
            label: INERTIA,
            width: 92,
            valueFormatter: (v) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "inertia",
            data: inertia,
            label: INERTIA,
            color: t.palette[0],
            showMark: true,
            shape: "circle",
            curve: "monotoneX",
            area: true,
          },
          {
            id: "elbow",
            data: elbowSeries,
            label: `Elbow (k = ${elbowK})`,
            color: t.palette[0],
            showMark: true,
            shape: "circle",
            disableHighlight: true,
          },
        ]}
        sx={{
          '& .MuiLineChart-area[data-series="inertia"]': { fillOpacity: 0.1 },
          '& .MuiLineChart-line[data-series="inertia"]': { strokeWidth: 3 },
          '& .MuiLineChart-mark[data-series="inertia"]': { r: 6, fill: t.pageBg, strokeWidth: 2.5 },
          '& .MuiLineChart-mark[data-series="elbow"]': { r: ELBOW_R, fill: t.palette[0], stroke: t.ink, strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ElbowGuide />
      </LineChart>
    </div>
  );
}
