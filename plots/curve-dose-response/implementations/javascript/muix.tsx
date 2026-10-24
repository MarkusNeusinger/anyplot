// anyplot.ai
// curve-dose-response: Pharmacological Dose-Response Curve
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-24

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Constants
const TITLE = "curve-dose-response · javascript · muix · anyplot.ai";
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const CURVE_SAMPLES = 90;
const LOG_PAD_SHARE = 0.09;
const Y_PAD_SHARE = 0.12;
const ERROR_CAP = 7;

const SUPERSCRIPT: Record<string, string> = {
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
  "-": "⁻",
};

const SI_PREFIXES = [
  { exp: -12, prefix: "p" },
  { exp: -9, prefix: "n" },
  { exp: -6, prefix: "µ" },
  { exp: -3, prefix: "m" },
  { exp: 0, prefix: "" },
];

const T_CRIT_95: Record<number, number> = {
  1: 12.706,
  2: 4.303,
  3: 3.182,
  4: 2.776,
  5: 2.571,
  6: 2.447,
  7: 2.365,
  8: 2.306,
  9: 2.262,
  10: 2.228,
  12: 2.179,
  15: 2.131,
  20: 2.086,
  30: 2.042,
};

// Columns: set these to your data's column names
const COMPOUND = "Compound"; // role: compound
const CONCENTRATION = "Concentration (M)"; // role: concentration
const RESPONSE = "Response (%)"; // role: response
const RESPONSE_SEM = "Response SEM (%)"; // role: response_sem

// Data: replace this block with your own records
const data = [
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-9, [RESPONSE]: 2.8, [RESPONSE_SEM]: 2.6 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 3.16e-9, [RESPONSE]: 4.1, [RESPONSE_SEM]: 3.1 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-8, [RESPONSE]: 5.6, [RESPONSE_SEM]: 3.4 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 3.16e-8, [RESPONSE]: 18.2, [RESPONSE_SEM]: 4.2 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-7, [RESPONSE]: 50.4, [RESPONSE_SEM]: 4.8 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 3.16e-7, [RESPONSE]: 82.1, [RESPONSE_SEM]: 4.1 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-6, [RESPONSE]: 94.3, [RESPONSE_SEM]: 3.3 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 3.16e-6, [RESPONSE]: 97.1, [RESPONSE_SEM]: 2.9 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-5, [RESPONSE]: 97.8, [RESPONSE_SEM]: 2.7 },
  { [COMPOUND]: "Osimertinib", [CONCENTRATION]: 1e-4, [RESPONSE]: 98.1, [RESPONSE_SEM]: 2.5 },

  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-9, [RESPONSE]: 5.2, [RESPONSE_SEM]: 2.8 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 3.16e-9, [RESPONSE]: 6.1, [RESPONSE_SEM]: 3.0 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-8, [RESPONSE]: 7.4, [RESPONSE_SEM]: 3.2 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 3.16e-8, [RESPONSE]: 9.8, [RESPONSE_SEM]: 3.6 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-7, [RESPONSE]: 16.5, [RESPONSE_SEM]: 4.1 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 3.16e-7, [RESPONSE]: 30.8, [RESPONSE_SEM]: 4.7 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-6, [RESPONSE]: 49.2, [RESPONSE_SEM]: 5.1 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 3.16e-6, [RESPONSE]: 68.4, [RESPONSE_SEM]: 4.4 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-5, [RESPONSE]: 79.1, [RESPONSE_SEM]: 3.7 },
  { [COMPOUND]: "Gefitinib", [CONCENTRATION]: 1e-4, [RESPONSE]: 84.6, [RESPONSE_SEM]: 3.1 },
];

// Plot: reads only data and the constants above
const COMPOUND_NAMES = Array.from(new Set(data.map((d) => String(d[COMPOUND]))));
const allConcs = data.map((d) => Number(d[CONCENTRATION]));
const allResp = data.map((d) => Number(d[RESPONSE]));
const allSem = data.map((d) => Number(d[RESPONSE_SEM]));

