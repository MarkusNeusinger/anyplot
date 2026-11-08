// anyplot.ai
// phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PHASE_LABELS = { solid: "Solid", liquid: "Liquid", gas: "Gas", supercritical: ["Supercritical", "fluid"] };
const TRIPLE_LABEL = "Triple point";
const CRITICAL_LABEL = "Critical point";
const SUPERSCRIPT = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const X_PAD_LEFT = 0.04; // share of the temperature span
const X_PAD_RIGHT = 0.12; // wider on the right, where the supercritical region lies
const Y_PAD_DECADES = 0.05; // share of the log-pressure span
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const TEMPERATURE = "Temperature (K)"; // role: temperature
const PRESSURE = "Pressure (Pa)"; // role: pressure
const BOUNDARY = "Phase boundary"; // role: phase_boundary

// Data: replace the two points and the records with your own, one object per row
// Water (IAPWS triple and critical point). Vaporization follows the Wagner-Pruss saturation
// equation (IAPWS 1992), smooth from the triple point and exact at the critical point;
// sublimation follows Clausius-Clapeyron; the Simon-Glatzel melting equation for ice Ih, whose
// negative slope is water's anomaly, runs up to 209.9 MPa, where ice Ih gives way to ice III
const TRIPLE_POINT = { [TEMPERATURE]: 273.16, [PRESSURE]: 611.657 }; // role: triple_point
const CRITICAL_POINT = { [TEMPERATURE]: 647.096, [PRESSURE]: 22.064e6 }; // role: critical_point
const GAS_CONSTANT = 8.314; // J/(mol K)
const ICE_IH_LIMIT = 209.9e6; // Pa, the ice Ih–ice III–liquid triple point
const WAGNER_PRUSS = [
  [-7.85951783, 1],
  [1.84408259, 1.5],
  [-11.7866497, 3],
  [22.6807411, 3.5],
  [-15.9618719, 4],
  [1.80122502, 7.5],
]; // [coefficient, exponent of 1 − T/Tc]
const TT = TRIPLE_POINT[TEMPERATURE];
const PT = TRIPLE_POINT[PRESSURE];
const TC = CRITICAL_POINT[TEMPERATURE];
const PC = CRITICAL_POINT[PRESSURE];
const melting = Array.from({ length: 36 }, (_, i) => {
  const p = 10 ** (Math.log10(PT) + (i * (Math.log10(ICE_IH_LIMIT) - Math.log10(PT))) / 35);
  return { [BOUNDARY]: "Solid–liquid (melting)", [TEMPERATURE]: TT * (1 + (p - PT) / -395.2e6) ** (1 / 9), [PRESSURE]: p };
});
const vaporization = Array.from({ length: 41 }, (_, i) => {
  const temp = TT + (i * (TC - TT)) / 40;
  const tau = Math.max(0, 1 - temp / TC); // never below 0, where the fractional powers are undefined
  const lnRatio = (TC / temp) * WAGNER_PRUSS.reduce((sum, [a, e]) => sum + a * tau ** e, 0);
  return { [BOUNDARY]: "Liquid–gas (vaporization)", [TEMPERATURE]: temp, [PRESSURE]: PC * Math.exp(lnRatio) };
});
const sublimation = Array.from({ length: 30 }, (_, i) => {
  const temp = 200 + (i * (TT - 200)) / 29;
  return { [BOUNDARY]: "Solid–gas (sublimation)", [TEMPERATURE]: temp, [PRESSURE]: PT * Math.exp((-51000 / GAS_CONSTANT) * (1 / temp - 1 / TT)) };
});
const data = [...melting, ...vaporization, ...sublimation];

// Plot: reads only data and the constants above
const boundaryNames = [...new Set(data.map((d) => d[BOUNDARY]))];
const boundaries = boundaryNames.map((name) => {
  const rows = data.filter((d) => d[BOUNDARY] === name).sort((a, b) => a[TEMPERATURE] - b[TEMPERATURE]);
  return { name, temperature: rows.map((d) => d[TEMPERATURE]), pressure: rows.map((d) => d[PRESSURE]) };
});

const allT = [...data.map((d) => d[TEMPERATURE]), TRIPLE_POINT[TEMPERATURE], CRITICAL_POINT[TEMPERATURE]];
const allLogP = [...data.map((d) => d[PRESSURE]), TRIPLE_POINT[PRESSURE], CRITICAL_POINT[PRESSURE]].map((p) => Math.log10(p));
const tSpan = Math.max(...allT) - Math.min(...allT);
const xMin = Math.min(...allT) - tSpan * X_PAD_LEFT;
const xMax = Math.max(...allT) + tSpan * X_PAD_RIGHT;
const logSpan = Math.max(...allLogP) - Math.min(...allLogP);
const logMin = Math.min(...allLogP) - logSpan * Y_PAD_DECADES;
const logMax = Math.max(...allLogP) + logSpan * Y_PAD_DECADES;
const decades = Array.from({ length: Math.floor(logMax) - Math.ceil(logMin) + 1 }, (_, i) => 10 ** (Math.ceil(logMin) + i));

