// anyplot.ai
// line-reaction-coordinate: Reaction Coordinate Energy Diagram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "system-ui, -apple-system, sans-serif";
const Y_PAD_BOTTOM_FRAC = 0.2;
const Y_PAD_TOP_FRAC = 0.25;
const EA_X_OFFSET_FRAC = 0.14;
const DH_X_FRAC = 0.86;
const REACTANT_LABEL_X_FRAC = 0.02;
const PRODUCT_LABEL_X_FRAC = 0.72;

// Columns: set these to your data's column names
const COORD = "Reaction coordinate"; // role: reaction_coordinate
const ENERGY = "Potential energy (kJ/mol)"; // role: energy
const STAGE = "Reaction stage"; // role: stage

// Data: replace this block with your own records
const N_POINTS = 201;
const data: Array<Record<string, number | string>> = [];
for (let i = 0; i < N_POINTS; i++) {
  const x = Math.round((i / (N_POINTS - 1)) * 1000) / 1000;
  let energy: number;
  if (x <= 0.14) {
    energy = 50;
  } else if (x <= 0.4) {
    const u = (x - 0.14) / (0.4 - 0.14);
    energy = 50 + (120 - 50) * (3 * u * u - 2 * u * u * u);
  } else if (x <= 0.72) {
    const u = (x - 0.4) / (0.72 - 0.4);
    energy = 120 + (20 - 120) * (3 * u * u - 2 * u * u * u);
  } else {
    energy = 20;
  }
  const stage =
    x <= 0.14
      ? "Reactants"
      : Math.abs(x - 0.4) < 0.003
        ? "Transition State ‡"
        : x >= 0.72
          ? "Products"
          : "Pathway";
  data.push({
    [COORD]: x,
    [ENERGY]: Math.round(energy * 10) / 10,
    [STAGE]: stage,
  });
}

// Plot: reads only data and the constants above
const sortedData = [...data].sort((a, b) => Number(a[COORD]) - Number(b[COORD]));
const xData = sortedData.map((r) => Number(r[COORD]));
const yData = sortedData.map((r) => Number(r[ENERGY]));

const reactantRow = sortedData[0];
const productRow = sortedData[sortedData.length - 1];
let peakRow = sortedData[0];
for (const row of sortedData) {
  if (Number(row[ENERGY]) > Number(peakRow[ENERGY])) {
    peakRow = row;
  }
}

const eReactants = Number(reactantRow[ENERGY]);
const eProducts = Number(productRow[ENERGY]);
const eTransition = Number(peakRow[ENERGY]);
const xPeak = Number(peakRow[COORD]);
const xMin = xData[0];
const xMax = xData[xData.length - 1];
const xSpan = xMax - xMin;

const stageReactants = String(reactantRow[STAGE]);
const stageProducts = String(productRow[STAGE]);
const stageTransition = String(peakRow[STAGE]);

const unitMatch = ENERGY.match(/\(([^)]+)\)/);
const ENERGY_UNIT = unitMatch ? unitMatch[1] : "";
const activationEnergy = Math.round(eTransition - eReactants);
const enthalpyChange = Math.round(eProducts - eReactants);
const enthalpyText =
  enthalpyChange < 0 ? `−${Math.abs(enthalpyChange)}` : `+${enthalpyChange}`;

const minEnergy = Math.min(...yData);
const maxEnergy = Math.max(...yData);
const energyRange = maxEnergy - minEnergy;
const yMin = minEnergy - energyRange * Y_PAD_BOTTOM_FRAC;
const yMax = maxEnergy + energyRange * Y_PAD_TOP_FRAC;

