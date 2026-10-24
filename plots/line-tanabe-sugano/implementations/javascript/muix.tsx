// anyplot.ai
// line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
// Library: muix 9.x | JavaScript 22.23.3
// Quality: 90/100 | Created: 2026-10-01
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width: WIDTH, height: HEIGHT } = window.ANYPLOT_SIZE;

// Constants
const FIELD_COL = "Ligand-field strength Δo / B" as const;
const TERM_COL = "Term Symbol" as const;
const ENERGY_COL = "Term energy E / B" as const;
const SPIN_ALLOWED_COL = "Spin Allowed" as const;
const COMPLEX_COL = "Example Complex" as const;
const COMPLEX_FIELD_COL = "Complex Δo / B" as const;
const C_OVER_B_COL = "Racah C / B" as const;

const LABEL_MIN_GAP_PX = 32;
const ENERGY_CEIL_STEP = 10;

// Data — d³ (Cr³⁺) in an octahedral field at C/B = 4.5, energies in units of B
const TERM_SPECS: Array<{ name: string; spinAllowed: boolean }> = [
  { name: "⁴A₂g", spinAllowed: true },
  { name: "⁴T₂g", spinAllowed: true },
  { name: "⁴T₁g(F)", spinAllowed: true },
  { name: "⁴T₁g(P)", spinAllowed: true },
  { name: "²Eg", spinAllowed: false },
  { name: "²T₂g", spinAllowed: false },
];

const DATA: Array<Record<string, number | string | boolean>> = [];
const N_STEPS = 160;
for (let step = 0; step <= N_STEPS; step++) {
  const d = (step * 40) / N_STEPS;
  const cOverB = 4.5;
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
    9 + 3 * cOverB,
    15 + 3 * cOverB,
  ];

  for (let k = 0; k < TERM_SPECS.length; k++) {
    DATA.push({
      [FIELD_COL]: d,
      [TERM_COL]: TERM_SPECS[k].name,
      [ENERGY_COL]: energies[k],
      [SPIN_ALLOWED_COL]: TERM_SPECS[k].spinAllowed,
      [COMPLEX_COL]: "[Cr(H₂O)₆]³⁺",
      [COMPLEX_FIELD_COL]: Math.round((17400 / 700) * 10) / 10,
      [C_OVER_B_COL]: cOverB,
    });
  }
}

const terms: string[] = [];
for (const row of DATA) {
  const termName = String(row[TERM_COL]);
  if (!terms.includes(termName)) terms.push(termName);
}

const fieldSet: number[] = [];
for (const row of DATA) {
  const f = Number(row[FIELD_COL]);
  if (!fieldSet.includes(f)) fieldSet.push(f);
}
const fieldStrengths = [...fieldSet].sort((a, b) => a - b);
const fieldMin = fieldStrengths[0];
const fieldMax = fieldStrengths[fieldStrengths.length - 1];

const allEnergies = DATA.map((r) => Number(r[ENERGY_COL]));
const energyMin = Math.min(...allEnergies);
const energyMax =
  Math.ceil(Math.max(...allEnergies) / ENERGY_CEIL_STEP) * ENERGY_CEIL_STEP;

const cOverBVal = Number(DATA[0][C_OVER_B_COL]);
const exampleComplexName = String(DATA[0][COMPLEX_COL]);
const exampleFieldVal = Number(DATA[0][COMPLEX_FIELD_COL]);

const termSeries = terms.map((termName, i) => {
  const rows = DATA.filter((r) => String(r[TERM_COL]) === termName).sort(
    (a, b) => Number(a[FIELD_COL]) - Number(b[FIELD_COL]),
  );
  const spinAllowed = Boolean(rows[0]?.[SPIN_ALLOWED_COL]);
  const points = rows.map((r) => ({
    x: Number(r[FIELD_COL]),
    y: Number(r[ENERGY_COL]),
  }));
  const finalEnergy = points[points.length - 1]?.y ?? 0;
  // Interpolate energy at exampleFieldVal
  let exampleEnergy = 0;
  for (let j = 0; j < points.length - 1; j++) {
    if (
      exampleFieldVal >= points[j].x &&
      exampleFieldVal <= points[j + 1].x
    ) {
      const span = points[j + 1].x - points[j].x || 1;
      const frac = (exampleFieldVal - points[j].x) / span;
      exampleEnergy = points[j].y + frac * (points[j + 1].y - points[j].y);
      break;
    }
  }
  return {
    id: `term-${i}`,
    label: termName,
    color: t.palette[i],
    spinAllowed,
    points,
    finalEnergy,
    exampleEnergy,
  };
});

