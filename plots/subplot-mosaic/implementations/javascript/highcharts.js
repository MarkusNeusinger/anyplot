// anyplot.ai
// subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
// "muted" semantic anchor (other/rest) — not in ANYPLOT_TOKENS, so derive it
// the same way the harness derives inkSoft/grid (theme-adaptive, off ink).
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic, retail-operations scenario) -----------
const weeks = Array.from({ length: 12 }, (_, i) => `Wk ${i + 1}`);
const revenueNorth = [82, 85, 88, 84, 91, 95, 93, 98, 101, 99, 104, 108];
const revenueSouth = [55, 58, 57, 60, 62, 59, 64, 66, 63, 68, 67, 70];
const revenueWest = [40, 44, 42, 47, 45, 50, 48, 52, 55, 51, 56, 58];

const categories = ["Electronics", "Apparel", "Home Goods", "Sporting Goods", "Beauty"];
const unitsSold = [1240, 2860, 1975, 1330, 2100];

const hours = ["9a", "10a", "11a", "12p", "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p"];
const footTraffic = [120, 180, 240, 310, 360, 340, 300, 280, 260, 320, 410, 260];

const metrics = [
  { title: "Conversion Rate", actual: 3.8, target: 4.5, suffix: "%", good: false },
  { title: "Avg. Basket Size", actual: 61.5, target: 58.0, suffix: "$", good: true },
  { title: "Return Rate", actual: 2.1, target: 3.0, suffix: "%", good: true },
];

// --- Layout (mosaic grid built as DOM; each cell mounts its own Highcharts
//     instance, exactly like matplotlib's ASCII subplot_mosaic strings but
//     expressed as CSS grid-template-areas — "." marks a deliberate gap) -----
const root = document.getElementById("container");

const header = document.createElement("div");
header.style.cssText = `padding:20px 28px 6px; font-size:22px; font-weight:600; color:${t.ink}; font-family:inherit;`;
header.textContent = "subplot-mosaic · javascript · highcharts · anyplot.ai";
root.appendChild(header);

const mosaic = document.createElement("div");
mosaic.style.cssText = [
  "display:grid",
  "grid-template-columns:repeat(6, 1fr)",
  "grid-template-rows:1.35fr 1.35fr 1.1fr 0.85fr",
  `grid-template-areas:` +
    `"overview overview overview overview overview overview" ` +
    `"overview overview overview overview overview overview" ` +
    `"detail1 detail1 detail1 detail2 detail2 detail2" ` +
    `"metric0 metric0 . metric1 metric1 metric2"`,
  "gap:18px",
  "margin:8px 28px 26px",
  "height:calc(100% - 66px)",
].join(";");
root.appendChild(mosaic);

function makeCell(area, id) {
  const card = document.createElement("div");
  card.style.cssText = `grid-area:${area}; background:${t.elevatedBg}; border-radius:12px; padding:14px 18px; min-width:0; min-height:0;`;
  const mount = document.createElement("div");
  mount.id = id;
  mount.style.cssText = "width:100%; height:100%;";
  card.appendChild(mount);
  mosaic.appendChild(card);
  return mount;
}

const overviewMount = makeCell("overview", "cell-overview");
const detail1Mount = makeCell("detail1", "cell-detail1");
const detail2Mount = makeCell("detail2", "cell-detail2");
const metricMounts = metrics.map((m, i) => makeCell(`metric${i}`, `cell-metric${i}`));

// Chart instances created below, so their sizes can be reflowed once the grid
// has actually resolved row heights (see the reflow block at the bottom of
// this file — a fresh mount's percentage height reads back as 0 the instant
// Highcharts.chart() runs, so every panel would otherwise fall back to
// Highcharts' default 400px and clip most of the data out of view).
const panelCharts = [];

