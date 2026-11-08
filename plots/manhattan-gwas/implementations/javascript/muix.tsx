// anyplot.ai
// manhattan-gwas: Manhattan Plot for GWAS
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GENOME_WIDE_P = 5e-8; // genome-wide significance threshold
const SUGGESTIVE_P = 1e-5; // suggestive threshold
const Y_PAD_SHARE = 0.08; // share of the highest -log10 p added above it

// Columns: set these to your data's column names
const CHROMOSOME = "Chromosome"; // role: chromosome
const POSITION = "Position (bp)"; // role: position
const P_VALUE = "P-value"; // role: p_value
const SNP = "SNP"; // role: snp_id

// Data: replace this block with your own records, one object per row
// Simulated GWAS on the 22 autosomes: null p-values everywhere plus three associated loci (chr 6, 11, 17).
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
  const lengthsMb = [248, 242, 198, 190, 181, 170, 159, 145, 138, 133, 135, 133, 114, 107, 101, 90, 83, 80, 58, 63, 46, 50];
  const peaks = { 6: 14.5, 11: 9.6, 17: 11.3 };
  const rows = [];
  const push = (chrom, position, negLogP) =>
    rows.push({
      [CHROMOSOME]: String(chrom),
      [POSITION]: Math.round(position),
      [P_VALUE]: Number((10 ** -negLogP).toPrecision(3)),
      [SNP]: `rs${2000000 + rows.length * 7919}`,
    });
  lengthsMb.forEach((mb, i) => {
    const chrom = i + 1;
    const length = mb * 1e6;
    for (let k = 0; k < Math.round(mb / 3); k += 1) push(chrom, rand() * length, -Math.log(rand()) / Math.LN10);
    if (peaks[chrom]) {
      const peakPos = length * (0.3 + rand() * 0.4);
      const spread = length * 0.08;
      for (let k = 0; k < 45; k += 1) {
        const position = Math.min(Math.max(peakPos + (rand() + rand() + rand() - 1.5) * spread, 1), length);
        // Association falls off with distance from the causal variant, so each locus tapers into the null band
        const distance = (position - peakPos) / (spread / 2);
        push(chrom, position, -Math.log(rand()) / Math.LN10 + peaks[chrom] * Math.exp(-distance * distance));
      }
    }
  });
  return rows;
})();

// Plot: reads only data and the constants above
// Chromosomes are laid end to end in their order of appearance, each as wide as its largest position.
const rows = data.filter((d) => d[P_VALUE] != null && d[P_VALUE] > 0);
const chromosomes = [...new Set(rows.map((d) => d[CHROMOSOME]))];
const chromIndex = new Map(chromosomes.map((c, i) => [c, i]));
const chromSpan = chromosomes.map((c) => Math.max(...rows.filter((d) => d[CHROMOSOME] === c).map((d) => d[POSITION])));
const offsets = chromSpan.map((_, i) => chromSpan.slice(0, i).reduce((sum, v) => sum + v, 0));
const genomeLength = offsets[offsets.length - 1] + chromSpan[chromSpan.length - 1];
const centers = chromosomes.map((_, i) => offsets[i] + chromSpan[i] / 2);
const labelAtCenter = new Map(centers.map((x, i) => [x, chromosomes[i]]));

const genomeWide = -Math.log10(GENOME_WIDE_P);
const suggestive = -Math.log10(SUGGESTIVE_P);
const points = rows.map((d, k) => {
  const i = chromIndex.get(d[CHROMOSOME]);
  return { id: k, x: offsets[i] + d[POSITION], y: -Math.log10(d[P_VALUE]), chrom: i, snp: d[SNP], p: d[P_VALUE] };
});
// Adjacent chromosomes alternate between two colours; variants past genome-wide significance take a third
const groups = [
  { id: "alternate-a", color: t.palette[0], size: 3, points: points.filter((p) => p.y < genomeWide && p.chrom % 2 === 0) },
  { id: "alternate-b", color: t.palette[1], size: 3, points: points.filter((p) => p.y < genomeWide && p.chrom % 2 === 1) },
  { id: "significant", color: t.palette[2], size: 5, points: points.filter((p) => p.y >= genomeWide) },
];
const significant = groups[2].points;
const leads = chromosomes
  .map((_, i) => significant.filter((p) => p.chrom === i).sort((a, b) => b.y - a.y)[0])
  .filter(Boolean);
const yMax = Math.max(genomeWide, ...points.map((p) => p.y)) * (1 + Y_PAD_SHARE);

const formatP = (p: number) => p.toExponential(1);

const TITLE = "manhattan-gwas · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} variants on ${chromosomes.length} chromosomes · ${significant.length} past genome-wide significance, highlighted · lead ${SNP} labelled per chromosome`;
const HEADER_H = 80;

function LeadLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {leads.map((p) => (
        <text key={p.snp} x={xScale(p.x)} y={yScale(p.y) - 14} textAnchor="middle" fontSize={15} fontWeight={600} fill={t.ink}>
          {`${p.snp} · p = ${formatP(p.p)}`}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 112px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <ScatterChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        disableHitArea
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: genomeLength,
            tickInterval: centers,
            tickLabelMinGap: 2,
            valueFormatter: (v: number) => labelAtCenter.get(v) ?? "",
            label: CHROMOSOME,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: yMax,
            label: `−log₁₀(${P_VALUE})`,
            width: 72,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={groups.map((g) => ({
          id: g.id,
          color: g.color,
          markerSize: g.size,
          data: g.points.map((p) => ({ x: p.x, y: p.y, id: p.id })),
          valueFormatter: (_v, { dataIndex }) =>
            `${g.points[dataIndex].snp} · ${CHROMOSOME} ${chromosomes[g.points[dataIndex].chrom]} · p = ${formatP(g.points[dataIndex].p)}`,
        }))}
        sx={{
          '& [data-series="alternate-a"] .MuiScatterChart-marker, & [data-series="alternate-b"] .MuiScatterChart-marker': {
            fillOpacity: 0.75,
          },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsReferenceLine
          y={suggestive}
          label={`Suggestive, p < ${formatP(SUGGESTIVE_P)}`}
          labelAlign="end"
          spacing={{ x: 8, y: 8 }}
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "3 5", strokeWidth: 1.5 }}
        />
        <ChartsReferenceLine
          y={genomeWide}
          label={`Genome-wide significance, p < ${formatP(GENOME_WIDE_P)}`}
          labelAlign="end"
          spacing={{ x: 8, y: 8 }}
          labelStyle={{ fontSize: 15, fill: t.ink }}
          lineStyle={{ stroke: t.ink, strokeDasharray: "9 6", strokeWidth: 2 }}
        />
        <LeadLabels />
      </ScatterChart>
    </div>
  );
}
