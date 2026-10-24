// anyplot.ai
// line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 89/100 | Updated: 2026-10-24
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
const LABEL_MIN_GAP_PX = 25;
const LABEL_FONT_PX = 19;
const ENERGY_TICK_STEP = 10;
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
  "₉": "9",
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
const ENERGY_CEILING = 90; // top of the plotted E/B range

// Tanabe-Sugano d³ energy matrices (Tanabe & Sugano 1954) in the strong-field
// basis t₂g³⁻ⁿ egⁿ: E = b·B + c·C + n·Δo, in units of B; A is dropped
const R2 = Math.SQRT2;
const R3 = Math.sqrt(3);
const BLOCKS: Array<{
  symbol: string;
  roots: string[];
  b: number[][];
  c: number[][];
  eg: number[];
}> = [
  { symbol: "⁴A₂g", roots: [""], b: [[0]], c: [[0]], eg: [0] },
  { symbol: "⁴T₂g", roots: [""], b: [[0]], c: [[0]], eg: [1] },
  {
    symbol: "⁴T₁g",
    roots: ["(F)", "(P)"],
    b: [
      [12, 6],
      [6, 3],
    ],
    c: [
      [0, 0],
      [0, 0],
    ],
    eg: [1, 2],
  },
  { symbol: "²A₁g", roots: [""], b: [[4]], c: [[3]], eg: [1] },
  { symbol: "²A₂g", roots: [""], b: [[24]], c: [[3]], eg: [1] },
  {
    symbol: "²Eg",
    roots: ["(1)", "(2)", "(3)", "(4)"],
    b: [
      [9, -3 * R2, -6 * R2, 0],
      [-3 * R2, 14, 10, -2 * R3],
      [-6 * R2, 10, 23, -2 * R3],
      [0, -2 * R3, -2 * R3, 7],
    ],
    c: [
      [3, 0, 0, 0],
      [0, 3, 0, 0],
      [0, 0, 6, -R3],
      [0, 0, -R3, 4],
    ],
    eg: [0, 1, 1, 3],
  },
  {
    symbol: "²T₁g",
    roots: ["(1)", "(2)", "(3)", "(4)", "(5)"],
    b: [
      [9, -3, 3, -2 * R3, 0],
      [-3, 9, -3, R3, -3],
      [3, -3, 15, -3 * R3, 3],
      [-2 * R3, R3, -3 * R3, 13, -2 * R3],
      [0, -3, 3, -2 * R3, 9],
    ],
    c: [
      [3, 0, 0, 0, 0],
      [0, 3, 0, 0, 0],
      [0, 0, 3, 0, 0],
      [0, 0, 0, 3, 0],
      [0, 0, 0, 0, 3],
    ],
    eg: [0, 1, 1, 2, 2],
  },
  {
    symbol: "²T₂g",
    roots: ["(1)", "(2)", "(3)", "(4)", "(5)"],
    b: [
      [15, -5 * R3, -3 * R3, 2, 4],
      [-5 * R3, 19, 3, R3, -R3],
      [-3 * R3, 3, 9, -3 * R3, -3 * R3],
      [2, R3, -3 * R3, 13, 10],
      [4, -R3, -3 * R3, 10, 21],
    ],
    c: [
      [5, 0, 0, 0, 2],
      [0, 3, 0, 0, 0],
      [0, 0, 3, 0, 0],
      [0, 0, 0, 3, 0],
      [2, 0, 0, 0, 5],
    ],
    eg: [0, 1, 1, 2, 2],
  },
];

// Cyclic Jacobi rotations: eigenvalues of a real symmetric matrix, ascending
function symmetricEigenvalues(matrix: number[][]): number[] {
  const a = matrix.map((row) => [...row]);
  const n = a.length;
  for (let sweep = 0; sweep < 50; sweep += 1) {
    let offDiagonal = 0;
    for (let p = 0; p < n; p += 1) {
      for (let q = p + 1; q < n; q += 1) offDiagonal += a[p][q] ** 2;
    }
    if (offDiagonal < 1e-20) break;
    for (let p = 0; p < n; p += 1) {
      for (let q = p + 1; q < n; q += 1) {
        if (Math.abs(a[p][q]) < 1e-15) continue;
        const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const tan =
          Math.sign(theta || 1) / (Math.abs(theta) + Math.hypot(theta, 1));
        const cos = 1 / Math.hypot(tan, 1);
        const sin = tan * cos;
        for (let k = 0; k < n; k += 1) {
          const akp = a[k][p];
          const akq = a[k][q];
          a[k][p] = cos * akp - sin * akq;
          a[k][q] = sin * akp + cos * akq;
        }
        for (let k = 0; k < n; k += 1) {
          const apk = a[p][k];
          const aqk = a[q][k];
          a[p][k] = cos * apk - sin * aqk;
          a[q][k] = sin * apk + cos * aqk;
        }
      }
    }
  }
  return a.map((row, i) => row[i]).sort((x, y) => x - y);
}