const rawLogMin = Math.log10(Math.min(...allConcs));
const rawLogMax = Math.log10(Math.max(...allConcs));
const logSpan = rawLogMax - rawLogMin;
const logMin = rawLogMin - logSpan * LOG_PAD_SHARE;
const logMax = rawLogMax + logSpan * LOG_PAD_SHARE;
const xMin = Math.pow(10, logMin);
const xMax = Math.pow(10, logMax);

const rawYMin = Math.min(...allResp.map((v, i) => v - allSem[i]));
const rawYMax = Math.max(...allResp.map((v, i) => v + allSem[i]));
const ySpan = rawYMax - rawYMin;
const yMin = rawYMin - ySpan * Y_PAD_SHARE;
const yMax = rawYMax + ySpan * Y_PAD_SHARE;

const CONC_UNIT = CONCENTRATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const RESP_UNIT = RESPONSE.match(/\(([^)]+)\)/)?.[1] ?? "";

const tickPowers: number[] = [];
for (let p = Math.ceil(logMin); p <= Math.floor(logMax); p++) {
  tickPowers.push(Math.pow(10, p));
}

const curveXs = Array.from({ length: CURVE_SAMPLES }, (_, i) =>
  Math.pow(10, logMin + (i / (CURVE_SAMPLES - 1)) * (logMax - logMin)),
);