const tUnit = (TEMPERATURE.match(/\(([^)]+)\)/) ?? ["", ""])[1];
const pUnit = (PRESSURE.match(/\(([^)]+)\)/) ?? ["", ""])[1];

// Region label anchors from the two points and the axis extents (log midpoints in pressure)
const tt = TRIPLE_POINT[TEMPERATURE];
const tc = CRITICAL_POINT[TEMPERATURE];
const logPt = Math.log10(TRIPLE_POINT[PRESSURE]);
const logPc = Math.log10(CRITICAL_POINT[PRESSURE]);
const regionAnchors = [
  { text: PHASE_LABELS.solid, t: (xMin + tt) / 2, p: 10 ** ((logPt + logMax) / 2) },
  { text: PHASE_LABELS.liquid, t: (tt + tc) / 2, p: 10 ** ((logPc + logMax) / 2) },
  { text: PHASE_LABELS.gas, t: (tt + tc) / 2, p: 10 ** ((logMin + logPt) / 2) },
];

const TITLE = "Water · phase-diagram-pt · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} boundary points on ${boundaries.length} curves · pressure on a log scale over ${Math.round(logMax - logMin)} decades`;

function PhaseAnnotations() {
  const xScale = useXScale("x-0");
  const yScale = useYScale("pressure");
  const tripleX = xScale(TRIPLE_POINT[TEMPERATURE]);
  const tripleY = yScale(TRIPLE_POINT[PRESSURE]);
  const criticalX = xScale(CRITICAL_POINT[TEMPERATURE]);
  const criticalY = yScale(CRITICAL_POINT[PRESSURE]);
  const guide = { stroke: t.inkSoft, strokeDasharray: "8 6", strokeWidth: 1.5 };
  const superX = (criticalX + xScale(xMax)) / 2;
  const superY = yScale(10 ** ((logPc + logMax) / 2));

  return (
    <g>
      <line x1={criticalX} x2={criticalX} y1={criticalY} y2={yScale(10 ** logMax)} {...guide} />
      <line x1={criticalX} x2={xScale(xMax)} y1={criticalY} y2={criticalY} {...guide} />

      {regionAnchors.map((r) => (
        <text key={r.text} x={xScale(r.t)} y={yScale(r.p)} fill={t.inkSoft} fontSize={24} fontWeight={600} textAnchor="middle">
          {r.text}
        </text>
      ))}
      <text x={superX} y={superY} fill={t.inkSoft} fontSize={17} fontWeight={600} textAnchor="middle">
        <tspan x={superX} dy="0">{PHASE_LABELS.supercritical[0]}</tspan>
        <tspan x={superX} dy="1.2em">{PHASE_LABELS.supercritical[1]}</tspan>
      </text>

      <circle cx={tripleX} cy={tripleY} r={9} fill={t.ink} stroke={t.pageBg} strokeWidth={2} />
      <text x={tripleX + 16} y={tripleY + 24} fill={t.ink} fontSize={16} fontWeight={600}>
        {TRIPLE_LABEL}
      </text>
      <text x={tripleX + 16} y={tripleY + 44} fill={t.inkSoft} fontSize={14}>
        {TRIPLE_POINT[TEMPERATURE]} {tUnit}, {TRIPLE_POINT[PRESSURE].toLocaleString("en-US")} {pUnit}
      </text>

      <rect
        x={criticalX - 9}
        y={criticalY - 9}
        width={18}
        height={18}
        transform={`rotate(45 ${criticalX} ${criticalY})`}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={2}
      />
      <text x={criticalX - 18} y={criticalY - 36} fill={t.ink} fontSize={16} fontWeight={600} textAnchor="end">
        {CRITICAL_LABEL}
      </text>
      <text x={criticalX - 18} y={criticalY - 16} fill={t.inkSoft} fontSize={14} textAnchor="end">
        {CRITICAL_POINT[TEMPERATURE]} {tUnit}, {CRITICAL_POINT[PRESSURE].toLocaleString("en-US")} {pUnit}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 8, left: 16 }}
        grid={{ horizontal: true }}
        xAxis={boundaries.map((b, i) => ({
          id: `x-${i}`,
          data: b.temperature,
          scaleType: "linear",
          min: xMin,
          max: xMax,
          position: i === 0 ? "bottom" : "none",
          label: TEMPERATURE,
          height: 64,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        }))}
        yAxis={[
          {
            id: "pressure",
            scaleType: "log",
            min: 10 ** logMin,
            max: 10 ** logMax,
            tickInterval: decades,
            valueFormatter: (v) =>
              `10${String(Math.round(Math.log10(v)))
                .split("")
                .map((ch) => SUPERSCRIPT[ch])
                .join("")}`,
            label: `${PRESSURE}, log scale`,
            width: 84,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        series={boundaries.map((b, i) => ({
          id: `boundary-${i}`,
          xAxisId: `x-${i}`,
          yAxisId: "pressure",
          data: b.pressure,
          label: b.name,
          color: t.palette[i],
          showMark: false,
          curve: "linear",
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3.5 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <PhaseAnnotations />
      </LineChart>
    </div>
  );
}
