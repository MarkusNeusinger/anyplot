// anyplot.ai
// heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
// Library: muix 9.2.1 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-20
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;
const FONT = "system-ui, -apple-system, sans-serif";

// Constants
const RISK_NAME_COL = "risk_name";
const LIKELIHOOD_COL = "likelihood";
const IMPACT_COL = "impact";

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
  { label: "Low (1–4)", maxScore: 4, color: "#009E73" },
  { label: "Medium (5–9)", maxScore: 9, color: "#DDCC77" },
  { label: "High (10–16)", maxScore: 16, color: "#BD8233" },
  { label: "Critical (20–25)", maxScore: 25, color: "#AE3030" },
];

// Data
const DATA = [
  { [RISK_NAME_COL]: "Data Breach", [LIKELIHOOD_COL]: 3, [IMPACT_COL]: 5 },
  { [RISK_NAME_COL]: "Ransomware", [LIKELIHOOD_COL]: 4, [IMPACT_COL]: 5 },
  { [RISK_NAME_COL]: "DDoS Attack", [LIKELIHOOD_COL]: 4, [IMPACT_COL]: 3 },
  { [RISK_NAME_COL]: "Supply Chain", [LIKELIHOOD_COL]: 2, [IMPACT_COL]: 4 },
  { [RISK_NAME_COL]: "Insider Threat", [LIKELIHOOD_COL]: 2, [IMPACT_COL]: 5 },
  { [RISK_NAME_COL]: "API Failure", [LIKELIHOOD_COL]: 3, [IMPACT_COL]: 3 },
  { [RISK_NAME_COL]: "Key Staff Loss", [LIKELIHOOD_COL]: 3, [IMPACT_COL]: 4 },
  { [RISK_NAME_COL]: "Budget Cut", [LIKELIHOOD_COL]: 4, [IMPACT_COL]: 2 },
  { [RISK_NAME_COL]: "Compliance", [LIKELIHOOD_COL]: 2, [IMPACT_COL]: 3 },
  { [RISK_NAME_COL]: "Cloud Outage", [LIKELIHOOD_COL]: 2, [IMPACT_COL]: 4 },
  { [RISK_NAME_COL]: "Phishing", [LIKELIHOOD_COL]: 5, [IMPACT_COL]: 2 },
  { [RISK_NAME_COL]: "HW Failure", [LIKELIHOOD_COL]: 1, [IMPACT_COL]: 3 },
];

const ratings = Array.from(
  new Set([
    ...DATA.map((r) => r[LIKELIHOOD_COL]),
    ...DATA.map((r) => r[IMPACT_COL]),
  ]),
).sort((a, b) => a - b);
const minRating = Math.min(...ratings);
const maxRating = Math.max(...ratings);
const gridCount = maxRating - minRating + 1;
const axisMin = minRating - 0.5;
const axisMax = maxRating + 0.5;
const tickRatings = Array.from({ length: gridCount }, (_, i) => minRating + i);

const gridCells: Array<{
  lh: number;
  imp: number;
  score: number;
  color: string;
}> = [];

for (let lh = minRating; lh <= maxRating; lh++) {
  for (let imp = minRating; imp <= maxRating; imp++) {
    const score = lh * imp;
    let color = ZONE_LEGEND[ZONE_LEGEND.length - 1].color;
    for (const z of ZONE_LEGEND) {
      if (score <= z.maxScore) {
        color = z.color;
        break;
      }
    }
    gridCells.push({ lh, imp, score, color });
  }
}

const cellCounts = new Map<string, number>();
for (const r of DATA) {
  const k = `${r[LIKELIHOOD_COL]}-${r[IMPACT_COL]}`;
  cellCounts.set(k, (cellCounts.get(k) ?? 0) + 1);
}

const cellSeen = new Map<string, number>();
const risksPlaced = DATA.map((r, id) => {
  const lh = r[LIKELIHOOD_COL];
  const imp = r[IMPACT_COL];
  const k = `${lh}-${imp}`;
  const idx = cellSeen.get(k) ?? 0;
  cellSeen.set(k, idx + 1);
  const siblings = cellCounts.get(k) ?? 1;
  if (siblings === 1) {
    return {
      id,
      name: r[RISK_NAME_COL],
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
    name: r[RISK_NAME_COL],
    lh,
    imp,
    jx: imp + 0.14 * Math.sin(angle),
    jy: lh - 0.18 * Math.cos(angle),
    labelBelow: idx % 2 === 1,
  };
});

const scatterData = risksPlaced.map((r) => ({ id: r.id, x: r.jx, y: r.jy }));
const criticalCount = DATA.filter(
  (r) => r[LIKELIHOOD_COL] * r[IMPACT_COL] >= 20,
).length;
const highCount = DATA.filter((r) => {
  const s = r[LIKELIHOOD_COL] * r[IMPACT_COL];
  return s >= 10 && s <= 16;
}).length;

const TITLE = "heatmap-risk-matrix · javascript · muix · anyplot.ai";
const SUBTITLE = `${DATA.length} assessed risks across ${gridCount}×${gridCount} likelihood × impact matrix (${criticalCount} Critical, ${highCount} High)`;

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
        const cx = left + (cell.imp - minRating) * cW;
        const cy = top + (maxRating - cell.lh) * cH;
        return (
          <g key={`cell-${cell.lh}-${cell.imp}`}>
            <rect
              x={cx}
              y={cy}
              width={cW}
              height={cH}
              fill={cell.color}
              fillOpacity={0.42}
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
              fill={t.ink}
              fillOpacity={0.55}
              fontFamily={FONT}
            >
              {cell.score}
            </text>
          </g>
        );
      })}

      {risksPlaced.map((r) => {
        const sx = left + ((r.jx - axisMin) / gridCount) * width;
        const sy = top + ((axisMax - r.jy) / gridCount) * height;
        const labelY = r.labelBelow ? sy + 24 : sy - 18;
        const pillW = r.name.length * 8.2 + 14;
        const pillH = 22;
        return (
          <g key={`risk-${r.id}`}>
            <circle
              cx={sx}
              cy={sy}
              r={9}
              fill={t.elevatedBg}
              stroke={t.ink}
              strokeWidth={2.5}
            />
            <rect
              x={sx - pillW / 2}
              y={labelY - pillH / 2 - 4}
              width={pillW}
              height={pillH}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.88}
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
              fillOpacity={0.7}
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
          markerSize: 8,
        },
      ]}
      xAxis={[
        {
          id: "impact-axis",
          min: axisMin,
          max: axisMax,
          tickInterval: tickRatings,
          height: 62,
          label: "Consequence Impact",
          valueFormatter: (v: number) => IMPACT_LABELS[Math.round(v) - 1] ?? "",
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
          label: "Likelihood",
          valueFormatter: (v: number) =>
            LIKELIHOOD_LABELS[Math.round(v) - 1] ?? "",
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
      <ScatterPlot />
      <RiskMatrixLayer />
      <ChartsXAxis axisId="impact-axis" />
      <ChartsYAxis axisId="likelihood-axis" />
    </ChartsContainer>
  );
}
