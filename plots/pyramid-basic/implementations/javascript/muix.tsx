// anyplot.ai
// pyramid-basic: Basic Pyramid Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD = 0.08; // share of the largest value kept free beyond the longest bar
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const GENRE = "Favourite genre"; // role: category
const STREAMVISTA = "StreamVista (subscribers)"; // role: value_left
const WAVEFLIX = "WaveFlix (subscribers)"; // role: value_right

// Data: replace this block with your own records, one object per row
// Survey of 400 subscribers per streaming service: the genre each watches most
const data = [
  { [GENRE]: "Action & Adventure", [STREAMVISTA]: 75, [WAVEFLIX]: 60 },
  { [GENRE]: "Drama", [STREAMVISTA]: 90, [WAVEFLIX]: 94 },
  { [GENRE]: "Comedy", [STREAMVISTA]: 65, [WAVEFLIX]: 71 },
  { [GENRE]: "Sci-Fi & Fantasy", [STREAMVISTA]: 50, [WAVEFLIX]: 38 },
  { [GENRE]: "Reality TV", [STREAMVISTA]: 33, [WAVEFLIX]: 46 },
  { [GENRE]: "Anime", [STREAMVISTA]: 40, [WAVEFLIX]: 45 },
  { [GENRE]: "Documentary", [STREAMVISTA]: 27, [WAVEFLIX]: 36 },
  { [GENRE]: "Kids & Family", [STREAMVISTA]: 20, [WAVEFLIX]: 10 },
];

// Plot: reads only data and the constants above
// Genres have no natural order: rank them by their combined count, the largest at the base
const rows = [...data].sort((a, b) => (a[STREAMVISTA] ?? 0) + (a[WAVEFLIX] ?? 0) - ((b[STREAMVISTA] ?? 0) + (b[WAVEFLIX] ?? 0)));
const sides = [STREAMVISTA, WAVEFLIX].map((column, i) => {
  const match = column.match(/^(.*?)\s*\(([^)]+)\)$/);
  const hex = t.palette[i];
  const [r, g, b] = [1, 3, 5].map((k) => {
    const c = parseInt(hex.slice(k, k + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return {
    column,
    name: match ? match[1] : column,
    unit: match ? match[2] : "",
    color: hex,
    // the ink with the higher WCAG contrast on this bar colour (dark ink #1A1A17 has luminance 0.0103)
    ink: (luminance + 0.05) / 0.0603 >= 1.05 / (luminance + 0.05) ? DARK_INK : LIGHT_INK,
    total: rows.reduce((sum, d) => sum + (d[column] ?? 0), 0),
  };
});
const maxValue = Math.max(...rows.flatMap((d) => [d[STREAMVISTA], d[WAVEFLIX]]).filter((v) => Number.isFinite(v)));
const limit = maxValue * (1 + X_PAD);

const TITLE = "pyramid-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${sides[0].total} ${sides[0].name} and ${sides[1].total} ${sides[1].name} ${sides[0].unit} across ${rows.length} genres`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <BarChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        layout="horizontal"
        skipAnimation
        margin={{ top: 12, right: 48, bottom: 8, left: 16 }}
        grid={{ vertical: true }}
        series={sides.map((side, i) => ({
          barLabel: (item) => (item.value === null ? null : `${Math.abs(item.value)}`),
          id: `side-${i}`,
          stack: "pyramid",
          data: rows.map((d) => (d[side.column] === null || d[side.column] === undefined ? null : i === 0 ? -d[side.column] : d[side.column])),
          label: side.name,
          color: side.color,
          valueFormatter: (v) => (v === null ? "" : `${Math.abs(v)} ${side.unit}`),
        }))}
        xAxis={[
          {
            id: "value",
            min: -limit,
            max: limit,
            tickNumber: 10,
            valueFormatter: (v) => `${Math.abs(v)}`,
            label: `${sides[0].unit[0].toUpperCase()}${sides[0].unit.slice(1)} (← ${sides[0].name} · ${sides[1].name} →)`,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: rows.map((d) => d[GENRE]),
            categoryGapRatio: 0.3,
            label: GENRE,
            width: 180,
            disableTicks: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft },
          },
        }}
        sx={{
          ...Object.fromEntries(
            sides.map((side, i) => [`& [data-series="side-${i}"] .MuiBarChart-label`, { fill: side.ink, fontSize: 14, fontWeight: 600 }]),
          ),
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine x={0} axisId="value" lineStyle={{ stroke: t.ink, strokeWidth: 2 }} />
      </BarChart>
    </div>
  );
}
