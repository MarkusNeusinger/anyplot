// anyplot.ai
// area-stacked-confidence: Stacked Area Chart with Confidence Bands
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "area-stacked-confidence · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const BAND_OPACITY = 0.32;
const SYMMETRY_TOL = 0.05; // bounds whose offsets differ by less than this share of the band width count as symmetric

// Columns: set these to your data's column names
const QUARTER = "Quarter"; // role: x
const PRODUCT_LINE = "Product line"; // role: category
const REVENUE = "Revenue ($M)"; // role: y
const LOWER = "Lower bound ($M)"; // role: y_lower
const UPPER = "Upper bound ($M)"; // role: y_upper
const BAND_NAME = "90% prediction interval"; // what the lower and upper bounds describe

// Data: replace this block with your own records, one object per row
// Quarterly revenue forecast by product line, Q1 2024 to Q4 2028, largest line
// first so it anchors the stack. The interval widens with the forecast horizon,
// the fan-out of a real forecast. Seeded LCG, since the browser has no seeded RNG.
const data = (() => {
  let state = 42;
  const random = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  const lines = [
    { name: "Hardware", base: 42, trend: -0.35, season: 3.0, phase: 0, spread: 0.04, growth: 0.006 },
    { name: "Software", base: 18, trend: 1.15, season: 1.6, phase: 1.4, spread: 0.05, growth: 0.009 },
    { name: "Services", base: 10, trend: 0.55, season: 0.9, phase: 2.6, spread: 0.045, growth: 0.007 },
  ];
  return lines.flatMap((line) =>
    Array.from({ length: 20 }, (_, i) => {
      const center = Math.max(
        1,
        line.base + line.trend * i + line.season * Math.sin((i * Math.PI) / 2 + line.phase) + (random() - 0.5) * 1.6,
      );
      const fraction = line.spread + i * line.growth;
      return {
        [QUARTER]: new Date(2024 + Math.floor(i / 4), (i % 4) * 3, 1),
        [PRODUCT_LINE]: line.name,
        [REVENUE]: Number(center.toFixed(2)),
        [LOWER]: Number((center * (1 - fraction)).toFixed(2)),
        [UPPER]: Number((center * (1 + fraction)).toFixed(2)),
      };
    }),
  );
})();

// Plot: reads only data and the constants above
const quarters = [...new Map(data.map((d) => [d[QUARTER].getTime(), d[QUARTER]])).values()].sort(
  (a, b) => a.getTime() - b.getTime(),
);
const lines = [...new Set(data.map((d) => d[PRODUCT_LINE]))];
const rowByKey = new Map(data.map((d) => [`${d[PRODUCT_LINE]}|${d[QUARTER].getTime()}`, d]));
const cells = lines.map((line) => quarters.map((q) => rowByKey.get(`${line}|${q.getTime()}`) ?? null));

// Stack offset below each layer, shared by its central area and its band so both
// keep one stack order at every quarter
const below = lines.map((_, g) =>
  quarters.map((_, k) => cells.slice(0, g).reduce((s, row) => s + (row[k]?.[REVENUE] ?? 0), 0)),
);

// Band half-widths relative to the central value, for the symmetry note and subtitle
const halfShares = data.map((d) => (d[UPPER] - d[LOWER]) / 2 / d[REVENUE]);
const asymmetry = Math.max(
  ...data.map((d) => Math.abs(d[UPPER] - d[REVENUE] - (d[REVENUE] - d[LOWER])) / (d[UPPER] - d[LOWER] || 1)),
);
const symmetric = asymmetry <= SYMMETRY_TOL;
const fmtQuarter = (v: Date) => `Q${Math.floor(v.getMonth() / 3) + 1} ${v.getFullYear()}`;

const SUBTITLE = `${quarters.length} quarters, ${fmtQuarter(quarters[0])} – ${fmtQuarter(quarters[quarters.length - 1])} · ${lines.length} stacked series · band half-width ${Math.round(Math.min(...halfShares) * 100)}–${Math.round(Math.max(...halfShares) * 100)}% of the value`;
const BAND_LEGEND = `${BAND_NAME} around each layer's edge${symmetric ? "" : " (asymmetric)"}`;

// Each band is two stacked series: an invisible one carrying the offset (stack
// below + lower bound) and a filled one adding the band's own width on top
const series = [
  ...lines.map((line, g) => ({
    id: `line-${g}`,
    label: line,
    data: cells[g].map((d) => d?.[REVENUE] ?? null),
    color: t.palette[g],
    stack: "revenue",
    area: true,
    showMark: false,
    curve: "monotoneX" as const,
    // The tooltip row carries the bounds, since the band helpers below stay out of it
    valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) => {
      const d = cells[g][dataIndex];
      return v == null || !d ? null : `$${v.toFixed(1)}M (${d[LOWER].toFixed(1)}–${d[UPPER].toFixed(1)})`;
    },
  })),
  ...lines.flatMap((_, g) => [
    {
      id: `band-base-${g}`,
      data: cells[g].map((d, k) => (d ? below[g][k] + d[LOWER] : null)),
      color: t.palette[g],
      stack: `band-${g}`,
      showMark: false,
      curve: "monotoneX" as const,
      valueFormatter: () => null,
    },
    {
      id: `band-width-${g}`,
      data: cells[g].map((d) => (d ? d[UPPER] - d[LOWER] : null)),
      color: t.palette[g],
      stack: `band-${g}`,
      area: true,
      showMark: false,
      curve: "monotoneX" as const,
      valueFormatter: () => null,
    },
  ]),
];

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
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: quarters,
            scaleType: "time",
            valueFormatter: fmtQuarter,
            tickInterval: quarters.filter((_, k) => k % 2 === 0), // every other quarter keeps labels apart
            label: QUARTER,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            label: REVENUE,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={series}
        margin={{ top: 12, right: 40, bottom: 8, left: 24 }}
        sx={{
          '& .MuiLineChart-area[data-series^="line-"]': { fillOpacity: 0.85, filter: "none" },
          '& .MuiLineChart-line[data-series^="line-"]': { strokeWidth: 2.5 },
          '& .MuiLineChart-area[data-series^="band-width-"]': { fillOpacity: BAND_OPACITY, filter: "none" },
          '& .MuiLineChart-line[data-series^="band-"]': { display: "none" },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
      <Box
        sx={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "28px",
          pb: "8px",
          boxSizing: "border-box",
        }}
      >
        {lines.map((line, g) => (
          <Box key={line} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 16, height: 16, bgcolor: t.palette[g], borderRadius: "3px" }} />
            <Typography sx={{ fontSize: 15, color: t.ink }}>{line}</Typography>
          </Box>
        ))}
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box
            sx={{
              width: 28,
              height: 16,
              borderRadius: "3px",
              background: `linear-gradient(90deg, ${lines.map((_, g) => t.palette[g]).join(", ")})`,
              opacity: BAND_OPACITY + 0.2,
            }}
          />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{BAND_LEGEND}</Typography>
        </Box>
      </Box>
    </Box>
  );
}
