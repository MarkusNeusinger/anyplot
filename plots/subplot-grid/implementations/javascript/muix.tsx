// anyplot.ai
// subplot-grid: Subplot Grid Layout
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-09
import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { PieChart } from "@mui/x-charts/PieChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.08; // room around the outermost marks of a panel
const PEAK_PAD_SHARE = 0.18; // room above the price peak for its label
const INK_ON_LIGHT = "#1A1A17"; // text on a light slice
const INK_ON_DARK = "#FAF8F1"; // text on a dark slice
const LUMINANCE_SPLIT = 0.19; // above this relative luminance a slice takes the dark ink

// Columns: set these to your data's column names
const DAY = "Trading day"; // role: x
const CLOSE = "Close (USD)"; // role: y
const VOLUME = "Volume (shares)"; // role: y
const SECTOR = "Sector"; // role: x
const WEIGHT = "Portfolio weight (%)"; // role: y

// Data: replace this block with your own records, one object per row
// A portfolio dashboard: 18 trading days of one holding's close and volume,
// and the portfolio's allocation across sectors
const sectors = [
  { [SECTOR]: "Technology", [WEIGHT]: 34 },
  { [SECTOR]: "Healthcare", [WEIGHT]: 24 },
  { [SECTOR]: "Financials", [WEIGHT]: 22 },
  { [SECTOR]: "Energy", [WEIGHT]: 20 },
];
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const days: Date[] = [];
  for (const d = new Date(2024, 2, 4); days.length < 18; d.setDate(d.getDate() + 1)) {
    if (d.getDay() !== 0 && d.getDay() !== 6) days.push(new Date(d));
  }
  let price = 128;
  const closes = days.map(() => {
    price += (rand() - 0.47) * 2.4;
    return Math.round(price * 100) / 100;
  });
  return days.map((day, i) => ({ [DAY]: day, [CLOSE]: closes[i], [VOLUME]: Math.round(420_000 + rand() * 380_000) }));
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[DAY] != null).sort((a, b) => (a[DAY] as Date).getTime() - (b[DAY] as Date).getTime());
const days = rows.map((d) => d[DAY] as Date);
const closes = rows.map((d) => d[CLOSE] as number);
const volumes = rows.map((d) => d[VOLUME] as number);
const closeUnit = CLOSE.match(/\(([^)]+)\)/)?.[1] ?? "";
const weightUnit = WEIGHT.match(/\(([^)]+)\)/)?.[1] ?? "";
const DAY_FORMAT: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };

// Price panel: the highest close is the one reference line
const closeMin = Math.min(...closes);
const closeMax = Math.max(...closes);
const closeSpan = closeMax - closeMin;

// Scatter panel: Pearson r between volume and close
const meanV = volumes.reduce((a, b) => a + b, 0) / volumes.length;
const meanC = closes.reduce((a, b) => a + b, 0) / closes.length;
let sVC = 0;
let sVV = 0;
let sCC = 0;
for (let i = 0; i < rows.length; i += 1) {
  sVC += (volumes[i] - meanV) * (closes[i] - meanC);
  sVV += (volumes[i] - meanV) ** 2;
  sCC += (closes[i] - meanC) ** 2;
}
const pearsonR = sVC / Math.sqrt(sVV * sCC);
const volMin = Math.min(...volumes);
const volMax = Math.max(...volumes);
const scatterPoints = rows.map((d, i) => ({ id: i, x: d[VOLUME] as number, y: d[CLOSE] as number }));

