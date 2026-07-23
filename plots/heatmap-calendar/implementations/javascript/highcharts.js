// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 82/100 | Created: 2026-07-23

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily website visits for 2023, with a weekly seasonality (weekday traffic
// higher than weekend) plus a data-collection outage in August (missing dates).
let lcgState = 42;
function nextRandom() {
  lcgState = (lcgState * 1103515245 + 12345) % 2147483648;
  return lcgState / 2147483648;
}

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const START = Date.UTC(2023, 0, 1); // Jan 1 2023 — a Sunday
const DAY_MS = 24 * 60 * 60 * 1000;
const TOTAL_DAYS = 365;
// Monday-indexed weekday (0=Mon..6=Sun) of the first day, so weeks align to
// Monday-start columns matching the Mon-Sun y-axis labels.
const firstMondayIndex = (new Date(START).getUTCDay() + 6) % 7;

// The core Highcharts bundle has no heatmap/colorAxis-mapping module (see
// prompts/library/highcharts.md), so each cell's fill is computed by hand —
// a linear interpolation across the two-stop imprint_seq gradient.
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);
function valueToColor(value, min, max) {
  const frac = max > min ? (value - min) / (max - min) : 0;
  const rgb = seqLow.map((c, i) => Math.round(c + (seqHigh[i] - c) * frac));
  return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
}

const cells = [];
const missingCells = [];
let minVisits = Infinity;
let maxVisits = -Infinity;

for (let i = 0; i < TOTAL_DAYS; i++) {
  const date = new Date(START + i * DAY_MS);
  const mondayIndex = (date.getUTCDay() + 6) % 7; // 0=Mon .. 6=Sun
  const weekIndex = Math.floor((i + firstMondayIndex) / 7);

  // Simulated data-collection outage: 12 days in mid-August with no records.
  const isOutage = i >= 215 && i < 227;

  if (isOutage) {
    missingCells.push({ x: weekIndex, y: mondayIndex });
    continue;
  }

  const weekdayBoost = mondayIndex < 5 ? 1.3 : 0.6; // weekdays busier than weekends
  const seasonal = 1 + 0.35 * Math.sin((i / TOTAL_DAYS) * 2 * Math.PI + 1.2);
  const noise = 0.75 + nextRandom() * 0.5;
  const visits = Math.round(220 * weekdayBoost * seasonal * noise);

  minVisits = Math.min(minVisits, visits);
  maxVisits = Math.max(maxVisits, visits);
  cells.push({ x: weekIndex, y: mondayIndex, value: visits, date: date.toISOString().slice(0, 10) });
}
cells.forEach((c) => {
  c.color = valueToColor(c.value, minVisits, maxVisits);
});

const weekCount = Math.floor((TOTAL_DAYS - 1 + firstMondayIndex) / 7) + 1;

// Tick position (week index) for the first day of each month, for the top axis.
const monthTicks = [];
for (let m = 0; m < 12; m++) {
  const first = Date.UTC(2023, m, 1);
  const daysSinceStart = Math.round((first - START) / DAY_MS);
  const mondayIndex = (new Date(first).getUTCDay() + 6) % 7;
  const weekIndex = Math.floor((daysSinceStart + firstMondayIndex) / 7);
  monthTicks.push({ value: weekIndex, label: MONTH_LABELS[m] });
}

// Discrete swatches standing in for a continuous color-scale legend (no
// colorAxis legend without the heatmap module — see comment above).
const LEGEND_STEPS = 4;
const legendBins = Array.from({ length: LEGEND_STEPS }, (_, i) => {
  const value = minVisits + ((maxVisits - minVisits) * i) / (LEGEND_STEPS - 1);
  return { value: Math.round(value), color: valueToColor(value, minVisits, maxVisits) };
});

// --- Chart -------------------------------------------------------------------
const title = "heatmap-calendar · javascript · highcharts · anyplot.ai";

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginLeft: 60,
    marginRight: 40,
    marginTop: 130,
    marginBottom: 90,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: title,
    align: "left",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Daily website visits, 2023 — outage gap in August shown as empty cells",
    align: "left",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.7,
    max: weekCount - 0.3,
    startOnTick: false,
    endOnTick: false,
    lineWidth: 0,
    gridLineWidth: 0,
    tickWidth: 0,
    opposite: true,
    tickPositions: monthTicks.map((m) => m.value),
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        const tick = monthTicks.find((m) => m.value === this.value);
        return tick ? tick.label : "";
      },
    },
  },
  yAxis: {
    title: { text: null },
    min: -1.5,
    max: 7.5,
    startOnTick: false,
    endOnTick: false,
    tickPositions: [0, 1, 2, 3, 4, 5, 6],
    reversed: true,
    lineWidth: 0,
    gridLineWidth: 0,
    tickWidth: 0,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return WEEKDAY_LABELS[this.value] ?? "";
      },
    },
  },
  legend: {
    enabled: true,
    layout: "horizontal",
    align: "left",
    verticalAlign: "bottom",
    y: 10,
    itemDistance: 24,
    itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "normal" },
    itemHoverStyle: { color: t.ink },
    title: {
      text: "Visits / day",
      style: { color: t.inkSoft, fontSize: "14px" },
    },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, enableMouseTracking: false },
    scatter: {
      marker: { symbol: "square", radius: 12, states: { hover: { enabled: false } } },
    },
  },
  series: [
    {
      name: "Visits",
      data: cells,
      showInLegend: false,
    },
    {
      name: "No data",
      data: missingCells,
      color: t.grid,
      showInLegend: true,
    },
    ...legendBins.map((bin) => ({
      name: `${bin.value}`,
      color: bin.color,
      data: [],
      showInLegend: true,
      marker: { symbol: "square", radius: 12 },
    })),
  ],
});
