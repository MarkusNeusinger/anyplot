// anyplot.ai
// scatter-hr-diagram: Hertzsprung-Russell Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-26
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsAxis } from "@mui/x-charts/ChartsAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SPECTRAL_SEQUENCE = ["O", "B", "A", "F", "G", "K", "M"]; // hottest to coolest
// Conventional star colours (blue O/B, white A, yellow F/G, orange K, red M) mapped to the
// nearest Imprint hues; the palette has no white, so lavender, its palest hue, stands in for A
const SPECTRAL_COLORS = {
  O: t.palette[2],
  B: t.palette[5],
  A: t.palette[1],
  F: t.amber,
  G: t.palette[3],
  K: t.palette[6],
  M: t.palette[4],
};
const REFERENCE_LUMINOSITY = 1; // luminosity is in solar units, so the reference star sits at exactly 1
const TEMPERATURE_PAD_SHARE = 0.03; // room beyond the hottest and coolest star, as a share of the span
const LOG_PAD_SHARE = 0.04; // room above and below the extreme luminosities, as a share of the decades spanned
const SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹";
const TEMPERATURE_TICK_COUNT = 16; // about this many temperature ticks, one even step across the axis
const STAR_OPACITY = 0.8;
const LABEL_CHAR_WIDTH = 0.6; // average glyph width of the annotation labels, as a share of the font size

// Columns: set these to your data's column names
const TEMPERATURE = "Surface temperature (K)"; // role: temperature
const LUMINOSITY = "Luminosity (L/L☉)"; // role: luminosity
const SPECTRAL_TYPE = "Spectral type"; // role: spectral_type
const STAR_NAME = "Star"; // role: star_name
const REGION = "Region"; // role: region

// Data: replace this block with your own records, one object per row
// Synthetic stellar populations (main sequence with L ~ T^3.9, red giants,
// supergiants, white dwarfs) plus the Sun and three named stars with approximate
// literature values. Spectral types follow the Harvard temperature bounds.
const data = (() => {
  let seed = 42;
  const uniform = (min, max) => {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return min + (seed / 4294967295) * (max - min);
  };
  const lowerBounds = [["O", 30000], ["B", 10000], ["A", 7500], ["F", 6000], ["G", 5200], ["K", 3700], ["M", 0]];
  const star = (temperature, luminosity, region, name = null) => ({
    [TEMPERATURE]: Math.round(temperature),
    [LUMINOSITY]: Number(luminosity.toPrecision(4)),
    [SPECTRAL_TYPE]: lowerBounds.find(([, lower]) => temperature >= lower)[0],
    [STAR_NAME]: name,
    [REGION]: region,
  });
  const rows = [];
  for (let k = 0; k < 180; k += 1) {
    const temperature = uniform(2600, 38000);
    rows.push(star(temperature, (temperature / 5778) ** 3.9 * uniform(0.55, 1.8), "Main sequence"));
  }
  for (let k = 0; k < 40; k += 1) rows.push(star(uniform(3400, 5200), uniform(15, 900), "Red giants"));
  for (let k = 0; k < 25; k += 1) rows.push(star(uniform(3000, 30000), uniform(8000, 800000), "Supergiants"));
  for (let k = 0; k < 35; k += 1) rows.push(star(uniform(8000, 40000), uniform(0.0001, 0.02), "White dwarfs"));
  rows.push(star(5778, 1, "Main sequence", "Sun"));
  rows.push(star(9940, 25.4, "Main sequence", "Sirius A"));
  rows.push(star(12100, 120000, "Supergiants", "Rigel"));
  rows.push(star(3500, 126000, "Supergiants", "Betelgeuse"));
  return rows;
})();

// Plot: reads only data and the constants above
const referenceRow = data.find((d) => d[STAR_NAME] && d[LUMINOSITY] === REFERENCE_LUMINOSITY);
const stars = data.filter((d) => d !== referenceRow);

// Spectral types in the conventional hot-to-cool order; a type outside it follows in order of appearance
const presentTypes = [...new Set(stars.map((d) => d[SPECTRAL_TYPE]))];
const types = [
  ...SPECTRAL_SEQUENCE.filter((s) => presentTypes.includes(s)),
  ...presentTypes.filter((s) => !SPECTRAL_SEQUENCE.includes(s)),
];
const spareColors = t.palette.filter((c) => !Object.values(SPECTRAL_COLORS).includes(c));
const unmappedTypes = types.filter((s) => !(s in SPECTRAL_COLORS));
const typeColor = Object.fromEntries(
  types.map((s) => [s, SPECTRAL_COLORS[s] ?? spareColors[unmappedTypes.indexOf(s)]]),
);

// Secondary axis: each spectral letter at the middle of its temperature range
const classTicks = types.map((s) => {
  const temps = data.filter((d) => d[SPECTRAL_TYPE] === s).map((d) => d[TEMPERATURE]);
  return { type: s, at: (Math.min(...temps) + Math.max(...temps)) / 2 };
});
const classByTick = new Map(classTicks.map((c) => [c.at, c.type]));

// Region labels sit at the centroid of their own population, in the axes' own spaces
const regionLabels = [...new Set(data.map((d) => d[REGION]))].map((region) => {
  const rows = data.filter((d) => d[REGION] === region);
  return {
    text: region,
    x: rows.reduce((s, d) => s + d[TEMPERATURE], 0) / rows.length,
    y: 10 ** (rows.reduce((s, d) => s + Math.log10(d[LUMINOSITY]), 0) / rows.length),
  };
});
const namedStars = data.filter((d) => d[STAR_NAME]);

