// anyplot.ai
// line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
// Library: muix 7.29.1 | JavaScript 22.23.3
// Quality: pending | Created: 2026-10-01
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width: WIDTH, height: HEIGHT } = window.ANYPLOT_SIZE;

// Constants
const LABEL_MIN_GAP_PX = 32;
const ENERGY_TOP_PAD_SHARE = 0.03;
const SHIFT: Record<"base" | "sup" | "sub", number> = {
  base: 0,
  sup: -0.42,
  sub: 0.26,
};
const SUP_MAP: Record<string, string> = {
  "⁰": "0",
  "¹": "1",
  "²": "2",
  "³": "3",
  "⁴": "4",
  "⁵": "5",
  "⁶": "6",
  "⁷": "7",
  "⁸": "8",
  "⁹": "9",
  "⁺": "+",
  "⁻": "-",
};
const SUB_MAP: Record<string, string> = {
  "₀": "0",
  "₁": "1",
  "₂": "2",
  "₃": "3",
  "₄": "4",
  "₅": "5",
  "₆": "6",
  "₇": "7",
  "₈": "8",
  "⁹": "9",
  "ₒ": "o",
};

// Columns: set these to your data's column names
const DELTA_OVER_B = "Ligand-field strength Δo / B"; // role: delta_over_b
const TERM = "Term symbol"; // role: term
const ENERGY_OVER_B = "Term energy E / B"; // role: energy_over_b
const SPIN_ALLOWED = "Spin allowed"; // role: spin_allowed

// Data: replace this block with your own records
const CONFIG = "d³ (Cr³⁺)";
const C_OVER_B = 4.5;
const EXAMPLE_COMPLEX = "[Cr(H₂O)₆]³⁺";
const EXAMPLE_FIELD = 17400 / 700;

const TERM_SPECS: Array<{ name: string; spinAllowed: boolean }> = [
  { name: "⁴A₂g", spinAllowed: true },
  { name: "⁴T₂g", spinAllowed: true },
  { name: "⁴T₁g(F)", spinAllowed: true },
  { name: "⁴T₁g(P)", spinAllowed: true },
  { name: "²Eg", spinAllowed: false },
  { name: "²T₂g", spinAllowed: false },
];

const N_STEPS = 320;
const data: Array<Record<string, number | string | boolean>> = [];
for (let step = 0; step <= N_STEPS; step += 1) {
  const d = (step * 40) / N_STEPS;
  const t1gFDiag = 1.8 * d;
  const t1gPDiag = 15 + 1.2 * d;
  const mixing = 0.4 * d;
  const centre = (t1gFDiag + t1gPDiag) / 2;
  const splitting = Math.hypot((t1gFDiag - t1gPDiag) / 2, mixing);

  const energies = [
    0,
    d,
    centre - splitting,
    centre + splitting,
    9 + 3 * C_OVER_B,
    15 + 3 * C_OVER_B,
  ];

  for (let k = 0; k < TERM_SPECS.length; k += 1) {
    data.push({
      [DELTA_OVER_B]: d,
      [TERM]: TERM_SPECS[k].name,
      [ENERGY_OVER_B]: energies[k],
      [SPIN_ALLOWED]: TERM_SPECS[k].spinAllowed,
    });
  }
}

// Plot: reads only data and the constants above
interface TypesetRun {
  text: string;
  dyFactor: number;
  fontScale: number;
}

const stringsToParse = new Set<string>([
  DELTA_OVER_B,
  `${CONFIG} in an octahedral field · C/B = ${C_OVER_B} · spin-allowed quartets solid, spin-forbidden doublets dashed`,
  `${EXAMPLE_COMPLEX} · Δo / B = ${EXAMPLE_FIELD.toFixed(1)}`,
  "ν₁",
  "ν₂",
]);
for (const row of data) {
  stringsToParse.add(String(row[TERM]));
}

const parsedRunsByText: Record<string, TypesetRun[]> = {};
for (const rawText of stringsToParse) {
  const rawSegments: Array<{ kind: "base" | "sup" | "sub"; text: string }> = [];
  let inMulliken = false;
  for (let i = 0; i < rawText.length; i += 1) {
    const ch = rawText[i];
    const prev = i > 0 ? rawText[i - 1] : "";
    let kind: "base" | "sup" | "sub" = "base";
    let mapped = ch;
    if (ch in SUP_MAP) {
      kind = "sup";
      mapped = SUP_MAP[ch];
      inMulliken = false;
    } else if (ch in SUB_MAP) {
      kind = "sub";
      mapped = SUB_MAP[ch];
    } else if ((ch === "g" || ch === "u") && inMulliken) {
      kind = "sub";
      inMulliken = false;
    } else if (ch === "o" && prev === "Δ") {
      kind = "sub";
    } else {
      inMulliken = ch === "A" || ch === "B" || ch === "E" || ch === "T";
    }
    const last = rawSegments[rawSegments.length - 1];
    if (last && last.kind === kind) {
      last.text += mapped;
    } else {
      rawSegments.push({ kind, text: mapped });
    }
  }
  let offset = 0;
  parsedRunsByText[rawText] = rawSegments.map((seg) => {
    const dyFactor = SHIFT[seg.kind] - offset;
    offset = SHIFT[seg.kind];
    return {
      text: seg.text,
      dyFactor,
      fontScale: seg.kind === "base" ? 1 : 0.66,
    };
  });
}