function EnergyAnnotations() {
  const xScale = useXScale("coord") as (v: number) => number;
  const yScale = useYScale("energy") as (v: number) => number;

  const yR = yScale(eReactants);
  const yTS = yScale(eTransition);
  const yP = yScale(eProducts);

  const xEa = xScale(xPeak + xSpan * EA_X_OFFSET_FRAC);
  const xDH = xScale(xMin + xSpan * DH_X_FRAC);

  const AW = 5;
  const AH = 9;

  const ink = t.ink;
  const inkSoft = t.inkSoft;
  const green = t.palette[0];

  let curveD = "";
  for (let i = 0; i < sortedData.length; i++) {
    const px = xScale(xData[i]);
    const py = yScale(yData[i]);
    curveD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)} `;
  }

  return (
    <g fontFamily={FONT}>
      {/* Reaction coordinate energy curve */}
      <path
        d={curveD}
        fill="none"
        stroke={green}
        strokeWidth={3.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Transition state peak marker — hollow circle on the curve */}
      <circle
        cx={xScale(xPeak)}
        cy={yTS}
        r={7}
        fill={t.pageBg}
        stroke={green}
        strokeWidth={2.5}
      />

      {/* Ea arrow: reactant level -> transition state */}
      <line
        x1={xEa}
        y1={yTS + AH + 1}
        x2={xEa}
        y2={yR - AH - 1}
        stroke={ink}
        strokeWidth={1.5}
      />
      <polygon
        points={`${xEa - AW},${yTS + AH} ${xEa + AW},${yTS + AH} ${xEa},${yTS}`}
        fill={ink}
      />
      <polygon
        points={`${xEa - AW},${yR - AH} ${xEa + AW},${yR - AH} ${xEa},${yR}`}
        fill={ink}
      />
      <text
        x={xEa + 12}
        y={(yTS + yR) / 2}
        fill={ink}
        fontSize={18}
        dominantBaseline="middle"
        fontWeight="500"
      >
        {`Ea = ${activationEnergy} ${ENERGY_UNIT}`}
      </text>

      {/* ΔH arrow: reactant level -> product level */}
      <line
        x1={xDH}
        y1={yR + AH + 1}
        x2={xDH}
        y2={yP - AH - 1}
        stroke={inkSoft}
        strokeWidth={1.5}
        strokeDasharray="6 3"
      />
      <polygon
        points={`${xDH - AW},${yR + AH} ${xDH + AW},${yR + AH} ${xDH},${yR}`}
        fill={inkSoft}
      />
      <polygon
        points={`${xDH - AW},${yP - AH} ${xDH + AW},${yP - AH} ${xDH},${yP}`}
        fill={inkSoft}
      />
      <text
        x={xDH + 12}
        y={(yR + yP) / 2}
        fill={inkSoft}
        fontSize={18}
        dominantBaseline="middle"
      >
        {`ΔH = ${enthalpyText} ${ENERGY_UNIT}`}
      </text>

      {/* Transition State label (above peak marker) */}
      <text
        x={xScale(xPeak)}
        y={yTS - 22}
        fill={ink}
        fontSize={18}
        textAnchor="middle"
        fontWeight="500"
      >
        {stageTransition}
      </text>

      {/* Reactants label — offset above flat reactant shelf */}
      <text
        x={xScale(xMin + xSpan * REACTANT_LABEL_X_FRAC)}
        y={yR - 18}
        fill={ink}
        fontSize={18}
        textAnchor="start"
      >
        {`${stageReactants} (${eReactants} ${ENERGY_UNIT})`}
      </text>

      {/* Products label — offset below flat product shelf so it clears ΔH arrow */}
      <text
        x={xScale(xMin + xSpan * PRODUCT_LABEL_X_FRAC)}
        y={yP + 28}
        fill={ink}
        fontSize={18}
        textAnchor="start"
      >
        {`${stageProducts} (${eProducts} ${ENERGY_UNIT})`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleH = 52;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        pt: "14px",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
          mb: "4px",
          fontFamily: "inherit",
        }}
      >
        line-reaction-coordinate · javascript · muix · anyplot.ai
      </Typography>

      <ChartsContainer
        width={width}
        height={height - titleH}
        skipAnimation
        margin={{ left: 24, right: 64, top: 36, bottom: 20 }}
        series={[
          {
            type: "line",
            id: "energy",
            data: yData,
            xAxisId: "coord",
            yAxisId: "energy",
            color: t.palette[0],
            showMark: false,
            curve: "linear",
            label: ENERGY,
          },
        ]}
        xAxis={[
          {
            id: "coord",
            data: xData,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 58,
            label: COORD,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fontWeight: "500", fill: t.inkSoft, fontFamily: FONT },
            disableLine: true,
            disableTicks: true,
          },
        ]}
        yAxis={[
          {
            id: "energy",
            min: yMin,
            max: yMax,
            width: 88,
            label: ENERGY,
            valueFormatter: (v: number | null) =>
              v === null ? "" : `${Math.round(v)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 16, fontWeight: "500", fill: t.inkSoft, fontFamily: FONT },
            disableLine: true,
            disableTicks: true,
          },
        ]}
      >
        <ChartsReferenceLine
          y={eReactants}
          axisId="energy"
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "8 5",
            strokeWidth: 1.2,
            opacity: 0.65,
          }}
        />
        <ChartsReferenceLine
          y={eProducts}
          axisId="energy"
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "8 5",
            strokeWidth: 1.2,
            opacity: 0.65,
          }}
        />

        <LinePlot skipAnimation />
        <ChartsXAxis axisId="coord" />
        <ChartsYAxis axisId="energy" />
        <EnergyAnnotations />
      </ChartsContainer>
    </Box>
  );
}
