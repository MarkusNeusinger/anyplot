// anyplot.ai
// frontier-efficient: Efficient Frontier for Portfolio Optimization
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "frontier-efficient · javascript · muix · anyplot.ai";
const FRONTIER_LABEL = "Efficient Frontier";
const CML_LABEL = "Capital Market Line";
const GMV_LABEL = "Min-Variance Portfolio";
const TAN_LABEL = "Max-Sharpe (Tangency) Portfolio";
const RF_LABEL = "Risk-free rate";
const SHARPE_LOW_LABEL = "Low Sharpe ratio";
const SHARPE_HIGH_LABEL = "High Sharpe ratio";
const CML_DASH = "10,6";

const RF_RATE = 0.02;
const FRONTIER_R_MAX_MULT = 1.18;
const FRONTIER_STEPS = 80;
const X_MAX_PAD_MULT = 1.08;
const Y_MIN_PAD_SHARE = 0.14;
const Y_MAX_PAD_MULT = 1.05;

// Columns: set these to your data's column names
const PORTFOLIO_ID = "Portfolio";
const RISK = "Portfolio Risk — Annualized Standard Deviation (%)"; // role: risk
const RETURN = "Expected Portfolio Return — Annualized (%)"; // role: return

// Data: replace this block with your own records
const N_PORTFOLIOS = 300;
const ASSET_RETURNS = [0.095, 0.075, 0.11, 0.035, 0.085, 0.045];
const ASSET_VOLS = [0.16, 0.18, 0.24, 0.055, 0.19, 0.15];
const ASSET_CORR_ROWS = [
  "1.00,0.82,0.72,-0.08,0.58,0.02",
  "0.82,1.00,0.78,-0.04,0.52,0.08",
  "0.72,0.78,1.00,-0.12,0.48,0.12",
  "-0.08,-0.04,-0.12,1.00,0.10,0.18",
  "0.58,0.52,0.48,0.10,1.00,0.06",
  "0.02,0.08,0.12,0.18,0.06,1.00",
];

const nAssets = ASSET_RETURNS.length;
const covMatrix = ASSET_CORR_ROWS.map((rowStr, i) =>
  rowStr.split(",").map((cStr, j) => Number(cStr) * ASSET_VOLS[i] * ASSET_VOLS[j]),
);

let lcgSeed = 7;
const data: Record<string, string | number>[] = [];

for (let k = 0; k < N_PORTFOLIOS; k++) {
  const expSamples: number[] = [];
  let weightSum = 0;
  for (let i = 0; i < nAssets; i++) {
    lcgSeed = (Math.imul(1664525, lcgSeed) + 1013904223) >>> 0;
    const u = lcgSeed / 4294967296;
    const e = -Math.log(1 - u);
    expSamples.push(e);
    weightSum += e;
  }
  const weights = expSamples.map((e) => e / weightSum);
  let portRet = 0;
  let portVar = 0;
  for (let i = 0; i < nAssets; i++) {
    portRet += weights[i] * ASSET_RETURNS[i];
    for (let j = 0; j < nAssets; j++) {
      portVar += weights[i] * covMatrix[i][j] * weights[j];
    }
  }
  const portRisk = Math.sqrt(Math.max(0, portVar));
  data.push({
    [PORTFOLIO_ID]: `p${k}`,
    [RISK]: portRisk,
    [RETURN]: portRet,
  });
}

// Plot: reads only data and the constants above
const augMatrix = covMatrix.map((row, i) => [
  ...row,
  ...Array.from({ length: nAssets }, (_, j) => (i === j ? 1 : 0)),
]);

for (let col = 0; col < nAssets; col++) {
  let pivotRow = col;
  let maxVal = Math.abs(augMatrix[col][col]);
  for (let r = col + 1; r < nAssets; r++) {
    if (Math.abs(augMatrix[r][col]) > maxVal) {
      maxVal = Math.abs(augMatrix[r][col]);
      pivotRow = r;
    }
  }
  const tmpRow = augMatrix[col];
  augMatrix[col] = augMatrix[pivotRow];
  augMatrix[pivotRow] = tmpRow;

  const pivot = augMatrix[col][col];
  for (let j = 0; j < 2 * nAssets; j++) {
    augMatrix[col][j] /= pivot;
  }
  for (let r = 0; r < nAssets; r++) {
    if (r === col) continue;
    const factor = augMatrix[r][col];
    for (let j = 0; j < 2 * nAssets; j++) {
      augMatrix[r][j] -= factor * augMatrix[col][j];
    }
  }
}

const covInv = augMatrix.map((row) => row.slice(nAssets));
const invOnes = covInv.map((row) => row.reduce((s, v) => s + v, 0));
const invMu = covInv.map((row) => row.reduce((s, v, j) => s + v * ASSET_RETURNS[j], 0));

