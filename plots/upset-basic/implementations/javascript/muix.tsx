// anyplot.ai
// upset-basic: UpSet Plot for Multi-Set Intersection Analysis
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-09
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_COLUMNS = 15; // the largest intersections shown; smaller ones are left out
const TITLE = "upset-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEFT_W = 340; // px column for the set names and set-size bars
const TOP_H = 380; // px row for the intersection-size bars
const SET_AXIS_W = 150; // px band for the set names
const COUNT_AXIS_W = 84; // px band for the intersection-count axis
const SIZE_AXIS_H = 64; // px band for the set-size axis
const PLOT_MARGIN = { top: 12, right: 36 };

// Columns: set these to your data's column names
const GENE = "Gene"; // role: element
const ASSAY = "Assay"; // role: sets

// Data: replace this block with your own records, one object per row
// 2,000 genes screened by six genomic assays, one row per gene and assay that
// flags it. Each assay flags a gene with its own hit rate; a gene no assay
// flags is assigned to the first one, so every gene sits in at least one set.
const data = (() => {
  let seed = 42;
  const nextRandom = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const assays = [
    ["RNA-seq", 0.38],
    ["ChIP-seq", 0.29],
    ["ATAC-seq", 0.24],
    ["Proteomics", 0.19],
    ["Methylation", 0.14],
    ["CRISPR screen", 0.1],
  ];
  const rows = [];
  for (let i = 0; i < 2000; i += 1) {
    const gene = `G${String(i + 1).padStart(4, "0")}`;
    const hits = assays.filter(([, rate]) => nextRandom() < rate).map(([name]) => name);
    (hits.length > 0 ? hits : [assays[0][0]]).forEach((assay) => rows.push({ [GENE]: gene, [ASSAY]: assay }));
  }
  return rows;
})();

// Plot: reads only data and the constants above
const membership = new Map();
data.forEach((d) => {
  if (d[GENE] == null || d[ASSAY] == null) return;
  if (!membership.has(d[GENE])) membership.set(d[GENE], new Set());
  membership.get(d[GENE]).add(d[ASSAY]);
});

// Matrix rows: the sets, largest first (ties keep their order of appearance)
const appearance = [...new Set(data.map((d) => d[ASSAY]).filter((s) => s != null))];
const sizeOf = new Map(appearance.map((s) => [s, [...membership.values()].filter((m) => m.has(s)).length]));
const sets = [...appearance].sort((a, b) => sizeOf.get(b) - sizeOf.get(a));

// Matrix columns: each exact combination of sets, largest first, then by degree
const comboCounts = new Map();
membership.forEach((m) => {
  const key = sets.filter((s) => m.has(s)).join("\n");
  comboCounts.set(key, (comboCounts.get(key) ?? 0) + 1);
});
const intersections = [...comboCounts.entries()]
  .map(([key, size]) => ({ key, members: key.split("\n"), size }))
  .sort((a, b) => b.size - a.size || a.members.length - b.members.length)
  .slice(0, MAX_COLUMNS);
const columnIds = intersections.map((d) => d.key);

// Degree (sets per intersection) is ordered, so it takes steps of the sequential
// ramp, spread over the degrees the shown intersections have
const degreesShown = [...new Set(intersections.map((d) => d.members.length))].sort((a, b) => a - b);
const [seqA, seqB] = [t.seq[0], t.seq[1]].map((hex) => [16, 8, 0].map((s) => (parseInt(hex.slice(1), 16) >> s) & 255));
const degreeColor = new Map(
  degreesShown.map((k, i) => {
    const f = degreesShown.length > 1 ? i / (degreesShown.length - 1) : 0;
    return [k, `rgb(${seqA.map((v, c) => Math.round(v + (seqB[c] - v) * f)).join(",")})`];
  }),
);

const SUBTITLE = `${membership.size.toLocaleString("en-US")} ${GENE.toLowerCase()}s across ${sets.length} ${ASSAY.toLowerCase()}s · the ${intersections.length} largest of ${comboCounts.size} intersections, sorted by size`;
const COUNT_LABEL = `${GENE}s per intersection`;
const SIZE_LABEL = `${GENE}s per ${ASSAY.toLowerCase()}`;
const MATRIX_H = window.ANYPLOT_SIZE.height - TITLE_H - TOP_H;

