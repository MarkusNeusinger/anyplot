// anyplot.ai
// stock-event-flags: Stock Chart with Event Flags
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
// Flag icons per event type, stroked paths in a 16 x 16 box; other types get a ring
const EVENT_ICONS: Record<string, string> = {
  Earnings: "M2.5 15.5V9 M8 15.5V4.5 M13.5 15.5V1",
  Dividend:
    "M11.8 4.4C11.2 3 9.8 2.3 8 2.3 5.8 2.3 4.4 3.4 4.4 5 4.4 6.7 5.9 7.4 8 8 10.1 8.6 11.6 9.3 11.6 11.1 11.6 12.7 10.1 13.7 8 13.7 6 13.7 4.7 13 4.1 11.6 M8 0.4V15.6",
  "Stock split": "M8 15.5V8 M8 8L2.5 2.2 M8 8L13.5 2.2 M2.5 2.2H6 M2.5 2.2V5.7 M13.5 2.2H10 M13.5 2.2V5.7",
  News: "M8 1L10.1 5.5 15 6 11.3 9.3 12.3 14.2 8 11.7 3.7 14.2 4.7 9.3 1 6 5.9 5.5Z",
};
const ICON_FALLBACK = "M8 2.5A5.5 5.5 0 1 0 8.01 2.5Z";
const Y_PAD_LOW_SHARE = 0.3; // room below the price for downward flags
const Y_PAD_HIGH_SHARE = 0.3; // room above the price for upward flags
const FLAG_GAP_PX = 24; // clearance between a flag and the price line or a neighbouring flag
const FLAG_H = 56;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const CLOSE = "Close (USD)"; // role: close
const EVENT_DATE = "Event date"; // role: event_date
const EVENT_TYPE = "Event type"; // role: event_type
const EVENT_LABEL = "Event"; // role: event_label

// Data: replace this block with your own records, one object per row
// A year of daily closes for a technology share, with quarterly earnings,
// ex-dividend dates, a share split and a product launch; earnings move the
// price on the day, dividends and the (already adjusted) split do not.
const tradingDates: Date[] = [];
for (const cursor = new Date(2024, 0, 2); tradingDates.length < 220; cursor.setDate(cursor.getDate() + 1)) {
  if (cursor.getDay() !== 0 && cursor.getDay() !== 6) tradingDates.push(new Date(cursor));
}
const eventDays = [
  { day: 18, type: "News", label: "New product line", shock: 0.03 },
  { day: 42, type: "Earnings", label: "Q1 earnings beat", shock: 0.06 },
  { day: 63, type: "Dividend", label: "Ex-dividend $0.24", shock: 0 },
  { day: 96, type: "Earnings", label: "Q2 earnings miss", shock: -0.07 },
  { day: 124, type: "Dividend", label: "Ex-dividend $0.24", shock: 0 },
  { day: 152, type: "Stock split", label: "4-for-1 split", shock: 0 },
  { day: 176, type: "Earnings", label: "Q3 earnings beat", shock: 0.05 },
  { day: 208, type: "Earnings", label: "Q4 earnings beat", shock: 0.04 },
];
const events = eventDays.map((e) => ({
  [EVENT_DATE]: tradingDates[e.day],
  [EVENT_TYPE]: e.type,
  [EVENT_LABEL]: e.label,
}));
let seed = 42;
let price = 148;
const data = tradingDates.map((date, i) => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const shock = eventDays.find((e) => e.day === i)?.shock ?? 0;
  price = Math.max(20, price * (1 + 0.0009 + (seed / 0x7fffffff - 0.5) * 0.024 + shock));
  return { [DATE]: date, [CLOSE]: Number(price.toFixed(2)) };
});

// Plot: reads only data and the constants above
const prices = data
  .filter((d) => d[DATE] != null)
  .sort((a, b) => (a[DATE] as Date).getTime() - (b[DATE] as Date).getTime());
const dates = prices.map((d) => d[DATE] as Date);
const closes = prices.map((d) => d[CLOSE] as number | null);
const closeValues = closes.filter((v): v is number => v != null);
const minClose = Math.min(...closeValues);
const maxClose = Math.max(...closeValues);
const closeRange = maxClose - minClose;
const yMin = minClose - closeRange * Y_PAD_LOW_SHARE;
const yMax = maxClose + closeRange * Y_PAD_HIGH_SHARE;

// One tick at the first trading day of every month
const monthStarts = new Set(
  dates.map((d, i) => (i === 0 || d.getMonth() !== dates[i - 1].getMonth() ? i : -1)).filter((i) => i >= 0),
);
const DAY_FORMAT: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
const YEAR_FORMAT: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" };

// Each event snaps to the first trading day on or after its date; flags alternate above and below
const eventTypes = [...new Set(events.map((e) => e[EVENT_TYPE] as string))];
const flags = events
  .filter((e) => e[EVENT_DATE] != null)
  .sort((a, b) => (a[EVENT_DATE] as Date).getTime() - (b[EVENT_DATE] as Date).getTime())
  .map((e) => ({ e, idx: dates.findIndex((d) => d.getTime() >= (e[EVENT_DATE] as Date).getTime()) }))
  .filter(({ idx }) => idx >= 0 && closes[idx] != null)
  .map(({ e, idx }, k) => {
    const type = e[EVENT_TYPE] as string;
    const label = e[EVENT_LABEL] as string;
    const detail = `${type} · ${dates[idx].toLocaleDateString("en-US", DAY_FORMAT)}`;
    return {
      key: `${idx}-${k}`,
      date: dates[idx],
      close: closes[idx] as number,
      up: k % 2 === 0,
      label,
      detail,
      icon: EVENT_ICONS[type] ?? ICON_FALLBACK,
      color: t.palette[1 + eventTypes.indexOf(type)],
      width: 54 + Math.max(label.length * 8.6, detail.length * 7.6),
    };
  });

