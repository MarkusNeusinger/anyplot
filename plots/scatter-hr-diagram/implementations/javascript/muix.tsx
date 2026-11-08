// anyplot.ai
// scatter-hr-diagram: Hertzsprung-Russell Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsAxis } from "@mui/x-charts/ChartsAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SPECTRAL_SEQUENCE = ["O", "B", "A", "F", "G", "K", "M"]; // hottest to coolest
// Conventional star colours (blue O/B, white A, yellow F/G, orange K, red M) mapped to the
// nearest Imprint palette members: the palette has no white, so lavender, its palest hue, stands
// in for A, and lime, its yellowest hue next to the ochre of G, stands in for yellow-white F
const SPECTRAL_COLORS = {
  O: t.palette[2],
  B: t.palette[5],
  A: t.palette[1],
  F: t.palette[7],
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
const STAR_RADIUS = 6; // px
const RING_RADIUS = 11; // px around a named star
const REFERENCE_RING_RADIUS = 14; // px around the reference star
const LABEL_CHAR_WIDTH = 0.6; // average glyph width of the annotation labels, as a share of the font size
const LABEL_PAD = 4; // px of clear space kept around each label
const LABEL_DIRECTIONS = 8; // candidate label positions around each anchor, starting straight above
const LABEL_STEP = 12; // px between successive rings of candidate positions
const LABEL_STEPS = 16; // rings tried before a label falls back to its first position

// Columns: set these to your data's column names
const TEMPERATURE = "Surface temperature (K)"; // role: temperature
const LUMINOSITY = "Luminosity (L/L☉)"; // role: luminosity
const SPECTRAL_TYPE = "Spectral type"; // role: spectral_type
const STAR_NAME = "Star"; // role: star_name
const REGION = "Region"; // role: region

// Data: replace this block with your own records, one object per row
// Synthetic stellar populations (main sequence with L ~ T^6, close to the observed
// slope from M dwarfs to O stars, red giants, supergiants, white dwarfs) plus the
// Sun and three named stars with approximate literature values. Spectral types
// follow the Harvard temperature bounds.
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
    rows.push(star(temperature, (temperature / 5778) ** 6 * uniform(0.55, 1.8), "Main sequence"));
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

// Each region label is anchored at the centroid of its own population, in the axes' own spaces;
// the layer below moves it to the nearest spot beside that population that covers no star
const regionLabels = [...new Set(data.map((d) => d[REGION]))].map((region) => {
  const rows = data.filter((d) => d[REGION] === region);
  return {
    text: region,
    x: rows.reduce((s, d) => s + d[TEMPERATURE], 0) / rows.length,
    y: 10 ** (rows.reduce((s, d) => s + Math.log10(d[LUMINOSITY]), 0) / rows.length),
  };
});
const namedStars = data.filter((d) => d[STAR_NAME]);
const ringOf = new Map(namedStars.map((d) => [d, d === referenceRow ? REFERENCE_RING_RADIUS : RING_RADIUS]));

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
  const { left, top, width, height } = useDrawingArea();
  const obstacles = data.map((d) => ({
    x: xScale(d[TEMPERATURE]),
    y: yScale(d[LUMINOSITY]),
    r: ringOf.get(d) ?? STAR_RADIUS,
  }));
  // Named stars first, then the regions; each label takes the first candidate, nearest first,
  // whose box stays inside the plot and clear of every star, ring and label placed before it
  const requests = [
    ...namedStars.map((d) => ({
      text: d[STAR_NAME],
      fontSize: d === referenceRow ? 16 : 14,
      fill: t.ink,
      ax: xScale(d[TEMPERATURE]),
      ay: yScale(d[LUMINOSITY]),
      gap: ringOf.get(d) + LABEL_PAD,
    })),
    ...regionLabels.map((r) => ({ text: r.text, fontSize: 17, fill: t.inkSoft, ax: xScale(r.x), ay: yScale(r.y), gap: 0 })),
  ];
  const placed: { x: number; y: number; w: number; h: number; text: string; fontSize: number; fill: string }[] = [];
  requests.forEach((q) => {
    const w = q.text.length * q.fontSize * LABEL_CHAR_WIDTH + 2 * LABEL_PAD;
    const h = q.fontSize + 2 * LABEL_PAD;
    const candidates = Array.from({ length: LABEL_STEPS }, (_, s) => q.gap + s * LABEL_STEP).flatMap((gap) =>
      Array.from({ length: LABEL_DIRECTIONS }, (_, k) => Math.PI / 2 + (2 * Math.PI * k) / LABEL_DIRECTIONS).map((a) => {
        const cos = Math.round(Math.cos(a) * 1e6) / 1e6;
        const sin = Math.round(Math.sin(a) * 1e6) / 1e6;
        const x = q.ax + (gap === 0 ? 0 : cos * (gap + w / 2));
        const y = q.ay - (gap === 0 ? 0 : sin * (gap + h / 2));
        return { x, y };
      }),
    );
    const free = candidates.find(({ x, y }) => {
      const x0 = x - w / 2;
      const x1 = x + w / 2;
      const y0 = y - h / 2;
      const y1 = y + h / 2;
      if (x0 < left || x1 > left + width || y0 < top || y1 > top + height) return false;
      if (obstacles.some((o) => o.x > x0 - o.r && o.x < x1 + o.r && o.y > y0 - o.r && o.y < y1 + o.r)) return false;
      return !placed.some((p) => x0 < p.x + p.w / 2 && p.x - p.w / 2 < x1 && y0 < p.y + p.h / 2 && p.y - p.h / 2 < y1);
    });
    placed.push({ ...(free ?? candidates[0]), w, h, text: q.text, fontSize: q.fontSize, fill: q.fill });
  });
  return (
    <g>
      {namedStars.map((d) => (
        <circle
          key={`ring-${d[STAR_NAME]}`}
          cx={xScale(d[TEMPERATURE])}
          cy={yScale(d[LUMINOSITY])}
          r={ringOf.get(d)}
          fill="none"
          stroke={t.ink}
          strokeWidth={d === referenceRow ? 2.5 : 1.5}
        />
      ))}
      {placed.map((p) => (
        <text
          key={`label-${p.text}`}
          x={p.x}
          y={p.y}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={p.fontSize}
          fontWeight={600}
          fill={p.fill}
          stroke={t.pageBg}
          strokeWidth={4}
          strokeLinejoin="round"
          paintOrder="stroke"
        >
          {p.text}
        </text>
      ))}
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
            markerSize: STAR_RADIUS,
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