const temps = data.map((d) => d[TEMPERATURE]);
const tPad = (Math.max(...temps) - Math.min(...temps)) * TEMPERATURE_PAD_SHARE;
const tMin = Math.min(...temps) - tPad;
const tMax = Math.max(...temps) + tPad;
const logLums = data.map((d) => Math.log10(d[LUMINOSITY]));
const logPad = (Math.max(...logLums) - Math.min(...logLums)) * LOG_PAD_SHARE;
const logMin = Math.min(...logLums) - logPad;
const logMax = Math.max(...logLums) + logPad;
const lumTicks = Array.from(
  { length: Math.floor(logMax) - Math.ceil(logMin) + 1 },
  (_, k) => 10 ** (Math.ceil(logMin) + k),
);

const TITLE = "scatter-hr-diagram · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} stars across ${regionLabels.length} regions · colour: ${SPECTRAL_TYPE.toLowerCase()} · ringed: named stars`;
const HEADER_HEIGHT = 76;
const LEGEND_HEIGHT = 40;

function Annotations() {
  const xScale = useXScale();
  const yScale = useYScale();
  const regionBoxes = regionLabels.map((r) => ({ ...r, fontSize: 17, fill: t.inkSoft, px: xScale(r.x), py: yScale(r.y) }));
  const starBoxes = namedStars.map((d) => ({
    text: d[STAR_NAME],
    fontSize: d === referenceRow ? 16 : 14,
    fill: t.ink,
    px: xScale(d[TEMPERATURE]),
    py: yScale(d[LUMINOSITY]) - 30,
  }));
  return (
    <g>
      {namedStars.map((d) => (
        <circle
          key={`ring-${d[STAR_NAME]}`}
          cx={xScale(d[TEMPERATURE])}
          cy={yScale(d[LUMINOSITY])}
          r={d === referenceRow ? 14 : 11}
          fill="none"
          stroke={t.ink}
          strokeWidth={d === referenceRow ? 2.5 : 1.5}
        />
      ))}
      {[...regionBoxes, ...starBoxes].map((b) => {
        const boxWidth = b.text.length * b.fontSize * LABEL_CHAR_WIDTH + 20;
        const boxHeight = b.fontSize + 12;
        return (
          <g key={`label-${b.text}`}>
            <rect
              x={b.px - boxWidth / 2}
              y={b.py - boxHeight / 2}
              width={boxWidth}
              height={boxHeight}
              rx={6}
              fill={t.pageBg}
              fillOpacity={0.82}
            />
            <text
              x={b.px}
              y={b.py}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={b.fontSize}
              fontWeight={600}
              fill={b.fill}
            >
              {b.text}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_HEIGHT - LEGEND_HEIGHT}
        margin={{ top: 4, right: 48, bottom: 8, left: 24 }}
        skipAnimation
        series={[
          ...types.map((s) => ({
            type: "scatter" as const,
            id: `type-${s}`,
            label: s,
            color: typeColor[s],
            markerSize: 6,
            data: stars
              .filter((d) => d[SPECTRAL_TYPE] === s)
              .map((d, k) => ({ id: `${s}-${k}`, x: d[TEMPERATURE], y: d[LUMINOSITY] })),
          })),
          ...(referenceRow
            ? [
                {
                  type: "scatter" as const,
                  id: "reference",
                  label: referenceRow[STAR_NAME],
                  color: t.ink,
                  markerSize: 7,
                  data: [{ id: "reference", x: referenceRow[TEMPERATURE], y: referenceRow[LUMINOSITY] }],
                },
              ]
            : []),
        ]}
        xAxis={[
          {
            id: "temperature",
            scaleType: "linear",
            reverse: true,
            min: tMin,
            max: tMax,
            label: TEMPERATURE,
            tickNumber: TEMPERATURE_TICK_COUNT,
            height: 64,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
          {
            id: "spectral",
            scaleType: "linear",
            reverse: true,
            position: "top",
            min: tMin,
            max: tMax,
            label: SPECTRAL_TYPE,
            height: 60,
            tickInterval: classTicks.map((c) => c.at),
            tickLabelInterval: () => true,
            valueFormatter: (v: number) => classByTick.get(v) ?? "",
            tickLabelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "luminosity",
            scaleType: "log",
            min: 10 ** logMin,
            max: 10 ** logMax,
            label: LUMINOSITY,
            width: 84,
            tickInterval: lumTicks,
            valueFormatter: (v: number, ctx) => {
              if (ctx.location !== "tick") return v.toPrecision(3);
              const exponent = Math.round(Math.log10(v));
              const digits = [...String(Math.abs(exponent))].map((c) => SUPERSCRIPT_DIGITS[Number(c)]).join("");
              return exponent === 0 ? "1" : `10${exponent < 0 ? "⁻" : ""}${digits}`;
            },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, height: LEGEND_HEIGHT, alignItems: "center" }} />
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { fillOpacity: STAR_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
              '& [data-series="reference"] .MuiScatterChart-marker': { fillOpacity: 1 },
            }}
          >
            <ChartsGrid horizontal vertical />
            <ChartsAxis />
            <ScatterPlot />
            <Annotations />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