const GROUPS = COMPOUND_NAMES.map((name, idx) => {
  const rows = data
    .filter((d) => String(d[COMPOUND]) === name)
    .map((d, i) => ({
      id: `${name}-${i}`,
      x: Number(d[CONCENTRATION]),
      y: Number(d[RESPONSE]),
      sem: Number(d[RESPONSE_SEM]),
    }))
    .sort((a, b) => a.x - b.x);

  const color = t.palette[idx];

  let bottom = rows[0].y;
  let top = rows[rows.length - 1].y;
  const initHalf = (bottom + top) / 2;
  let logEc50 = (rawLogMin + rawLogMax) / 2;
  for (let i = 0; i < rows.length - 1; i++) {
    if ((rows[i].y - initHalf) * (rows[i + 1].y - initHalf) <= 0) {
      const denom = rows[i + 1].y - rows[i].y;
      const frac = (initHalf - rows[i].y) / denom;
      logEc50 =
        Math.log10(rows[i].x) + frac * (Math.log10(rows[i + 1].x) - Math.log10(rows[i].x));
      break;
    }
  }
  let hill = 1.4;

  const steps = [0.25, 0.08, 0.02, 0.005];
  for (const step of steps) {
    for (let iter = 0; iter < 15; iter++) {
      for (let paramIdx = 0; paramIdx < 4; paramIdx++) {
        const delta = paramIdx < 2 ? step * 4 : step;
        let bestVal = [bottom, top, logEc50, hill][paramIdx];
        let bestSse = Infinity;
        for (const mult of [-1, 0, 1]) {
          const cand = [bottom, top, logEc50, hill];
          cand[paramIdx] += mult * delta;
          const [bC, tC, lC, hC] = cand;
          const ecC = Math.pow(10, lC);
          let sse = 0;
          for (const r of rows) {
            const pred = bC + (tC - bC) / (1 + Math.pow(ecC / r.x, hC));
            sse += (r.y - pred) ** 2;
          }
          if (sse < bestSse) {
            bestSse = sse;
            bestVal = cand[paramIdx];
          }
        }
        if (paramIdx === 0) bottom = bestVal;
        if (paramIdx === 1) top = bestVal;
        if (paramIdx === 2) logEc50 = bestVal;
        if (paramIdx === 3) hill = bestVal;
      }
    }
  }

  const ec50 = Math.pow(10, logEc50);
  const halfMax = (bottom + top) / 2;
  const curveY = curveXs.map((c) => bottom + (top - bottom) / (1 + Math.pow(ec50 / c, hill)));

  // Residual variance s² = SSE / (n - 4) + numeric Jacobian covariance (J^T J)^-1 s²
  let finalSse = 0;
  for (const r of rows) {
    const pred = bottom + (top - bottom) / (1 + Math.pow(ec50 / r.x, hill));
    finalSse += (r.y - pred) ** 2;
  }
  const df = rows.length - 4;
  const s2 = finalSse / df;
  const tCrit = T_CRIT_95[df];

  const eps = [1e-4, 1e-4, 1e-5, 1e-4];
  const jtj = Array.from({ length: 4 }, () => [0, 0, 0, 0]);
  for (let k = 0; k < 4; k++) jtj[k][k] = 1e-8;
  for (const r of rows) {
    const gRow = [0, 0, 0, 0];
    for (let k = 0; k < 4; k++) {
      const pPlus = [bottom, top, logEc50, hill];
      const pMinus = [bottom, top, logEc50, hill];
      pPlus[k] += eps[k];
      pMinus[k] -= eps[k];
      const fPlus =
        pPlus[0] + (pPlus[1] - pPlus[0]) / (1 + Math.pow(Math.pow(10, pPlus[2]) / r.x, pPlus[3]));
      const fMinus =
        pMinus[0] +
        (pMinus[1] - pMinus[0]) / (1 + Math.pow(Math.pow(10, pMinus[2]) / r.x, pMinus[3]));
      gRow[k] = (fPlus - fMinus) / (2 * eps[k]);
    }
    for (let a = 0; a < 4; a++) {
      for (let b = 0; b < 4; b++) {
        jtj[a][b] += gRow[a] * gRow[b];
      }
    }
  }

  // Invert 4x4 jtj via Gauss-Jordan
  const aug = jtj.map((row, rIdx) => [
    ...row,
    rIdx === 0 ? 1 : 0,
    rIdx === 1 ? 1 : 0,
    rIdx === 2 ? 1 : 0,
    rIdx === 3 ? 1 : 0,
  ]);
  for (let col = 0; col < 4; col++) {
    let piv = col;
    for (let rIdx = col + 1; rIdx < 4; rIdx++) {
      if (Math.abs(aug[rIdx][col]) > Math.abs(aug[piv][col])) piv = rIdx;
    }
    const tmp = aug[col];
    aug[col] = aug[piv];
    aug[piv] = tmp;
    const div = aug[col][col];
    for (let j = 0; j < 8; j++) aug[col][j] /= div;
    for (let rIdx = 0; rIdx < 4; rIdx++) {
      if (rIdx === col) continue;
      const factor = aug[rIdx][col];
      for (let j = 0; j < 8; j++) aug[rIdx][j] -= factor * aug[col][j];
    }
  }
  const jtjInv = aug.map((row) => row.slice(4, 8));

  const ciUpper: number[] = [];
  const ciLower: number[] = [];
  for (let i = 0; i < curveXs.length; i++) {
    const cx = curveXs[i];
    const gVec = [0, 0, 0, 0];
    for (let k = 0; k < 4; k++) {
      const pPlus = [bottom, top, logEc50, hill];
      const pMinus = [bottom, top, logEc50, hill];
      pPlus[k] += eps[k];
      pMinus[k] -= eps[k];
      const fPlus =
        pPlus[0] + (pPlus[1] - pPlus[0]) / (1 + Math.pow(Math.pow(10, pPlus[2]) / cx, pPlus[3]));
      const fMinus =
        pMinus[0] +
        (pMinus[1] - pMinus[0]) / (1 + Math.pow(Math.pow(10, pMinus[2]) / cx, pMinus[3]));
      gVec[k] = (fPlus - fMinus) / (2 * eps[k]);
    }
    let varPred = 0;
    for (let a = 0; a < 4; a++) {
      for (let b = 0; b < 4; b++) {
        varPred += gVec[a] * jtjInv[a][b] * gVec[b];
      }
    }
    const se = Math.sqrt(Math.max(0, varPred * s2));
    const halfBand = tCrit * se;
    ciUpper.push(curveY[i] + halfBand);
    ciLower.push(curveY[i] - halfBand);
  }

  let bestPrefix = SI_PREFIXES[0];
  for (const entry of SI_PREFIXES) {
    if (Math.log10(ec50) >= entry.exp) {
      bestPrefix = entry;
    }
  }
  const scaledEc50 = Number((ec50 / Math.pow(10, bestPrefix.exp)).toPrecision(3));
  const ec50Label = `${name} (EC₅₀ = ${scaledEc50} ${bestPrefix.prefix}${CONC_UNIT})`;

  return {
    name,
    color,
    rows,
    bottom,
    top,
    ec50,
    hill,
    halfMax,
    ec50Label,
    curveY,
    ciUpper,
    ciLower,
  };
});