// Pie panel: slices in data order, each label in the ink that contrasts with its slice
const slices = sectors.map((s, i) => ({ id: i, label: s[SECTOR] as string, value: s[WEIGHT] as number, color: t.palette[i] }));
const sliceInk = slices.map((s) => {
  const [r, g, b] = [1, 3, 5].map((k) => {
    const c = parseInt(s.color.slice(k, k + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > LUMINANCE_SPLIT ? INK_ON_LIGHT : INK_ON_DARK;
});

const TITLE = "subplot-grid · javascript · muix · anyplot.ai";
const PANEL_TITLES = [
  `${CLOSE} · ${rows.length} ${DAY.toLowerCase()}s`,
  `${VOLUME} · ${rows.length} ${DAY.toLowerCase()}s`,
  `${CLOSE} vs ${VOLUME} · r = ${Number(pearsonR.toFixed(2)).toFixed(2)}`,
  `${WEIGHT} by ${SECTOR.toLowerCase()}`,
];
const FIGURE_TITLE_H = 52;
const OUTER_GAP = 16;
const CELL_GAP = 24;
const CELL_TITLE_H = 30;
const AXIS_X_H = 56;
const AXIS_Y_W = 76;
const PANEL_MARGIN = { top: 10, right: 24, bottom: 4, left: 8 };
const axisText = { tickLabelStyle: { fontSize: 14, fill: t.inkSoft }, labelStyle: { fontSize: 15, fill: t.ink } };
const panelSx = {
  "& .MuiChartsAxis-line": { stroke: t.inkSoft },
  "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
  "& .MuiChartsGrid-line": { stroke: t.grid },
};
const dayAxis = {
  scaleType: "band" as const,
  data: days,
  label: DAY,
  height: AXIS_X_H,
  valueFormatter: (d: Date) => d.toLocaleDateString("en-US", DAY_FORMAT),
  tickLabelInterval: (_d: Date, i: number) => days[i]?.getDay() === 1,
  ...axisText,
};

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;
  const cellW = (W - 2 * OUTER_GAP - CELL_GAP) / 2;
  const cellH = (H - FIGURE_TITLE_H - 2 * OUTER_GAP - CELL_GAP) / 2;
  const chartH = cellH - CELL_TITLE_H;
  const titleSx = { height: CELL_TITLE_H, fontSize: 16, fontWeight: 600, color: t.ink, pl: `${PANEL_MARGIN.left + AXIS_Y_W}px` };

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Typography sx={{ height: FIGURE_TITLE_H, lineHeight: `${FIGURE_TITLE_H}px`, fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </Typography>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: `repeat(2, ${cellW}px)`,
          gridTemplateRows: `repeat(2, ${cellH}px)`,
          gap: `${CELL_GAP}px`,
        }}
      >
        <Box>
          <Typography sx={titleSx}>{PANEL_TITLES[0]}</Typography>
          <LineChart
            width={cellW}
            height={chartH}
            skipAnimation
            hideLegend
            grid={{ horizontal: true }}
            margin={PANEL_MARGIN}
            xAxis={[dayAxis]}
            yAxis={[
              {
                min: closeMin - closeSpan * PAD_SHARE,
                max: closeMax + closeSpan * PEAK_PAD_SHARE,
                label: CLOSE,
                width: AXIS_Y_W,
                ...axisText,
              },
            ]}
            series={[{ id: "close", data: closes, label: CLOSE, color: t.palette[0], showMark: false, curve: "linear" }]}
            sx={{ ...panelSx, "& .MuiLineChart-line": { strokeWidth: 3 } }}
          >
            <ChartsReferenceLine
              y={closeMax}
              label={`Peak ${closeMax.toFixed(2)} ${closeUnit}`}
              labelAlign="end"
              lineStyle={{ stroke: t.amber, strokeDasharray: "6 4", strokeWidth: 2 }}
              labelStyle={{ fill: t.ink, fontSize: 14, fontWeight: 600 }}
            />
          </LineChart>
        </Box>

        <Box>
          <Typography sx={titleSx}>{PANEL_TITLES[1]}</Typography>
          <BarChart
            width={cellW}
            height={chartH}
            skipAnimation
            hideLegend
            grid={{ horizontal: true }}
            margin={PANEL_MARGIN}
            xAxis={[dayAxis]}
            yAxis={[
              {
                min: 0,
                label: VOLUME,
                width: AXIS_Y_W,
                valueFormatter: (v: number) => `${Math.round(v / 1000)}K`,
                ...axisText,
              },
            ]}
            series={[{ id: "volume", data: volumes, label: VOLUME, color: t.palette[0] }]}
            sx={panelSx}
          />
        </Box>

        <Box>
          <Typography sx={titleSx}>{PANEL_TITLES[2]}</Typography>
          <ScatterChart
            width={cellW}
            height={chartH}
            skipAnimation
            hideLegend
            grid={{ horizontal: true, vertical: true }}
            margin={PANEL_MARGIN}
            xAxis={[
              {
                min: volMin - (volMax - volMin) * PAD_SHARE,
                max: volMax + (volMax - volMin) * PAD_SHARE,
                label: VOLUME,
                height: AXIS_X_H,
                valueFormatter: (v: number) => `${Math.round(v / 1000)}K`,
                ...axisText,
              },
            ]}
            yAxis={[
              {
                min: closeMin - closeSpan * PAD_SHARE,
                max: closeMax + closeSpan * PAD_SHARE,
                label: CLOSE,
                width: AXIS_Y_W,
                ...axisText,
              },
            ]}
            series={[{ id: "days", data: scatterPoints, label: DAY, color: t.palette[0], markerSize: 8 }]}
            sx={panelSx}
          />
        </Box>

        <Box>
          <Typography sx={titleSx}>{PANEL_TITLES[3]}</Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: chartH, gap: "40px" }}>
            <Box sx={{ width: chartH, height: chartH, flexShrink: 0 }}>
            <PieChart
              width={chartH}
              height={chartH}
              skipAnimation
              hideLegend
              margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
              series={[
                {
                  data: slices,
                  innerRadius: chartH * 0.17,
                  outerRadius: chartH * 0.46,
                  paddingAngle: 2,
                  arcLabel: (item) => `${item.value}${weightUnit}`,
                  arcLabelMinAngle: 15,
                },
              ]}
              sx={Object.fromEntries(
                sliceInk.map((ink, i) => [
                  `& .MuiPieChart-arcLabel:nth-of-type(${i + 1})`,
                  { fill: ink, fontSize: 15, fontWeight: 600 },
                ]),
              )}
            />
            </Box>
            <Box sx={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {slices.map((s) => (
                <Box key={s.id} sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Box sx={{ width: 16, height: 16, borderRadius: "3px", bgcolor: s.color }} />
                  <Typography sx={{ fontSize: 15, color: t.ink }}>{s.label}</Typography>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