const terms: string[] = [];
for (const row of data) {
  const termName = String(row[TERM]);
  if (!terms.includes(termName)) terms.push(termName);
}

const fieldSet: number[] = [];
for (const row of data) {
  const f = Number(row[DELTA_OVER_B]);
  if (!fieldSet.includes(f)) fieldSet.push(f);
}
const fieldStrengths = [...fieldSet].sort((a, b) => a - b);
const fieldMin = fieldStrengths[0];
const fieldMax = fieldStrengths[fieldStrengths.length - 1];

const allEnergies = data.map((r) => Number(r[ENERGY_OVER_B]));
const energyMin = Math.min(...allEnergies);
const maxRawEnergy = Math.max(...allEnergies);
const energyMax = maxRawEnergy * (1 + ENERGY_TOP_PAD_SHARE);

const termSeries = terms.map((termName, i) => {
  const rows = data
    .filter((r) => String(r[TERM]) === termName)
    .sort((a, b) => Number(a[DELTA_OVER_B]) - Number(b[DELTA_OVER_B]));
  const spinAllowed = Boolean(rows[0][SPIN_ALLOWED]);
  const points = rows.map((r) => ({
    x: Number(r[DELTA_OVER_B]),
    y: Number(r[ENERGY_OVER_B]),
  }));
  const yValues = points.map((p) => p.y);
  const finalEnergy = points[points.length - 1].y;
  let exampleEnergy = 0;
  for (let j = 0; j < points.length - 1; j += 1) {
    if (
      EXAMPLE_FIELD >= points[j].x &&
      EXAMPLE_FIELD <= points[j + 1].x
    ) {
      const span = points[j + 1].x - points[j].x;
      const frac = (EXAMPLE_FIELD - points[j].x) / span;
      exampleEnergy = points[j].y + frac * (points[j + 1].y - points[j].y);
      break;
    }
  }
  return {
    id: `term-${i}`,
    label: termName,
    runs: parsedRunsByText[termName],
    color: t.palette[i],
    spinAllowed,
    yValues,
    finalEnergy,
    exampleEnergy,
  };
});

// Identify excited spin-allowed transitions from ground state sorted by energy at EXAMPLE_FIELD
const spinAllowedExcited = termSeries
  .filter((s) => s.spinAllowed && s.finalEnergy > 0)
  .sort((a, b) => a.exampleEnergy - b.exampleEnergy);
const bandTransitions = spinAllowedExcited.slice(0, 2).map((s, idx) => {
  const lbl = idx === 0 ? "ν₁" : "ν₂";
  return {
    id: `nu-${idx + 1}`,
    runs: parsedRunsByText[lbl],
    targetEnergy: s.exampleEnergy,
    dx: idx === 0 ? -12 : 12,
  };
});

const subtitleText = `${CONFIG} in an octahedral field · C/B = ${C_OVER_B} · spin-allowed quartets solid, spin-forbidden doublets dashed`;
const complexMarkerText = `${EXAMPLE_COMPLEX} · Δo / B = ${EXAMPLE_FIELD.toFixed(1)}`;

