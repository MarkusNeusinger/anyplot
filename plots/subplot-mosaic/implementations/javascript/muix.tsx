// anyplot.ai
// subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-09
import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { Gauge, gaugeClasses } from "@mui/x-charts/Gauge";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
// Mosaic layout: a repeated letter spans grid cells, "." leaves a cell empty
const MOSAIC = ["AAAAAA", "BBBCCC", "DDEEFF"];
const ROW_SHARE = [0.41, 0.35, 0.24]; // share of the grid height per mosaic row
const TREND_CELL = "A"; // the dominant panel holds the primary series
const DEVICE_CELL = "B";
const PAGE_CELL = "C";
const PAD_SHARE = 0.06; // room around the outermost scatter marks

// Columns: set these to your data's column names
const DAY = "Day of month"; // role: x
const PAGEVIEWS = "Pageviews"; // role: y
const DEVICE = "Device"; // role: x
const SESSIONS = "Avg. daily sessions"; // role: y
const BOUNCE = "Bounce rate (%)"; // role: x
const DURATION = "Avg. duration (s)"; // role: y
const CHANNEL = "Acquisition channel"; // role: extra
const KPI = "KPI"; // role: x
const KPI_VALUE = "Value (%)"; // role: y
const KPI_MIN = "Scale minimum (%)"; // role: extra
const KPI_MAX = "Scale maximum (%)"; // role: extra

// Data: replace this block with your own records, one object per row
// A website analytics dashboard: 30 days of site pageviews, the average daily sessions
// per device (about 2.7 pageviews per session), 35 landing pages per acquisition
// channel, and three KPIs on their own scales
const devices = [
  { [DEVICE]: "Desktop", [SESSIONS]: 6400 },
  { [DEVICE]: "Mobile", [SESSIONS]: 8700 },
  { [DEVICE]: "Tablet", [SESSIONS]: 1800 },
];
const kpis = [
  { [KPI]: "Conversion rate", [KPI_VALUE]: 4.8, [KPI_MIN]: 0, [KPI_MAX]: 10 },
  { [KPI]: "Uptime SLA", [KPI_VALUE]: 99.95, [KPI_MIN]: 95, [KPI_MAX]: 100 },
  { [KPI]: "Support CSAT", [KPI_VALUE]: 92, [KPI_MIN]: 0, [KPI_MAX]: 100 },
];
const { pages, data } = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  let level = 42000;
  const days = Array.from({ length: 30 }, (_, i) => {
    level += (rand() - 0.4) * 2600;
    return { [DAY]: i + 1, [PAGEVIEWS]: Math.round(Math.max(30000, level)) };
  });
  const channels = [
    { name: "Organic", bounce: 38, duration: 210 },
    { name: "Paid", bounce: 52, duration: 140 },
    { name: "Direct", bounce: 30, duration: 260 },
    { name: "Referral", bounce: 46, duration: 175 },
  ];
  const pageRows = channels.flatMap((c) =>
    Array.from({ length: 35 }, () => ({
      [CHANNEL]: c.name,
      [BOUNCE]: Number(Math.max(5, Math.min(95, c.bounce + (rand() - 0.5) * 26)).toFixed(1)),
      [DURATION]: Math.round(Math.max(20, c.duration + (rand() - 0.5) * 100)),
    })),
  );
  return { pages: pageRows, data: days };
})();

// Plot: reads only the records and the constants above
// Mosaic cells: the bounding rows and columns of every letter
const letters = [...new Set(MOSAIC.join("").replace(/\./g, ""))];
const cells = Object.fromEntries(
  letters.map((letter) => {
    const rows = MOSAIC.flatMap((row, r) => (row.includes(letter) ? [r] : []));
    const cols = MOSAIC.flatMap((row) => [...row].flatMap((ch, c) => (ch === letter ? [c] : [])));
    const row = Math.min(...rows);
    const col = Math.min(...cols);
    return [letter, { row, col, rowSpan: Math.max(...rows) - row + 1, colSpan: Math.max(...cols) - col + 1 }];
  }),
);
const gridCols = MOSAIC[0].length;
const gridTemplateAreas = MOSAIC.map((row) => `"${[...row].join(" ")}"`).join(" ");
const kpiCells = letters.filter((l) => ![TREND_CELL, DEVICE_CELL, PAGE_CELL].includes(l));
// One gauge per KPI cell, in KPI order; KPIs beyond the free cells get no panel
const kpiPanels = kpis.slice(0, kpiCells.length).map((kpi, i) => ({ kpi, cell: kpiCells[i] }));