const scalarA = invOnes.reduce((s, v) => s + v, 0);
const scalarB = invMu.reduce((s, v) => s + v, 0);
const scalarC = ASSET_RETURNS.reduce((s, mu_i, i) => s + mu_i * invMu[i], 0);
const scalarD = scalarA * scalarC - scalarB * scalarB;

const rGmv = scalarB / scalarA;
const riskGmv = Math.sqrt(1 / scalarA);

const excessReturns = ASSET_RETURNS.map((m) => m - RF_RATE);
const zTan = covInv.map((row) => row.reduce((s, v, j) => s + v * excessReturns[j], 0));
const sumZTan = zTan.reduce((a, b) => a + b, 0);
const wTan = zTan.map((z) => z / sumZTan);
const rTan = wTan.reduce((s, w, i) => s + w * ASSET_RETURNS[i], 0);
let varTan = 0;
for (let i = 0; i < nAssets; i++) {
  for (let j = 0; j < nAssets; j++) {
    varTan += wTan[i] * covMatrix[i][j] * wTan[j];
  }
}
const riskTan = Math.sqrt(Math.max(0, varTan));
const sharpeTan = (rTan - RF_RATE) / riskTan;

const rFrontierMax = Math.max(...ASSET_RETURNS) * FRONTIER_R_MAX_MULT;
const frontierReturns = Array.from(
  { length: FRONTIER_STEPS },
  (_, i) => rGmv + ((rFrontierMax - rGmv) * i) / (FRONTIER_STEPS - 1),
);
const frontierRisks = frontierReturns.map((r) =>
  Math.sqrt(Math.max(0, (scalarA * r * r - 2 * scalarB * r + scalarC) / scalarD)),
);

const portfolios = data.map((row) => {
  const x = Number(row[RISK]);
  const y = Number(row[RETURN]);
  const z = (y - RF_RATE) / x;
  return {
    id: String(row[PORTFOLIO_ID]),
    x,
    y,
    z,
  };
});

const sharpeVals = portfolios.map((p) => p.z);
const sharpeMin = Math.min(...sharpeVals);
const sharpeMax = Math.max(...sharpeVals, sharpeTan);

const xMax = Math.max(riskTan, riskGmv, ...frontierRisks, ...portfolios.map((p) => p.x)) * X_MAX_PAD_MULT;
const rawYMin = Math.min(RF_RATE, rGmv, ...portfolios.map((p) => p.y));
const rawYMax = Math.max(rFrontierMax, ...portfolios.map((p) => p.y));
const yMin = rawYMin - (rawYMax - rawYMin) * Y_MIN_PAD_SHARE;
const yMax = rawYMax * Y_MAX_PAD_MULT;

const cmlXEnd = Math.min(xMax, (yMax - RF_RATE) / sharpeTan);
const cmlYEnd = RF_RATE + sharpeTan * cmlXEnd;
const cmlLabelX = 0.58 * cmlXEnd;
const cmlLabelY = RF_RATE + sharpeTan * cmlLabelX;