function TanabeSuganoLayer() {
  const { left, top, width, height } = useDrawingArea();
  const xScale = useXScale("field") as (v: number) => number;
  const yScale = useYScale("energy") as (v: number) => number;

  // Declutter right-margin term labels in top-to-bottom pixel order
  const rawLabels = termSeries
    .map((s) => ({
      ...s,
      rawY: yScale(s.finalEnergy),
    }))
    .sort((a, b) => a.rawY - b.rawY);

  let lowestY = -Infinity;
  const placedLabels = rawLabels.map((item) => {
    const placedY = Math.max(item.rawY, lowestY + LABEL_MIN_GAP_PX);
    lowestY = placedY;
    return { ...item, placedY };
  });

  const exX = xScale(EXAMPLE_FIELD);
  const yZero = yScale(0);

  return (
    <g>
      <defs>
        <marker
          id="band-arrow"
          markerUnits="userSpaceOnUse"
          markerWidth={14}
          markerHeight={14}
          refX={7}
          refY={7}
          orient="auto"
        >
          <path d="M0,0 L14,7 L0,14 z" fill={t.inkSoft} />
        </marker>
      </defs>

      {/* Observed UV-Vis transition arrows at example complex field strength */}
      {bandTransitions.map((b) => {
        const yTarget = yScale(b.targetEnergy);
        return (
          <g key={b.id}>
            <line
              x1={exX + b.dx}
              y1={yZero}
              x2={exX + b.dx}
              y2={yTarget + 7}
              stroke={t.inkSoft}
              strokeWidth={2}
              markerEnd="url(#band-arrow)"
            />
            <text
              x={exX + b.dx + Math.sign(b.dx) * 9}
              y={(yZero + yTarget) / 2}
              fill={t.inkSoft}
              fontSize={17}
              textAnchor={b.dx < 0 ? "end" : "start"}
              dominantBaseline="middle"
            >
              {b.runs.map((r, idx) => (
                <tspan
                  key={idx}
                  dy={r.dyFactor * 17}
                  fontSize={17 * r.fontScale}
                >
                  {r.text}
                </tspan>
              ))}
            </text>
          </g>
        );
      })}

      {/* Vertical label for example complex */}
      <text
        x={0}
        y={0}
        fill={t.inkSoft}
        fontSize={15}
        textAnchor="end"
        transform={`translate(${exX - 12} ${top + 16}) rotate(-90)`}
      >
        {parsedRunsByText[complexMarkerText].map((r, idx) => (
          <tspan key={idx} dy={r.dyFactor * 15} fontSize={15 * r.fontScale}>
            {r.text}
          </tspan>
        ))}
      </text>

      {/* Direct right-margin term symbol labels with true super/subscripts */}
      {placedLabels.map((lbl) => (
        <text
          key={lbl.id}
          x={left + width + 14}
          y={lbl.placedY}
          fill={lbl.color}
          fontSize={20}
          fontWeight={lbl.spinAllowed ? 600 : 500}
          dominantBaseline="middle"
        >
          {lbl.runs.map((r, idx) => (
            <tspan key={idx} dy={r.dyFactor * 20} fontSize={20 * r.fontScale}>
              {r.text}
            </tspan>
          ))}
        </text>
      ))}

      {/* Title, subtitle, and axis titles */}
      <text
        x={left + width / 2}
        y={40}
        fill={t.ink}
        fontSize={22}
        fontWeight={600}
        textAnchor="middle"
      >
        line-tanabe-sugano · javascript · muix · anyplot.ai
      </text>
      <text
        x={left + width / 2}
        y={70}
        fill={t.inkSoft}
        fontSize={15}
        textAnchor="middle"
      >
        {parsedRunsByText[subtitleText].map((r, idx) => (
          <tspan key={idx} dy={r.dyFactor * 15} fontSize={15 * r.fontScale}>
            {r.text}
          </tspan>
        ))}
      </text>
      <text
        x={left + width / 2}
        y={HEIGHT - 24}
        fill={t.ink}
        fontSize={17}
        textAnchor="middle"
      >
        {parsedRunsByText[DELTA_OVER_B].map((r, idx) => (
          <tspan key={idx} dy={r.dyFactor * 17} fontSize={17 * r.fontScale}>
            {r.text}
          </tspan>
        ))}
      </text>
      <text
        x={28}
        y={top + height / 2}
        fill={t.ink}
        fontSize={17}
        textAnchor="middle"
        transform={`rotate(-90 28 ${top + height / 2})`}
      >
        {ENERGY_OVER_B}
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: WIDTH, height: HEIGHT, background: t.pageBg }}>
      <ChartsContainer
        width={WIDTH}
        height={HEIGHT}
        skipAnimation
        margin={{ top: 96, right: 172, bottom: 48, left: 44 }}
        series={termSeries.map((s) => ({
          type: "line",
          id: s.id,
          xAxisId: "field",
          yAxisId: "energy",
          label: s.label,
          color: s.color,
          showMark: false,
          curve: "linear",
          data: s.yValues,
        }))}
        xAxis={[
          {
            id: "field",
            data: fieldStrengths,
            scaleType: "linear",
            min: fieldMin,
            max: fieldMax,
            tickNumber: 9,
            height: 40,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            tickSize: 7,
          },
        ]}
        yAxis={[
          {
            id: "energy",
            min: energyMin,
            max: energyMax,
            tickNumber: 9,
            width: 52,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            tickSize: 7,
          },
        ]}
        sx={Object.fromEntries(
          termSeries.map((s) => [
            `& .MuiLineChart-line[data-series="${s.id}"]`,
            s.spinAllowed
              ? { strokeWidth: 4.2 }
              : { strokeWidth: 2.4, strokeDasharray: "13 8" },
          ]),
        )}
      >
        <ChartsGrid vertical horizontal />
        <ChartsReferenceLine
          x={EXAMPLE_FIELD}
          axisId="field"
          lineStyle={{
            stroke: t.inkSoft,
            strokeWidth: 2,
            strokeDasharray: "6 7",
          }}
        />
        <LinePlot skipAnimation />
        <ChartsXAxis axisId="field" />
        <ChartsYAxis axisId="energy" />
        <TanabeSuganoLayer />
        <ChartsTooltip trigger="axis" />
      </ChartsContainer>
    </div>
  );
}
