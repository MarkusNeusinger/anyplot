// anyplot.ai
// chord-basic: Basic Chord Diagram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 94/100 | Created: 2026-06-17
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADER_H = 98;
const FOOTER_H = 44;
const PAD_RAD = 0.05;
const R_OUT_SHARE = 0.39;
const R_IN_SHARE = 0.358;
const R_LABEL_SHARE = 0.422;

// Columns: set these to your data's column names
const SOURCE = "Origin region"; // role: source
const TARGET = "Destination region"; // role: target
const VALUE = "Annual flow (M)"; // role: value

// Data: replace this block with your own records, one object per row
const data = [
  { [SOURCE]: "Asia", [TARGET]: "Africa", [VALUE]: 1.2 },
  { [SOURCE]: "Asia", [TARGET]: "Europe", [VALUE]: 6.5 },
  { [SOURCE]: "Asia", [TARGET]: "N. America", [VALUE]: 7.8 },
  { [SOURCE]: "Asia", [TARGET]: "S. America", [VALUE]: 0.6 },
  { [SOURCE]: "Asia", [TARGET]: "Oceania", [VALUE]: 1.1 },
  { [SOURCE]: "Africa", [TARGET]: "Asia", [VALUE]: 0.9 },
  { [SOURCE]: "Africa", [TARGET]: "Europe", [VALUE]: 5.4 },
  { [SOURCE]: "Africa", [TARGET]: "N. America", [VALUE]: 1.3 },
  { [SOURCE]: "Africa", [TARGET]: "S. America", [VALUE]: 0.3 },
  { [SOURCE]: "Africa", [TARGET]: "Oceania", [VALUE]: 0.2 },
  { [SOURCE]: "Europe", [TARGET]: "Asia", [VALUE]: 2.1 },
  { [SOURCE]: "Europe", [TARGET]: "Africa", [VALUE]: 1.7 },
  { [SOURCE]: "Europe", [TARGET]: "N. America", [VALUE]: 4.2 },
  { [SOURCE]: "Europe", [TARGET]: "S. America", [VALUE]: 0.7 },
  { [SOURCE]: "Europe", [TARGET]: "Oceania", [VALUE]: 0.9 },
  { [SOURCE]: "N. America", [TARGET]: "Asia", [VALUE]: 1.4 },
  { [SOURCE]: "N. America", [TARGET]: "Africa", [VALUE]: 0.5 },
  { [SOURCE]: "N. America", [TARGET]: "Europe", [VALUE]: 2.8 },
  { [SOURCE]: "N. America", [TARGET]: "S. America", [VALUE]: 1.6 },
  { [SOURCE]: "N. America", [TARGET]: "Oceania", [VALUE]: 0.4 },
  { [SOURCE]: "S. America", [TARGET]: "Asia", [VALUE]: 0.4 },
  { [SOURCE]: "S. America", [TARGET]: "Africa", [VALUE]: 0.2 },
  { [SOURCE]: "S. America", [TARGET]: "Europe", [VALUE]: 2.3 },
  { [SOURCE]: "S. America", [TARGET]: "N. America", [VALUE]: 3.1 },
  { [SOURCE]: "S. America", [TARGET]: "Oceania", [VALUE]: 0.3 },
  { [SOURCE]: "Oceania", [TARGET]: "Asia", [VALUE]: 0.7 },
  { [SOURCE]: "Oceania", [TARGET]: "Africa", [VALUE]: 0.1 },
  { [SOURCE]: "Oceania", [TARGET]: "Europe", [VALUE]: 0.6 },
  { [SOURCE]: "Oceania", [TARGET]: "N. America", [VALUE]: 0.5 },
  { [SOURCE]: "Oceania", [TARGET]: "S. America", [VALUE]: 0.2 },
];

// Plot: reads only data and the constants above
const entities = Array.from(
  new Set(data.flatMap((d) => [String(d[SOURCE]), String(d[TARGET])])),
);
const nEntities = entities.length;
const entityIndex = new Map(entities.map((name, idx) => [name, idx]));

const unitMatch = VALUE.match(/\(([^)]+)\)/);
const unitSuffix = unitMatch ? unitMatch[1] : "";

const matrix = Array.from({ length: nEntities }, () =>
  Array.from({ length: nEntities }, () => 0),
);
for (const row of data) {
  const sIdx = entityIndex.get(String(row[SOURCE]));
  const tIdx = entityIndex.get(String(row[TARGET]));
  if (sIdx !== undefined && tIdx !== undefined && sIdx !== tIdx) {
    matrix[sIdx][tIdx] += Number(row[VALUE]);
  }
}

const groupTotal = matrix.map((row) => row.reduce((a, b) => a + b, 0));
const grandTotal = groupTotal.reduce((a, b) => a + b, 0) || 1;
const availRad = 2 * Math.PI - PAD_RAD * nEntities;

let curAngle = -Math.PI / 2 + PAD_RAD / 2;
const groups = entities.map((name, i) => {
  const span = (groupTotal[i] / grandTotal) * availRad;
  const gStart = curAngle;
  const gEnd = curAngle + span;
  let subCur = gStart;
  const subs = entities.map((_, j) => {
    const subSpan =
      groupTotal[i] > 0 ? (matrix[i][j] / groupTotal[i]) * span : 0;
    const range: [number, number] = [subCur, subCur + subSpan];
    subCur += subSpan;
    return range;
  });
  curAngle = gEnd + PAD_RAD;
  return {
    i,
    name,
    color: t.palette[i],
    total: groupTotal[i],
    gStart,
    gEnd,
    mid: (gStart + gEnd) / 2,
    subs,
  };
});

