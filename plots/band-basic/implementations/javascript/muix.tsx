// anyplot.ai
// band-basic: Basic Band Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "band-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const BAND_OPACITY = 0.28;
const BAND_COLOR = t.palette[0];
const CENTER_COLOR = t.palette[1];

// Columns: set these to your data's column names
const DAY = "Forecast day"; // role: x
const LOWER = "Lower bound (°C)"; // role: y_lower
const UPPER = "Upper bound (°C)"; // role: y_upper
const CENTER = "Forecast temperature (°C)"; // role: y_center
const BAND_NAME = "90% confidence band"; // what the lower and upper bounds describe

// Data: replace this block with your own records, one object per row
// 30-day temperature forecast: the further out the prediction, the wider the
// interval around it. Seeded LCG, since the browser has no seeded RNG.
const data = (() => {
  let state = 42;
  const random = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  const days = Array.from({ length: 30 }, (_, i) => i + 1);
  const temps = days.map((day) => {
    const seasonalDrift = 16 + 5 * Math.sin((day / 30) * Math.PI * 0.9);
    return Math.round((seasonalDrift + day * 0.1 + (random() - 0.5) * 0.9) * 10) / 10;
  });
  const lowers = temps.map((v, i) => Math.round((v - (0.6 + days[i] * 0.13 + random() * 0.3)) * 10) / 10);
  const uppers = temps.map((v, i) => Math.round((v + (0.6 + days[i] * 0.13 + random() * 0.3)) * 10) / 10);
  return days.map((day, i) => ({ [DAY]: day, [LOWER]: lowers[i], [UPPER]: uppers[i], [CENTER]: temps[i] }));
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DAY] - b[DAY]);
const xs = rows.map((d) => d[DAY]);

// The band is two stacked series: an invisible one at the lower bound and a filled
// one adding the band's width, so the fill spans exactly lower to upper
const lowerEdge = rows.map((d) => (d[LOWER] == null || d[UPPER] == null ? null : d[LOWER]));
const bandWidth = rows.map((d) => (d[LOWER] == null || d[UPPER] == null ? null : d[UPPER] - d[LOWER]));
const widths = bandWidth.filter((v) => v != null);

const UNIT = CENTER.match(/\(([^)]+)\)/)?.[1] ?? "";
const SUBTITLE = `${rows.length} points, ${DAY.toLowerCase()} ${xs[0]}–${xs[xs.length - 1]} · shaded: ${BAND_NAME}, width ${Math.min(...widths).toFixed(1)}–${Math.max(...widths).toFixed(1)} ${UNIT}`.trim();

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
            data: xs,
            scaleType: "linear",
            min: xs[0],
            max: xs[xs.length - 1],
            label: DAY,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            label: CENTER,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          { id: "lower", data: lowerEdge, label: LOWER, stack: "band", showMark: false, color: BAND_COLOR, curve: "monotoneX" },
          {
            id: "band",
            data: bandWidth,
            label: BAND_NAME,
            stack: "band",
            area: true,
            showMark: false,
            color: BAND_COLOR,
            curve: "monotoneX",
            valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) =>
              v == null ? "" : `${rows[dataIndex][LOWER]} – ${rows[dataIndex][UPPER]}`,
          },
          { id: "center", data: rows.map((d) => d[CENTER]), label: CENTER, showMark: false, color: CENTER_COLOR, curve: "monotoneX" },
        ]}
        margin={{ top: 12, right: 40, bottom: 8, left: 24 }}
        sx={{
          '& .MuiLineChart-line[data-series="lower"]': { display: "none" },
          '& .MuiLineChart-line[data-series="band"]': { display: "none" },
          '& .MuiLineChart-area[data-series="band"]': { fillOpacity: BAND_OPACITY, filter: "none" },
          '& .MuiLineChart-line[data-series="center"]': { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "36px" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Box sx={{ width: 28, height: 16, bgcolor: BAND_COLOR, opacity: BAND_OPACITY, borderRadius: "3px" }} />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{BAND_NAME}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Box sx={{ width: 28, height: 3, bgcolor: CENTER_COLOR }} />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{CENTER}</Typography>
        </Box>
      </Box>
    </Box>
  );
}