const TITLE = "stock-event-flags · javascript · muix · anyplot.ai";
const SUBTITLE = `${prices.length} trading days, ${dates[0].toLocaleDateString("en-US", YEAR_FORMAT)} to ${dates[dates.length - 1].toLocaleDateString("en-US", YEAR_FORMAT)} · ${flags.length} events`;
const HEADER_H = 76;
const LEGEND_H = 56;

// Flags: each box sits beyond the price extremes under its own span (above or below, alternating),
// clear of earlier boxes on the same side, with a dashed pole down or up to the close on its day
function EventFlags() {
  const xScale = useXScale() as (v: Date) => number;
  const yScale = useYScale() as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();
  const priceXs = dates.map((d) => xScale(d));
  const priceYs = closes.map((c) => (c == null ? null : yScale(c)));
  const placed: { up: boolean; x0: number; x1: number; y0: number; y1: number }[] = [];
  const layout = flags.map((f) => {
    const x = xScale(f.date);
    const y = yScale(f.close);
    const boxX = Math.min(Math.max(x, left + f.width / 2 + 4), left + width - f.width / 2 - 4) - f.width / 2;
    const spanYs = priceYs.filter((py, i): py is number => py != null && priceXs[i] >= boxX && priceXs[i] <= boxX + f.width);
    let boxY = f.up ? Math.min(y, ...spanYs) - FLAG_GAP_PX - FLAG_H : Math.max(y, ...spanYs) + FLAG_GAP_PX;
    for (const p of placed) {
      const overlaps = p.up === f.up && p.x0 < boxX + f.width && boxX < p.x1 && p.y0 < boxY + FLAG_H && boxY < p.y1;
      if (overlaps) boxY = f.up ? p.y0 - FLAG_GAP_PX - FLAG_H : p.y1 + FLAG_GAP_PX;
    }
    boxY = Math.min(Math.max(boxY, top + 4), top + height - FLAG_H - 4);
    placed.push({ up: f.up, x0: boxX, x1: boxX + f.width, y0: boxY, y1: boxY + FLAG_H });
    return { f, x, y, boxX, boxY };
  });

  return (
    <g>
      {layout.map(({ f, x, y, boxX, boxY }) => {
        const edgeY = f.up ? boxY + FLAG_H : boxY;
        return (
          <g key={f.key}>
            <line x1={x} y1={y} x2={x} y2={edgeY} stroke={f.color} strokeWidth={1.6} strokeDasharray="4 3" />
            <rect x={boxX} y={boxY} width={f.width} height={FLAG_H} rx={7} fill={t.elevatedBg} stroke={f.color} strokeWidth={1.5} />
            <rect x={boxX} y={boxY} width={5} height={FLAG_H} rx={2} fill={f.color} />
            <path
              d={f.icon}
              transform={`translate(${boxX + 16}, ${boxY + FLAG_H / 2 - 8})`}
              fill="none"
              stroke={f.color}
              strokeWidth={2.2}
              strokeLinejoin="round"
            />
            <text x={boxX + 42} y={boxY + 24} fontSize={15} fontWeight={600} fill={t.ink}>
              {f.label}
            </text>
            <text x={boxX + 42} y={boxY + 44} fontSize={14} fill={t.inkSoft}>
              {f.detail}
            </text>
            <circle cx={x} cy={y} r={5} fill={t.pageBg} stroke={f.color} strokeWidth={2.2} />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={W}
        height={H - HEADER_H - LEGEND_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 8, right: 36, bottom: 8, left: 24 }}
        series={[
          {
            id: "close",
            data: closes,
            label: CLOSE,
            color: t.palette[0],
            showMark: false,
            curve: "linear",
            area: true,
            valueFormatter: (v: number | null) => (v == null ? "" : v.toFixed(2)),
          },
        ]}
        xAxis={[
          {
            data: dates,
            scaleType: "point",
            label: DATE,
            height: 64,
            valueFormatter: (d: Date, ctx) =>
              d.toLocaleDateString("en-US", ctx.location === "tick" ? { month: "short" } : DAY_FORMAT),
            tickInterval: (_d: Date, i: number) => monthStarts.has(i),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: CLOSE,
            width: 76,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiLineChart-area": { fillOpacity: 0.12 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <EventFlags />
      </LineChart>
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "14px" }}>
        {eventTypes.map((type, i) => (
          <Box
            key={type}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 14px",
              borderRadius: "999px",
              border: `1px solid ${t.grid}`,
              bgcolor: t.elevatedBg,
            }}
          >
            <svg width={16} height={16} viewBox="0 0 16 16">
              <path d={EVENT_ICONS[type] ?? ICON_FALLBACK} fill="none" stroke={t.palette[1 + i]} strokeWidth={2.2} strokeLinejoin="round" />
            </svg>
            <Typography sx={{ color: t.inkSoft, fontSize: 15, fontWeight: 500 }}>{type}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