function FrontierOverlay() {
  const xScale = useXScale("risk") as (v: number) => number;
  const yScale = useYScale("return") as (v: number) => number;

  const x1 = xScale(0);
  const y1 = yScale(RF_RATE);
  const x2 = xScale(cmlXEnd);
  const y2 = yScale(cmlYEnd);
  const xLabel = xScale(cmlLabelX);
  const yLabel = yScale(cmlLabelY);

  const gmvX = xScale(riskGmv);
  const gmvY = yScale(rGmv);
  const tanX = xScale(riskTan);
  const tanY = yScale(rTan);

  return (
    <g>
      {/* Capital Market Line */}
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={t.palette[1]}
        strokeWidth={2.5}
        strokeDasharray={CML_DASH}
      />
      <text
        x={xLabel}
        y={yLabel - 28}
        textAnchor="middle"
        fontSize={14}
        fontWeight={600}
        fill={t.palette[1]}
        stroke={t.pageBg}
        strokeWidth={3.5}
        paintOrder="stroke"
      >
        {CML_LABEL}
      </text>

      {/* Highlight rings around GMV and Tangency markers */}
      <circle cx={gmvX} cy={gmvY} r={10} fill={t.ink} stroke={t.pageBg} strokeWidth={2.5} />
      <text
        x={gmvX - 14}
        y={gmvY + 5}
        textAnchor="end"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={3.5}
        paintOrder="stroke"
      >
        {`GMV (${(riskGmv * 100).toFixed(1)}%, ${(rGmv * 100).toFixed(1)}%)`}
      </text>

      <circle cx={tanX} cy={tanY} r={10} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={2.5} />
      <text
        x={tanX - 14}
        y={tanY - 12}
        textAnchor="end"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={3.5}
        paintOrder="stroke"
      >
        {`Max Sharpe = ${sharpeTan.toFixed(2)} (${(riskTan * 100).toFixed(1)}%, ${(rTan * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerH = 82;
  const legendH = 38;
  const colorbarH = 44;
  const chartH = height - headerH - legendH - colorbarH;
  const subtitle = `Mean-variance optimization across ${nAssets} assets · ${data.length} simulated portfolios · rf = ${(RF_RATE * 100).toFixed(1)}%`;

  return (
    <Box
      sx={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Box sx={{ height: headerH, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
        <Typography sx={{ fontSize: "22px", fontWeight: 600, color: t.ink }}>
          {TITLE}
        </Typography>
        <Typography sx={{ fontSize: "15px", color: t.inkSoft, mt: "2px" }}>
          {subtitle}
        </Typography>
      </Box>

      {/* Series legend rendered outside the SVG drawing area */}
      <Box
        sx={{
          height: legendH,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "28px",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width={28} height={14}>
            <line x1={0} y1={7} x2={28} y2={7} stroke={t.ink} strokeWidth={4} />
          </svg>
          <Typography sx={{ fontSize: "14px", color: t.ink }}>{FRONTIER_LABEL}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width={28} height={14}>
            <line
              x1={0}
              y1={7}
              x2={28}
              y2={7}
              stroke={t.palette[1]}
              strokeWidth={2.5}
              strokeDasharray={CML_DASH}
            />
          </svg>
          <Typography sx={{ fontSize: "14px", color: t.ink }}>{CML_LABEL}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width={18} height={18}>
            <circle cx={9} cy={9} r={7} fill={t.ink} stroke={t.pageBg} strokeWidth={1.5} />
          </svg>
          <Typography sx={{ fontSize: "14px", color: t.ink }}>{GMV_LABEL}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width={18} height={18}>
            <circle cx={9} cy={9} r={7} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={1.5} />
          </svg>
          <Typography sx={{ fontSize: "14px", color: t.ink }}>{TAN_LABEL}</Typography>
        </Box>
      </Box>

      <ChartsContainer
        width={width}
        height={chartH}
        skipAnimation
        margin={{ top: 12, right: 48, bottom: 16, left: 20 }}
        sx={{ '& .MuiLineChart-line[data-series="frontier"]': { strokeWidth: 4 } }}
        series={[
          {
            type: "line",
            id: "frontier",
            data: frontierReturns,
            xAxisId: "risk",
            yAxisId: "return",
            color: t.ink,
            showMark: false,
            curve: "monotoneX",
            label: FRONTIER_LABEL,
          },
          {
            type: "scatter",
            id: "cloud",
            data: portfolios,
            xAxisId: "risk",
            yAxisId: "return",
            zAxisId: "sharpe",
            markerSize: 5.5,
          },
        ]}
        xAxis={[
          {
            id: "risk",
            scaleType: "linear",
            data: frontierRisks,
            min: 0,
            max: xMax,
            height: 54,
            label: RISK,
            valueFormatter: (v: number) => `${(v * 100).toFixed(0)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "return",
            min: yMin,
            max: yMax,
            width: 84,
            label: RETURN,
            valueFormatter: (v: number) => `${(v * 100).toFixed(0)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "sharpe",
            min: sharpeMin,
            max: sharpeMax,
            colorMap: {
              type: "continuous",
              min: sharpeMin,
              max: sharpeMax,
              color: [t.seq[0], t.seq[1]],
            },
          },
        ]}
      >
        <ChartsGrid horizontal vertical />
        <ScatterPlot skipAnimation />
        <LinePlot skipAnimation />
        <ChartsReferenceLine
          y={RF_RATE}
          axisId="return"
          label={`${RF_LABEL} (${(RF_RATE * 100).toFixed(0)}%)`}
          labelAlign="end"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4,4", strokeWidth: 1.2, opacity: 0.65 }}
        />
        <FrontierOverlay />
        <ChartsXAxis axisId="risk" />
        <ChartsYAxis axisId="return" />
      </ChartsContainer>

      <Box
        sx={{
          height: colorbarH,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "12px",
          pb: "6px",
        }}
      >
        <Typography sx={{ fontSize: "14px", color: t.inkSoft }}>
          {`${SHARPE_LOW_LABEL} (${sharpeMin.toFixed(2)})`}
        </Typography>
        <Box
          sx={{
            width: 240,
            height: 14,
            borderRadius: "3px",
            background: `linear-gradient(to right, ${t.seq[0]}, ${t.seq[1]})`,
          }}
        />
        <Typography sx={{ fontSize: "14px", color: t.inkSoft }}>
          {`${SHARPE_HIGH_LABEL} (${sharpeMax.toFixed(2)})`}
        </Typography>
      </Box>
    </Box>
  );
}