// Panel A: pageviews in day order
const trend = [...data].sort((a, b) => a[DAY] - b[DAY]);
const thousands = (v: number) => `${Math.round(v / 1000)}k`;

// Panel C: one scatter series per channel, in order of first appearance
const channelNames = [...new Set(pages.map((d) => d[CHANNEL]))];
const bounceMin = Math.min(...pages.map((d) => d[BOUNCE]));
const bounceMax = Math.max(...pages.map((d) => d[BOUNCE]));
const durationMin = Math.min(...pages.map((d) => d[DURATION]));
const durationMax = Math.max(...pages.map((d) => d[DURATION]));
const channelSeries = channelNames.map((name, i) => ({
  id: `channel-${i}`,
  label: name,
  color: t.palette[i],
  markerSize: 6,
  data: pages
    .filter((d) => d[CHANNEL] === name)
    .map((d, j) => ({ id: j, x: d[BOUNCE], y: d[DURATION] })),
}));

// Panels D–F: one gauge per KPI, in the cells left after the three charts
const kpiUnit = KPI_VALUE.match(/\(([^)]+)\)/)?.[1] ?? "";

const TITLE = "Website Analytics Dashboard · subplot-mosaic · javascript · muix · anyplot.ai";
const SUBTITLE = `Mosaic layout "${MOSAIC.join(";")}" · ${letters.length} panels on a ${MOSAIC.length} × ${gridCols} grid`;
const PANEL_TITLES = {
  [TREND_CELL]: `${PAGEVIEWS} by ${DAY.toLowerCase()} · ${trend.length} days`,
  [DEVICE_CELL]: `${SESSIONS} by ${DEVICE.toLowerCase()}`,
  [PAGE_CELL]: `${DURATION} vs ${BOUNCE.toLowerCase()}, by ${CHANNEL.toLowerCase()}`,
};
const TITLE_H = 40;
const SUBTITLE_H = 26;
const OUTER_GAP = 16;
const GAP = 22;
const PANEL_TITLE_H = 28;
const LEGEND_H = 32;
const axisText = { tickLabelStyle: { fontSize: 14, fill: t.inkSoft }, labelStyle: { fontSize: 15, fill: t.ink } };
const panelSx = {
  "& .MuiChartsAxis-line": { stroke: t.inkSoft },
  "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
  "& .MuiChartsGrid-line": { stroke: t.grid },
};
const panelTitleSx = { height: PANEL_TITLE_H, fontSize: 16, fontWeight: 600, color: t.ink, lineHeight: `${PANEL_TITLE_H}px` };
const gaugeSx = {
  [`& .${gaugeClasses.valueArc}`]: { fill: t.palette[0] },
  [`& .${gaugeClasses.referenceArc}`]: { fill: t.grid },
  [`& .${gaugeClasses.valueText} text`]: { fill: t.ink, fontSize: 28, fontWeight: 600 },
};

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const gridW = width - 2 * OUTER_GAP;
  const gridH = height - TITLE_H - SUBTITLE_H - OUTER_GAP;
  const colW = (gridW - GAP * (gridCols - 1)) / gridCols;
  const rowH = ROW_SHARE.map((share) => Math.floor((gridH - GAP * (MOSAIC.length - 1)) * share));
  const size = Object.fromEntries(
    letters.map((l) => [
      l,
      {
        w: Math.floor(colW * cells[l].colSpan + GAP * (cells[l].colSpan - 1)),
        h: rowH.slice(cells[l].row, cells[l].row + cells[l].rowSpan).reduce((a, b) => a + b, 0) + GAP * (cells[l].rowSpan - 1),
      },
    ]),
  );

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Typography sx={{ height: TITLE_H, lineHeight: `${TITLE_H + 8}px`, fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </Typography>
      <Typography sx={{ height: SUBTITLE_H, lineHeight: `${SUBTITLE_H}px`, fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </Typography>
      <Box
        sx={{
          display: "grid",
          gridTemplateAreas,
          gridTemplateColumns: `repeat(${gridCols}, ${colW}px)`,
          gridTemplateRows: rowH.map((h) => `${h}px`).join(" "),
          gap: `${GAP}px`,
        }}
      >
        <Box sx={{ gridArea: TREND_CELL }}>
          <Typography sx={panelTitleSx}>{PANEL_TITLES[TREND_CELL]}</Typography>
          <LineChart
            width={size[TREND_CELL].w}
            height={size[TREND_CELL].h - PANEL_TITLE_H}
            skipAnimation
            hideLegend
            grid={{ horizontal: true }}
            margin={{ top: 10, right: 16, bottom: 4, left: 4 }}
            xAxis={[{ data: trend.map((d) => d[DAY]), label: DAY, height: 56, tickNumber: 15, ...axisText }]}
            yAxis={[{ label: PAGEVIEWS, width: 76, valueFormatter: thousands, ...axisText }]}
            series={[
              {
                id: "pageviews",
                data: trend.map((d) => d[PAGEVIEWS]),
                label: PAGEVIEWS,
                color: t.palette[0],
                showMark: false,
                curve: "monotoneX",
              },
            ]}
            sx={{ ...panelSx, "& .MuiLineChart-line": { strokeWidth: 3 } }}
          />
        </Box>

        <Box sx={{ gridArea: DEVICE_CELL }}>
          <Typography sx={panelTitleSx}>{PANEL_TITLES[DEVICE_CELL]}</Typography>
          <BarChart
            width={size[DEVICE_CELL].w}
            height={size[DEVICE_CELL].h - PANEL_TITLE_H}
            skipAnimation
            hideLegend
            grid={{ horizontal: true }}
            margin={{ top: 10, right: 16, bottom: 4, left: 4 }}
            xAxis={[{ scaleType: "band", data: devices.map((d) => d[DEVICE]), height: 32, ...axisText }]}
            yAxis={[{ min: 0, label: SESSIONS, width: 76, valueFormatter: thousands, ...axisText }]}
            series={[{ id: "sessions", data: devices.map((d) => d[SESSIONS]), label: SESSIONS, color: t.palette[0] }]}
            sx={panelSx}
          />
        </Box>

        <Box sx={{ gridArea: PAGE_CELL }}>
          <Typography sx={panelTitleSx}>{PANEL_TITLES[PAGE_CELL]}</Typography>
          <ScatterChart
            width={size[PAGE_CELL].w}
            height={size[PAGE_CELL].h - PANEL_TITLE_H - LEGEND_H}
            skipAnimation
            grid={{ horizontal: true }}
            margin={{ top: 10, right: 16, bottom: 4, left: 4 }}
            xAxis={[
              {
                min: bounceMin - (bounceMax - bounceMin) * PAD_SHARE,
                max: bounceMax + (bounceMax - bounceMin) * PAD_SHARE,
                label: BOUNCE,
                height: 52,
                ...axisText,
              },
            ]}
            yAxis={[
              {
                min: durationMin - (durationMax - durationMin) * PAD_SHARE,
                max: durationMax + (durationMax - durationMin) * PAD_SHARE,
                label: DURATION,
                width: 76,
                ...axisText,
              },
            ]}
            series={channelSeries}
            slotProps={{
              legend: {
                direction: "horizontal",
                position: { vertical: "top", horizontal: "center" },
                sx: { fontSize: 14, color: t.inkSoft },
              },
            }}
            sx={{ ...panelSx, "& .MuiScatterChart-marker": { fillOpacity: 0.8 } }}
          />
        </Box>

        {kpiPanels.map(({ kpi, cell }) => (
          <Box key={kpi[KPI]} sx={{ gridArea: cell, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <Typography sx={{ ...panelTitleSx, textAlign: "center" }}>
              {kpi[KPI]}
              <Box component="span" sx={{ fontWeight: 400, color: t.inkSoft, fontSize: 14 }}>
                {` · scale ${kpi[KPI_MIN]}–${kpi[KPI_MAX]}${kpiUnit}`}
              </Box>
            </Typography>
            <Gauge
              width={size[cell].w}
              height={size[cell].h - PANEL_TITLE_H}
              value={kpi[KPI_VALUE]}
              valueMin={kpi[KPI_MIN]}
              valueMax={kpi[KPI_MAX]}
              startAngle={-90}
              endAngle={90}
              innerRadius="74%"
              outerRadius="100%"
              cornerRadius="50%"
              text={({ value }) => `${value}${kpiUnit}`}
              skipAnimation
              sx={gaugeSx}
            />
          </Box>
        ))}
      </Box>
    </Box>
  );
}