const ribbons: {
  id: string;
  i: number;
  j: number;
  a: number;
  b: number;
  color: string;
  mag: number;
  sI: [number, number];
  sJ: [number, number];
}[] = [];

for (let i = 0; i < nEntities; i += 1) {
  for (let j = 0; j < i; j += 1) {
    const a = matrix[i][j];
    const b = matrix[j][i];
    if (a + b <= 0) continue;
    const dom = a >= b ? i : j;
    ribbons.push({
      id: `${entities[i]}-${entities[j]}`,
      i,
      j,
      a,
      b,
      color: groups[dom].color,
      mag: a + b,
      sI: groups[i].subs[j],
      sJ: groups[j].subs[i],
    });
  }
}
ribbons.sort((x, y) => y.mag - x.mag);

const TITLE = "chord-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${nEntities} ${SOURCE.replace(/^Origin\s+/i, "")}s · ${ribbons.length} bidirectional pairs · Total flow ${grandTotal.toFixed(1)}${unitSuffix}`;

function ChordDiagramLayer() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  const size = Math.min(width, height);
  const rOut = size * R_OUT_SHARE;
  const rIn = size * R_IN_SHARE;
  const rLabel = size * R_LABEL_SHARE;

  return (
    <g>
      {ribbons.map((rb) => {
        const stepsA = Math.max(
          2,
          Math.ceil(Math.abs(rb.sI[1] - rb.sI[0]) / 0.04),
        );
        const ptsA: string[] = [];
        for (let k = 0; k <= stepsA; k += 1) {
          const ang = rb.sI[0] + (rb.sI[1] - rb.sI[0]) * (k / stepsA);
          ptsA.push(
            `${(cx + rIn * Math.cos(ang)).toFixed(1)} ${(cy + rIn * Math.sin(ang)).toFixed(1)}`,
          );
        }

        const stepsB = Math.max(
          2,
          Math.ceil(Math.abs(rb.sJ[1] - rb.sJ[0]) / 0.04),
        );
        const ptsB: string[] = [];
        for (let k = 0; k <= stepsB; k += 1) {
          const ang = rb.sJ[0] + (rb.sJ[1] - rb.sJ[0]) * (k / stepsB);
          ptsB.push(
            `${(cx + rIn * Math.cos(ang)).toFixed(1)} ${(cy + rIn * Math.sin(ang)).toFixed(1)}`,
          );
        }

        const d =
          `M ${ptsA[0]}` +
          ptsA
            .filter((_, idx) => idx > 0)
            .map((p) => ` L ${p}`)
            .join("") +
          ` Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ptsB[0]}` +
          ptsB
            .filter((_, idx) => idx > 0)
            .map((p) => ` L ${p}`)
            .join("") +
          ` Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ptsA[0]} Z`;

        return (
          <path
            key={rb.id}
            d={d}
            fill={rb.color}
            fillOpacity={0.62}
            stroke={t.pageBg}
            strokeWidth={0.9}
            strokeOpacity={0.55}
          >
            <title>
              {`${entities[rb.i]} → ${entities[rb.j]}: ${rb.a.toFixed(1)}${unitSuffix}\n${entities[rb.j]} → ${entities[rb.i]}: ${rb.b.toFixed(1)}${unitSuffix}`}
            </title>
          </path>
        );
      })}

      {groups.map((g) => {
        const steps = Math.max(
          2,
          Math.ceil(Math.abs(g.gEnd - g.gStart) / 0.04),
        );
        const outerPts: string[] = [];
        const innerPts: string[] = [];
        for (let k = 0; k <= steps; k += 1) {
          const angOut = g.gStart + (g.gEnd - g.gStart) * (k / steps);
          outerPts.push(
            `${(cx + rOut * Math.cos(angOut)).toFixed(1)} ${(cy + rOut * Math.sin(angOut)).toFixed(1)}`,
          );
          const angIn = g.gEnd + (g.gStart - g.gEnd) * (k / steps);
          innerPts.push(
            `${(cx + rIn * Math.cos(angIn)).toFixed(1)} ${(cy + rIn * Math.sin(angIn)).toFixed(1)}`,
          );
        }
        const d =
          `M ${outerPts[0]}` +
          outerPts
            .filter((_, idx) => idx > 0)
            .map((p) => ` L ${p}`)
            .join("") +
          innerPts.map((p) => ` L ${p}`).join("") +
          " Z";

        const cosMid = Math.cos(g.mid);
        const sinMid = Math.sin(g.mid);
        const lx = cx + rLabel * cosMid + (cosMid > 0.33 ? 8 : cosMid < -0.33 ? -8 : 0);
        const ly = cy + rLabel * sinMid;
        const anchor =
          cosMid > 0.33 ? "start" : cosMid < -0.33 ? "end" : "middle";

        return (
          <g key={g.name}>
            <path
              d={d}
              fill={g.color}
              stroke={t.pageBg}
              strokeWidth={1.5}
            >
              <title>{`${g.name} · outbound ${g.total.toFixed(1)}${unitSuffix}`}</title>
            </path>
            <text
              x={lx}
              y={ly - 8}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={19}
              fontWeight={700}
              fill={g.color}
            >
              {g.name}
            </text>
            <text
              x={lx}
              y={ly + 14}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {`${g.total.toFixed(1)}${unitSuffix} out`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H - FOOTER_H;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          paddingTop: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
        series={[]}
        skipAnimation
      >
        <ChordDiagramLayer />
      </ChartsContainer>

      <div
        style={{
          height: FOOTER_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        Each chord carries both directions; arc length is proportional to total outbound {VALUE.toLowerCase()}
      </div>
    </div>
  );
}
