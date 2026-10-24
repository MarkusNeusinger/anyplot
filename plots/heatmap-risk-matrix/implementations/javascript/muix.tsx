// anyplot.ai
// heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "heatmap-risk-matrix · javascript · muix · anyplot.ai";

const RATING_MIN = 1;
const RATING_MAX = 5;
const CELL_FILL_OPACITY = 0.62;
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

const LIKELIHOOD_LABELS = [
  "Rare (1)",
  "Unlikely (2)",
  "Possible (3)",
  "Likely (4)",
  "Almost Certain (5)",
];
const IMPACT_LABELS = [
  "Negligible (1)",
  "Minor (2)",
  "Moderate (3)",
  "Major (4)",
  "Catastrophic (5)",
];

const ZONE_LEGEND = [
  { name: "Low", label: "Low (1–4)", maxScore: 4, color: t.palette[0] },
  { name: "Medium", label: "Medium (5–9)", maxScore: 9, color: t.amber },
  { name: "High", label: "High (10–16)", maxScore: 16, color: t.palette[3] },
  { name: "Critical", label: "Critical (20–25)", maxScore: 25, color: t.palette[4] },
];

// Columns: set these to your data's column names
const RISK_NAME = "Risk"; // role: risk_name
const LIKELIHOOD = "Likelihood"; // role: likelihood
const IMPACT = "Consequence Impact"; // role: impact

// Data: replace this block with your own records
const data = [
  { [RISK_NAME]: "Data Breach", [LIKELIHOOD]: 3, [IMPACT]: 5 },
  { [RISK_NAME]: "Ransomware", [LIKELIHOOD]: 4, [IMPACT]: 5 },
  { [RISK_NAME]: "DDoS Attack", [LIKELIHOOD]: 4, [IMPACT]: 3 },
  { [RISK_NAME]: "Supply Chain", [LIKELIHOOD]: 2, [IMPACT]: 4 },
  { [RISK_NAME]: "Insider Threat", [LIKELIHOOD]: 2, [IMPACT]: 5 },
  { [RISK_NAME]: "API Failure", [LIKELIHOOD]: 3, [IMPACT]: 3 },
  { [RISK_NAME]: "Key Staff Loss", [LIKELIHOOD]: 3, [IMPACT]: 4 },
  { [RISK_NAME]: "Budget Cut", [LIKELIHOOD]: 4, [IMPACT]: 2 },
  { [RISK_NAME]: "Compliance", [LIKELIHOOD]: 2, [IMPACT]: 3 },
  { [RISK_NAME]: "Cloud Outage", [LIKELIHOOD]: 2, [IMPACT]: 4 },
  { [RISK_NAME]: "Phishing", [LIKELIHOOD]: 5, [IMPACT]: 2 },
  { [RISK_NAME]: "HW Failure", [LIKELIHOOD]: 1, [IMPACT]: 3 },
];

// Plot: reads only data and the constants above
const gridCount = RATING_MAX - RATING_MIN + 1;
const axisMin = RATING_MIN - 0.5;
const axisMax = RATING_MAX + 0.5;
const tickRatings = Array.from({ length: gridCount }, (_, i) => RATING_MIN + i);

const bgInt = parseInt(t.pageBg.slice(1), 16);
const bgR = (bgInt >> 16) & 255;
const bgG = (bgInt >> 8) & 255;
const bgB = bgInt & 255;

const gridCells: Array<{
  lh: number;
  imp: number;
  score: number;
  color: string;
  scoreTextFill: string;
}> = [];

for (let lh = RATING_MIN; lh <= RATING_MAX; lh++) {
  for (let imp = RATING_MIN; imp <= RATING_MAX; imp++) {
    const score = lh * imp;
    const zone = ZONE_LEGEND.find((z) => score <= z.maxScore) ?? ZONE_LEGEND[ZONE_LEGEND.length - 1];
    const zInt = parseInt(zone.color.slice(1), 16);
    const zR = (zInt >> 16) & 255;
    const zG = (zInt >> 8) & 255;
    const zB = zInt & 255;
    const effR = bgR * (1 - CELL_FILL_OPACITY) + zR * CELL_FILL_OPACITY;
    const effG = bgG * (1 - CELL_FILL_OPACITY) + zG * CELL_FILL_OPACITY;
    const effB = bgB * (1 - CELL_FILL_OPACITY) + zB * CELL_FILL_OPACITY;
    const lum = (0.2126 * effR + 0.7152 * effG + 0.0722 * effB) / 255;
    const scoreTextFill = lum > 0.52 ? DARK_INK : LIGHT_INK;
    gridCells.push({ lh, imp, score, color: zone.color, scoreTextFill });
  }
}

const cellCounts = new Map<string, number>();
for (const r of data) {
  const k = `${r[LIKELIHOOD]}-${r[IMPACT]}`;
  cellCounts.set(k, (cellCounts.get(k) ?? 0) + 1);
}

const cellSeen = new Map<string, number>();
const risksPlaced = data.map((r, id) => {
  const lh = r[LIKELIHOOD];
  const imp = r[IMPACT];
  const k = `${lh}-${imp}`;
  const idx = cellSeen.get(k) ?? 0;
  cellSeen.set(k, idx + 1);
  const siblings = cellCounts.get(k)!;
  if (siblings === 1) {
    return {
      id,
      name: r[RISK_NAME],
      lh,
      imp,
      jx: imp,
      jy: lh,
      labelBelow: false,
    };
  }
  const angle = (2 * Math.PI * idx) / siblings - Math.PI / 2;
  return {
    id,
    name: r[RISK_NAME],
    lh,
    imp,
    jx: imp + 0.14 * Math.sin(angle),
    jy: lh - 0.18 * Math.cos(angle),
    labelBelow: idx % 2 === 1,
  };
});

