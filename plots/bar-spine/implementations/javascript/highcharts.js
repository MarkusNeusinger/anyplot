// anyplot.ai
// bar-spine: Spine Plot for Two-Variable Proportions
// Library: highcharts 13.1.1 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

const t = window.ANYPLOT_TOKENS;

// Constants
// Retained (good) keeps the brand-green first slot and Churned (bad) the
// semantic-red anchor; any other status takes the Imprint colour of its position.
const STATUS_COLORS = { Retained: t.palette[0], Churned: t.palette[4] };
const MIN_LABEL_SHARE = 3; // segments below this share (%) stay unlabelled

// Columns: set these to your data's column names
const TIER = "Subscription tier"; // role: x_category
const STATUS = "Customer status"; // role: fill_category
const CUSTOMERS = "Customer count"; // role: count

// Data: replace this block with your own records, one object per row
const data = [
  { [TIER]: "Free", [STATUS]: "Retained", [CUSTOMERS]: 2800 },
  { [TIER]: "Free", [STATUS]: "Churned", [CUSTOMERS]: 1200 },
  { [TIER]: "Basic", [STATUS]: "Retained", [CUSTOMERS]: 2000 },
  { [TIER]: "Basic", [STATUS]: "Churned", [CUSTOMERS]: 500 },
  { [TIER]: "Pro", [STATUS]: "Retained", [CUSTOMERS]: 1080 },
  { [TIER]: "Pro", [STATUS]: "Churned", [CUSTOMERS]: 120 },
  { [TIER]: "Enterprise", [STATUS]: "Retained", [CUSTOMERS]: 288 },
  { [TIER]: "Enterprise", [STATUS]: "Churned", [CUSTOMERS]: 12 },
];

// Plot: reads only data and the constants above
// Highcharts' core bundle has no variable-width column series (that lives in
// the variwide module, which isn't loaded). The spine plot is a percent-
// stacked, fully opaque area chart on a linear x-axis instead: each tier spans
// its cumulative customer count, with one point at each end holding the same
// count, so every segment is flat across the tier and steps at the boundary.
// A tiny epsilon keeps boundary x-values strictly increasing (duplicates
// would double-count in Highcharts' per-x stacking sum) while staying far
// below one screen pixel.
const tiers = [...new Set(data.map((d) => d[TIER]))];
const statuses = [...new Set(data.map((d) => d[STATUS]))];
const totalWidth = data.reduce((sum, d) => sum + (d[CUSTOMERS] ?? 0), 0);
const eps = totalWidth * 1e-6;

let cursor = 0;
const bars = tiers.map((tier) => {
  const rows = data.filter((d) => d[TIER] === tier);
  const total = rows.reduce((sum, d) => sum + (d[CUSTOMERS] ?? 0), 0);
  const bar = { tier, rows, total, x0: cursor, x1: cursor + total, center: cursor + total / 2 };
  cursor += total;
  return bar;
});

// Highcharts stacks the first series on top, so the last status sits on the
// baseline.
const areaSeries = statuses.map((status, i) => {
  const color = STATUS_COLORS[status] ?? t.palette[i];
  return {
    type: "area",
    name: status,
    color,
    data: bars.flatMap((bar, j) => {
      const y = bar.rows.find((d) => d[STATUS] === status)?.[CUSTOMERS] ?? null;
      return [
        { x: j === 0 ? bar.x0 : bar.x0 + eps, y },
        { x: j === bars.length - 1 ? bar.x1 : bar.x1 - eps, y },
      ];
    }),
  };
});

// Percentage labels sit at the vertical middle of their own segment: a
// label-only series places them in data units, centred on each band.
const labelPoints = bars.flatMap((bar) => {
  let below = 0;
  return [...statuses].reverse().flatMap((status) => {
    const value = bar.rows.find((d) => d[STATUS] === status)?.[CUSTOMERS] ?? 0;
    const share = (100 * value) / bar.total;
    const point = { x: bar.center, y: below + share / 2, label: `${Math.round(share)}%` };
    below += share;
    return share >= MIN_LABEL_SHARE ? [point] : [];
  });
});

const titleText =
  "SaaS Subscription Churn by Tier · bar-spine · javascript · highcharts · anyplot.ai";
const titleFontSize = Math.max(18, Math.round(30 * Math.min(1, 67 / titleText.length)));

Highcharts.chart("container", {
  palette: { colorScheme: t.theme },
  chart: {
    backgroundColor: "transparent",
    animation: false,
    spacingRight: 28, // room for the last tier's label under a narrow bar
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: titleText,
    style: { color: t.ink, fontSize: `${titleFontSize}px`, fontWeight: "600" },
  },
  xAxis: {
    min: 0,
    max: totalWidth,
    title: {
      text: `${TIER} — width ∝ ${CUSTOMERS.toLowerCase()}`,
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    tickPositions: bars.map((bar) => bar.center),
    gridLineWidth: 0,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    tickLength: 6,
    // A page-coloured hairline marks where two adjacent tiers meet, also
    // where their segments share a height.
    plotLines: bars.slice(1).map((bar) => ({
      value: bar.x0,
      color: t.pageBg,
      width: 2,
      zIndex: 4,
    })),
    labels: {
      formatter: function () {
        return bars.find((bar) => bar.center === this.value)?.tier ?? "";
      },
      style: { color: t.inkSoft, fontSize: "14px" },
    },
  },
  yAxis: {
    tickInterval: 20,
    title: {
      text: `Share within ${TIER.toLowerCase()} (%)`,
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      format: "{value}%",
      style: { color: t.inkSoft, fontSize: "14px" },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolRadius: 2,
    itemDistance: 24,
    margin: 20,
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    borderWidth: 1,
    borderRadius: 6,
    padding: 12,
  },
  tooltip: {
    shared: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
    formatter: function () {
      const bar = bars.find((b) => this.x >= b.x0 && this.x <= b.x1);
      const lines = this.points.map(
        (p) => `${p.series.name}: ${p.percentage.toFixed(1)}% (${p.y.toLocaleString("en-US")})`
      );
      return [`<b>${bar.tier}</b>`, ...lines].join("<br/>");
    },
  },
  plotOptions: {
    series: { animation: false },
    area: {
      stacking: "percent",
      fillOpacity: 1,
      lineWidth: 1,
      lineColor: t.pageBg,
      marker: { enabled: false },
      states: { hover: { enabled: false } },
    },
  },
  series: [
    ...areaSeries,
    {
      type: "scatter",
      name: "Share labels",
      data: labelPoints,
      showInLegend: false,
      enableMouseTracking: false,
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        align: "center",
        verticalAlign: "middle",
        format: "{point.label}",
        style: {
          color: "#FFFFFF",
          fontSize: "14px",
          fontWeight: "600",
          textOutline: "1px rgba(26, 26, 23, 0.55)",
        },
      },
    },
  ],
});
