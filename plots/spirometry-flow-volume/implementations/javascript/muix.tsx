// anyplot.ai
// spirometry-flow-volume: Spirometry Flow-Volume Loop
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 90/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const FEV_TIME_S = 1; // FEV1 is the volume exhaled in the first second
const FLOW_QUANTITY = "Flow"; // the y quantity of every flow-volume loop
const MEASURED_LABEL = "Measured";
const PREDICTED_LABEL = "Predicted normal";
const X_PAD_SHARE = 0.04;
const Y_PAD_SHARE = 0.08;

// Columns: set these to your data's column names
const VOLUME = "Volume (L)"; // role: volume
const FLOW_EXP = "Expiratory flow (L/s)"; // role: flow_expiratory
const FLOW_INSP = "Inspiratory flow (L/s)"; // role: flow_inspiratory
const VOLUME_PRED = "Predicted volume (L)"; // role: volume_predicted
const FLOW_PRED_EXP = "Predicted expiratory flow (L/s)"; // role: flow_predicted_expiratory
const FLOW_PRED_INSP = "Predicted inspiratory flow (L/s)"; // role: flow_predicted_inspiratory

// Data: replace this block with your own records, one object per row
// Forced expiration and inspiration of an adult with a mild obstructive pattern
// (reduced PEF, descending limb scooped toward the volume axis), sampled along the
// exhaled volume, beside the predicted-normal loop for the same patient.
const N_SAMPLES = 140;
const MEAS = { fvc: 5.0, pef: 9.5, vPeak: 0.35, scoop: 2.0, pif: 5.9 };
const PRED = { fvc: 5.6, pef: 10.6, vPeak: 0.3, scoop: 1.0, pif: 6.6 };
const data: Record<string, number>[] = [];
for (let i = 0; i < N_SAMPLES; i += 1) {
  const share = i / (N_SAMPLES - 1);
  const v = MEAS.fvc * share;
  const vp = PRED.fvc * share;
  const flowExp =
    v <= MEAS.vPeak
      ? MEAS.pef * (v / MEAS.vPeak) ** 0.55
      : MEAS.pef * ((MEAS.fvc - v) / (MEAS.fvc - MEAS.vPeak)) ** MEAS.scoop;
  const flowPredExp =
    vp <= PRED.vPeak
      ? PRED.pef * (vp / PRED.vPeak) ** 0.55
      : PRED.pef * ((PRED.fvc - vp) / (PRED.fvc - PRED.vPeak)) ** PRED.scoop;
  data.push({
    [VOLUME]: Number(v.toFixed(3)),
    [FLOW_EXP]: Number(flowExp.toFixed(3)),
    [FLOW_INSP]: Number((-MEAS.pif * Math.sin(Math.PI * share)).toFixed(3)),
    [VOLUME_PRED]: Number(vp.toFixed(3)),
    [FLOW_PRED_EXP]: Number(flowPredExp.toFixed(3)),
    [FLOW_PRED_INSP]: Number((-PRED.pif * Math.sin(Math.PI * share)).toFixed(3)),
  });
}

// Plot: reads only data and the constants above
// Each limb is sorted by volume; the expiratory limb above zero and the
// inspiratory limb below it meet at both ends of the volume range and close the loop.
const measured = data
  .filter((d) => d[VOLUME] != null && d[FLOW_EXP] != null && d[FLOW_INSP] != null)
  .sort((a, b) => a[VOLUME] - b[VOLUME]);
const predicted = data
  .filter((d) => d[VOLUME_PRED] != null && d[FLOW_PRED_EXP] != null && d[FLOW_PRED_INSP] != null)
  .sort((a, b) => a[VOLUME_PRED] - b[VOLUME_PRED]);
const measVol = measured.map((d) => d[VOLUME]);
const measExp = measured.map((d) => d[FLOW_EXP]);
const measInsp = measured.map((d) => d[FLOW_INSP]);
const predVol = predicted.map((d) => d[VOLUME_PRED]);
const predExp = predicted.map((d) => d[FLOW_PRED_EXP]);
const predInsp = predicted.map((d) => d[FLOW_PRED_INSP]);

const volUnit = VOLUME.match(/\(([^)]+)\)/)?.[1] ?? "";
const flowUnit = FLOW_EXP.match(/\(([^)]+)\)/)?.[1] ?? "";

// PEF: the highest measured expiratory flow; FVC: the width of the measured loop
const pefIdx = measExp.indexOf(Math.max(...measExp));
const pef = measExp[pefIdx];
const pefVolume = measVol[pefIdx];
const fvc = measVol[measVol.length - 1] - measVol[0];

// FEV1: elapsed time along the expiratory limb is the integral of dV / flow; the
// volume reached at FEV_TIME_S is FEV1 (the whole FVC if the limb ends sooner)
let elapsed = 0;
let fev1 = fvc;
for (let i = 1; i < measured.length; i += 1) {
  const dv = measVol[i] - measVol[i - 1];
  const meanFlow = (measExp[i] + measExp[i - 1]) / 2;
  const dt = meanFlow > 0 ? dv / meanFlow : Infinity;
  if (elapsed + dt >= FEV_TIME_S) {
    fev1 = measVol[i - 1] - measVol[0] + (dv * (FEV_TIME_S - elapsed)) / dt;
    break;
  }
  elapsed += dt;
}
const ratio = Math.round((fev1 / fvc) * 100);

