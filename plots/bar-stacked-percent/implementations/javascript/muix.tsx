// anyplot.ai
// bar-stacked-percent: 100% Stacked Bar Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-18
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Electricity Generation Mix · bar-stacked-percent · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const FULL = 100; // every bar spans the whole, 0 to 100 %
const MIN_LABEL_PX = 30; // a segment shorter than this keeps no percentage label
const DECIMALS = 1;
// Fixed label inks: segment fills keep their hex in both themes, so the ink follows the fill
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const COUNTRY = "Country"; // role: category
const SOURCE = "Energy source"; // role: component
const GENERATION = "Electricity generation (TWh per year)"; // role: value

// Data: replace this block with your own records, one object per row
// Illustrative annual generation for six national grids of very different size
const data = [
  { [COUNTRY]: "China", [SOURCE]: "Renewables", [GENERATION]: 3100 },
  { [COUNTRY]: "China", [SOURCE]: "Nuclear", [GENERATION]: 400 },
  { [COUNTRY]: "China", [SOURCE]: "Natural gas", [GENERATION]: 300 },
  { [COUNTRY]: "China", [SOURCE]: "Coal", [GENERATION]: 5200 },
  { [COUNTRY]: "USA", [SOURCE]: "Renewables", [GENERATION]: 900 },
  { [COUNTRY]: "USA", [SOURCE]: "Nuclear", [GENERATION]: 800 },
  { [COUNTRY]: "USA", [SOURCE]: "Natural gas", [GENERATION]: 1700 },
  { [COUNTRY]: "USA", [SOURCE]: "Coal", [GENERATION]: 700 },
  { [COUNTRY]: "Germany", [SOURCE]: "Renewables", [GENERATION]: 270 },
  { [COUNTRY]: "Germany", [SOURCE]: "Nuclear", [GENERATION]: 0 },
  { [COUNTRY]: "Germany", [SOURCE]: "Natural gas", [GENERATION]: 80 },
  { [COUNTRY]: "Germany", [SOURCE]: "Coal", [GENERATION]: 150 },
  { [COUNTRY]: "France", [SOURCE]: "Renewables", [GENERATION]: 120 },
  { [COUNTRY]: "France", [SOURCE]: "Nuclear", [GENERATION]: 320 },
  { [COUNTRY]: "France", [SOURCE]: "Natural gas", [GENERATION]: 30 },
  { [COUNTRY]: "France", [SOURCE]: "Coal", [GENERATION]: 5 },
  { [COUNTRY]: "Brazil", [SOURCE]: "Renewables", [GENERATION]: 550 },
  { [COUNTRY]: "Brazil", [SOURCE]: "Nuclear", [GENERATION]: 15 },
  { [COUNTRY]: "Brazil", [SOURCE]: "Natural gas", [GENERATION]: 60 },
  { [COUNTRY]: "Brazil", [SOURCE]: "Coal", [GENERATION]: 15 },
  { [COUNTRY]: "Norway", [SOURCE]: "Renewables", [GENERATION]: 150 },
  { [COUNTRY]: "Norway", [SOURCE]: "Nuclear", [GENERATION]: 0 },
  { [COUNTRY]: "Norway", [SOURCE]: "Natural gas", [GENERATION]: 0.5 },
  { [COUNTRY]: "Norway", [SOURCE]: "Coal", [GENERATION]: 0.1 },
];

// Plot: reads only data and the constants above
// Sources stack in order of first appearance and keep that palette position in every bar
const sources = [...new Set(data.map((d) => d[SOURCE]))];
const countryList = [...new Set(data.map((d) => d[COUNTRY]))];
const valueOf = new Map(data.map((d) => [`${d[COUNTRY]}\u0000${d[SOURCE]}`, d[GENERATION]]));
const countryTotals = new Map(
  countryList.map((c) => [c, sources.reduce((a, s) => a + (valueOf.get(`${c}\u0000${s}`) ?? 0), 0)]),
);
const shareOf = new Map(
  data.map((d) => [
    `${d[COUNTRY]}\u0000${d[SOURCE]}`,
    d[GENERATION] == null || !countryTotals.get(d[COUNTRY]) ? null : (d[GENERATION] / countryTotals.get(d[COUNTRY])) * FULL,
  ]),
);

// Bars ordered by the share of the first source, highest first
const countries = [...countryList].sort(
  (a, b) => (shareOf.get(`${b}\u0000${sources[0]}`) ?? 0) - (shareOf.get(`${a}\u0000${sources[0]}`) ?? 0),
);
const shares = sources.map((s) => countries.map((c) => shareOf.get(`${c}\u0000${s}`) ?? null));

// Segment label ink per source: whichever fixed ink contrasts more with the fill
const labelInks = sources.map((_, i) => {
  const [R, G, B] = [1, 3, 5].map((k) => {
    const c = parseInt(t.palette[i].slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const lum = 0.2126 * R + 0.7152 * G + 0.0722 * B;
  return (lum + 0.05) / 0.0603 >= 0.985 / (lum + 0.05) ? DARK_INK : LIGHT_INK;
});

const firstShares = shares[0];
const SUBTITLE = `${countries.length} grids, each normalized to its own total · sorted by ${sources[0].toLowerCase()} share: ${countries[0]} ${firstShares[0].toFixed(DECIMALS)}% to ${countries[countries.length - 1]} ${firstShares[firstShares.length - 1].toFixed(DECIMALS)}%`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <BarChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        colors={t.palette}
        skipAnimation
        series={sources.map((s, i) => ({
          id: `s${i}`,
          label: s,
          stack: "share",
          data: shares[i],
          valueFormatter: (v: number | null) => (v == null ? null : `${v.toFixed(DECIMALS)}%`),
          barLabel: (item: { value: number | null }, ctx: { bar: { height: number } }) =>
            item.value == null || ctx.bar.height < MIN_LABEL_PX ? null : `${item.value.toFixed(DECIMALS)}%`,
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: countries,
            label: COUNTRY,
            height: 64,
            categoryGapRatio: 0.35,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: FULL,
            label: `Share of ${COUNTRY.toLowerCase()} total (%)`,
            width: 84,
            disableTicks: true,
            valueFormatter: (v: number) => `${v}%`,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 40, bottom: 8, left: 24 }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiBarChart-element": { stroke: t.elevatedBg, strokeWidth: 1 },
          "& .MuiBarChart-label": { fontSize: 15, fontWeight: 600 },
          ...Object.fromEntries(sources.map((_, i) => [`& [data-series="s${i}"] .MuiBarChart-label`, { fill: labelInks[i] }])),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
        }}
      />
    </Box>
  );
}
