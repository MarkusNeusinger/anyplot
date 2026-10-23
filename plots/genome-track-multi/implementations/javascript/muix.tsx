// anyplot.ai
// genome-track-multi: Genome Track Viewer
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-25
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_QUALITY = 60;
const GRID_STEP = 2000;
const TITLE_HEIGHT = 40;
const LEGEND_HEIGHT = 30;

// Columns: set these to your data's column names
const CHROMOSOME = "Chromosome region"; // role: chromosome
const START = "Position (bp)"; // role: start
const END = "End (bp)"; // role: end
const TRACK = "Track"; // role: track
const FEATURE_TYPE = "Feature type"; // role: feature_type
const VALUE = "Signal / quality"; // role: value
const STRAND = "Strand"; // role: strand
const LABEL = "Gene / feature label"; // role: label

// Data: replace this block with your own records, one object per row
const data = (() => {
  const region = "chr7:140,700,000-140,712,000";
  const genes = [
    {
      symbol: "GENE1",
      strand: "+",
      exons: [
        [400, 1100],
        [1900, 2300],
        [3100, 3900],
        [4400, 4900],
      ],
    },
    {
      symbol: "GENE2",
      strand: "-",
      exons: [
        [6600, 7200],
        [7900, 8300],
        [9000, 9600],
        [10100, 10700],
        [11100, 11600],
      ],
    },
  ];
  const regulatory = [
    { type: "Promoter", start: 100, end: 400 },
    { type: "Enhancer", start: 5100, end: 5500 },
    { type: "Promoter", start: 6300, end: 6600 },
    { type: "Enhancer", start: 11800, end: 12000 },
  ];
  const variants = [
    { pos: 550, type: "SNP", quality: 42 },
    { pos: 1050, type: "Indel", quality: 28 },
    { pos: 2150, type: "SNP", quality: 55 },
    { pos: 3400, type: "SNP", quality: 33 },
    { pos: 4650, type: "Indel", quality: 47 },
    { pos: 5800, type: "SNP", quality: 50 },
    { pos: 7000, type: "SNP", quality: 38 },
    { pos: 8900, type: "Indel", quality: 52 },
    { pos: 10300, type: "SNP", quality: 44 },
  ];

  const allExons = genes.flatMap((g) => g.exons);
  const insideExon = (offset) =>
    allExons.some(([s, e]) => offset >= s && offset <= e);

  let lcgSeed = 42;
  const nextRandom = () => {
    lcgSeed = (lcgSeed * 1103515245 + 12345) & 0x7fffffff;
    return lcgSeed / 0x7fffffff;
  };

  const rows = [];
  genes.forEach((gene) => {
    gene.exons.forEach(([s, e]) => {
      rows.push({
        [CHROMOSOME]: region,
        [START]: s,
        [END]: e,
        [TRACK]: "Genes",
        [FEATURE_TYPE]: "Exon",
        [VALUE]: null,
        [STRAND]: gene.strand,
        [LABEL]: gene.symbol,
      });
    });
  });
  regulatory.forEach((el) => {
    rows.push({
      [CHROMOSOME]: region,
      [START]: el.start,
      [END]: el.end,
      [TRACK]: "Regulatory",
      [FEATURE_TYPE]: el.type,
      [VALUE]: null,
      [STRAND]: null,
      [LABEL]: null,
    });
  });
  for (let offset = 0; offset <= 12000; offset += 200) {
    const baseline = 6 + nextRandom() * 5;
    const exonBoost = insideExon(offset) ? 45 + nextRandom() * 25 : 0;
    rows.push({
      [CHROMOSOME]: region,
      [START]: offset,
      [END]: offset,
      [TRACK]: "Coverage",
      [FEATURE_TYPE]: null,
      [VALUE]: baseline + exonBoost,
      [STRAND]: null,
      [LABEL]: null,
    });
  }
  variants.forEach((v) => {
    rows.push({
      [CHROMOSOME]: region,
      [START]: v.pos,
      [END]: v.pos,
      [TRACK]: "Variants",
      [FEATURE_TYPE]: v.type,
      [VALUE]: v.quality,
      [STRAND]: null,
      [LABEL]: null,
    });
  });
  return rows;
})();

// Plot: reads only data and the constants above
const regionLabel = data[0][CHROMOSOME];
const regionStart = Math.min(...data.map((d) => d[START]));
const regionEnd = Math.max(...data.map((d) => d[END]));
const tracks = [...new Set(data.map((d) => d[TRACK]))];
const discreteTypes = [
  ...new Set(
    data.map((d) => d[FEATURE_TYPE]).filter((ft) => ft !== null),
  ),
];
const featureColor = Object.fromEntries(
  discreteTypes.map((ft, i) => [ft, t.palette[i]]),
);