const N_STEPS = 320;
const data: Array<Record<string, number | string | boolean>> = [];
for (let step = 0; step <= N_STEPS; step += 1) {
  const d = (step * 40) / N_STEPS;
  const levels = BLOCKS.flatMap((block) =>
    symmetricEigenvalues(
      block.b.map((row, i) =>
        row.map(
          (bij, j) =>
            bij + C_OVER_B * block.c[i][j] + (i === j ? block.eg[i] * d : 0),
        ),
      ),
    ).map((energy, k) => ({
      term: `${block.symbol}${block.roots[k]}`,
      multiplicity: block.symbol[0],
      energy,
    })),
  );
  const ground = levels.reduce((lo, lvl) => (lvl.energy < lo.energy ? lvl : lo));
  for (const lvl of levels) {
    const energy = lvl.energy - ground.energy;
    if (energy > ENERGY_CEILING) continue;
    data.push({
      [DELTA_OVER_B]: d,
      [TERM]: lvl.term,
      [ENERGY_OVER_B]: energy,
      [SPIN_ALLOWED]: lvl.multiplicity === ground.multiplicity,
    });
  }
}

// Plot: reads only data and the constants above
interface TypesetRun {
  text: string;
  dyFactor: number;
  fontScale: number;
}

const subtitleText = `${CONFIG} in an octahedral field · C/B = ${C_OVER_B} · colour marks symmetry · spin-allowed terms solid, spin-forbidden dashed`;
const complexMarkerText = `${EXAMPLE_COMPLEX} · Δo / B = ${EXAMPLE_FIELD.toFixed(1)}`;