const SUBTITLE = `4PL sigmoid fit across ${GROUPS.length} ${COMPOUND}s · ${RESPONSE} ± ${RESPONSE_SEM} with pointwise 95% CI bands and EC₅₀ drop-lines`;

const scatterSeries = GROUPS.map((g) => ({
  type: "scatter" as const,
  id: `scatter-${g.name}`,
  label: g.ec50Label,
  data: g.rows,
  color: g.color,
  markerSize: 7,
  xAxisId: "concentration",
  yAxisId: "response",
}));

function DoseResponseOverlay() {
  const xScale = useXScale("concentration") as any;
  const yScale = useYScale("response") as any;
  const { left, width: areaW, top, height: areaH } = useDrawingArea();

  const yBottomAxis = top + areaH;

  return (
    <g fontFamily={FONT}>
      {/* Pointwise 95% CI bands */}
      {GROUPS.map((g) => {
        const upper = curveXs.map((x, i) => [xScale(x), yScale(g.ciUpper[i])]);
        const lower = curveXs.map((x, i) => [xScale(x), yScale(g.ciLower[i])]);
        const pts = [...upper, ...lower.slice().reverse()];
        const d =
          pts
            .map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`)
            .join(" ") + " Z";
        return <path key={`ci-${g.name}`} d={d} fill={g.color} fillOpacity={0.18} stroke="none" />;
      })}

      {/* Top and bottom plateau asymptote dashed lines */}
      {GROUPS.map((g, idx) => {
        const yTop = yScale(g.top);
        const yBot = yScale(g.bottom);
        const labelX = left + 12 + idx * 145;
        return (
          <g key={`asym-${g.name}`}>
            <line
              x1={left}
              y1={yTop}
              x2={left + areaW}
              y2={yTop}
              stroke={g.color}
              strokeDasharray="4,5"
              strokeWidth={1.3}
              strokeOpacity={0.55}
            />
            <text
              x={labelX}
              y={yTop - 6}
              fontSize={14}
              fontWeight={500}
              fill={g.color}
            >
              {`Top ${Math.round(g.top)}${RESP_UNIT}`}
            </text>
            <line
              x1={left}
              y1={yBot}
              x2={left + areaW}
              y2={yBot}
              stroke={g.color}
              strokeDasharray="4,5"
              strokeWidth={1.3}
              strokeOpacity={0.55}
            />
            <text
              x={left + areaW - 12 - (GROUPS.length - 1 - idx) * 120}
              y={idx === 0 ? yBot + 18 : yBot - 6}
              textAnchor="end"
              fontSize={14}
              fontWeight={500}
              fill={g.color}
            >
              {`Bottom ${Math.round(g.bottom)}${RESP_UNIT}`}
            </text>
          </g>
        );
      })}

      {/* EC50 horizontal & vertical drop-lines intersecting at (ec50, halfMax) */}
      {GROUPS.map((g, idx) => {
        const cx = xScale(g.ec50);
        const cy = yScale(g.halfMax);
        const badgeX = idx === 0 ? cx - 108 : cx + 10;
        const badgeY = idx === 0 ? cy - 30 : cy + 10;
        return (
          <g key={`ec50-${g.name}`}>
            <line
              x1={left}
              y1={cy}
              x2={cx}
              y2={cy}
              stroke={g.color}
              strokeDasharray="6,4"
              strokeWidth={1.6}
              strokeOpacity={0.85}
            />
            <line
              x1={cx}
              y1={cy}
              x2={cx}
              y2={yBottomAxis}
              stroke={g.color}
              strokeDasharray="6,4"
              strokeWidth={1.6}
              strokeOpacity={0.85}
            />
            <circle cx={cx} cy={cy} r={5} fill={t.pageBg} stroke={g.color} strokeWidth={2.5} />
            <rect
              x={badgeX}
              y={badgeY}
              width={98}
              height={22}
              rx={4}
              fill={t.pageBg}
              opacity={0.92}
            />
            <text
              x={badgeX + 6}
              y={badgeY + 16}
              fontSize={14}
              fontWeight={600}
              fill={g.color}
            >
              {`EC₅₀ (${Math.round(g.halfMax)}${RESP_UNIT})`}
            </text>
          </g>
        );
      })}

      {/* Smooth 4PL fitted sigmoid curves */}
      {GROUPS.map((g) => {
        const d = curveXs
          .map((x, i) => {
            const px = xScale(x).toFixed(1);
            const py = yScale(g.curveY[i]).toFixed(1);
            return `${i === 0 ? "M" : "L"}${px},${py}`;
          })
          .join(" ");
        return (
          <path
            key={`curve-${g.name}`}
            d={d}
            fill="none"
            stroke={g.color}
            strokeWidth={3}
            strokeLinecap="round"
          />
        );
      })}

      {/* SEM error bars */}
      {GROUPS.map((g) =>
        g.rows.map((r) => {
          const cx = xScale(r.x);
          const ytop = yScale(r.y + r.sem);
          const ybot = yScale(r.y - r.sem);
          return (
            <g key={`err-${r.id}`}>
              <line x1={cx} y1={ytop} x2={cx} y2={ybot} stroke={g.color} strokeWidth={2.2} />
              <line
                x1={cx - ERROR_CAP}
                y1={ytop}
                x2={cx + ERROR_CAP}
                y2={ytop}
                stroke={g.color}
                strokeWidth={2.2}
              />
              <line
                x1={cx - ERROR_CAP}
                y1={ybot}
                x2={cx + ERROR_CAP}
                y2={ybot}
                stroke={g.color}
                strokeWidth={2.2}
              />
            </g>
          );
        }),
      )}
    </g>
  );
}

export default function Chart() {
  const chartW = width - 48;
  const chartH = height - 150;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: "18px",
        px: "24px",
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 700,
          color: t.ink,
          fontFamily: FONT,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        {TITLE}
      </Typography>
      <Typography
        sx={{
          fontSize: 15,
          color: t.inkSoft,
          fontFamily: FONT,
          textAlign: "center",
          mt: "4px",
          mb: "4px",
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
        width={chartW}
        height={chartH}
        skipAnimation
        margin={{ top: 20, right: 36, bottom: 16, left: 20 }}
        series={scatterSeries}
        xAxis={[
          {
            id: "concentration",
            scaleType: "log",
            min: xMin,
            max: xMax,
            height: 60,
            label: CONCENTRATION,
            tickInterval: tickPowers,
            valueFormatter: (v: number) => {
              const exp = String(Math.round(Math.log10(v)))
                .split("")
                .map((c) => SUPERSCRIPT[c] || c)
                .join("");
              return `10${exp}`;
            },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "response",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 80,
            label: RESPONSE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fill: t.ink, fontFamily: FONT },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeDasharray: "4 4" },
        }}
      >
        <ChartsGrid horizontal />
        <DoseResponseOverlay />
        <ScatterPlot skipAnimation />
        <ChartsXAxis axisId="concentration" />
        <ChartsYAxis axisId="response" />
      </ChartsContainer>

      <Box
        sx={{
          display: "flex",
          gap: "28px",
          alignItems: "center",
          justifyContent: "center",
          mt: "4px",
        }}
      >
        {GROUPS.map((g) => (
          <Box key={g.name} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width={28} height={16}>
              <rect x={2} y={2} width={24} height={12} fill={g.color} fillOpacity={0.22} rx={2} />
              <line x1={2} y1={8} x2={26} y2={8} stroke={g.color} strokeWidth={3} strokeLinecap="round" />
              <circle cx={14} cy={8} r={4.5} fill={g.color} />
            </svg>
            <Typography sx={{ fontSize: 14, color: t.ink, fontFamily: FONT }}>
              {`${g.ec50Label} · 95% CI`}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