// Each track's renderer is chosen by a rule over its own rows, never by its
// position: genes carry a strand or a label; coverage rows have no feature type
// but a value; variants are points (start = end) with a feature type; any other
// track is drawn as regulatory intervals.
const present = (v) => v !== null && v !== undefined;
function trackKind(rows) {
  if (rows.some((d) => present(d[STRAND]) || present(d[LABEL]))) return "genes";
  if (
    rows.every((d) => !present(d[FEATURE_TYPE])) &&
    rows.some((d) => Number.isFinite(d[VALUE]))
  ) {
    return "coverage";
  }
  if (rows.every((d) => d[START] === d[END] && present(d[FEATURE_TYPE]))) {
    return "variants";
  }
  return "regulatory";
}
const trackBands = tracks.map((label) => {
  const rows = data.filter((d) => d[TRACK] === label);
  return { label, kind: trackKind(rows), rows };
});

const TITLE = "genome-track-multi · javascript · muix · anyplot.ai";

function GenesTrack({ xScale, top, height, rows }) {
  if (rows.length === 0) return null;
  const centerY = top + height / 2;
  const exonHeight = Math.min(28, height * 0.4);
  const exonTop = centerY - exonHeight / 2;
  const genes = [...new Set(rows.map((d) => d[LABEL]))].map((sym) => {
    const geneRows = rows.filter((d) => d[LABEL] === sym);
    return {
      symbol: sym,
      strand: geneRows[0][STRAND],
      featureType: geneRows[0][FEATURE_TYPE],
      exons: geneRows.map((r) => [r[START], r[END]]),
    };
  });

  return (
    <g>
      {genes.map((gene) => {
        const geneStart = Math.min(...gene.exons.map((e) => e[0]));
        const geneEnd = Math.max(...gene.exons.map((e) => e[1]));
        const arrowOffsets = [];
        for (let offset = geneStart + 300; offset < geneEnd; offset += 500) {
          arrowOffsets.push(offset);
        }

        return (
          <g key={gene.symbol}>
            <line
              x1={xScale(geneStart)}
              x2={xScale(geneEnd)}
              y1={centerY}
              y2={centerY}
              stroke={t.inkSoft}
              strokeWidth={2}
            />
            {arrowOffsets.map((offset) => {
              const x = xScale(offset);
              const dx = gene.strand === "+" ? 5 : -5;
              return (
                <path
                  key={`${gene.symbol}-arrow-${offset}`}
                  d={`M ${x - dx} ${centerY - 5} L ${x + dx} ${centerY} L ${x - dx} ${centerY + 5}`}
                  stroke={t.inkSoft}
                  strokeWidth={1.5}
                  fill="none"
                />
              );
            })}
            {gene.exons.map(([start, end]) => (
              <rect
                key={`${gene.symbol}-${start}`}
                x={xScale(start)}
                y={exonTop}
                width={Math.max(1, xScale(end) - xScale(start))}
                height={exonHeight}
                fill={featureColor[gene.featureType]}
              />
            ))}
            <text
              x={xScale(geneStart)}
              y={exonTop - 8}
              fontSize={13}
              fill={t.inkSoft}
            >
              {`${gene.symbol} (${gene.strand})`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function RegulatoryTrack({ xScale, top, height, rows }) {
  if (rows.length === 0) return null;
  const rectHeight = height * 0.55;
  const rectTop = top + (height - rectHeight) / 2;

  return (
    <g>
      {rows.map((element) => (
        <rect
          key={`${element[FEATURE_TYPE]}-${element[START]}`}
          x={xScale(element[START])}
          y={rectTop}
          width={Math.max(2, xScale(element[END]) - xScale(element[START]))}
          height={rectHeight}
          fill={featureColor[element[FEATURE_TYPE]]}
          rx={2}
        />
      ))}
    </g>
  );
}

function CoverageTrack({ xScale, top, height, rows }) {
  const samples = rows
    .filter((d) => Number.isFinite(d[VALUE]))
    .sort((a, b) => a[START] - b[START]);
  if (samples.length === 0) return null;
  const maxDepth = Math.max(...samples.map((d) => d[VALUE]));
  const depthScale = maxDepth > 0 ? maxDepth : 1;
  const baseline = top + height - 6;
  const usableHeight = height - 14;
  const points = samples.map((sample) => {
    const x = xScale(sample[START]);
    const y = baseline - (sample[VALUE] / depthScale) * usableHeight;
    return `${x},${y}`;
  });
  const firstX = xScale(samples[0][START]);
  const lastX = xScale(samples[samples.length - 1][START]);
  const areaPath = `M ${firstX},${baseline} L ${points.join(" L ")} L ${lastX},${baseline} Z`;

  return (
    <path
      d={areaPath}
      fill={t.palette[0]}
      fillOpacity={0.35}
      stroke={t.palette[0]}
      strokeWidth={1.5}
    />
  );
}

function VariantsTrack({ xScale, top, height, rows }) {
  if (rows.length === 0) return null;
  const baseline = top + height - 6;
  const usableHeight = height - 20;

  return (
    <g>
      {rows.map((variant, i) => {
        const x = xScale(variant[START]);
        const stemTop = baseline - (variant[VALUE] / MAX_QUALITY) * usableHeight;
        const color = featureColor[variant[FEATURE_TYPE]];
        return (
          <g key={`variant-${i}`}>
            <line
              x1={x}
              x2={x}
              y1={baseline}
              y2={stemTop}
              stroke={color}
              strokeWidth={1.5}
            />
            <circle cx={x} cy={stemTop} r={5} fill={color} />
          </g>
        );
      })}
    </g>
  );
}

const TRACK_RENDERERS = {
  genes: GenesTrack,
  regulatory: RegulatoryTrack,
  coverage: CoverageTrack,
  variants: VariantsTrack,
};

function GenomeTracks() {
  const xScale = useXScale();
  const drawing = useDrawingArea();
  const gap = 12;
  const bandHeight =
    (drawing.height - gap * (trackBands.length - 1)) / trackBands.length;
  const bandTop = (index) => drawing.top + index * (bandHeight + gap);
  const firstGrid = Math.ceil(regionStart / GRID_STEP) * GRID_STEP;
  const gridOffsets = Array.from(
    { length: Math.floor((regionEnd - firstGrid) / GRID_STEP) + 1 },
    (_, i) => firstGrid + i * GRID_STEP,
  );

  return (
    <g>
      {gridOffsets.map((offset) => (
        <line
          key={`grid-${offset}`}
          x1={xScale(offset)}
          x2={xScale(offset)}
          y1={drawing.top}
          y2={drawing.top + drawing.height}
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      {trackBands.map((_, index) =>
        index % 2 === 1 ? (
          <rect
            key={`band-${index}`}
            x={drawing.left}
            y={bandTop(index)}
            width={drawing.width}
            height={bandHeight}
            fill={t.elevatedBg}
          />
        ) : null,
      )}
      {trackBands.map(({ label }, index) => (
        <text
          key={`label-${index}`}
          x={drawing.left - 14}
          y={bandTop(index) + bandHeight / 2}
          textAnchor="end"
          dominantBaseline="middle"
          fontSize={15}
          fontWeight={500}
          fill={t.ink}
        >
          {label}
        </text>
      ))}
      {trackBands.map((band, index) => {
        const Renderer = TRACK_RENDERERS[band.kind];
        return (
          <Renderer
            key={`track-${index}`}
            xScale={xScale}
            top={bandTop(index)}
            height={bandHeight}
            rows={band.rows}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const width = window.ANYPLOT_SIZE.width;
  const height = window.ANYPLOT_SIZE.height;
  const chartHeight = height - TITLE_HEIGHT - LEGEND_HEIGHT;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
        px: 2,
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          lineHeight: `${TITLE_HEIGHT}px`,
        }}
      >
        {TITLE}
      </Typography>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 3,
          height: LEGEND_HEIGHT,
        }}
      >
        {discreteTypes.map((ft) => (
          <Box
            key={ft}
            sx={{ display: "flex", alignItems: "center", gap: 0.75 }}
          >
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: "2px",
                bgcolor: featureColor[ft],
              }}
            />
            <Typography sx={{ fontSize: 13, color: t.inkSoft }}>
              {ft}
            </Typography>
          </Box>
        ))}
      </Box>
      <ChartsContainer
        width={width - 32}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ left: 110, right: 30, top: 16, bottom: 16 }}
        xAxis={[
          {
            id: "genomicPosition",
            scaleType: "linear",
            min: regionStart,
            max: regionEnd,
            height: 64,
            valueFormatter: (value) => value.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
            label: `${START} — ${regionLabel}`,
            labelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[{ position: "none" }]}
      >
        <ChartsXAxis axisId="genomicPosition" />
        <GenomeTracks />
      </ChartsContainer>
    </Box>
  );
}