// The dot matrix shares the band axes of both bar charts, so every column sits
// under its intersection bar and every row beside its set-size bar.
function DotMatrix() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, width } = useDrawingArea();
  const colCenter = (key) => xScale(key) + xScale.bandwidth() / 2;
  const rowCenter = (set) => yScale(set) + yScale.bandwidth() / 2;
  const rowStep = yScale.step();

  return (
    <g>
      {sets.map((set, j) =>
        j % 2 === 1 ? (
          <rect key={`band-${set}`} x={left} y={rowCenter(set) - rowStep / 2} width={width} height={rowStep} fill={t.grid} opacity={0.45} />
        ) : null,
      )}
      {intersections.map((inter) => {
        const cx = colCenter(inter.key);
        const color = degreeColor.get(inter.members.length);
        const ys = inter.members.map((s) => rowCenter(s));
        return (
          <g key={`col-${inter.key}`}>
            {sets.map((set) => (
              <circle key={`off-${set}`} cx={cx} cy={rowCenter(set)} r={6} fill={t.inkSoft} opacity={0.28} />
            ))}
            {inter.members.length > 1 && (
              <line x1={cx} x2={cx} y1={Math.min(...ys)} y2={Math.max(...ys)} stroke={color} strokeWidth={4} />
            )}
            {inter.members.map((set) => (
              <circle key={`on-${set}`} cx={cx} cy={rowCenter(set)} r={10} fill={color} />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const matrixW = width - LEFT_W;
  const axisStyle = {
    "& .MuiChartsAxis-line": { stroke: t.inkSoft },
    "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
    "& .MuiChartsGrid-line": { stroke: t.grid },
  };

  return (
    <div style={{ width, height, background: t.pageBg }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: `${LEFT_W}px ${matrixW}px`, gridTemplateRows: `${TOP_H}px ${MATRIX_H}px` }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end", padding: "0 0 28px 36px" }}>
          <div style={{ fontSize: 15, color: t.ink, marginBottom: 10 }}>Intersection degree</div>
          <div style={{ display: "flex", gap: 14 }}>
            {degreesShown.map((k) => (
              <div key={`deg-${k}`} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 16, height: 16, borderRadius: 8, background: degreeColor.get(k), display: "inline-block" }} />
                <span style={{ fontSize: 15, color: t.inkSoft }}>{k}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ gridColumn: 2, gridRow: 1 }}>
        <BarChart
          width={matrixW}
          height={TOP_H}
          skipAnimation
          hideLegend
          grid={{ horizontal: true }}
          margin={{ top: 24, right: PLOT_MARGIN.right, bottom: 4, left: 0 }}
          series={[{ id: "intersection-size", data: intersections.map((d) => d.size), label: COUNT_LABEL, color: t.palette[0] }]}
          xAxis={[{ id: "columns", scaleType: "band", data: columnIds, disableTicks: true, height: 4, tickLabelStyle: { display: "none" } }]}
          yAxis={[
            {
              id: "count",
              min: 0,
              width: COUNT_AXIS_W,
              label: COUNT_LABEL,
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              labelStyle: { fontSize: 15, fill: t.ink },
            },
          ]}
          sx={axisStyle}
        />
        </div>

        <div style={{ gridColumn: 1, gridRow: 2 }}>
        <BarChart
          layout="horizontal"
          width={LEFT_W}
          height={MATRIX_H}
          skipAnimation
          hideLegend
          grid={{ vertical: true }}
          margin={{ top: PLOT_MARGIN.top, right: 20, bottom: 8, left: 24 }}
          series={[{ id: "set-size", data: sets.map((s) => sizeOf.get(s)), label: SIZE_LABEL, color: t.palette[0] }]}
          yAxis={[{ id: "sets", scaleType: "band", data: sets, width: SET_AXIS_W, disableTicks: true, tickLabelStyle: { fontSize: 15, fill: t.ink } }]}
          xAxis={[
            {
              id: "size",
              min: 0,
              height: SIZE_AXIS_H,
              tickNumber: 3,
              label: SIZE_LABEL,
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              labelStyle: { fontSize: 15, fill: t.ink },
            },
          ]}
          sx={axisStyle}
        />
        </div>

        <div style={{ gridColumn: 2, gridRow: 2 }}>
        <ChartsContainer
          width={matrixW}
          height={MATRIX_H}
          series={[]}
          skipAnimation
          margin={{ top: PLOT_MARGIN.top, right: PLOT_MARGIN.right, bottom: 8 + SIZE_AXIS_H, left: COUNT_AXIS_W }}
          xAxis={[{ id: "columns", scaleType: "band", data: columnIds, position: "none" }]}
          yAxis={[{ id: "sets", scaleType: "band", data: sets, position: "none" }]}
        >
          <DotMatrix />
        </ChartsContainer>
        </div>
      </div>
    </div>
  );
}
