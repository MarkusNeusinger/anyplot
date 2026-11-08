// anyplot.ai
// heatmap-stripes-climate: Climate Warming Stripes
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
// imprint_div's midpoint is the page colour, so a stripe near zero would vanish
// into the page: every stripe starts at this share of its pole's tint and the
// anomaly's size adds the rest. A zero anomaly is neither warm nor cold and takes
// half this share of the neutral ink, which sits farther from the page than either
// pole, so it stays as pale as the palest warm and cold stripes.
const MIN_INTENSITY = 0.2;
const BAND_WIDTH_SHARE = 0.94; // stripe band width as a share of the canvas width
const BAND_ASPECT = 3.1; // stripe band width : height

// Columns: set these to your data's column names
const YEAR = "Year"; // role: year
const ANOMALY = "Temperature anomaly (°C)"; // role: anomaly

// Data: replace this block with your own records, one object per year
// Synthetic global-mean temperature anomaly against a 1961-1990-style baseline,
// 1900-2024: a slow start, accelerating warming after about 1975, and
// year-to-year noise from a fixed-seed LCG.
const data = (() => {
  let state = 42;
  const random = () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
  const rows = [];
  for (let year = 1900; year <= 2024; year += 1) {
    const progress = (year - 1900) / (2024 - 1900);
    const trend = -0.25 + 1.35 * progress ** 2.2;
    const noise = (random() - 0.5) * 0.28;
    rows.push({ [YEAR]: year, [ANOMALY]: Math.round((trend + noise) * 100) / 100 });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[YEAR] - b[YEAR]);
// Symmetric limits: the larger of the coldest and the warmest anomaly sets both poles
const maxAbsAnomaly = Math.max(...rows.map((d) => Math.abs(d[ANOMALY] ?? 0)));
const [coldRgb, midRgb, warmRgb, neutralRgb] = [t.div[2], t.div[1], t.div[0], t.inkSoft].map((hex) =>
  [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)),
);
const stripeColors = rows.map((d) => {
  const fraction = d[ANOMALY] / maxAbsAnomaly;
  const share = fraction === 0 ? MIN_INTENSITY / 2 : MIN_INTENSITY + (1 - MIN_INTENSITY) * Math.abs(fraction);
  const pole = fraction < 0 ? coldRgb : fraction > 0 ? warmRgb : neutralRgb;
  const [r, g, b] = midRgb.map((c, k) => Math.round(c + (pole[k] - c) * share));
  return `rgb(${r}, ${g}, ${b})`;
});

const TITLE = "heatmap-stripes-climate · javascript · muix · anyplot.ai";

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const bandWidth = Math.round(width * BAND_WIDTH_SHARE);
  const bandHeight = Math.round(bandWidth / BAND_ASPECT);

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, mb: "24px" }}>{TITLE}</Typography>
      {/* Every stripe runs the full band height: only colour encodes the anomaly */}
      <Box sx={{ width: bandWidth, height: bandHeight, flex: "none" }}>
        <BarChart
          width={bandWidth}
          height={bandHeight}
          skipAnimation
          hideLegend
          borderRadius={0}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          series={[
            {
              id: "stripes",
              data: rows.map((d) => (d[ANOMALY] == null ? null : 1)),
              colorGetter: ({ dataIndex }) => stripeColors[dataIndex],
              valueFormatter: (_value, { dataIndex }) => `${ANOMALY}: ${rows[dataIndex][ANOMALY]}`,
            },
          ]}
          xAxis={[{ scaleType: "band", data: rows.map((d) => d[YEAR]), categoryGapRatio: 0, position: "none" }]}
          yAxis={[{ min: 0, max: 1, position: "none" }]}
        />
      </Box>
    </Box>
  );
}
