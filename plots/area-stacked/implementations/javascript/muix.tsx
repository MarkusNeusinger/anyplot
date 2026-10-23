// anyplot.ai
// area-stacked: Stacked Area Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-23
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const MONTH = "Month"; // role: x (Date)
const SOURCE = "Source"; // role: group
const VISITS = "Monthly Visits"; // role: value

// Data: replace this block with your own records, one object per row
// Monthly website traffic by source, Jan 2024 – Dec 2025 (24 months), generated
// with a tiny fixed-seed LCG — the browser has no seeded RNG
function lcg(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967295;
  };
}
const rand = lcg(42);
const SOURCE_SHAPES: [string, (i: number) => number, number][] = [
  [
    "Organic Search",
    (i) => 4200 + i * 55 + 300 * Math.sin(((i - 6) * Math.PI) / 6),
    200,
  ],
  [
    "Direct",
    (i) => 2100 + i * 22 + 120 * Math.sin(((i - 3) * Math.PI) / 6),
    140,
  ],
  [
    "Referral",
    (i) => 1150 + i * 9 + 80 * Math.sin(((i - 9) * Math.PI) / 6),
    90,
  ],
  ["Social", (i) => 650 + i * 30 + 150 * Math.sin((i * Math.PI) / 6), 110],
];
const data = SOURCE_SHAPES.flatMap(([source, trend, noise]) =>
  Array.from({ length: 24 }, (_, i) => ({
    [MONTH]: new Date(2024, i, 1),
    [SOURCE]: source,
    [VISITS]: Math.round(trend(i) + (rand() - 0.5) * noise),
  })),
);

// Plot: reads only data and the constants above
const fmtMonth = (v: Date) =>
  v.toLocaleString("en-US", { month: "short", year: "numeric" });

const months = [
  ...new Map(data.map((d) => [d[MONTH].getTime(), d[MONTH]])).values(),
].sort((a, b) => a.getTime() - b.getTime());
const valueAt = (source: string, m: Date) =>
  data.find(
    (d) => d[SOURCE] === source && d[MONTH].getTime() === m.getTime(),
  )?.[VISITS] ?? null;
const seriesValues = (source: string) => months.map((m) => valueAt(source, m));
const sum = (vs: (number | null)[]) => vs.reduce((a, v) => a + (v ?? 0), 0);

// Largest source at the bottom of the stack (the first series stacks first)
const sources = [...new Set(data.map((d) => d[SOURCE]))].sort(
  (a, b) => sum(seriesValues(b)) - sum(seriesValues(a)),
);

// Storytelling aids: the average stack total (reference line) and the
// fastest-growing source's overall lift (callout), both derived from the data.
const totals = months.map((m) => sum(sources.map((s) => valueAt(s, m))));
const avgTotal = sum(totals) / totals.length;
const growth = sources.map((s) => {
  const vs = seriesValues(s).filter((v): v is number => v != null);
  return vs.length > 1 && vs[0] ? (vs[vs.length - 1] - vs[0]) / vs[0] : -Infinity;
});
const focalIdx = growth.indexOf(Math.max(...growth));
const focalGrowthPct = Math.round(growth[focalIdx] * 100);

const TITLE =
  "Website Traffic Sources · area-stacked · javascript · muix · anyplot.ai";
const TITLE_H = 58;
const LEGEND_H = 44;

// --- Chart (default-exported component — the harness mounts it) ------------

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: "40px",
          pt: "10px",
        }}
      >
        <Typography
          sx={{
            color: t.ink,
            fontSize: "22px",
            fontWeight: 600,
            lineHeight: 1,
          }}
        >
          {TITLE}
        </Typography>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            bgcolor: t.elevatedBg,
            borderRadius: "6px",
            px: "12px",
            py: "6px",
          }}
        >
          <Box
            sx={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              bgcolor: t.palette[focalIdx % t.palette.length],
            }}
          />
          <Typography
            sx={{
              color: t.inkSoft,
              fontSize: "13px",
              fontWeight: 500,
              lineHeight: 1,
            }}
          >
            {`${sources[focalIdx]}: fastest-growing channel, ${focalGrowthPct >= 0 ? "+" : ""}${focalGrowthPct}% since ${fmtMonth(months[0])}`}
          </Typography>
        </Box>
      </Box>

      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        colors={t.palette}
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: months,
            scaleType: "time",
            valueFormatter: fmtMonth,
            tickNumber: 8,
            label: MONTH,
            height: 72,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: VISITS,
            valueFormatter: (v: number) => `${Math.round(v / 1000)}k`,
            width: 84,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        series={sources.map((source, i) => ({
          id: `s${i}`,
          data: seriesValues(source),
          label: source,
          stack: "traffic",
          area: true,
          showMark: false,
          curve: "monotoneX",
        }))}
        margin={{ top: 20, bottom: 10, left: 20, right: 40 }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.82 },
          "& .MuiLineChart-line": { strokeWidth: 2 },
          [`& .MuiLineChart-line[data-series="s${focalIdx}"]`]: {
            strokeWidth: 3,
          },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 14 },
          },
        }}
      >
        <ChartsReferenceLine
          y={avgTotal}
          label={`Avg total: ${(avgTotal / 1000).toFixed(1)}k`}
          labelAlign="start"
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "4 4",
            strokeWidth: 1.5,
          }}
          labelStyle={{
            fill: t.inkSoft,
            fontSize: 13,
            fontWeight: 600,
            stroke: t.pageBg,
            strokeWidth: 5,
            paintOrder: "stroke",
          }}
        />
      </LineChart>
    </Box>
  );
}