const scatterData = risksPlaced.map((r) => ({ id: r.id, x: r.jx, y: r.jy }));

const zoneCountMap = new Map<string, number>();
for (const z of ZONE_LEGEND) zoneCountMap.set(z.name, 0);
for (const r of data) {
  const score = r[LIKELIHOOD] * r[IMPACT];
  const zone = ZONE_LEGEND.find((z) => score <= z.maxScore) ?? ZONE_LEGEND[ZONE_LEGEND.length - 1];
  zoneCountMap.set(zone.name, (zoneCountMap.get(zone.name) ?? 0) + 1);
}
const topTwoSummary = ZONE_LEGEND.slice(-2)
  .reverse()
  .map((z) => `${zoneCountMap.get(z.name)} ${z.name}`)
  .join(", ");

const SUBTITLE = `${data.length} ${RISK_NAME}s across ${gridCount}×${gridCount} ${LIKELIHOOD} × ${IMPACT} matrix (${topTwoSummary})`;

function RiskMatrixLayer() {
  const { left, top, width, height } = useDrawingArea();
  const cW = width / gridCount;
  const cH = height / gridCount;
  const legendY = top + height + 104;
  const colW = width / ZONE_LEGEND.length;

  return (
    <g>
      <text
        x={W / 2}
        y={42}
        textAnchor="middle"
        fontSize={22}
        fontWeight="600"
        fill={t.ink}
        fontFamily={FONT}
      >
        {TITLE}
      </text>
      <text
        x={W / 2}
        y={70}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        {SUBTITLE}
      </text>

      {gridCells.map((cell) => {
        const cx = left + (cell.imp - RATING_MIN) * cW;
        const cy = top + (RATING_MAX - cell.lh) * cH;
        return (
          <g key={`cell-${cell.lh}-${cell.imp}`}>
            <rect
              x={cx}
              y={cy}
              width={cW}
              height={cH}
              fill={cell.color}
              fillOpacity={CELL_FILL_OPACITY}
              stroke={t.ink}
              strokeOpacity={0.24}
              strokeWidth={1.5}
            />
            <text
              x={cx + cW - 10}
              y={cy + cH - 10}
              textAnchor="end"
              fontSize={14}
              fontWeight="600"
              fill={cell.scoreTextFill}
              fontFamily={FONT}
            >
              {cell.score}
            </text>
          </g>
        );
      })}

      {ZONE_LEGEND.map((z, i) => {
        const lx = left + colW * i + colW / 2 - 72;
        return (
          <g key={z.label}>
            <rect
              x={lx}
              y={legendY - 10}
              width={20}
              height={20}
              fill={z.color}
              fillOpacity={CELL_FILL_OPACITY}
              stroke={t.ink}
              strokeOpacity={0.25}
              rx={3}
            />
            <text
              x={lx + 28}
              y={legendY + 1}
              dominantBaseline="central"
              fontSize={14}
              fontWeight="600"
              fill={t.ink}
              fontFamily={FONT}
            >
              {z.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function RiskLabelsLayer() {
  const { left, top, width, height } = useDrawingArea();

  return (
    <g>
      {risksPlaced.map((r) => {
        const sx = left + ((r.jx - axisMin) / gridCount) * width;
        const sy = top + ((axisMax - r.jy) / gridCount) * height;
        const labelY = r.labelBelow ? sy + 26 : sy - 20;
        const pillW = r.name.length * 8.2 + 14;
        const pillH = 22;
        return (
          <g key={`risk-${r.id}`}>
            <rect
              x={sx - pillW / 2}
              y={labelY - pillH / 2 - 4}
              width={pillW}
              height={pillH}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.92}
              stroke={t.grid}
              strokeWidth={1}
            />
            <text
              x={sx}
              y={labelY}
              textAnchor="middle"
              fontSize={14}
              fontWeight="600"
              fill={t.ink}
              fontFamily={FONT}
            >
              {r.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  return (
    <ChartsContainer
      width={W}
      height={H}
      margin={{ left: 32, top: 96, right: 44, bottom: 84 }}
      series={[
        {
          type: "scatter",
          id: "risks",
          data: scatterData,
          color: t.ink,
          markerSize: 9,
        },
      ]}
      xAxis={[
        {
          id: "impact-axis",
          min: axisMin,
          max: axisMax,
          tickInterval: tickRatings,
          height: 62,
          label: IMPACT,
          valueFormatter: (v: number) => IMPACT_LABELS[Math.round(v) - RATING_MIN] ?? "",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          labelStyle: {
            fontSize: 15,
            fontWeight: 600,
            fill: t.ink,
            fontFamily: FONT,
          },
        },
      ]}
      yAxis={[
        {
          id: "likelihood-axis",
          min: axisMin,
          max: axisMax,
          tickInterval: tickRatings,
          width: 158,
          label: LIKELIHOOD,
          valueFormatter: (v: number) =>
            LIKELIHOOD_LABELS[Math.round(v) - RATING_MIN] ?? "",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          labelStyle: {
            fontSize: 15,
            fontWeight: 600,
            fill: t.ink,
            fontFamily: FONT,
          },
        },
      ]}
      skipAnimation
    >
      <RiskMatrixLayer />
      <ScatterPlot />
      <RiskLabelsLayer />
      <ChartsXAxis axisId="impact-axis" />
      <ChartsYAxis axisId="likelihood-axis" />
    </ChartsContainer>
  );
}