const stringsToParse = new Set<string>([
  DELTA_OVER_B,
  subtitleText,
  complexMarkerText,
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

// Colour by Mulliken symmetry: the key without multiplicity and root suffix
const symmetryOf = (termName: string) =>
  termName.replace(/\(.*\)$/, "").replace(/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+/, "");
const symmetries: string[] = [];
for (const termName of terms) {
  if (!symmetries.includes(symmetryOf(termName))) {
    symmetries.push(symmetryOf(termName));
  }
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
const energyMax =
  Math.ceil(Math.max(...allEnergies) / ENERGY_TICK_STEP) * ENERGY_TICK_STEP;

const termSeries = terms.map((termName, i) => {
  const rows = data
    .filter((r) => String(r[TERM]) === termName)
    .sort((a, b) => Number(a[DELTA_OVER_B]) - Number(b[DELTA_OVER_B]));
  const spinAllowed = Boolean(rows[0][SPIN_ALLOWED]);
  const points = rows.map((r) => ({
    x: Number(r[DELTA_OVER_B]),
    y: Number(r[ENERGY_OVER_B]),
  }));
  const energyAt = new Map(points.map((p) => [p.x, p.y]));
  const yValues = fieldStrengths.map((f) => energyAt.get(f) ?? null);
  const lastPoint = points[points.length - 1];
  let exampleEnergy: number | null = null;
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
    color: t.palette[symmetries.indexOf(symmetryOf(termName))],
    spinAllowed,
    yValues,
    lastPoint,
    leavesTop: lastPoint.x < fieldMax,
    exampleEnergy,
  };
});

// The two lowest spin-allowed excited terms at the example complex's field
const bandTransitions = termSeries
  .filter((s) => s.spinAllowed && s.exampleEnergy !== null && s.lastPoint.y > 0)
  .sort((a, b) => Number(a.exampleEnergy) - Number(b.exampleEnergy))
  .slice(0, 2)
  .map((s, idx) => ({
    id: `nu-${idx + 1}`,
    runs: parsedRunsByText[idx === 0 ? "ν₁" : "ν₂"],
    targetEnergy: Number(s.exampleEnergy),
    dx: idx === 0 ? -12 : 12,
  }));

function TypesetText({
  runs,
  fontSize,
}: {
  runs: TypesetRun[];
  fontSize: number;
}) {
  return (
    <>
      {runs.map((r, idx) => (
        <tspan key={idx} dy={r.dyFactor * fontSize} fontSize={fontSize * r.fontScale}>
          {r.text}
        </tspan>
      ))}
    </>
  );
}

function TanabeSuganoLayer() {
  const { left, top, width, height } = useDrawingArea();
  const xScale = useXScale("field") as (v: number) => number;
  const yScale = useYScale("energy") as (v: number) => number;
  const labelWidth = (s: (typeof termSeries)[number]) =>
    s.runs.reduce(
      (sum, r) => sum + r.text.length * LABEL_FONT_PX * r.fontScale * 0.62,
      0,
    );

  // Right-edge labels for curves that reach Δo/B max, stacked top to bottom
  let lowestY = -Infinity;
  const edgeLabels = termSeries
    .filter((s) => !s.leavesTop)
    .map((s) => ({ ...s, rawY: yScale(s.lastPoint.y) }))
    .sort((a, b) => a.rawY - b.rawY)
    .map((s) => {
      const placedY = Math.max(s.rawY, lowestY + LABEL_MIN_GAP_PX);
      lowestY = placedY;
      return { ...s, placedY };
    });

  // Top-edge labels for curves that leave through the ceiling, left to right
  let rightmostX = -Infinity;
  const topLabels = termSeries
    .filter((s) => s.leavesTop)
    .map((s) => ({ ...s, rawX: xScale(s.lastPoint.x), w: labelWidth(s) }))
    .sort((a, b) => a.rawX - b.rawX)
    .map((s) => {
      const placedX = Math.max(s.rawX - s.w / 2, rightmostX + 10);
      rightmostX = placedX + s.w;
      return { ...s, placedX };
    });

  const exX = xScale(EXAMPLE_FIELD);
  const yZero = yScale(0);
  const edgeX = left + width;

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
              <TypesetText runs={b.runs} fontSize={17} />
            </text>
          </g>
        );
      })}

      {/* Example complex label in the open corner right of its marker */}
      <text
        x={exX + 26}
        y={yZero - 36}
        fill={t.inkSoft}
        fontSize={15}
      >
        <TypesetText runs={parsedRunsByText[complexMarkerText]} fontSize={15} />
      </text>

      {/* Right-margin term symbols with true super/subscripts and leaders */}
      {edgeLabels.map((lbl) => (
        <g key={lbl.id}>
          <polyline
            points={`${edgeX + 2},${lbl.rawY} ${edgeX + 8},${lbl.rawY} ${edgeX + 16},${lbl.placedY}`}
            fill="none"
            stroke={lbl.color}
            strokeWidth={1.2}
          />
          <text
            x={edgeX + 20}
            y={lbl.placedY}
            fill={lbl.color}
            fontSize={LABEL_FONT_PX}
            fontWeight={lbl.spinAllowed ? 700 : 500}
            dominantBaseline="middle"
          >
            <TypesetText runs={lbl.runs} fontSize={LABEL_FONT_PX} />
          </text>
        </g>
      ))}

      {/* Term symbols above the ceiling where their curve leaves the plot */}
      {topLabels.map((lbl) => (
        <g key={lbl.id}>
          <line
            x1={lbl.rawX}
            y1={top - 2}
            x2={lbl.placedX + lbl.w / 2}
            y2={top - 12}
            stroke={lbl.color}
            strokeWidth={1.2}
          />
          <text
            x={lbl.placedX}
            y={top - 20}
            fill={lbl.color}
            fontSize={LABEL_FONT_PX}
            fontWeight={lbl.spinAllowed ? 700 : 500}
          >
            <TypesetText runs={lbl.runs} fontSize={LABEL_FONT_PX} />
          </text>
        </g>
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
        <TypesetText runs={parsedRunsByText[subtitleText]} fontSize={15} />
      </text>
      <text
        x={left + width / 2}
        y={HEIGHT - 24}
        fill={t.ink}
        fontSize={17}
        textAnchor="middle"
      >
        <TypesetText runs={parsedRunsByText[DELTA_OVER_B]} fontSize={17} />
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
        margin={{ top: 136, right: 150, bottom: 48, left: 44 }}
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
            tickNumber: energyMax / ENERGY_TICK_STEP,
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
              : { strokeWidth: 2.2, strokeDasharray: "11 7" },
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
