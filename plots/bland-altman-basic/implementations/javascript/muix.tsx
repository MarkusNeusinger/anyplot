// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOA_Z = 1.96; // 95% limits of agreement: bias ± 1.96 SD of the differences
const X_PAD_SHARE = 0.04; // axis padding as a share of the data span
const Y_PAD_SHARE = 0.08;

// Columns: set these to your data's column names
const CUFF = "Oscillometric cuff (mmHg)"; // role: method1
const REFERENCE = "Mercury reference (mmHg)"; // role: method2

// Data: replace this block with your own records, one object per row
// Systolic blood pressure of 70 patients, each measured once with a new
// oscillometric cuff and once with the mercury-column reference standard.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const gaussian = () => {
    const u1 = Math.max(rand(), 1e-9);
    const u2 = rand();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };
  const reference = Array.from({ length: 70 }, () => 122 + gaussian() * 15);
  // The cuff reads slightly high and its scatter widens with the pressure
  return reference.map((value) => ({
    [CUFF]: value + 3.4 + gaussian() * (4 + value * 0.02),
    [REFERENCE]: value,
  }));
})();

// Plot: reads only data and the constants above
const n = data.length;
const points = data.map((d, i) => ({
  id: i,
  x: (d[CUFF] + d[REFERENCE]) / 2,
  y: d[CUFF] - d[REFERENCE],
}));
const bias = points.reduce((sum, p) => sum + p.y, 0) / n;
const sdDiff = Math.sqrt(points.reduce((sum, p) => sum + (p.y - bias) ** 2, 0) / (n - 1));
const upperLimit = bias + LOA_Z * sdDiff;
const lowerLimit = bias - LOA_Z * sdDiff;

const xs = points.map((p) => p.x);
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const xPad = (xMax - xMin) * X_PAD_SHARE;
const ys = [...points.map((p) => p.y), upperLimit, lowerLimit];
const yMin = Math.min(...ys);
const yMax = Math.max(...ys);
const yPad = (yMax - yMin) * Y_PAD_SHARE;

// Axis titles name both methods; the shared unit comes from the column names
const cuffName = CUFF.replace(/\s*\([^)]*\)\s*$/, "");
const referenceName = REFERENCE.replace(/\s*\([^)]*\)\s*$/, "");
const unit = CUFF.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const unitSuffix = unit ? ` ${unit}` : "";
const xLabel = `Mean of ${cuffName} and ${referenceName}${unit ? ` (${unit})` : ""}`;
const yLabel = `${cuffName} − ${referenceName}${unit ? ` (${unit})` : ""}`;

const references = [
  { value: upperLimit, name: `+${LOA_Z} SD`, color: t.inkSoft, weight: 400, dash: "8 6", stroke: 1.75 },
  { value: bias, name: "Bias", color: t.ink, weight: 600, dash: undefined, stroke: 2.5 },
  { value: lowerLimit, name: `−${LOA_Z} SD`, color: t.inkSoft, weight: 400, dash: "8 6", stroke: 1.75 },
];

const TITLE = "bland-altman-basic · javascript · muix · anyplot.ai";
const subtitle = `n = ${n} paired readings · SD of the differences ${sdDiff.toFixed(1)}${unitSuffix}`;
const TITLE_H = 76;

function LimitLabels() {
  const yScale = useYScale();
  const area = useDrawingArea();
  const x = area.left + area.width + 14;
  return (
    <g>
      {references.map((r) => (
        <text key={r.name} x={x} y={yScale(r.value)} fill={r.color} fontSize={15} fontWeight={r.weight}>
          <tspan x={x} dy="-0.25em">
            {r.name}
          </tspan>
          <tspan x={x} dy="1.25em">
            {`${r.value.toFixed(1).replace("-", "−")}${unitSuffix}`}
          </tspan>
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ScatterChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        series={[{ id: "pairs", data: points, markerSize: 7, color: t.palette[0] }]}
        xAxis={[
          {
            min: xMin - xPad,
            max: xMax + xPad,
            label: xLabel,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: yMin - yPad,
            max: yMax + yPad,
            label: yLabel,
            width: 84,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        margin={{ left: 24, right: 150, top: 16, bottom: 16 }}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiScatterChart-marker": { fillOpacity: 0.6, stroke: t.pageBg, strokeWidth: 1 },
        }}
      >
        {references.map((r) => (
          <ChartsReferenceLine
            key={r.name}
            y={r.value}
            lineStyle={{ stroke: r.color, strokeWidth: r.stroke, strokeDasharray: r.dash }}
          />
        ))}
        <LimitLabels />
      </ScatterChart>
    </div>
  );
}