const panelRows = [
  ["PEF", `${pef.toFixed(1)} ${flowUnit}`],
  [`FEV${FEV_TIME_S}`, `${fev1.toFixed(2)} ${volUnit}`],
  ["FVC", `${fvc.toFixed(2)} ${volUnit}`],
  [`FEV${FEV_TIME_S}/FVC`, `${ratio} %`],
];

const allVol = [...measVol, ...predVol];
const allFlow = [...measExp, ...measInsp, ...predExp, ...predInsp];
const volSpan = Math.max(...allVol) - Math.min(...allVol);
const flowSpan = Math.max(...allFlow) - Math.min(...allFlow);
const xMin = Math.min(...allVol) - volSpan * X_PAD_SHARE;
const xMax = Math.max(...allVol) + volSpan * X_PAD_SHARE;
const yMin = Math.min(...allFlow) - flowSpan * Y_PAD_SHARE;
const yMax = Math.max(...allFlow) + flowSpan * Y_PAD_SHARE;

const TITLE = "spirometry-flow-volume · javascript · muix · anyplot.ai";
const TITLE_H = 56;
const PANEL_W = 280;
const PANEL_H = 204;
const MEASURED_STROKE = 3.5;
const PREDICTED_STROKE = 2.5;
const PREDICTED_DASH = "9 6";

// PEF marker, limb notes at the zero-flow line, and the legend + clinical values panel
function ClinicalOverlay() {
  const xs = useXScale("measured") as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const { left, top, width } = useDrawingArea();
  const zeroY = ys(0);
  const midX = xs((measVol[0] + measVol[measVol.length - 1]) / 2);
  const pefX = xs(pefVolume);
  const pefY = ys(pef);
  const px = left + width - PANEL_W - 18;
  const py = top + 14;

  return (
    <g>
      <text x={midX} y={zeroY - 12} fontSize={14} textAnchor="middle" fill={t.inkSoft}>
        Expiration ▲
      </text>
      <text x={midX} y={zeroY + 24} fontSize={14} textAnchor="middle" fill={t.inkSoft}>
        Inspiration ▼
      </text>

      <circle cx={pefX} cy={pefY} r={9} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={2.5} />
      <line x1={pefX + 4} y1={pefY + 9} x2={pefX + 18} y2={pefY + 62} stroke={t.ink} strokeWidth={1.5} />
      <text
        x={pefX + 20}
        y={pefY + 82}
        fontSize={15}
        fontWeight={600}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={5}
        paintOrder="stroke"
        strokeLinejoin="round"
      >
        {`PEF ${pef.toFixed(1)} ${flowUnit}`}
      </text>

      <rect x={px} y={py} width={PANEL_W} height={PANEL_H} rx={8} fill={t.elevatedBg} stroke={t.grid} strokeWidth={1} />
      <line x1={px + 18} y1={py + 28} x2={px + 52} y2={py + 28} stroke={t.palette[0]} strokeWidth={MEASURED_STROKE} />
      <text x={px + 64} y={py + 33} fontSize={15} fill={t.ink}>
        {MEASURED_LABEL}
      </text>
      <line
        x1={px + 18}
        y1={py + 54}
        x2={px + 52}
        y2={py + 54}
        stroke={t.inkSoft}
        strokeWidth={PREDICTED_STROKE}
        strokeDasharray={PREDICTED_DASH}
      />
      <text x={px + 64} y={py + 59} fontSize={15} fill={t.ink}>
        {PREDICTED_LABEL}
      </text>
      <line x1={px + 16} y1={py + 74} x2={px + PANEL_W - 16} y2={py + 74} stroke={t.grid} strokeWidth={1} />
      {panelRows.map(([k, v], i) => (
        <g key={k}>
          <text x={px + 18} y={py + 101 + i * 28} fontSize={15} fill={t.inkSoft}>
            {k}
          </text>
          <text x={px + PANEL_W - 18} y={py + 101 + i * 28} fontSize={15} fontWeight={600} textAnchor="end" fill={t.ink}>
            {v}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 600,
          textAlign: "center",
          height: TITLE_H,
          lineHeight: `${TITLE_H}px`,
          flexShrink: 0,
        }}
      >
        {TITLE}
      </Typography>
      <LineChart
        width={W}
        height={H - TITLE_H}
        skipAnimation
        hideLegend
        margin={{ top: 24, right: 44, bottom: 16, left: 24 }}
        grid={{ horizontal: true, vertical: true }}
        xAxis={[
          {
            id: "measured",
            data: measVol,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: VOLUME,
            tickNumber: 8,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
          {
            id: "predicted",
            data: predVol,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            position: "none",
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: `${FLOW_QUANTITY} (${flowUnit})`,
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={[
          { id: "predicted-exp", xAxisId: "predicted", data: predExp, label: FLOW_PRED_EXP, color: t.inkSoft, showMark: false, curve: "linear" },
          { id: "predicted-insp", xAxisId: "predicted", data: predInsp, label: FLOW_PRED_INSP, color: t.inkSoft, showMark: false, curve: "linear" },
          { id: "measured-exp", xAxisId: "measured", data: measExp, label: FLOW_EXP, color: t.palette[0], showMark: false, curve: "linear" },
          { id: "measured-insp", xAxisId: "measured", data: measInsp, label: FLOW_INSP, color: t.palette[0], showMark: false, curve: "linear" },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: MEASURED_STROKE },
          '& .MuiLineChart-line[data-series="predicted-exp"], & .MuiLineChart-line[data-series="predicted-insp"]': {
            strokeWidth: PREDICTED_STROKE,
            strokeDasharray: PREDICTED_DASH,
          },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine y={0} lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5 }} />
        <ClinicalOverlay />
      </LineChart>
    </Box>
  );
}
