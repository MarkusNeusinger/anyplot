// anyplot.ai
// subplot-grid: Subplot Grid Layout
// Library: Highcharts 12.6.0 | Node 22.23.2
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Fixed-seed LCG (no seeded RNG in the browser) ----------------------------------
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
const rand = lcg(20260909);
function randNormal(mean, sd) {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return mean + sd * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Panel 1 data: monthly website visits, a seasonal trend (line) -----------------
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const seasonal = [1, 0, -1, -2, -2, -1, 1, 2, 1, 0, 1, 3];
const visitsThousands = seasonal.map((s, i) => Math.round(48 + s * 4 + i * 1.4 + randNormal(0, 1.6)));

// --- Panel 2 data: quarterly revenue by product category (bar) ---------------------
const categories = ["Electronics", "Apparel", "Home & Garden", "Sporting Goods", "Books"];
const revenueThousands = [312, 248, 196, 141, 87];

// --- Panel 3 data: product price vs. customer rating (scatter) ---------------------
const nProducts = 48;
const priceUsd = [];
const rating = [];
for (let i = 0; i < nProducts; i++) {
  const price = 8 + 290 * rand();
  const r = Math.min(5, Math.max(1, 3.1 + 0.0055 * price + randNormal(0, 0.45)));
  priceUsd.push(Math.round(price * 100) / 100);
  rating.push(Math.round(r * 10) / 10);
}

// --- Panel 4 data: order value distribution, right-skewed (histogram via column) ---
const nOrders = 600;
const orderValues = [];
for (let i = 0; i < nOrders; i++) {
  orderValues.push(Math.exp(randNormal(3.6, 0.55)));
}
const binWidth = 20;
const binCount = 12;
const binCounts = new Array(binCount).fill(0);
orderValues.forEach((v) => {
  const idx = Math.min(binCount - 1, Math.floor(v / binWidth));
  binCounts[idx] += 1;
});
const binLabels = binCounts.map((_, i) => `${i * binWidth}-${(i + 1) * binWidth}`);

// --- Shared chart chrome for every panel --------------------------------------------
function baseOptions(type, panelTitle, xTitle, yTitle) {
  return {
    chart: { type, backgroundColor: "transparent", animation: false,
             spacing: [10, 16, 10, 10], style: { fontFamily: "inherit" } },
    credits: { enabled: false },
    colors: t.palette,
    title: { text: panelTitle, style: { color: t.ink, fontSize: "16px", fontWeight: "600" }, margin: 12 },
    xAxis: { title: { text: xTitle, style: { color: t.inkSoft, fontSize: "13px" } },
             lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineColor: t.grid,
             labels: { style: { color: t.inkSoft, fontSize: "12px" } } },
    yAxis: { title: { text: yTitle, style: { color: t.inkSoft, fontSize: "13px" } },
             gridLineColor: t.grid, lineColor: t.inkSoft, tickColor: t.inkSoft, tickWidth: 1,
             labels: { style: { color: t.inkSoft, fontSize: "12px" } } },
    legend: { enabled: false },
    plotOptions: { series: { animation: false } },
  };
}

// Panel 1 — Monthly Website Visits (line): a time series with independent axes -------
const panel1 = baseOptions("spline", "Monthly Website Visits", "Month", "Visits (thousands)");
panel1.xAxis.categories = months;
panel1.tooltip = { formatter: function () { return `${this.x}: ${this.y}k visits`; } };
panel1.series = [{
  name: "Visits",
  data: visitsThousands,
  color: t.palette[0],
  lineWidth: 2.5,
  marker: { radius: 4, fillColor: t.palette[0], lineColor: t.pageBg, lineWidth: 1 },
}];

// Panel 2 — Revenue by Product Category (bar): categorical comparison ---------------
const panel2 = baseOptions("bar", "Revenue by Category", "Revenue (thousand $)", null);
panel2.xAxis.categories = categories;
panel2.xAxis.title = null;
panel2.yAxis.gridLineColor = t.grid;
panel2.tooltip = { formatter: function () { return `${this.point.category}: $${this.y}k`; } };
panel2.series = [{ name: "Revenue", data: revenueThousands, colorByPoint: true }];

// Panel 3 — Price vs. Customer Rating (scatter): correlation between two variables ---
const panel3 = baseOptions("scatter", "Price vs. Customer Rating", "Price ($)", "Rating (1-5)");
panel3.tooltip = {
  formatter: function () { return `Price: $${this.x.toFixed(2)}<br/>Rating: ${this.y.toFixed(1)}`; },
};
panel3.series = [{
  name: "Products",
  data: priceUsd.map((p, i) => ({ x: p, y: rating[i] })),
  marker: { symbol: "circle", radius: 4.5, fillColor: t.palette[0], lineColor: t.pageBg, lineWidth: 1 },
}];

// Panel 4 — Order Value Distribution (histogram via binned column) -------------------
const panel4 = baseOptions("column", "Order Value Distribution", "Order value ($)", "Number of orders");
panel4.xAxis.categories = binLabels;
panel4.xAxis.labels.rotation = -45;
panel4.plotOptions.column = { pointPadding: 0, groupPadding: 0.04, borderWidth: 0 };
panel4.tooltip = { formatter: function () { return `$${this.point.category}: ${this.y} orders`; } };
panel4.series = [{ name: "Orders", data: binCounts, color: t.palette[0] }];

// --- Layout: shared header + a configurable 2x2 grid of independently-mounted panels ---
const root = document.getElementById("container");

const header = document.createElement("div");
header.style.cssText = `padding:18px 24px 4px; font-size:22px; font-weight:600; color:${t.ink}; font-family:inherit;`;
header.textContent = "subplot-grid · javascript · highcharts · anyplot.ai";
root.appendChild(header);

const gridRows = 2;
const gridCols = 2;
const grid = document.createElement("div");
grid.style.cssText =
  `display:grid; grid-template-columns:repeat(${gridCols}, 1fr); grid-template-rows:repeat(${gridRows}, 1fr); ` +
  "gap:16px; margin:4px 20px 20px; height:calc(100% - 62px);";
root.appendChild(grid);

const panelIds = ["panel-visits", "panel-revenue", "panel-price-rating", "panel-order-dist"];
panelIds.forEach((id) => {
  const cell = document.createElement("div");
  cell.id = id;
  grid.appendChild(cell);
});

Highcharts.chart("panel-visits", panel1);
Highcharts.chart("panel-revenue", panel2);
Highcharts.chart("panel-price-rating", panel3);
Highcharts.chart("panel-order-dist", panel4);
