// anyplot.ai
// line-stress-strain: Engineering Stress-Strain Curve
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const OFFSET = 0.002; // strain offset of the yield construction (the 0.2% offset method)
const ELASTIC_SECANT_SHARE = 0.95; // a sample is elastic while its secant modulus stays within this share of the first one
const OFFSET_LINE_OVERSHOOT = 0.3; // the offset line continues this share of the yield stress past the curve
const X_PAD_SHARE = 0.04; // share of the strain range added right of the fracture point
const Y_PAD_SHARE = 0.12; // share of the peak stress added above it for the labels

// Columns: set these to your data's column names
const STRAIN = "Engineering strain (mm/mm)"; // role: strain
const STRESS = "Engineering stress (MPa)"; // role: stress_mpa

// Data: replace this block with your own records, one object per row
// Tensile test of a mild-steel specimen: elastic line, serrated yield plateau, strain hardening, necking.
const data = (() => {
  const modulus = 200000;
  const yieldStress = 250;
  const elasticEnd = yieldStress / modulus;
  const plateauStart = elasticEnd + 0.002;
  const plateauEnd = 0.02;
  const utsStrain = 0.2;
  const utsStress = 450;
  const fractureStrain = 0.26;
  const fractureStress = 300;
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const span = (a, b, n) => Array.from({ length: n }, (_, i) => a + ((b - a) * i) / (n - 1));
  const strains = [
    ...span(0, elasticEnd, 6),
    ...span(elasticEnd, plateauStart, 6).slice(1),
    ...span(plateauStart, plateauEnd, 24).slice(1),
    ...span(plateauEnd, utsStrain, 90).slice(1),
    ...span(utsStrain, fractureStrain, 46).slice(1),
  ];
  return strains.map((strain) => {
    let stress;
    if (strain <= elasticEnd) stress = modulus * strain;
    else if (strain <= plateauEnd) stress = yieldStress + (rand() - 0.5) * 6;
    else if (strain <= utsStrain) {
      const f = (strain - plateauEnd) / (utsStrain - plateauEnd);
      stress = yieldStress + (utsStress - yieldStress) * (2 * f - f * f);
    } else {
      const f = (strain - utsStrain) / (fractureStrain - utsStrain);
      stress = utsStress - (utsStress - fractureStress) * (3 * f * f - 2 * f * f * f);
    }
    return { [STRAIN]: Math.round(strain * 1e6) / 1e6, [STRESS]: Math.round(stress * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[STRAIN] - b[STRAIN]);
const strains = rows.map((d) => d[STRAIN]);
const stresses = rows.map((d) => d[STRESS]);
const unit = STRESS.match(/\(([^)]+)\)/)?.[1] ?? "";
const last = rows.length - 1;

// Elastic region: the leading samples whose secant modulus stays near the first loaded sample's;
// the modulus is the least-squares slope through the origin over them.
const firstLoaded = strains.findIndex((s) => s > 0);
const initialSecant = stresses[firstLoaded] / strains[firstLoaded];
let elasticEnd = firstLoaded;
while (elasticEnd < last && stresses[elasticEnd + 1] / strains[elasticEnd + 1] >= ELASTIC_SECANT_SHARE * initialSecant) {
  elasticEnd += 1;
}
const elastic = rows.slice(0, elasticEnd + 1);
const modulus =
  elastic.reduce((sum, d) => sum + d[STRAIN] * d[STRESS], 0) / elastic.reduce((sum, d) => sum + d[STRAIN] ** 2, 0);

// Yield: first crossing of the curve below the offset line, interpolated within the segment
const gap = rows.map((d) => d[STRESS] - modulus * (d[STRAIN] - OFFSET));
const cross = gap.findIndex((g, i) => i > 0 && gap[i - 1] > 0 && g <= 0);
const share = cross > 0 ? gap[cross - 1] / (gap[cross - 1] - gap[cross]) : 0;
const yieldPoint =
  cross > 0
    ? {
        strain: strains[cross - 1] + share * (strains[cross] - strains[cross - 1]),
        stress: stresses[cross - 1] + share * (stresses[cross] - stresses[cross - 1]),
      }
    : null;
const utsIndex = stresses.indexOf(Math.max(...stresses));
const uts = { strain: strains[utsIndex], stress: stresses[utsIndex] };
const fracture = { strain: strains[last], stress: stresses[last] };

const fmtStress = (v: number) => `${Math.round(v).toLocaleString("en-US")} ${unit}`;
const offsetTop = (yieldPoint ? yieldPoint.stress * (1 + OFFSET_LINE_OVERSHOOT) : uts.stress);
const criticalPoints = [
  yieldPoint && { ...yieldPoint, text: `Yield ${fmtStress(yieldPoint.stress)}`, anchor: "start", dx: 16, dy: -18 },
  { ...uts, text: `UTS ${fmtStress(uts.stress)}`, anchor: "middle", dx: 0, dy: -22 },
  { ...fracture, text: `Fracture ${fmtStress(fracture.stress)}`, anchor: "end", dx: -12, dy: 34 },
].filter(Boolean);

// Region labels sit above the curve at the middle of the strain span they name, on the side
// where the curve falls away: left of the anchor on a rising stretch, right of it on a falling one
const plasticAt = yieldPoint && utsIndex > cross ? strains.findIndex((s) => s >= (yieldPoint.strain + uts.strain) / 2) : -1;
const neckingAt = utsIndex < last ? strains.findIndex((s) => s >= (uts.strain + fracture.strain) / 2) : -1;
const regionLabels = [
  { at: plasticAt, text: "Plastic (strain hardening)" },
  { at: neckingAt, text: "Necking" },
]
  .filter((r) => r.at > 0 && r.at < last)
  .map((r) => ({ ...r, rising: stresses[r.at + 1] >= stresses[r.at - 1] }));
const elasticMid = elastic[Math.floor(elastic.length / 2)];

const TITLE = "line-stress-strain · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} samples · E fitted over the first ${elastic.length} samples · yield by the ${OFFSET * 100}% offset method · elongation at fracture ${(fracture.strain * 100).toFixed(1)}%`;
const HEADER_H = 80;

function CurveAnnotations() {
  const xScale = useXScale();
  const yScale = useYScale();
  const y0 = yScale(0);
  return (
    <g>
      <line
        x1={xScale(OFFSET)}
        y1={y0}
        x2={xScale(OFFSET + offsetTop / modulus)}
        y2={yScale(offsetTop)}
        stroke={t.inkSoft}
        strokeWidth={2}
        strokeDasharray="8 5"
      />
      <text
        x={xScale(OFFSET + offsetTop / modulus) + 10}
        y={yScale(offsetTop)}
        fontSize={15}
        fill={t.inkSoft}
        dominantBaseline="middle"
      >
        {`${OFFSET * 100}% offset line, slope E`}
      </text>
      <text
        x={xScale(elasticMid[STRAIN]) + 40}
        y={yScale(elasticMid[STRESS])}
        fontSize={16}
        fontWeight={500}
        fill={t.ink}
        dominantBaseline="middle"
      >
        {`Elastic · E = ${fmtStress(modulus)}`}
      </text>
      {regionLabels.map((r) => (
        <text
          key={r.text}
          x={xScale(strains[r.at]) + (r.rising ? -8 : 8)}
          y={yScale(stresses[r.at]) - 20}
          fontSize={16}
          fontWeight={500}
          fill={t.ink}
          textAnchor={r.rising ? "end" : "start"}
        >
          {r.text}
        </text>
      ))}
      {criticalPoints.map((p) => (
        <g key={p.text}>
          <line
            x1={xScale(p.strain)}
            y1={yScale(p.stress)}
            x2={xScale(p.strain)}
            y2={y0}
            stroke={t.inkSoft}
            strokeOpacity={0.6}
            strokeWidth={1.25}
            strokeDasharray="2 4"
          />
          <circle cx={xScale(p.strain)} cy={yScale(p.stress)} r={8} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={3} />
          <text
            x={xScale(p.strain) + p.dx}
            y={yScale(p.stress) + p.dy}
            fontSize={15}
            fill={t.inkSoft}
            textAnchor={p.anchor}
          >
            {p.text}
          </text>
        </g>
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
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: strains,
            scaleType: "linear",
            min: 0,
            max: fracture.strain * (1 + X_PAD_SHARE),
            tickNumber: 14,
            valueFormatter: (v: number) => v.toFixed(2),
            label: STRAIN,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: uts.stress * (1 + Y_PAD_SHARE),
            label: STRESS,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "curve",
            data: stresses,
            label: STRESS,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            valueFormatter: (v: number | null) => (v == null ? "" : fmtStress(v)),
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <CurveAnnotations />
      </LineChart>
    </div>
  );
}