// --- Overview: wide dominant panel, weekly revenue trend by region ---------
panelCharts.push(Highcharts.chart(overviewMount.id, {
  chart: { type: "spline", backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "Weekly Revenue by Region", align: "left", style: { color: t.ink, fontSize: "18px", fontWeight: "600" } },
  xAxis: {
    categories: weeks,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "13px" } },
  },
  yAxis: {
    title: { text: "Revenue ($k)", style: { color: t.inkSoft, fontSize: "14px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "13px" } },
  },
  legend: { itemStyle: { color: t.inkSoft, fontSize: "13px" }, itemHoverStyle: { color: t.ink } },
  plotOptions: { series: { animation: false, lineWidth: 3, marker: { radius: 4 } } },
  series: [
    { name: "North", data: revenueNorth },
    { name: "South", data: revenueSouth },
    { name: "West", data: revenueWest },
  ],
}));

// --- Detail 1: medium panel, units sold by category -------------------------
panelCharts.push(Highcharts.chart(detail1Mount.id, {
  chart: { type: "column", backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "Units Sold by Category", align: "left", style: { color: t.ink, fontSize: "16px", fontWeight: "600" } },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "12px" } },
  },
  yAxis: {
    title: { text: null },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "12px" } },
  },
  legend: { enabled: false },
  plotOptions: { series: { animation: false }, column: { borderWidth: 0 } },
  series: [{ name: "Units", data: unitsSold, colorByPoint: true }],
}));

// --- Detail 2: medium panel, hourly foot traffic ----------------------------
panelCharts.push(Highcharts.chart(detail2Mount.id, {
  chart: { type: "area", backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "Foot Traffic by Hour", align: "left", style: { color: t.ink, fontSize: "16px", fontWeight: "600" } },
  xAxis: {
    categories: hours,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "12px" } },
  },
  yAxis: {
    title: { text: null },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "12px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    area: { fillOpacity: 0.18, lineWidth: 2.5, marker: { enabled: false } },
  },
  series: [{ name: "Visitors", data: footTraffic, color: t.palette[0] }],
}));

// --- Metrics row: three small KPI panels, actual vs. target ----------------
metrics.forEach((m, i) => {
  const statusColor = m.good ? t.palette[0] : t.amber;
  const format = (v) => (m.suffix === "$" ? `$${v.toFixed(2)}` : `${v.toFixed(1)}%`);
  panelCharts.push(Highcharts.chart(metricMounts[i].id, {
    chart: { type: "bar", backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
    credits: { enabled: false },
    title: { text: m.title, align: "left", style: { color: t.ink, fontSize: "14px", fontWeight: "600" } },
    xAxis: {
      categories: ["Actual", "Target"],
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      labels: { style: { color: t.inkSoft, fontSize: "12px" } },
    },
    yAxis: { title: { text: null }, gridLineColor: t.grid, labels: { enabled: false } },
    legend: { enabled: false },
    plotOptions: {
      series: {
        animation: false,
        dataLabels: {
          enabled: true,
          style: { color: t.ink, fontSize: "12px", fontWeight: "600", textOutline: "none" },
          formatter() {
            return format(this.y);
          },
        },
      },
      bar: { borderWidth: 0, pointPadding: 0.15, groupPadding: 0.1 },
    },
    series: [
      {
        data: [
          { y: m.actual, color: statusColor },
          { y: m.target, color: MUTED },
        ],
      },
    ],
  }));
});

// A brand-new mount's percentage height resolves to 0 the instant
// Highcharts.chart() reads it (CSS Grid rows haven't settled a layout pass
// yet), so every panel above was created at Highcharts' 400px fallback.
// chart.reflow() alone doesn't fix this — it still trusts the container's
// computed CSS height, which stays wrong for a percentage-height mount in
// some Chromium timing cases — so set each chart's real pixel size directly
// from its mount's post-layout bounding box once two animation frames have
// let the grid settle, then signal the harness explicitly.
const panelMounts = [overviewMount, detail1Mount, detail2Mount, ...metricMounts];
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    panelCharts.forEach((chart, i) => {
      const rect = panelMounts[i].getBoundingClientRect();
      chart.setSize(rect.width, rect.height, false);
    });
    window.__anyplotReady = true;
  });
});