// Identify excited spin-allowed transitions from ground state for UV-Vis band arrows
const spinAllowedExcited = termSeries.filter(
  (s) => s.spinAllowed && s.finalEnergy > 0,
);
const bandTransitions = spinAllowedExcited.slice(0, 2).map((s, idx) => ({
  id: `nu-${idx + 1}`,
  label: idx === 0 ? "ν₁" : "ν₂",
  targetEnergy: s.exampleEnergy,
  dx: idx === 0 ? -12 : 12,
}));

function TanabeSuganoLayer() {
  const { left, top, width, height } = useDrawingArea();
  const xScale = useXScale("field") as (v: number) => number | undefined;
  const yScale = useYScale("energy") as (v: number) => number | undefined;

  const toX = (v: number) => Number(xScale(v) ?? 0);
  const toY = (v: number) => Number(yScale(v) ?? 0);

  // Declutter right-margin term labels in top-to-bottom pixel order
  const rawLabels = termSeries
    .map((s) => ({
      ...s,
      rawY: toY(s.finalEnergy),
    }))
    .sort((a, b) => a.rawY - b.rawY);

  let lowestY = -Infinity;
  const placedLabels = rawLabels.map((item) => {
    const placedY = Math.max(item.rawY, lowestY + LABEL_MIN_GAP_PX);
    lowestY = placedY;
    return { ...item, placedY };
  });

  const exX = toX(exampleFieldVal);
  const yZero = toY(0);

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

      {/* Term energy curves: solid for spin-allowed quartets, dashed for spin-forbidden doublets */}
      {termSeries.map((s) => {
        let dPath = "";
        for (let i = 0; i < s.points.length; i++) {
          const px = toX(s.points[i].x);
          const py = toY(s.points[i].y);
          dPath += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)} `;
        }
        return (
          <path
            key={s.id}
            d={dPath}
            fill="none"
            stroke={s.color}
            strokeWidth={s.spinAllowed ? 4.2 : 2.4}
            strokeDasharray={s.spinAllowed ? undefined : "13 8"}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}

      {/* Observed UV-Vis transition arrows at example complex field strength */}
      {bandTransitions.map((b) => {
        const yTarget = toY(b.targetEnergy);
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
              {b.label}
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
        {`${exampleComplexName} · Δo / B = ${exampleFieldVal.toFixed(1)}`}
      </text>

      {/* Direct right-margin term symbol labels */}
      {placedLabels.map((lbl) => {
        const match = lbl.label.match(/^([^g]+)g(.*)$/);
        return (
          <text
            key={lbl.id}
            x={left + width + 14}
            y={lbl.placedY}
            fill={lbl.color}
            fontSize={20}
            fontWeight={lbl.spinAllowed ? 600 : 500}
            dominantBaseline="middle"
          >
            {match ? (
              <>
                <tspan>{match[1]}</tspan>
                <tspan dy={4} fontSize={14}>
                  g
                </tspan>
                {match[2] ? (
                  <tspan dy={-4} fontSize={20}>
                    {match[2]}
                  </tspan>
                ) : null}
              </>
            ) : (
              lbl.label
            )}
          </text>
        );
      })}

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
        {`d³ (Cr³⁺) in an octahedral field · C/B = ${cOverBVal} · spin-allowed quartets solid, spin-forbidden doublets dashed`}
      </text>
      <text
        x={left + width / 2}
        y={HEIGHT - 24}
        fill={t.ink}
        fontSize={17}
        textAnchor="middle"
      >
        {FIELD_COL}
      </text>
      <text
        x={28}
        y={top + height / 2}
        fill={t.ink}
        fontSize={17}
        textAnchor="middle"
        transform={`rotate(-90 28 ${top + height / 2})`}
      >
        {ENERGY_COL}
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
        margin={{ top: 96, right: 172, bottom: 48, left: 44 }}
        series={[]}
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
      >
        <ChartsGrid vertical horizontal />
        <ChartsReferenceLine
          x={exampleFieldVal}
          axisId="field"
          lineStyle={{
            stroke: t.inkSoft,
            strokeWidth: 2,
            strokeDasharray: "6 7",
          }}
        />
        <ChartsXAxis axisId="field" />
        <ChartsYAxis axisId="energy" />
        <TanabeSuganoLayer />
      </ChartsContainer>
    </div>
  );
}
